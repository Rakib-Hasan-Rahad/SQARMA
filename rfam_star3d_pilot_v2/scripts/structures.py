"""Phase 2a: download mmCIF + RNAcentral records for shortlisted structure links and extract
per-chain evidence (entity, chain IDs, deposited sequence, observed residues, modifications,
source organism records, engineered differences, ligands, method, resolution, citation).

Outputs
  review/evidence/<PDB>_<chain>.json        raw extracted evidence per structure link
  mappings/structure_sequence_map.tsv       one row per (family, row, PDB, chain) link + mapping-only chains
"""
import csv
import json
import os
import re
import sys
from collections import defaultdict

import hashlib

import gemmi
import yaml

sys.path.insert(0, os.path.dirname(__file__))
import fetch  # noqa: E402
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
STAR3D_ATOMS = ["C3'", "C4'", "C5'", "O3'", "O5'", "P"]
STD = {"A", "C", "G", "U"}


def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) is None or r.get(k) == "" else r[k]) for k in fields})


def table(block, cat, cols):
    """Return list of dicts for mmCIF category (empty list if absent). '?'/'.' -> None."""
    try:
        t = block.find(cat, cols)
    except Exception:
        return []
    out = []
    for row in t:
        d = {}
        for i, c in enumerate(cols):
            v = row[i] if row.has(i) else "?"
            d[c] = None if v in ("?", ".") else gemmi.cif.as_string(v)
        out.append(d)
    return out


def opt_table(block, cat, cols):
    """Like table() but tolerant of missing optional columns."""
    present = [c for c in cols if block.find_value(cat + c) is not None or block.find_loop(cat + c)]
    if not present:
        return []
    return table(block, cat, present)


def get_mmcif(pdb):
    return fetch.fetch(CFG["sources"]["rcsb_mmcif"].format(pdb=pdb), f"structures/mmcif/{pdb}.cif.gz",
                       f"RCSB mmCIF for {pdb} (source coordinates/metadata)")


def get_rnacentral(urs):
    url = f"https://rnacentral.org/api/v1/rna/{urs}.json"
    return fetch.fetch_json(url, f"rnacentral/{urs}.json", f"RNAcentral record for {urs} (row origin)")


def get_rnacentral_xrefs(urs, taxid):
    url = f"https://rnacentral.org/api/v1/rna/{urs}/xrefs/{taxid}.json?page_size=200"
    try:
        return fetch.fetch_json(url, f"rnacentral/{urs}_{taxid}_xrefs.json",
                                f"RNAcentral cross-references for {urs}_{taxid} (row provenance)")
    except RuntimeError as e:
        return {"error": str(e)}


