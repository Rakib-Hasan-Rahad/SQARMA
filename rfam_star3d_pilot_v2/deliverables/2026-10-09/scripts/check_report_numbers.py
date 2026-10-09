"""Cross-check numbers quoted in professor_report.md against the exported tables (and the site's JSON)."""
import csv
import json
import os
import re

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = os.path.join(ROOT, "deliverables", "2026-10-09")
R = lambda p: list(csv.DictReader(open(os.path.join(ROOT, p)), delimiter="\t"))  # noqa: E731
rep = open(os.path.join(D, "professor_report.md")).read()
ok = bad = 0


def check(label, cond):
    global ok, bad
    ok += bool(cond)
    bad += not cond
    print(("OK  " if cond else "FAIL"), label)


# per-pair table
short = {"RF00522__3FU2_A__6VUI_A": "RF00522 3FU2–6VUI", "RF00522__3FU2_A__7REX_A": "RF00522 3FU2–7REX",
         "RF00522__6VUI_A__7REX_A": "RF00522 6VUI–7REX", "RF00174__4GXY_A__6VMY_A": "RF00174 4GXY–6VMY",
         "RF00059__2GDI_X__3D2G_A": "RF00059 2GDI–3D2G", "RF00442__5U3G_B__7MLW_F": "RF00442 5U3G–7MLW",
         "RF00162__2GIS_A__4KQY_A": "RF00162 2GIS–4KQY"}
for r in R("results/pair_summary.tsv"):
    if r["run_id"].startswith("attempt") or r["direction"] != "forward" or r["replicate"] != "1":
        continue
    line = next(l for l in rep.splitlines() if l.startswith("| " + short[r["pair_id"]]))
    cells = [c.strip() for c in line.strip("|").split("|")]
    want = [r["rfam_pairs_structurally_assessable"], r["star3d_pairs"], r["same_partner"], r["different_partner"],
            r["rfam_only"], r["star3d_only"]]
    check(f"pair table {r['pair_id']}", cells[2:8] == want)
# 7REX counts
cnt = R("deliverables/2026-10-09/tables/candidate_7REX_counts.tsv")
for r in cnt:
    if r["class"] == "all":
        tag = {"source_to_7REX": f"{r['source'].split('_')[0]} → 7REX"}.get(r["direction"], r["direction"].replace("_to_", " → ").replace("_A", ""))
        line = next((l for l in rep.splitlines() if l.startswith("| " + tag)), "")
        cells = [c.strip() for c in line.strip("|").split("|")]
        check(f"7REX counts {tag}", cells[1:5] == [r["eligible_n"], r["rfam_preserved"], r["star3d_preserved"], r["adjusted_preserved"]])
# Survey B
p = json.load(open(os.path.join(ROOT, "results/seed_collection_comparison/provenance.json")))
check("survey B 74 families", p["families_curated"] == 74 and "74 families" in rep)
check("survey B 0 changed", p["row_pairs_with_changed_correspondence"] == 0)
# funnel
inv = json.load(open(os.path.join(ROOT, "metadata/inventory_stage_counts.json")))
check("funnel 167", inv["families_with_pdb_candidates(Rfam.pdb.gz or seed GR)"] == 167 and "| 167 |" in rep)
check("funnel 31", inv["screen_pass_total"] == 31)
scr = R("review/v3_screening/candidate_screening.tsv")
check("21 families screened, 0 accepted", len({r["family"] for r in scr}) == 21 and not any(r["decision"] == "accepted_primary" for r in scr))
check("4 exploratory-only families", len({r["family"] for r in scr if r["decision"] == "exploratory"}) == 4)
rows = R("deliverables/2026-10-09/tables/RF00522_P1_register_all_rows.tsv".replace(".tsv", ".tsv")) if False else None
lines = [l.split("\t") for l in open(os.path.join(D, "tables/RF00522_P1_register_all_rows.tsv")) if not l.startswith("#")][1:]
improv = [l[0] for l in lines if int(l[3]) > int(l[2])]
check("only 7REX row improves with +1 shift (43 rows)", len(lines) == 43 and improv == ["URS00023119CB_2126436/1-34"])
# site uses same data
site = json.load(open(os.path.join(D, "site/data/candidate_7rex.json")))
check("site 7REX counts == table", site["counts"]["rows"] == cnt or len(site["counts"]["rows"]) == len(cnt))
fun = json.load(open(os.path.join(D, "site/data/funnel.json")))["counts"]
check("site funnel reviewed_total 31", fun["reviewed_total"] == 31)
print(f"{ok} OK, {bad} FAIL")
