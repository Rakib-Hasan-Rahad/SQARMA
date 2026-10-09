"""Phase 2 close-out: sequence groups, construct review table, representatives and frozen pair list.

Usage: cohort.py [--freeze]
Without --freeze, writes draft tables. With --freeze, refuses if any representative in a primary or
exploratory family is still 'pending', then writes results/selected_pairs.tsv and
metadata/cohort_v<version>_freeze.json (sha256 of config, decisions, link table, outputs).
Primary direction: query = lexicographically smaller '<PDB>_<authchain>' (config: sorted_stable_id).
"""
import csv
import datetime as dt
import hashlib
import itertools
import json
import os
import sys
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def write_tsv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) in (None, "", []) else (";".join(map(str, r[k])) if isinstance(r[k], list) else r[k]))
                        for k in fields})


def main(freeze):
    dec = yaml.safe_load(open(P("review/decisions.yaml")))["families"]
    links = [r for r in read_tsv(P("mappings/structure_sequence_map.tsv")) if r["rfam_acc"] in dec]
    explicit = {f"{r['pdb_id']}_{r['chain_token']}": r for r in links if r["link_basis"] == "explicit_GR_feature"}

    # layer 1: exact normalized family-region sequence groups (explicit links only)
    groups = defaultdict(list)
    for r in links:
        if r["link_basis"] == "explicit_GR_feature" and r["row_seq_hash"] != "NA":
            groups[(r["rfam_acc"], r["row_seq_hash"])].append(r)
    rep_keys = {rep["key"]: (fam, rep) for fam, d in dec.items() for rep in d.get("representatives", [])}
    sg = []
    for (fam, h), mem in sorted(groups.items()):
        keys = [f"{m['pdb_id']}_{m['chain_token']}" for m in mem]
        chosen = [k for k in keys if k in rep_keys]
        sg.append(dict(rfam_acc=fam, row_seq_hash=h, row_name=mem[0]["row_name"], row_len=mem[0]["row_len"],
                       n_structures=len(mem), members=keys, link_statuses=sorted({m["link_status"] for m in mem}),
                       entity_sources=sorted({m["entity_source_records"] for m in mem}),
                       representative=chosen[0] if chosen else None,
                       group_decision=(rep_keys[chosen[0]][1]["decision"] if chosen else
                                       "not_selected (see decisions.yaml alternatives / family reason)")))
    write_tsv(P("results/sequence_groups.tsv"), sg, list(sg[0].keys()))

    # construct review table + representatives
    cr, reps = [], []
    for fam, d in dec.items():
        for rep in d.get("representatives", []):
            k = rep["key"]
            r = explicit.get(k)
            if r is None:
                raise SystemExit(f"{k}: no explicit standard-seed link in structure_sequence_map.tsv")
            cr.append(dict(rfam_acc=fam, key=k, family_decision=d["decision"], source=rep.get("source"),
                           source_evidence=rep.get("source_evidence"), construct_changes=rep.get("construct_changes"),
                           masked_label_seq_ids=rep.get("masked", []), relevance=rep.get("relevance"),
                           ligand_state=rep.get("ligand_state"), alternatives=rep.get("alternatives"),
                           decision=rep["decision"], reason=rep.get("reason"),
                           mmcif_pdbx_mutation=r["entity_pdbx_mutation"], mmcif_struct_ref_seq_dif=r["struct_ref_seq_dif"],
                           link_status=r["link_status"], reviewer="AI agent (Claude); no human approval"))
            if rep["decision"] in ("accept", "accept_with_masked_engineering", "exploratory"):
                reps.append(dict(r, rep_id=f"{fam}__{k}", key=k, decision=rep["decision"],
                                 family_decision=d["decision"], masked_label_seq_ids=rep.get("masked", []),
                                 source=rep.get("source")))
    write_tsv(P("review/construct_review.tsv"), cr, list(cr[0].keys()))
    fields = ["rep_id", "key", "rfam_acc", "family_decision", "decision", "source", "masked_label_seq_ids",
              "row_name", "seed_row_aligned_sha256", "seed_row_lines", "pdb_id", "chain_token", "label_asym_id",
              "auth_asym_id", "entity_id", "row_start", "row_end", "row_offset_in_deposited", "family_label_seq_start",
              "family_label_seq_end", "deposited_seq_parent_mapped", "observed_fraction", "link_status",
              "reference_source", "rfam_release", "seed_sha256"]
    write_tsv(P("results/selected_representatives.tsv"), reps, fields)

    # pairs
    pending = [c for c in cr if c["decision"] == "pending" and not c["family_decision"].startswith("excluded")]
    pairs = []
    by_fam = defaultdict(list)
    for r in reps:
        by_fam[r["rfam_acc"]].append(r)
    for fam, rs in sorted(by_fam.items()):
        tier = "primary" if all(x["decision"] != "exploratory" for x in rs) and \
            dec[fam]["decision"].startswith("primary") else "exploratory"
        for a, b in itertools.combinations(sorted(rs, key=lambda x: x["key"]), 2):
            if a["link_status"] != "verified" or b["link_status"] != "verified":
                continue
            pairs.append(dict(pair_id=f"{fam}__{a['key']}__{b['key']}", rfam_acc=fam, tier=tier,
                              query_rep=a["rep_id"], target_rep=b["rep_id"], query=a["key"], target=b["key"],
                              primary_direction=f"{a['key']}->{b['key']}", run_both_directions="yes",
                              rationale=f"{a['source']} vs {b['source']}; both explicit standard-seed rows verified",
                              reference_source="Rfam.seed.gz", rfam_release=CFG["reference"]["rfam_release"],
                              seed_sha256=CFG["reference"]["seed_sha256"], cohort_version=CFG["cohort_version"]))
    cap = CFG["cohort"]["max_pairs_per_family"][CFG["mode"]]
    for fam in by_fam:
        if cap and sum(p["rfam_acc"] == fam for p in pairs) > cap:
            raise SystemExit(f"{fam}: pair cap exceeded; deterministic subset rule must be applied")
    out = P("results/selected_pairs.tsv" if freeze else "results/selected_pairs.DRAFT.tsv")
    if freeze and pending:
        raise SystemExit(f"cannot freeze: pending decisions {[c['key'] for c in pending]}")
    write_tsv(out, pairs, list(pairs[0].keys()) if pairs else ["pair_id"])
    print(f"groups {len(sg)}; reviewed reps {len(cr)}; selected reps {len(reps)}; pairs {len(pairs)} "
          f"({sum(p['tier'] == 'primary' for p in pairs)} primary); pending {[c['key'] for c in pending]}")
    for p in pairs:
        print("  ", p["tier"], p["pair_id"])
    if freeze:
        files = ["config.yaml", "review/decisions.yaml", "mappings/structure_sequence_map.tsv",
                 "results/selected_representatives.tsv", "results/selected_pairs.tsv", "review/construct_review.tsv",
                 "results/sequence_groups.tsv"]
        meta = dict(cohort_version=CFG["cohort_version"], frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                    note="frozen before any research STAR3D run and before Phase-3 correspondence extraction",
                    sha256={f: sha(P(f)) for f in files})
        json.dump(meta, open(P(f"metadata/cohort_v{CFG['cohort_version']}_freeze.json"), "w"), indent=1)
        print("FROZEN", meta["frozen_utc"])


if __name__ == "__main__":
    main("--freeze" in sys.argv)