def extract_entry(pdb, path):
    doc = gemmi.cif.read(path)
    b = doc.sole_block()
    ev = {"pdb_id": pdb}
    ev["exptl_method"] = [r["method"] for r in table(b, "_exptl.", ["method"])]
    res = [r.get("ls_d_res_high") for r in opt_table(b, "_refine.", ["ls_d_res_high"])]
    res += [r.get("resolution") for r in opt_table(b, "_em_3d_reconstruction.", ["resolution"])]
    ev["resolution"] = next((float(x) for x in res if x), None)
    rev = opt_table(b, "_pdbx_audit_revision_history.", ["ordinal", "revision_date"])
    ev["initial_release_date"] = rev[0]["revision_date"] if rev else None
    ev["title"] = b.find_value("_struct.title") and gemmi.cif.as_string(b.find_value("_struct.title"))
    ev["citations"] = opt_table(b, "_citation.", ["id", "title", "journal_abbrev", "year",
                                                   "pdbx_database_id_PubMed", "pdbx_database_id_DOI"])
    ev["entities"] = opt_table(b, "_entity.", ["id", "type", "src_method", "pdbx_description",
                                                "pdbx_mutation", "pdbx_fragment", "details"])
    ev["entity_poly"] = opt_table(b, "_entity_poly.", ["entity_id", "type", "nstd_monomer",
                                                       "pdbx_seq_one_letter_code", "pdbx_seq_one_letter_code_can",
                                                       "pdbx_strand_id"])
    ev["src_gen"] = opt_table(b, "_entity_src_gen.", ["entity_id", "pdbx_gene_src_scientific_name",
                                                       "pdbx_gene_src_ncbi_taxonomy_id",
                                                       "pdbx_host_org_scientific_name", "pdbx_host_org_ncbi_taxonomy_id",
                                                       "pdbx_seq_type", "pdbx_beg_seq_num", "pdbx_end_seq_num"])
    ev["src_nat"] = opt_table(b, "_entity_src_nat.", ["entity_id", "pdbx_organism_scientific",
                                                       "pdbx_ncbi_taxonomy_id", "details"])
    ev["src_syn"] = opt_table(b, "_pdbx_entity_src_syn.", ["entity_id", "organism_scientific",
                                                            "ncbi_taxonomy_id", "details"])
    ev["struct_ref"] = opt_table(b, "_struct_ref.", ["id", "entity_id", "db_name", "db_code",
                                                      "pdbx_db_accession", "pdbx_seq_one_letter_code",
                                                      "pdbx_align_begin"])
    ev["struct_ref_seq"] = opt_table(b, "_struct_ref_seq.", ["align_id", "ref_id", "pdbx_strand_id",
                                                              "seq_align_beg", "seq_align_end", "db_align_beg",
                                                              "db_align_end", "pdbx_auth_seq_align_beg",
                                                              "pdbx_auth_seq_align_end"])
    ev["struct_ref_seq_dif"] = opt_table(b, "_struct_ref_seq_dif.", ["align_id", "pdbx_pdb_strand_id", "mon_id",
                                                                      "seq_num", "pdbx_auth_seq_num",
                                                                      "db_mon_id", "pdbx_seq_db_seq_num", "details"])
    ev["mod_residues"] = opt_table(b, "_pdbx_struct_mod_residue.", ["label_asym_id", "label_seq_id",
                                                                     "auth_asym_id", "auth_seq_id",
                                                                     "label_comp_id", "parent_comp_id", "details"])
    ev["chem_comp_parent"] = {r["id"]: r.get("mon_nstd_parent_comp_id")
                              for r in opt_table(b, "_chem_comp.", ["id", "type", "mon_nstd_parent_comp_id"])}
    ev["nonpoly"] = opt_table(b, "_pdbx_entity_nonpoly.", ["entity_id", "name", "comp_id"])
    ev["scheme"] = opt_table(b, "_pdbx_poly_seq_scheme.", ["asym_id", "entity_id", "seq_id", "mon_id",
                                                            "pdb_seq_num", "auth_seq_num", "pdb_mon_id",
                                                            "pdb_strand_id", "pdb_ins_code", "hetero"])
    ev["models"] = None
    return ev, b


def observed_atoms(path):
    """label (asym, seq_id) -> set(atom names) from the FIRST model, all altlocs merged."""
    st = gemmi.read_structure(path)
    st.setup_entities()
    out = {}
    model = st[0]
    for ch in model:
        for res in ch:
            if res.label_seq is None:
                continue
            key = (res.subchain, res.label_seq)
            out.setdefault(key, set()).update(a.name for a in res)
    return out, len(st), st


def pick_chain(ev, chain, row_seq):
    """Resolve the GR chain token to (label_asym_id, auth_chain, entity) using explicit IDs.
    Rfam chain tokens are author chain IDs; label match is recorded as an alternative."""
    by_auth = defaultdict(set)
    by_label = defaultdict(set)
    for s in ev["scheme"]:
        by_auth[s["pdb_strand_id"]].add((s["asym_id"], s["entity_id"]))
        by_label[s["asym_id"]].add((s["pdb_strand_id"], s["entity_id"]))
    cands = []
    for asym, ent in sorted(by_auth.get(chain, [])):
        cands.append(("auth", asym, chain, ent))
    for auth, ent in sorted(by_label.get(chain, [])):
        if ("auth", chain, auth, ent) not in cands and auth != chain:
            cands.append(("label", chain, auth, ent))
    return cands


def norm(s):
    return s.upper().replace("T", "U")


