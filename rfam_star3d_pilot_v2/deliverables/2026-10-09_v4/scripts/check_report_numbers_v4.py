"""Cross-check numbers quoted in the v4 reports and guide against the authoritative tables and the site JSON."""
import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = os.path.join(ROOT, "deliverables", "2026-10-09_v4")
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
R = lambda p: list(csv.DictReader(open(P(p)), delimiter="\t"))  # noqa: E731
txt = {n: open(os.path.join(D, n)).read() for n in
       ("professor_report_v4.md", "dataset_and_provenance_v4.md", "method_audit_v4.md", "candidate_evidence_update_v4.md",
        "validation_v4.md", "architecture/SQARMA_Project_Architecture_and_Pipeline_Guide.md")}
rep = txt["professor_report_v4.md"]
ok = bad = 0


def check(label, cond):
    global ok, bad
    ok += bool(cond)
    bad += not cond
    print(("OK  " if cond else "FAIL"), label)


# per-pair table (development + prospective)
short = {"RF00522__3FU2_A__6VUI_A": "RF00522 3FU2–6VUI", "RF00522__3FU2_A__7REX_A": "RF00522 3FU2–7REX",
         "RF00522__6VUI_A__7REX_A": "RF00522 6VUI–7REX", "RF00174__4GXY_A__6VMY_A": "RF00174 4GXY–6VMY",
         "RF00059__2GDI_X__3D2G_A": "RF00059 2GDI–3D2G", "RF00442__5U3G_B__7MLW_F": "RF00442 5U3G–7MLW",
         "RF00162__2GIS_A__4KQY_A": "RF00162 2GIS–4KQY", "RF00005__5CCB_N__7EQJ_B": "*Prospective:* RF00005 5CCB–7EQJ"}
for path in ("results/pair_summary.tsv", "expansion_v4/results/pair_summary.tsv"):
    for r in R(path):
        if r["run_id"].startswith("attempt") or r["direction"] != "forward" or r["replicate"] != "1":
            continue
        line = next(l for l in rep.splitlines() if l.startswith("| " + short[r["pair_id"]]))
        cells = [c.strip() for c in line.strip("|").split("|")]
        want = [r["rfam_pairs_structurally_assessable"], r["star3d_pairs"], r["same_partner"], r["different_partner"],
                r["rfam_only"], r["star3d_only"]]
        check(f"pair table {r['pair_id']}", cells[2:8] == want)
# region classification counts
from collections import Counter  # noqa: E402
c = Counter(r["classification"] for r in R("review/region_review_v4.tsv"))
check("region counts", (c["supported_candidate_Rfam_correspondence_issue"], c["possible_STAR3D_correspondence_issue"],
                        c["construct_or_coordinate_confound"], c["STAR3D_coverage_limitation"], c["insufficient_evidence"],
                        c["not_adjudicated_ineligible"]) == (2, 1, 2, 2, 7, 6) and "| Insufficient evidence | 7 |" in rep)
# sensitivity table
s1 = {(r["pair_id"], r["direction"]): r for r in R("results/sensitivity/S1_vs_default.tsv")}
g = s1[("RF00442__5U3G_B__7MLW_F", "forward")]
check("S1 guanidine 78->25", g["default_aligned"] == "78" and g["S1_aligned"] == "25" and "78 to 25" in rep)
check("S1 preQ1 identical", all(s1[(p, "forward")]["identical_mapping"] == "True" for p in
                               ("RF00522__3FU2_A__6VUI_A", "RF00522__3FU2_A__7REX_A", "RF00522__6VUI_A__7REX_A")))
s2 = R("results/sensitivity/S2_vs_default.tsv")
check("S2 identical", all(r["identical_mapping"] == "True" for r in s2))
# mutation check / tests
m = R("deliverables/2026-10-09_v4/tables/mutation_check.tsv")
check("mutation 16/16", len(m) == 16 and all(r["result"] == "DETECTED" for r in m))
check("64 tests", "64 passed" in open(os.path.join(D, "logs", "pytest_final_v4.txt")).read())
# curated vs ordinary
cv = R("results/rfam_history/curated_vs_ordinary.tsv")
check("curated identical every release", all(r["curated_families"] == r["byte_identical_records"] for r in cv) and
      [r["release"] for r in cv] == ["14.9", "14.10", "15.0", "15.1"])
rf = {r["release"]: r for r in R("results/rfam_history/rf00522_rows.tsv")}
check("7REX row first in 15.0", rf["14.10"]["7REX_row_present"] == "False" and rf["15.0"]["7REX_row_present"] == "True"
      and rf["15.0"]["rex_aligned"] == rf["15.1"]["rex_aligned"])
# tRNA interactions
it = {(r["source_side"], r["interaction_class"]): r for r in R("expansion_v4/results/interaction_summary.tsv")
      if r["comparison"] == "rfam_vs_star3d_forward"}
a = it[("query", "all")]
check("tRNA 81/97", (a["eligible_unmasked"], a["rfam_preserved_eligible"], a["star3d_forward_preserved_eligible"]) == ("97", "81", "81")
      and "81/97" in rep)
# region-level canonical counts quoted for the candidate
sm = {r["region_id"]: r for r in R("results/region_evidence/summary.tsv")}
check("r7-23 canonical 7/0/5", sm["RF00522__6VUI_A__7REX_A__r7-23"]["canonical_eligible_rfam_star3d"] == "7/0/5")
check("r15-22 canonical 5/0/5", sm["RF00522__3FU2_A__7REX_A__r15-22"]["canonical_eligible_rfam_star3d"] == "5/0/5")
# guide example
isum = {(r["interaction_class"]): r for r in R("results/interaction_summary.tsv")
        if r["pair_id"] == "RF00522__6VUI_A__7REX_A" and r["source_side"] == "query" and r["comparison"] == "rfam_vs_star3d_forward"}
check("guide 19/47 29/47", (isum["all"]["eligible_unmasked"], isum["all"]["rfam_preserved_eligible"],
                            isum["all"]["star3d_forward_preserved_eligible"]) == ("47", "19", "29")
      and "19 of 47" in txt["architecture/SQARMA_Project_Architecture_and_Pipeline_Guide.md"])
# site uses the same data
site = os.path.join(D, "site", "data")
np_ = json.load(open(os.path.join(site, "new_pair_summary.json")))
check("site prospective pair available", np_.get("available") and any(g["pair_id"] == "RF00005__5CCB_N__7EQJ_B" for g in np_["rows"]))
v4t = json.load(open(os.path.join(site, "v4_tables.json")))["tables"]
check("site v4 tables all available", all(t["table"]["available"] for t in v4t))
mc = next(t for t in v4t if "mutation" in t["title"])
check("site mutation table == file", len(mc["table"]["rows"]) == 16)
fun = json.load(open(os.path.join(site, "funnel.json")))["counts"]
check("site funnel reviewed_total 31", fun["reviewed_total"] == 31)
print(f"{ok} OK, {bad} FAIL")
