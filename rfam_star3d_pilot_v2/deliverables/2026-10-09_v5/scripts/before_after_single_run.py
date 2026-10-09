"""Before/after for the v5 single-run refactor: v4 active tables (before/) vs v5 active tables.
Every value compared; differences are listed individually. Run for the study root and the expansion workspace."""
import csv
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
B = os.path.join(ROOT, "deliverables", "2026-10-09_v5", "before")
OUT = os.path.join(ROOT, "deliverables", "2026-10-09_v5", "tables")
R = lambda p: list(csv.DictReader(open(p), delimiter="\t"))  # noqa: E731


def run(label, before_dir, after_dir):
    rows = []

    def add(table, key, field, before, after, reason):
        rows.append(dict(scope=label, table=table, key=key, field=field, before=before, after=after, reason=reason))
    # pair summary: v4 forward replicate 1 (or the v4 primary replicate) vs v5 single row
    b = {r["pair_id"]: r for r in R(f"{before_dir}/pair_summary.tsv")
         if r["direction"] == "forward" and r["replicate"] == "1" and not r["run_id"].startswith("attempt")}
    a = {r["pair_id"]: r for r in R(f"{after_dir}/pair_summary.tsv")}
    for pid in sorted(set(a) | set(b)):
        if pid not in a or pid not in b:
            add("pair_summary", pid, "row", pid in b, pid in a, "pair missing on one side")
            continue
        if b[pid]["run_id"] != a[pid]["star3d_run_id"]:
            add("pair_summary", pid, "run_id", b[pid]["run_id"], a[pid]["star3d_run_id"], "different selected run")
        for f in a[pid]:
            if f in b[pid] and f not in ("run_id",) and a[pid][f] != b[pid][f]:
                add("pair_summary", pid, f, b[pid][f], a[pid][f], "value changed")
    nb_all = len(R(f"{before_dir}/pair_summary.tsv"))
    add("pair_summary", "ALL", "rows", nb_all, len(a), "rows removed: reverse-direction runs, replicates 2-3 and "
        "historical attempts are no longer active rows (archived)")
    # correspondence per residue
    bc = {(r["pair_id"], r["source_row_index"]): r for r in R(f"{before_dir}/correspondence_comparison.tsv")
          if r["direction"] == "forward" and r["replicate"] == "1" and not r["run_id"].startswith("attempt")}
    ac = {(r["pair_id"], r["source_row_index"]): r for r in R(f"{after_dir}/correspondence_comparison.tsv")}
    nd = 0
    for k in sorted(set(ac) | set(bc)):
        if k not in ac or k not in bc:
            add("correspondence_comparison", "|".join(k), "row", k in bc, k in ac, "residue row missing on one side"); nd += 1
            continue
        for f in ("rfam_partner", "star3d_partner", "category", "rfam_missing_reason", "star3d_missing_reason",
                  "rfam_pair_structurally_assessable", "partner_offset"):
            if ac[k][f] != bc[k][f]:
                add("correspondence_comparison", "|".join(k), f, bc[k][f], ac[k][f], "value changed"); nd += 1
    add("correspondence_comparison", "ALL", "residue rows compared", len(bc), len(ac), f"{nd} differing values")
    # interaction summary: v4 rfam_vs_star3d_forward -> v5 rfam_vs_star3d
    bi = {(r["pair_id"], r["source_side"], r["interaction_class"]): r for r in R(f"{before_dir}/interaction_summary.tsv")
          if r["comparison"] == "rfam_vs_star3d_forward"}
    ai = {(r["pair_id"], r["source_side"], r["interaction_class"]): r for r in R(f"{after_dir}/interaction_summary.tsv")}
    ni = 0
    for k in sorted(set(ai) | set(bi)):
        if k not in ai or k not in bi:
            add("interaction_summary", "|".join(k), "row", k in bi, k in ai, "missing on one side"); ni += 1
            continue
        for fb, fa in (("source_interactions", "source_interactions"), ("eligible_unmasked", "eligible_unmasked"),
                       ("rfam_preserved_eligible", "rfam_preserved_eligible"),
                       ("star3d_forward_preserved_eligible", "star3d_preserved_eligible"),
                       ("rfam_coverage_all", "rfam_coverage_all"), ("star3d_forward_coverage_all", "star3d_coverage_all"),
                       ("star3d_forward_preserved_all", "star3d_preserved_all")):
            if bi[k][fb] != ai[k][fa]:
                add("interaction_summary", "|".join(k), fa, bi[k][fb], ai[k][fa], "value changed"); ni += 1
    add("interaction_summary", "ALL", "rows (v4 all comparisons -> v5)", len(R(f"{before_dir}/interaction_summary.tsv")),
        len(ai), f"{ni} differing values on the retained comparison; 'rfam_vs_star3d_reverse' and 'all_three_methods' "
                 "comparisons and star3d_reverse columns removed from the active table (archived)")
    # interaction comparison per interaction
    key = lambda r: (r["pair_id"], r["source_side"], r["i"], r["j"], r["label"])  # noqa: E731
    bx = {key(r): r for r in R(f"{before_dir}/interaction_comparison.tsv")}
    ax = {key(r): r for r in R(f"{after_dir}/interaction_comparison.tsv")}
    nx = 0
    renamed = [0]
    for k in sorted(set(ax) | set(bx)):
        if k not in ax or k not in bx:
            add("interaction_comparison", "|".join(k), "row", k in bx, k in ax, "missing on one side"); nx += 1
            continue
        for fb, fa in (("rfam_status", "rfam_status"), ("star3d_forward_status", "star3d_status"),
                       ("star3d_forward_target", "star3d_target"), ("eligible_rfam_vs_star3d_forward", "eligible_rfam_vs_star3d"),
                       ("exclusion_rfam_vs_star3d_forward", "exclusion_rfam_vs_star3d")):
            bv = (bx[k][fb] or "").replace("star3d_forward_", "star3d_")   # method renamed star3d_forward -> star3d
            if bv != ax[k][fa]:
                add("interaction_comparison", "|".join(k), fa, bx[k][fb], ax[k][fa], "value changed"); nx += 1
            elif bx[k][fb] != ax[k][fa]:
                renamed[0] += 1
    add("interaction_comparison", "ALL", "interactions compared", len(bx), len(ax),
        f"{nx} differing values; {renamed[0]} exclusion labels renamed only (star3d_forward_* -> star3d_*); "
        "star3d_reverse and all_three_methods columns removed (archived)")
    # regions
    br = {r["region_id"]: r for r in R(f"{before_dir}/region_review.tsv")}
    ar = {r["region_id"]: r for r in R(f"{after_dir}/region_review.tsv")}
    nr = 0
    for k in sorted(set(ar) | set(br)):
        if k not in ar or k not in br:
            add("region_review", k, "row", k in br, k in ar, "region missing on one side"); nr += 1
            continue
        for f in ar[k]:
            if f in br[k] and ar[k][f] != br[k][f]:
                add("region_review", k, f, br[k][f][:80], ar[k][f][:80], "value changed"); nr += 1
    add("region_review", "ALL", "regions", len(br), len(ar), f"{nr} differing values; column "
        "'reverse_run_same_star3d_partner' removed")
    return rows


def main():
    out = run("study (7 pilot pairs)", os.path.join(B, "results"), os.path.join(ROOT, "results"))
    if os.path.exists(os.path.join(ROOT, "expansion_v4", "results", "pair_summary.tsv")):
        out += run("expansion_v4 (tRNA pair)", os.path.join(B, "expansion_v4_results"), os.path.join(ROOT, "expansion_v4", "results"))
    with open(os.path.join(OUT, "before_after_single_run.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(out[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    for r in out:
        print(r)


if __name__ == "__main__":
    main()