def build_link(fam, srow, ev, obs, nmodels, b):
    pdb, chain = srow["pdb_id"], srow["chain"]
    row_seq = srow["ungapped_row"]
    cands = pick_chain(ev, chain, row_seq)
    out = dict(rfam_acc=fam, row_name=srow["row_name"], gr_feature=srow["gr_feature"], pdb_id=pdb,
               chain_token=chain, urs=srow["urs"], row_taxid=srow["row_taxid"], row_start=srow["row_start"],
               row_end=srow["row_end"], row_len=srow["row_len"], row_seq_hash=srow["row_seq_hash"],
               in_mapping_file=srow["in_mapping_file"],
               n_models=nmodels)
    out["chain_candidates"] = ";".join(f"{k}:{a}/{au}/ent{e}" for k, a, au, e in cands)
    if not cands:
        out.update(link_status="failed", link_note="chain token not found as auth or label chain")
        return out, None
    auth_cands = [c for c in cands if c[0] == "auth"]
    kind, asym, auth, ent = (auth_cands or cands)[0]
    out.update(id_scheme_matched=kind, label_asym_id=asym, auth_asym_id=auth, entity_id=ent)
    ep = next((e for e in ev["entity_poly"] if e["entity_id"] == ent), {})
    out["entity_poly_type"] = ep.get("type")
    scheme = [s for s in ev["scheme"] if s["asym_id"] == asym]
    mons = [s["mon_id"] for s in scheme]
    can = re.sub(r"\s", "", ep.get("pdbx_seq_one_letter_code_can") or "")
    out["deposited_len"] = len(scheme)
    out["deposited_seq_can"] = can
    # modified residues: parent mapping, retain identity. Sources in priority order:
    #   1 _pdbx_struct_mod_residue.parent_comp_id  2 _chem_comp.mon_nstd_parent_comp_id
    #   3 wwPDB per-residue canonical code in _entity_poly.pdbx_seq_one_letter_code_can (only if
    #     its length equals the chain's residue count, so positions align one-to-one)
    parent = {}
    for m in ev["mod_residues"]:
        if m.get("label_asym_id") == asym and m.get("parent_comp_id"):
            parent[int(m["label_seq_id"])] = (m["parent_comp_id"], "pdbx_struct_mod_residue")
    can_ok = len(can) == len(scheme)
    mods, unknown, letters = [], [], []
    for i, s in enumerate(scheme):
        mon, sid = s["mon_id"], int(s["seq_id"])
        if mon in STD:
            letters.append(mon)
            continue
        par, how = parent.get(sid, (None, None))
        if par is None and ev["chem_comp_parent"].get(mon):
            par, how = ev["chem_comp_parent"][mon], "chem_comp"
        if par is None and can_ok and can[i].upper() in STD:
            par, how = can[i].upper(), "entity_poly_can"
        if par not in STD:
            unknown.append(f"{sid}:{mon}")
            letters.append("X")
        else:
            letters.append(par)
        mods.append(f"{sid}:{mon}->{par}[{how}]")
    out["modified_residues"] = ";".join(mods)
    out["unknown_or_unmapped_residues"] = ";".join(unknown)
    seq_par = "".join(letters)
    out["deposited_seq_parent_mapped"] = seq_par
    out["can_vs_parent_mapped_identical"] = "yes" if norm(can) == seq_par else "no"
    # locate row interval in deposited sequence
    rs, re_ = int(srow["row_start"]), int(srow["row_end"])
    nrow = norm(row_seq)
    match_kind, offset = None, None
    if rs <= re_ and re_ <= len(seq_par) and seq_par[rs - 1:re_] == nrow:
        match_kind, offset = "exact_at_row_coordinates", rs - 1
    else:
        hits = [m.start() for m in re.finditer(f"(?={re.escape(nrow)})", seq_par)]
        if len(hits) == 1:
            match_kind, offset = "exact_elsewhere", hits[0]
        elif len(hits) > 1:
            match_kind = "ambiguous_multiple_positions"
        else:
            match_kind = "no_exact_match"
    out["sequence_match"] = match_kind
    out["row_offset_in_deposited"] = offset
    if offset is not None:
        sub = scheme[offset:offset + len(nrow)]
        out["family_label_seq_start"] = sub[0]["seq_id"]
        out["family_label_seq_end"] = sub[-1]["seq_id"]
        out["family_auth_start"] = (sub[0]["auth_seq_num"] or "?") + (sub[0]["pdb_ins_code"] or "")
        out["family_auth_end"] = (sub[-1]["auth_seq_num"] or "?") + (sub[-1]["pdb_ins_code"] or "")
        observed = [s for s in sub if s["auth_seq_num"] is not None]
        bb_full = [s for s in sub if set(STAR3D_ATOMS) <= obs.get((asym, int(s["seq_id"])), set())]
        anyatom = [s for s in sub if obs.get((asym, int(s["seq_id"])))]
        out["row_residues_observed_scheme"] = len(observed)
        out["row_residues_with_any_atom"] = len(anyatom)
        out["row_residues_with_all_star3d_backbone_atoms"] = len(bb_full)
        out["observed_fraction"] = round(len(anyatom) / len(nrow), 3)
        out["missing_residue_seq_ids"] = ",".join(s["seq_id"] for s in sub if not obs.get((asym, int(s["seq_id"]))))
        out["incomplete_backbone_seq_ids"] = ",".join(
            s["seq_id"] for s in sub if obs.get((asym, int(s["seq_id"]))) and
            not set(STAR3D_ATOMS) <= obs[(asym, int(s["seq_id"]))])
        out["mods_in_family_interval"] = ";".join(
            m for m in mods if offset < int(m.split(":")[0]) <= offset + len(nrow))
        auth_nums = [s["auth_seq_num"] for s in sub if s["auth_seq_num"] is not None]
        ins = [s for s in sub if s["pdb_ins_code"]]
        out["auth_numbering_note"] = (f"auth {auth_nums[0]}..{auth_nums[-1]}" if auth_nums else "none observed") + \
            (f"; {len(ins)} insertion codes" if ins else "")
    unk_in = [u for u in unknown if offset is not None and offset < int(u.split(":")[0]) <= offset + len(nrow)]
    if match_kind is None or match_kind == "no_exact_match":
        # unknown residues ('X') inside the interval make an exact claim impossible -> ambiguous, not failed
        if "X" in seq_par[rs - 1:re_] and len(seq_par[rs - 1:re_]) == len(nrow) and all(
                a == b or a == "X" for a, b in zip(seq_par[rs - 1:re_], nrow)):
            match_kind = "match_except_unknown_residues"
            unk_in = [u for u in unknown if rs <= int(u.split(":")[0]) <= re_]
    out["sequence_match"] = match_kind
    out["unknown_in_family_interval"] = ";".join(unk_in)
    if match_kind == "exact_at_row_coordinates" and not unk_in:
        out["link_status"] = "verified"
    elif match_kind == "exact_elsewhere" and not unk_in:
        out["link_status"] = "verified"
        out["link_note"] = "row matches deposited sequence but not at row start/end coordinates (offset recorded)"
    elif match_kind in ("ambiguous_multiple_positions", "match_except_unknown_residues"):
        out["link_status"] = "ambiguous"
    else:
        out["link_status"] = "failed"
    # organism records for this RNA entity
    orgs = []
    for src, sci, tax in (("entity_src_gen", "pdbx_gene_src_scientific_name", "pdbx_gene_src_ncbi_taxonomy_id"),
                          ("entity_src_nat", "pdbx_organism_scientific", "pdbx_ncbi_taxonomy_id"),
                          ("pdbx_entity_src_syn", "organism_scientific", "ncbi_taxonomy_id")):
        key = {"entity_src_gen": "src_gen", "entity_src_nat": "src_nat", "pdbx_entity_src_syn": "src_syn"}[src]
        for r in ev[key]:
            if r["entity_id"] == ent:
                orgs.append(f"{src}:{r.get(sci)}|taxid={r.get(tax)}")
    out["entity_source_records"] = " ; ".join(orgs)
    hosts = [f"{r.get('pdbx_host_org_scientific_name')}|{r.get('pdbx_host_org_ncbi_taxonomy_id')}"
             for r in ev["src_gen"] if r["entity_id"] == ent and r.get("pdbx_host_org_scientific_name")]
    out["expression_host_records"] = ";".join(hosts)
    e = next((x for x in ev["entities"] if x["id"] == ent), {})
    out["entity_description"] = e.get("pdbx_description")
    out["entity_src_method"] = e.get("src_method")
    out["entity_pdbx_mutation"] = e.get("pdbx_mutation")
    out["struct_ref"] = ";".join(f"{r.get('db_name')}:{r.get('db_code')}/{r.get('pdbx_db_accession')}"
                                 for r in ev["struct_ref"] if r.get("entity_id") == ent)
    difs = [r for r in ev["struct_ref_seq_dif"] if r.get("pdbx_pdb_strand_id") == auth]
    out["struct_ref_seq_dif"] = ";".join(f"{r.get('seq_num')}{r.get('mon_id')}<-{r.get('db_mon_id')}:{r.get('details')}"
                                         for r in difs)
    out["exptl_method"] = ";".join(ev["exptl_method"])
    out["resolution"] = ev["resolution"]
    out["initial_release_date"] = ev["initial_release_date"]
    out["title"] = ev["title"]
    prim = next((c for c in ev["citations"] if c["id"] == "primary"), ev["citations"][0] if ev["citations"] else {})
    out["primary_citation"] = f"{prim.get('title')} | {prim.get('journal_abbrev')} {prim.get('year')} | " \
                              f"PMID {prim.get('pdbx_database_id_PubMed')} | DOI {prim.get('pdbx_database_id_DOI')}"
    out["ligands"] = ";".join(sorted({f"{r['comp_id']}({r['name']})" for r in ev["nonpoly"]
                                      if r["comp_id"] not in ("HOH",)}))
    other = [f"ent{x['id']}:{x.get('pdbx_description')}" for x in ev["entities"]
             if x["type"] == "polymer" and x["id"] != ent]
    out["other_polymer_entities"] = ";".join(other)[:500]
    out["n_other_polymer_entities"] = len(other)
    out["auth_chain_single_char"] = "yes" if len(auth) == 1 else "no"
    return out, scheme


