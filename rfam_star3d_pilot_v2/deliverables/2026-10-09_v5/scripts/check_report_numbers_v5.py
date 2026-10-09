"""Cross-check numbers quoted in the v5 reports, summary, guide and website JSON against the active tables."""
import csv
import json
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
V = os.path.join(ROOT, "deliverables", "2026-10-09_v5")
R = lambda p: list(csv.DictReader(open(os.path.join(ROOT, p)), delimiter="\t"))  # noqa: E731
rep = open(os.path.join(V, "professor_report_v5.md")).read()
guide = open(os.path.join(V, "architecture", "SQARMA_Project_Architecture_and_Pipeline_Guide.md")).read()
ok = bad = 0


def check(label, cond):
    global ok, bad
    ok += bool(cond)
    bad += not cond
    print(("OK  " if cond else "FAIL"), label)


short = {"RF00522__3FU2_A__6VUI_A": "3FU2–6VUI", "RF00522__3FU2_A__7REX_A": "3FU2–7REX", "RF00522__6VUI_A__7REX_A": "6VUI–7REX"}
ps = R("results/pair_summary.tsv")
check("3 accepted pairs", len(ps) == 3 and set(r["pair_id"] for r in ps) == set(short))
for r in ps:
    line = next(l for l in rep.splitlines() if l.startswith("| " + short[r["pair_id"]] + " | attempt"))
    cells = [c.strip() for c in line.strip("|").split("|")]
    check(f"pair table {r['pair_id']}", cells[2:8] == [r["rfam_pairs_structurally_assessable"], r["star3d_pairs"],
                                                       r["same_partner"], r["different_partner"], r["rfam_only"], r["star3d_only"]])
isum = {r["pair_id"]: r for r in R("results/interaction_summary.tsv") if r["source_side"] == "query" and r["interaction_class"] == "all"}
for pid, s in short.items():
    r = isum[pid]
    line = next(l for l in rep.splitlines() if l.startswith(f"| {s} | ") and "/" in l and "attempt" not in l)
    cells = [c.strip() for c in line.strip("|").split("|")]
    check(f"interaction {pid}", cells[1:3] == [f"{r['rfam_preserved_eligible']}/{r['eligible_unmasked']}",
                                               f"{r['star3d_preserved_eligible']}/{r['eligible_unmasked']}"])
el = R("review/natural_sequence_eligibility.tsv")
n = lambda k, v: sum(r[k] == v for r in el)  # noqa: E731
check("13 chains; 4 natural; 9 engineered; 0 unresolved", (len(el), n("natural_sequence_status", "verified_natural"),
      n("natural_sequence_status", "confirmed_engineered"), n("natural_sequence_status", "unresolved")) == (13, 4, 9, 0))
ba = {r["item"]: r for r in R("deliverables/2026-10-09_v5/tables/before_after_natural_dataset.tsv")}
check("before/after pairs 8->3", ba["Pairs"]["previous_dataset"] == "8" and ba["Pairs"]["natural_sequence_dataset"] == "3")
check("before/after structures 13->3", ba["Structures (RNA chains) analysed"]["previous_dataset"] == "13"
      and ba["Structures (RNA chains) analysed"]["natural_sequence_dataset"] == "3")
from collections import Counter  # noqa: E402
rv = [r for r in R("review/region_review_v4.tsv") if r["region_id"].startswith("RF00522")]
c = Counter(r["classification"] for r in rv)
check("region verdicts 2/1/2/4 and 8 regions", (c["supported_candidate_Rfam_correspondence_issue"], c["possible_STAR3D_correspondence_issue"],
      c["construct_or_coordinate_confound"], c["insufficient_evidence"]) == (2, 1, 2, 4) and len(R("results/region_review.tsv")) == 8)
sr = [r for r in R("deliverables/2026-10-09_v5/tables/before_after_single_run.tsv") if r["key"] == "ALL"]
check("single-run: 0 differing values", all(r["reason"].startswith("0 differing") or "0 differing values" in r["reason"]
                                            for r in sr if r["table"] != "pair_summary" and r["scope"].startswith("study")))
m = R("deliverables/2026-10-09_v5/tables/mutation_check_v5.tsv")
check("mutation 18/18", len(m) == 18 and all(r["result"] == "DETECTED" for r in m))
check("81 tests", "81 passed" in open(os.path.join(V, "logs", "pytest_final_v5.txt")).read() and "81 regression tests" in guide)
prim = R("results/primary_star3d_outputs.tsv")
check("primary outputs all selected forward", len(prim) == 3 and all(r["status"] == "selected" and "__forward" in r["selected_run_id"] for r in prim))
site = os.path.join(V, "site", "data")
k = json.load(open(os.path.join(site, "kpis.json")))["values"]
check("site KPIs", (k["accepted_pairs"], k["families_with_accepted_pairs"], k["verified_natural"], k["confirmed_engineered"],
                    k["star3d_outputs_used"]) == (3, 1, 4, 9, 3))
sp = json.load(open(os.path.join(site, "pair_summary.json")))
check("site pair rows == table", [r["pair_id"] for r in sp["rows"]] == [r["pair_id"] for r in ps])
bad_keys = {f"{r['pdb_id']}_{r['auth_chain']}" for r in el if r["analysis_eligibility"] != "accepted"}
leak = [f for f in ("pair_summary.json", "interactions.json", "regions.json", "alignment_views.json", "primary_outputs.json")
        if any(set(row.get("pair_id", "").split("__")[1:]) & bad_keys for row in json.load(open(os.path.join(site, f)))["rows"])]
check("no excluded pair in site results", not leak)
print(f"{ok} OK, {bad} FAIL")
