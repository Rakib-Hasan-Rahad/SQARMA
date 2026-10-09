"""Phase 5: candidate disagreement regions (ALL kept) and predeclared ranking for inspection.

Rule (config regions.merge_gap): a source residue is a disagreement residue if, in the primary
direction replicate 1, its category is different_partner, or rfam_only/star3d_only where the absent
side is NOT explained by missing coordinates. Disagreement residues whose source-row indices are
within merge_gap of each other form one region. Regions are also annotated by whether the reverse
run reproduces the disagreement.
Ranking (predeclared): (1) trustworthy = no masked/unobserved residue in region and partners;
(2) more interaction-status differences (Rfam vs STAR3D, same source interactions);
(3) region not within 3 residues of a row terminus; (4) larger size; (5) pair_id, start.
Outputs results/region_review.tsv (interpretation columns filled by manual inspection later).
"""
import csv
import os
import sys
from collections import defaultdict

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import locate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def primary_replicates(comp):
    """(pair_id, direction) -> lowest-numbered replicate whose run completed (failed replicates stay in tables)."""
    ok = {}
    for r in comp:
        if r["category"] != "technical_failure_or_no_alignment":
            key = (r["pair_id"], r["direction"])
            ok[key] = min(ok.get(key, 99), int(r["replicate"]))
    return ok


def main():
    reps = {r["rep_id"]: r for r in read_tsv(P("results/selected_representatives.tsv"))}
    comp = read_tsv(P("results/correspondence_comparison.tsv"))
    prim = primary_replicates(comp)
    inter = read_tsv(P("results/interaction_comparison.tsv")) if os.path.exists(P("results/interaction_comparison.tsv")) else []
    gap = CFG["regions"]["merge_gap"]
    fwd = defaultdict(list)
    rev = defaultdict(dict)
    for r in comp:
        if prim.get((r["pair_id"], r["direction"])) != int(r["replicate"]):
            continue
        if r["direction"] == "forward":
            fwd[r["pair_id"]].append(r)
        else:
            rev[r["pair_id"]][int(r["source_row_index"])] = r

    def is_dis(r):
        if r["category"] == "different_partner":
            return True
        if r["category"] == "rfam_only":
            return r["star3d_missing_reason"] == "algorithm_omission"
        if r["category"] == "star3d_only":
            return True
        return False

    out = []
    for pid, rows in sorted(fwd.items()):
        rows.sort(key=lambda r: int(r["source_row_index"]))
        n = len(rows)
        dis = [r for r in rows if is_dis(r)]
        groups, cur = [], []
        for r in dis:
            if cur and int(r["source_row_index"]) - int(cur[-1]["source_row_index"]) > gap:
                groups.append(cur)
                cur = []
            cur.append(r)
        if cur:
            groups.append(cur)
        rep = reps[rows[0]["source_rep"]]
        for g in groups:
            s, e = int(g[0]["source_row_index"]), int(g[-1]["source_row_index"])
            labs = [int(r["source_label_seq_id"]) for r in g]
            loc = locate.locate(rep["rfam_acc"], rep["row_name"], rep["row_offset_in_deposited"], labs)
            masked = any(r["source_masked"] == "yes" for r in g)
            unobs = any(r["source_observed"] != "yes" for r in g)
            ints = [x for x in inter if x["pair_id"] == pid and x["source_side"] == "query"
                    and (s <= int(x["i"]) <= e or s <= int(x["j"]) <= e)
                    and x["common_assessable_rfam_vs_star3d_forward"] == "yes"
                    and x["rfam_status"] != x["star3d_forward_status"]]
            rev_same = sum(1 for r in g if rev[pid].get(int(r["source_row_index"]), {}).get("star3d_partner") == r["star3d_partner"])
            out.append(dict(
                pair_id=pid, region_id=f"{pid}__r{s}-{e}", source_rep=rep["rep_id"], row_index_start=s, row_index_end=e,
                n_disagreement_residues=len(g), source_auth=f"{g[0]['source_auth']}..{g[-1]['source_auth']}",
                categories=";".join(sorted({r["category"] for r in g})),
                partner_offsets=";".join(sorted({r["partner_offset"] for r in g if r["partner_offset"] != "NA"})),
                seed_elements=";".join(sorted({x["element"] for x in loc})),
                ss_cons="".join(x.get("ss_cons", "?") for x in loc),
                motif_flags=";".join(sorted({f for x in loc for f in x.get("motif_flags", "").split(";") if f})),
                masked_overlap="yes" if masked else "no", unobserved_overlap="yes" if unobs else "no",
                near_terminus="yes" if (s <= 3 or e >= n - 2) else "no",
                interaction_status_differences=len(ints),
                reverse_run_same_star3d_partner=f"{rev_same}/{len(g)}",
                trustworthy="yes" if not masked and not unobs else "no"))
    out.sort(key=lambda r: (r["trustworthy"] != "yes", -r["interaction_status_differences"], r["near_terminus"] == "yes",
                            -r["n_disagreement_residues"], r["pair_id"], r["row_index_start"]))
    for i, r in enumerate(out, 1):
        r["inspection_rank"] = i
        r["inspected"] = "pending"
        r["classification"] = "not_inspected"
        r["interpretation"] = None
    fields = ["inspection_rank", "region_id", "pair_id", "source_rep", "row_index_start", "row_index_end",
              "n_disagreement_residues", "source_auth", "categories", "partner_offsets", "seed_elements", "ss_cons",
              "motif_flags", "masked_overlap", "unobserved_overlap", "near_terminus", "interaction_status_differences",
              "reverse_run_same_star3d_partner", "trustworthy", "inspected", "classification", "interpretation"]
    with open(P("results/region_review.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow({k: ("NA" if r.get(k) in (None, "") else r[k]) for k in fields})
    print(len(out), "candidate regions")
    for r in out[:12]:
        print(r["inspection_rank"], r["region_id"], r["n_disagreement_residues"], r["categories"], r["seed_elements"],
              "int", r["interaction_status_differences"], "trust", r["trustworthy"], "rev", r["reverse_run_same_star3d_partner"])


if __name__ == "__main__":
    main()