def seed_records(fams):
    path = P(CFG["reference"]["seed_path"])
    return {a.acc: a for a in stockholm.parse(path, only=fams)}


def candidate_links(sl):
    """(family, PDB, chain, row) candidates from the pinned standard seed only."""
    seed = seed_records(sl)
    out = []
    for c in read_tsv(P("metadata/chain_row_candidates.tsv")):
        if c["rfam_acc"] not in sl:
            continue
        if c["candidate_status"] == "explicit_gr_link":
            rows, basis = c["explicit_gr_rows"].split(";"), "explicit_GR_feature"
        elif c["candidate_status"].startswith("sequence_match"):
            rows, basis = c["sequence_match_rows"].split(";"), "sequence_match_only"
        else:
            out.append(dict(rfam_acc=c["rfam_acc"], pdb_id=c["pdb_id"], chain=c["chain"], row_name=None,
                            link_basis="none", candidate_status=c["candidate_status"]))
            continue
        a = seed[c["rfam_acc"]]
        for name in rows:
            base, st_, en = stockholm.split_name(name)
            m = re.match(r"^(URS[0-9A-F]{10})_(\d+)$", base)
            ung = norm(a.ungapped(name))
            feat = next((f for f in a.gr.get(name, {}) if f.upper() == f"{c['pdb_id']}_{c['chain']}_SS".upper()), None)
            out.append(dict(rfam_acc=c["rfam_acc"], pdb_id=c["pdb_id"], chain=c["chain"], row_name=name,
                            gr_feature=feat, link_basis=basis, n_candidate_rows=len(rows),
                            urs=m.group(1) if m else None, row_taxid=m.group(2) if m else None,
                            row_start=st_, row_end=en, row_len=len(ung),
                            row_seq_hash=hashlib.sha256(ung.encode()).hexdigest()[:16],
                            seed_row_aligned_sha256=hashlib.sha256(a.seqs[name].encode()).hexdigest(),
                            seed_row_lines=",".join(map(str, a.seq_lines[name])),
                            in_mapping_file=c["in_mapping_file"], ungapped_row=ung,
                            candidate_status=c["candidate_status"]))
    return out


