"""Phase 1 (V2): broad automated inventory against the pinned STANDARD seed only.

Inputs : Rfam.seed.gz (pinned), Rfam.pdb.gz (candidate metadata), wwPDB pdb_seqres.txt.gz
Outputs:
  metadata/rfam_pdb_mapping_parsed.tsv     every Rfam.pdb.gz line (no rows dropped)
  metadata/seed_gr_structure_links.tsv     every explicit #=GR <PDB>_<chain>_SS feature in Rfam.seed.gz
  metadata/chain_row_candidates.tsv        every mapped chain x seed-row link candidate (explicit / sequence)
  results/family_inventory.tsv             per-family stage counts (automated; NOT eligibility)
  metadata/inventory_stage_counts.json     successive-stage family counts
  metadata/shortlist_screen.tsv            every screened family with reasons
  metadata/stockholm_validation.json       parser validation summary
"""
import csv
import gzip
import hashlib
import json
import os
import re
import sys
from collections import defaultdict

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
GR_SS = re.compile(r"^(?P<pdb>[0-9A-Za-z]{4})_(?P<chain>[^_]+)_SS$")
URS = re.compile(r"^(?P<urs>URS[0-9A-F]{10})_(?P<taxid>\d+)$")
MAPPING_COLS = ["rfam_acc", "pdb_id", "chain", "pdb_start", "pdb_end", "bit_score", "evalue",
                "cm_start", "cm_end", "hex_colour"]
SYNTHETIC_TAXID = "32630"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def write_tsv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) is None or r.get(k) == "" else r[k]) for k in fields})


def norm(s):
    return s.upper().replace("T", "U")


def h16(s):
    return hashlib.sha256(s.encode()).hexdigest()[:16]


def check_reference():
    ref = CFG["reference"]
    path = P(ref["seed_path"])
    if os.path.basename(path) != "Rfam.seed.gz":
        raise SystemExit("reference source is not Rfam.seed.gz")
    got = sha256(path)
    if got != ref["seed_sha256"]:
        raise SystemExit(f"pinned seed sha256 mismatch: {got}")
    return path


def load_mapping():
    rows = []
    with gzip.open(P(CFG["sources"]["rfam_pdb_mapping"]), "rt") as f:
        for i, line in enumerate(f, 1):
            parts = line.rstrip("\n").split("\t")
            if len(parts) != len(MAPPING_COLS):
                raise ValueError(f"Rfam.pdb.gz line {i}: {len(parts)} fields")
            r = dict(zip(MAPPING_COLS, parts), line=i)
            r["pdb_id"] = r["pdb_id"].upper()
            rows.append(r)
    return rows


def load_seqres(wanted):
    """{(PDB, chain): (mol, sequence)} for wanted entries only."""
    out = {}
    with gzip.open(P("inputs/pdb/pdb_seqres.txt.gz"), "rt") as f:
        key = None
        for line in f:
            if line.startswith(">"):
                tok = line[1:].split()
                pdb, ch = tok[0].split("_", 1)
                pdb = pdb.upper()
                key = (pdb, ch) if pdb in wanted else None
                mol = tok[1].replace("mol:", "")
            elif key:
                out[key] = (mol, line.strip())
    return out


