"""v4: write the dated manual review (review/region_review_v4.tsv) into results/region_review.tsv.
The previous interpretation text is retained after 'previous:' so review history is never lost."""
import csv
import os
from collections import defaultdict

ROOT = os.environ.get("SQARMA_STUDY_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # v4: workspace override
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
rev = defaultdict(list)
for r in csv.DictReader(open(P("review/region_review_v4.tsv")), delimiter="\t"):
    rev[r["region_id"]].append(r)
rows = list(csv.DictReader(open(P("results/region_review.tsv")), delimiter="\t"))
fields = list(rows[0])
missing = [r["region_id"] for r in rows if r["region_id"] not in rev]
if missing:
    raise SystemExit(f"regions without a v4 review: {missing}")
for r in rows:
    v = rev[r["region_id"]]
    prev = "" if r["interpretation"] in ("", "NA") else f" || previous: [{r['classification']}] {r['interpretation']}"
    r["inspected"] = "inspected_v4"
    r["classification"] = " | ".join(f"{x['sub_span']}: {x['classification']} ({x['confidence']})" for x in v)
    r["interpretation"] = " | ".join(
        f"v4 {x['sub_span']}: for seed: {x['evidence_for_rfam']}; for STAR3D: {x['evidence_for_star3d']}; "
        f"confounds: {x['confounds_and_limits']}" for x in v) + prev
    r["interpretation_source"] = "manual review review/region_review_v4.tsv (AI agent, 2026-10-09; no human review); evidence results/region_evidence/"
tmp = P("results/region_review.tsv.tmp")
with open(tmp, "w", newline="") as f:
    w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
    w.writeheader()
    w.writerows(rows)
os.replace(tmp, P("results/region_review.tsv"))
print(len(rows), "regions updated")
