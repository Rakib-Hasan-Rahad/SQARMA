"""Render review/region_review_v4.tsv (+ prospective) and results/region_evidence/summary.tsv into Markdown."""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
R = lambda p: list(csv.DictReader(open(P(p)), delimiter="\t"))  # noqa: E731
summ = {r["region_id"]: r for r in R("results/region_evidence/summary.tsv")}
summ.update({r["region_id"]: r for r in R("expansion_v4/results/region_evidence/summary.tsv")})
rev = R("review/region_review_v4.tsv") + R("expansion_v4/review/region_review_v4.tsv")
out = ["# Region review: all regions (v4, 2026-10-09)", "",
       "*Generated from `review/region_review_v4.tsv`, `expansion_v4/review/region_review_v4.tsv` and "
       "`results/region_evidence/summary.tsv` by `deliverables/2026-10-09_v4/scripts/render_region_review.py`. "
       "Reviewer: AI agent (Claude); no human review.*", "",
       "How to read the evidence columns:",
       "",
       "- **Interactions:** canonical / noncanonical / stacking counts on the rfam-vs-STAR3D-forward eligible set, "
       "written as n / seed preserved / STAR3D preserved.",
       "- **Closer (C1′):** for the residues whose partners differ, how many had the seed partner closer and how many "
       "the STAR3D partner, after the shared-anchor fit.",
       "- **Local fit:** the same comparison using anchors within ±8 positions of the region.",
       "",
       "| Region | Sub-span | Classification (confidence) | Residues: categories | Interactions can/nc/stack | Closer (C1′, shared) | Local fit | Fwd=Rev |",
       "|---|---|---|---|---|---|---|---|"]
for r in rev:
    s = summ.get(r["region_id"], {})
    out.append(f"| {r['region_id'].replace('__', ' ')} | {r['sub_span']} | {r['classification']} ({r['confidence']}) | "
               f"{s.get('categories', 'NA')} | {s.get('canonical_eligible_rfam_star3d', 'NA')} · "
               f"{s.get('noncanonical_eligible_rfam_star3d', 'NA')} · {s.get('stack_eligible_rfam_star3d', 'NA')} | "
               f"{s.get('closer_C1p_shared', 'NA')} | {s.get('closer_C1p_local', 'NA')} | "
               f"{s.get('star3d_fwd_rev_same', 'NA')}/{s.get('n_residues', 'NA')} |")
out += ["", "## Evidence and confounds, region by region", ""]
for r in rev:
    out += [f"**{r['region_id']} — {r['sub_span']}: {r['classification']} ({r['confidence']})**", "",
            f"- For the seed: {r['evidence_for_rfam']}", f"- For STAR3D: {r['evidence_for_star3d']}",
            f"- Confounds and limits: {r['confounds_and_limits']}", ""]
open(P("deliverables/2026-10-09_v4/region_review_v4.md"), "w").write("\n".join(out))
print(len(rev), "rows rendered")
