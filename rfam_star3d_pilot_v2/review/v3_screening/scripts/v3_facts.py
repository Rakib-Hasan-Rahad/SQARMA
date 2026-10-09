"""Extract per-structure facts for v3 screening (read-only on downloaded mmCIF; run with python -I).
Usage: v3_facts.py ROOT FAM:PDB:CHAIN ...  -> prints JSON lines. Row sequence from metadata/seed_gr_structure_links.tsv."""
import csv, json, sys, os, gzip
import gemmi
ROOT = sys.argv[1]
links = {(r["rfam_acc"], r["pdb_id"], r["chain"]): r for r in
         csv.DictReader(open(os.path.join(ROOT, "metadata/seed_gr_structure_links.tsv")), delimiter="\t")}

def tab(b, cat, cols):
    t = b.find(cat, cols) if all(b.find_value(cat + c) is not None or True for c in cols) else []
    try:
        t = b.find(cat, [c if b.find_values(cat + c) else "?" + c for c in cols])
    except Exception:
        return []
    out = []
    for row in t:
        d = {}
        for i, c in enumerate(cols):
            v = row[i] if row.has(i) else None
            d[c] = gemmi.cif.as_string(v) if v not in (None, "?", ".") else None
        out.append(d)
    return out

for spec in sys.argv[2:]:
    fam, pdb, chain = spec.split(":")
    L = links[(fam, pdb, chain)]
    p = os.path.join(ROOT, "inputs/structures/mmcif", pdb + ".cif.gz")
    b = gemmi.cif.read(p).sole_block()
    out = {"spec": spec, "row": L["row_name"], "row_seq": L["ungapped_row"]}
    out["method"] = [r["method"] for r in tab(b, "_exptl.", ["method"])]
    res = [r["ls_d_res_high"] for r in tab(b, "_refine.", ["ls_d_res_high"])] + \
          [r["resolution"] for r in tab(b, "_em_3d_reconstruction.", ["resolution"])]
    out["resolution"] = next((x for x in res if x), None)
    out["title"] = gemmi.cif.as_string(b.find_value("_struct.title"))
    out["citation"] = tab(b, "_citation.", ["id", "title", "journal_abbrev", "year", "pdbx_database_id_PubMed", "pdbx_database_id_DOI"])
    scheme = tab(b, "_pdbx_poly_seq_scheme.", ["asym_id", "entity_id", "seq_id", "mon_id", "auth_seq_num", "pdb_strand_id", "pdb_ins_code", "pdb_seq_num"])
    sc = [s for s in scheme if s["pdb_strand_id"] == chain]
    asyms = sorted({s["asym_id"] for s in sc}); ent = sorted({s["entity_id"] for s in sc})
    out["label_asym"] = asyms; out["entity"] = ent
    ents = tab(b, "_entity.", ["id", "pdbx_description", "pdbx_mutation", "details", "src_method"])
    out["entity_rec"] = [e for e in ents if e["id"] in ent]
    out["src_syn"] = [r for r in tab(b, "_pdbx_entity_src_syn.", ["entity_id", "organism_scientific", "ncbi_taxonomy_id", "details"]) if r["entity_id"] in ent]
    out["src_gen"] = [r for r in tab(b, "_entity_src_gen.", ["entity_id", "pdbx_gene_src_scientific_name", "pdbx_gene_src_ncbi_taxonomy_id", "pdbx_gene_src_strain", "pdbx_host_org_scientific_name", "pdbx_description"]) if r["entity_id"] in ent]
    out["src_nat"] = [r for r in tab(b, "_entity_src_nat.", ["entity_id", "pdbx_organism_scientific", "pdbx_ncbi_taxonomy_id", "strain"]) if r["entity_id"] in ent]
    out["struct_ref"] = [r for r in tab(b, "_struct_ref.", ["entity_id", "db_name", "db_code", "pdbx_db_accession", "pdbx_seq_one_letter_code"]) if r["entity_id"] in ent]
    out["seq_dif"] = [r for r in tab(b, "_struct_ref_seq_dif.", ["pdbx_pdb_strand_id", "mon_id", "seq_num", "pdbx_auth_seq_num", "db_mon_id", "details"]) if r["pdbx_pdb_strand_id"] == chain]
    ep = [r for r in tab(b, "_entity_poly.", ["entity_id", "pdbx_seq_one_letter_code", "pdbx_seq_one_letter_code_can"]) if r["entity_id"] in ent]
    can = ep[0]["pdbx_seq_one_letter_code_can"].replace("\n", "").replace(" ", "") if ep else ""
    out["deposited_can"] = can
    out["deposited_raw"] = ep[0]["pdbx_seq_one_letter_code"].replace("\n", "").replace(" ", "") if ep else ""
    rs = L["ungapped_row"]
    hits = [i for i in range(len(can)) if can.startswith(rs, i)]
    out["row_hits_0based"] = hits
    st = gemmi.read_structure(p); out["n_models"] = len(st)
    st.remove_alternative_conformations()
    m = st[0]
    obs = {}
    for ch in m:
        if ch.name != chain: continue
        for r in ch:
            if r.label_seq is not None:
                obs[r.label_seq] = (r.name, r.seqid.num, r.seqid.icode, len(r), r.het_flag)
    sc_ent = [s for s in sc if s["asym_id"] == asyms[0]] if asyms else []
    if hits:
        a = hits[0] + 1; z = a + len(rs) - 1
        fam_rows = [s for s in sc_ent if a <= int(s["seq_id"]) <= z]
        out["family_label"] = [a, z]
        auth = [s["pdb_seq_num"] + (s["pdb_ins_code"] or "") for s in fam_rows]
        out["family_auth"] = [auth[0], auth[-1]] if auth else None
        out["icodes"] = sorted({s["pdb_ins_code"] for s in fam_rows if s["pdb_ins_code"]})
        miss = [int(s["seq_id"]) for s in fam_rows if int(s["seq_id"]) not in obs]
        out["missing_label_in_family"] = miss
        out["observed_fraction"] = round(1 - len(miss) / len(rs), 3)
        mods = [(k, v[0]) for k, v in obs.items() if a <= k <= z and v[0] not in ("A", "C", "G", "U")]
        out["modified_in_family"] = mods
        out["partial_lt12atoms"] = [k for k, v in obs.items() if a <= k <= z and v[3] < 12 and v[0] in ("A","C","G","U")]
        # auth monotonic?
        nums = [int(s["pdb_seq_num"]) for s in fam_rows]
        out["auth_monotonic"] = all(nums[i] < nums[i+1] for i in range(len(nums)-1))
    out["deposited_len"] = len(can)
    lig = tab(b, "_pdbx_entity_nonpoly.", ["entity_id", "name", "comp_id"])
    out["ligands"] = [(l["comp_id"], l["name"]) for l in lig]
    out["other_polymers"] = [(e["id"], e["pdbx_description"]) for e in ents if e["id"] not in ent]
    print(json.dumps(out))