def main():
    sl = {r["rfam_acc"] for r in read_tsv(P("metadata/shortlist_screen.tsv")) if r["shortlisted"] == "yes"}
    cands = candidate_links(sl)
    os.makedirs(P("review/evidence"), exist_ok=True)
    links, cache = [], {}
    for srow in sorted(cands, key=lambda r: (r["rfam_acc"], r["pdb_id"], r["chain"], r["row_name"] or "")):
        pdb = srow["pdb_id"]
        base = dict(reference_source="Rfam.seed.gz", rfam_release=CFG["reference"]["rfam_release"],
                    seed_sha256=CFG["reference"]["seed_sha256"])
        if not srow["row_name"]:
            links.append(dict(base, rfam_acc=srow["rfam_acc"], pdb_id=pdb, chain_token=srow["chain"],
                              link_basis="none", link_status="no_verified_standard_seed_row",
                              link_note=f"Phase 1 status {srow['candidate_status']}: no existing row in pinned Rfam.seed.gz "
                                        f"(no explicit GR feature, no exact row-sequence match in SEQRES)"))
            continue
        try:
            if pdb not in cache:
                path = get_mmcif(pdb)
                ev, b = extract_entry(pdb, path)
                obs, nmodels, _ = observed_atoms(path)
                cache = {pdb: (ev, b, obs, nmodels)}
            ev, b, obs, nmodels = cache[pdb]
            link, scheme = build_link(srow["rfam_acc"], srow, ev, obs, nmodels, b)
        except Exception as e:
            link = dict(rfam_acc=srow["rfam_acc"], row_name=srow["row_name"], pdb_id=pdb, chain_token=srow["chain"],
                        link_status="failed", link_note=f"{type(e).__name__}: {e}"[:300])
            scheme = None
        link.update(base)
        for k in ("link_basis", "n_candidate_rows", "seed_row_aligned_sha256", "seed_row_lines", "gr_feature"):
            link[k] = srow.get(k)
        if srow["link_basis"] == "sequence_match_only" and link.get("link_status") == "verified":
            link["link_status"] = "ambiguous"
            link["link_note"] = ("sequence matches an existing seed row but no explicit structure link; provenance "
                                 "(same source RNA) must be established before use")
        if srow["link_basis"] == "explicit_GR_feature" and (srow.get("n_candidate_rows") or 1) > 1:
            link["link_note"] = (link.get("link_note") or "") + "; multiple rows carry this GR feature"
        if srow["urs"]:
            try:
                rc = get_rnacentral(srow["urs"])
                link["rnacentral_seq_len"] = rc.get("length")
                dep = link.get("deposited_seq_parent_mapped") or ""
                link["rnacentral_seq_equals_deposited"] = "yes" if norm(rc.get("sequence", "")) == dep else "no"
                seg = norm(rc.get("sequence", ""))[int(srow["row_start"]) - 1:int(srow["row_end"])]
                link["row_equals_rnacentral_interval"] = "yes" if seg == srow["ungapped_row"] else "no"
            except RuntimeError as e:
                link["rnacentral_note"] = str(e)[:200]
        json.dump({"link": link, "scheme_chain": scheme},
                  open(P(f"review/evidence/{pdb}_{srow['chain']}_{srow['rfam_acc']}_{re.sub('[^A-Za-z0-9]', '_', srow['row_name'])}.json"), "w"), indent=1)
        links.append(link)
        print(f"{srow['rfam_acc']} {pdb}_{srow['chain']} {srow['link_basis'][:8]} {link.get('link_status')} "
              f"{link.get('sequence_match')} obs={link.get('observed_fraction')}", flush=True)
    fields = ["reference_source", "rfam_release", "seed_sha256", "rfam_acc", "row_name", "link_basis",
              "n_candidate_rows", "gr_feature", "seed_row_aligned_sha256", "seed_row_lines", "pdb_id", "chain_token",
              "id_scheme_matched", "label_asym_id", "auth_asym_id", "entity_id", "chain_candidates", "n_models",
              "entity_poly_type", "urs", "row_taxid", "row_start", "row_end", "row_len", "row_seq_hash",
              "in_mapping_file", "deposited_len", "sequence_match", "row_offset_in_deposited",
              "family_label_seq_start", "family_label_seq_end", "family_auth_start", "family_auth_end",
              "auth_numbering_note", "row_residues_observed_scheme", "row_residues_with_any_atom",
              "row_residues_with_all_star3d_backbone_atoms", "observed_fraction", "missing_residue_seq_ids",
              "incomplete_backbone_seq_ids", "modified_residues", "mods_in_family_interval",
              "unknown_or_unmapped_residues", "unknown_in_family_interval", "can_vs_parent_mapped_identical",
              "rnacentral_seq_len", "rnacentral_seq_equals_deposited", "row_equals_rnacentral_interval",
              "entity_description", "entity_src_method", "entity_source_records", "expression_host_records",
              "entity_pdbx_mutation", "struct_ref", "struct_ref_seq_dif", "exptl_method", "resolution",
              "initial_release_date", "title", "primary_citation", "ligands", "n_other_polymer_entities",
              "other_polymer_entities", "auth_chain_single_char", "link_status", "link_note",
              "deposited_seq_parent_mapped"]
    write_tsv(P("mappings/structure_sequence_map.tsv"), links, fields)


if __name__ == "__main__":
    main()