def main():
    seed_path = check_reference()
    mapping = load_mapping()
    write_tsv(P("metadata/rfam_pdb_mapping_parsed.tsv"), mapping, ["line"] + MAPPING_COLS)
    seed = {a.acc: a for a in stockholm.parse(seed_path)}
    val = {"reference_source": "Rfam.seed.gz", "rfam_release": CFG["reference"]["rfam_release"],
           "seed_sha256": CFG["reference"]["seed_sha256"], "records": len(seed),
           "sequence_rows": sum(len(a.seqs) for a in seed.values()),
           "gr_rows": sum(len(f) for a in seed.values() for f in a.gr.values()),
           "decode_fallback_lines_latin1": stockholm.DECODE_FALLBACKS,
           "note": "parse() raises on width/alphabet/annotation-link errors; no record rejected"}

    # explicit GR structure links inside the standard seed
    gr = []
    for acc, a in seed.items():
        for name, feats in a.gr.items():
            for feat in feats:
                m = GR_SS.match(feat)
                if m:
                    base, s, e = stockholm.split_name(name)
                    u = URS.match(base)
                    ung = norm(a.ungapped(name))
                    gr.append(dict(rfam_acc=acc, row_name=name, gr_feature=feat, pdb_id=m["pdb"].upper(),
                                   chain=m["chain"], urs=u["urs"] if u else None, row_taxid=u["taxid"] if u else None,
                                   row_start=s, row_end=e, row_len=len(ung), row_seq_hash=h16(ung),
                                   row_aligned_hash=h16(a.seqs[name]), ungapped_row=ung))
    write_tsv(P("metadata/seed_gr_structure_links.tsv"), gr,
              ["rfam_acc", "row_name", "gr_feature", "pdb_id", "chain", "urs", "row_taxid", "row_start", "row_end",
               "row_len", "row_seq_hash", "row_aligned_hash", "ungapped_row"])

    # candidate chains: Rfam.pdb.gz mappings + explicit GR links
    chains = defaultdict(set)
    for r in mapping:
        chains[r["rfam_acc"]].add((r["pdb_id"], r["chain"]))
    for g in gr:
        chains[g["rfam_acc"]].add((g["pdb_id"], g["chain"]))
    seqres = load_seqres({p for s in chains.values() for p, _ in s})

    cand = []
    fam_rows = []
    for acc in sorted(chains):
        a = seed.get(acc)
        rows_u = {n: norm(a.ungapped(n)) for n in a.seqs} if a else {}
        by_seq = defaultdict(list)
        for n, s in rows_u.items():
            by_seq[s].append(n)
        explicit = defaultdict(list)
        for g in gr:
            if g["rfam_acc"] == acc:
                explicit[(g["pdb_id"], g["chain"])].append(g["row_name"])
        seq_groups = set()
        for pdb, ch in sorted(chains[acc]):
            mol, sq = seqres.get((pdb, ch), (None, None))
            chseq = norm(sq) if sq else None
            if chseq:
                seq_groups.add(chseq)
            exp_rows = explicit.get((pdb, ch), [])
            seq_rows = []
            if chseq and rows_u:
                seq_rows = sorted({n for s, ns in by_seq.items() if len(s) >= 15 and s in chseq for n in ns})
            in_map = any(r["pdb_id"] == pdb and r["chain"] == ch for r in mapping if r["rfam_acc"] == acc)
            status = ("explicit_gr_link" if exp_rows else
                      ("sequence_match_only_pending_provenance" if seq_rows else
                       ("no_seqres" if not chseq else "no_standard_seed_row_candidate")))
            cand.append(dict(rfam_acc=acc, pdb_id=pdb, chain=ch, in_mapping_file="yes" if in_map else "no",
                             seqres_mol=mol, seqres_len=len(chseq) if chseq else None,
                             seqres_hash=h16(chseq) if chseq else None,
                             explicit_gr_rows=";".join(exp_rows), sequence_match_rows=";".join(seq_rows[:20]),
                             n_sequence_match_rows=len(seq_rows), candidate_status=status))
        fc = [c for c in cand if c["rfam_acc"] == acc]
        linked_rows = {n for c in fc for n in (c["explicit_gr_rows"].split(";") if c["explicit_gr_rows"] else [])}
        linked_rows_any = linked_rows | {n for c in fc for n in (c["sequence_match_rows"].split(";")
                                                                  if c["sequence_match_rows"] else [])}
        taxa = {URS.match(stockholm.split_name(n)[0])["taxid"] for n in linked_rows
                if URS.match(stockholm.split_name(n)[0])}
        fam_rows.append(dict(
            rfam_acc=acc, rfam_id=a.id if a else None, type=a.gf.get("TP", [None])[0] if a else None,
            model_length_RF=sum(1 for c in a.gc.get("RF", "") if c not in ".-") if a else None,
            in_standard_seed="yes" if a else "no", seed_rows=len(a.seqs) if a else None,
            mapping_pdb_entries=len({r["pdb_id"] for r in mapping if r["rfam_acc"] == acc}),
            mapping_chain_regions=sum(1 for r in mapping if r["rfam_acc"] == acc),
            candidate_chains=len(chains[acc]),
            candidate_chain_sequence_groups=len(seq_groups),
            chains_without_seqres=sum(1 for c in fc if c["candidate_status"] == "no_seqres"),
            explicit_gr_links=sum(1 for c in fc if c["explicit_gr_rows"]),
            explicit_linked_rows=len(linked_rows),
            explicit_linked_distinct_sequences=len({rows_u[n] for n in linked_rows if n in rows_u}),
            explicit_linked_taxa_all=len(taxa), explicit_linked_taxa_nonsynthetic=len(taxa - {SYNTHETIC_TAXID}),
            sequence_only_candidate_chains=sum(1 for c in fc if c["candidate_status"].startswith("sequence_match")),
            any_linked_distinct_sequences=len({rows_u[n] for n in linked_rows_any if n in rows_u}),
            review_status="pending"))
    write_tsv(P("metadata/chain_row_candidates.tsv"), cand, list(cand[0].keys()))

    st = {
        "families_with_pdb_candidates(Rfam.pdb.gz or seed GR)": len(fam_rows),
        "  of which in Rfam.pdb.gz": len({r["rfam_acc"] for r in mapping}),
        "  of which have explicit GR links in standard seed": sum(1 for f in fam_rows if f["explicit_gr_links"]),
        "families_with_>=2_candidate_chain_sequence_groups": sum(1 for f in fam_rows if f["candidate_chain_sequence_groups"] >= 2),
        "families_with_>=2_explicitly_linked_distinct_row_sequences": sum(1 for f in fam_rows if f["explicit_linked_distinct_sequences"] >= 2),
        "families_with_>=2_linked_distinct_row_sequences_incl_sequence_only_proposals": sum(1 for f in fam_rows if f["any_linked_distinct_sequences"] >= 2),
        "families_with_>=2_eligible_distinct_biological_representatives": "unknown outside reviewed scope (Phase 2)",
        "candidate_chains_total": len(cand),
        "candidate_chain_status_counts": {s: sum(1 for c in cand if c["candidate_status"] == s)
                                          for s in sorted({c["candidate_status"] for c in cand})},
    }

    sl = CFG["shortlist"]
    cap = sl["max_families_to_review"][CFG["mode"]]
    screen = []
    for f in fam_rows:
        reasons = []
        if f["explicit_linked_distinct_sequences"] < sl["min_distinct_linked_row_sequences"]:
            reasons.append("explicitly_linked_distinct_row_sequences<2")
        if f["model_length_RF"] and f["model_length_RF"] > sl["max_family_model_length"]:
            reasons.append(f"model_length>{sl['max_family_model_length']}")
        if f["type"] and re.search(sl["exclude_types_regex"], f["type"]):
            reasons.append("type_excluded:" + f["type"].strip())
        screen.append(dict(f, screen_status="excluded" if reasons else "pass", screen_reasons=";".join(reasons)))
    passing = sorted([s for s in screen if s["screen_status"] == "pass"],
                     key=lambda r: (-r["explicit_linked_taxa_nonsynthetic"], -r["explicit_linked_distinct_sequences"],
                                    r["model_length_RF"], r["rfam_acc"]))
    for i, r in enumerate(passing, 1):
        r["rank"] = i
        r["shortlisted"] = "yes" if cap is None or i <= cap else "no_beyond_cap"
    for r in screen:
        r.setdefault("rank", None)
        r.setdefault("shortlisted", "no")
    screen.sort(key=lambda r: (r["rank"] is None, r["rank"] or 0, r["rfam_acc"]))
    write_tsv(P("metadata/shortlist_screen.tsv"), screen,
              ["rank", "rfam_acc", "rfam_id", "type", "model_length_RF", "explicit_gr_links", "explicit_linked_rows",
               "explicit_linked_distinct_sequences", "explicit_linked_taxa_all", "explicit_linked_taxa_nonsynthetic",
               "sequence_only_candidate_chains", "screen_status", "screen_reasons", "shortlisted"])
    for f in fam_rows:
        s = next(x for x in screen if x["rfam_acc"] == f["rfam_acc"])
        f["screen_status"], f["shortlisted"] = s["screen_status"], s["shortlisted"]
    write_tsv(P("results/family_inventory.tsv"), fam_rows, list(fam_rows[0].keys()))
    st["shortlist"] = [r["rfam_acc"] for r in screen if r["shortlisted"] == "yes"]
    st["screen_pass_total"] = len(passing)
    json.dump(st, open(P("metadata/inventory_stage_counts.json"), "w"), indent=1)
    json.dump(val, open(P("metadata/stockholm_validation.json"), "w"), indent=1)
    print(json.dumps(st, indent=1))


if __name__ == "__main__":
    main()
