#!/usr/bin/env python3
"""v5 website exporter: writes deliverables/2026-10-09_v5/site/data/*.json from the ACTIVE tables only (natural-
sequence cohort, one selected original-STAR3D output per pair). Every number shown on the site comes from these JSON
files; data/export_manifest.json lists every source with sha256 and row count. Missing inputs -> 'unavailable'.
Usage (study directory): .venv/bin/python scripts/export_site_data.py"""
import csv
import datetime as dt
import hashlib
import json
import shutil
import subprocess
import sys
from collections import Counter
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parent.parent
DELIV = ROOT / "deliverables" / "2026-10-09_v5"
SITE = DELIV / "site"
DATA, ASSETS, DOWNLOADS = SITE / "data", SITE / "assets", SITE / "downloads"
csv.field_size_limit(sys.maxsize)
SOURCES, UNAVAILABLE = [], []


def rel(p):
    try:
        return str(Path(p).relative_to(ROOT))
    except ValueError:
        return str(p)


def sha(p):
    return hashlib.sha256(Path(p).read_bytes()).hexdigest()


def read(p, optional=False):
    p = Path(p)
    if not p.exists():
        if optional:
            UNAVAILABLE.append(rel(p))
            return None
        raise SystemExit(f"required input missing: {rel(p)}")
    lines = [l for l in open(p, encoding="utf-8") if not l.startswith("#")]
    rows = list(csv.DictReader(lines, delimiter="\t"))
    SOURCES.append({"path": rel(p), "sha256": sha(p), "rows": len(rows)})
    return rows


def payload(rows, p, columns=None):
    if rows is None:
        return {"available": False, "source": rel(p), "columns": [], "rows": []}
    cols = columns or (list(rows[0].keys()) if rows else [])
    return {"available": True, "source": rel(p), "columns": cols, "rows": [{c: r.get(c, "") for c in cols} for r in rows]}


def write(name, obj):
    (DATA / name).write_text(json.dumps(obj, indent=1, ensure_ascii=False))


def main():
    for d in (DATA, ASSETS, DOWNLOADS):
        d.mkdir(parents=True, exist_ok=True)
    R, RV, T = ROOT / "results", ROOT / "review", DELIV / "tables"
    elig_p = RV / "natural_sequence_eligibility.tsv"
    elig = read(elig_p)
    chains_p = R / "dataset_chains.tsv"
    pairs_p, reps_p = R / "selected_pairs.tsv", R / "selected_representatives.tsv"
    pairs, reps = read(pairs_p), read(reps_p)
    ps_p, prim_p = R / "pair_summary.tsv", R / "primary_star3d_outputs.tsv"
    ps, prim = read(ps_p), read(prim_p)
    is_p, rr_p = R / "interaction_summary.tsv", R / "region_review.tsv"
    isum, rr = read(is_p), read(rr_p)
    fam_p = R / "family_inventory.tsv"
    fam = read(fam_p)
    cur = Counter(r["current_status_v5_natural_policy"].split(":")[0] for r in fam)
    write("kpis.json", {"source": [rel(elig_p), rel(pairs_p), rel(fam_p)], "values": {
        "families_with_accepted_pairs": len({p["rfam_acc"] for p in pairs}),
        "accepted_pairs": len(pairs),
        "accepted_structures_in_pairs": len(reps),
        "chains_reviewed_under_policy": len(elig),
        "verified_natural": sum(r["natural_sequence_status"] == "verified_natural" for r in elig),
        "confirmed_engineered": sum(r["natural_sequence_status"] == "confirmed_engineered" for r in elig),
        "unresolved": sum(r["natural_sequence_status"] == "unresolved" for r in elig),
        "star3d_outputs_used": sum(r["status"] == "selected" for r in prim),
        "families_in_inventory": len(fam),
        "families_screen_pass": sum(r["screen_status"] == "pass" for r in fam)}})
    write("family_status.json", {"source": rel(fam_p), "unit": "Rfam family",
                                 "counts": dict(cur),
                                 "rows": [{k: r[k] for k in ("rfam_acc", "rfam_id", "screen_status",
                                                             "current_status_v5_natural_policy",
                                                             "historical_review_decision_v1_1")}
                                          for r in fam if r["current_status_v5_natural_policy"] != "not_eligible_by_screen"]})
    write("chains.json", payload(read(chains_p), chains_p))
    write("eligibility.json", payload(elig, elig_p))
    write("pairs.json", payload(pairs, pairs_p, ["pair_id", "rfam_acc", "query", "target", "primary_direction", "tier", "rationale"]))
    write("primary_outputs.json", payload(prim, prim_p, ["pair_id", "status", "alignment_order", "selected_run_id", "output_aln",
                                                         "output_sha256", "aligned_n", "rmsd", "parameters",
                                                         "earlier_records_not_selected"]))
    write("pair_summary.json", payload(ps, ps_p))
    write("interactions.json", payload(isum, is_p))
    write("regions.json", payload(rr, rr_p, ["inspection_rank", "region_id", "pair_id", "n_correspondence_disagreements",
                                             "n_coverage_differences", "seed_elements", "eligible_for_structural_adjudication",
                                             "classification", "interpretation"]))
    dv_p = R / "derived_alignment_views.tsv"
    write("alignment_views.json", payload(read(dv_p, optional=True), dv_p))
    re_p = R / "region_evidence" / "summary.tsv"
    write("region_evidence.json", payload(read(re_p, optional=True), re_p))
    cand = {}
    for name in ("adjustment_interaction_summary.tsv", "residue_evidence_RF00522__6VUI_A__7REX_A.tsv",
                 "residue_evidence_RF00522__3FU2_A__7REX_A.tsv"):
        p = RV / "candidate_RF00522" / name
        cand[name.replace(".tsv", "")] = payload(read(p, optional=True), p)
    write("candidate.json", cand)
    extra = {}
    for key, p in (("before_after_natural", T / "before_after_natural_dataset.tsv"),
                   ("before_after_single_run", T / "before_after_single_run.tsv"),
                   ("mutation_check", T / "mutation_check_v5.tsv"), ("tests", T / "test_results_v5.tsv"),
                   ("requirements", ROOT / "deliverables" / "2026-10-09_v4" / "tables" / "requirements_matrix.tsv")):
        rows = read(p, optional=True)
        if key == "before_after_single_run" and rows:
            rows = [r for r in rows if r["key"] == "ALL"]
        extra[key] = payload(rows, p)
    write("validation.json", extra)
    figs = []
    for p in [ROOT / "figures" / "fig_RF00522_6VUI_7REX_P1.png",
              ROOT / "deliverables" / "2026-10-09" / "figures" / "fig_7REX_correspondence_6VUI.png"]:
        if p.exists():
            shutil.copy2(p, ASSETS / p.name)
            SOURCES.append({"path": rel(p), "sha256": sha(p), "rows": None})
            figs.append({"file": f"assets/{p.name}", "source": rel(p)})
        else:
            UNAVAILABLE.append(rel(p))
    write("figures.json", {"figures": figs})
    dl = []
    for label, p, desc in [
        ("Professor report (v5, current)", DELIV / "professor_report_v5.md", "Current validated status"),
        ("Professor summary (current)", ROOT / "reports" / "professor_summary.md", "One page"),
        ("Natural-sequence eligibility decisions", elig_p, "All 13 previously analysed chains"),
        ("Dataset chains", R / "dataset_chains.md", "Readable chain-level table"),
        ("Before/after: natural-sequence dataset", T / "before_after_natural_dataset.tsv", "What changed and why"),
        ("Before/after: single-run refactor", T / "before_after_single_run.tsv", "Every compared value"),
        ("Primary STAR3D outputs", prim_p, "The one selected original output per pair, with hashes"),
        ("Derived alignment views", R / "derived_alignment_views.md", "SQARMA visualisation, not STAR3D raw output"),
        ("Region review", rr_p, "Accepted-pair regions"),
        ("Main report (cumulative)", ROOT / "reports" / "report.md", "Dated sections; v5 at top"),
        ("Architecture guide (PDF)", DELIV / "architecture" / "SQARMA_Project_Architecture_and_Pipeline_Guide.pdf", "Pipeline guide"),
        ("Architecture guide (Word)", DELIV / "architecture" / "SQARMA_Project_Architecture_and_Pipeline_Guide.docx", "Pipeline guide"),
        ("Archive note: multi-run history", ROOT / "archive" / "v4_multi_run_history" / "README.md", "Historical runs, not used"),
        ("Manifest", DELIV / "MANIFEST.tsv", "Outputs, inputs, software, checksums")]:
        if p.exists():
            shutil.copy2(p, DOWNLOADS / p.name)
            dl.append({"label": label, "href": f"downloads/{p.name}", "description": desc})
        else:
            dl.append({"label": label, "href": None, "description": desc})
            UNAVAILABLE.append(rel(p))
    write("downloads.json", {"downloads": dl})
    cfg = yaml.safe_load(open(ROOT / "config.yaml"))
    commit = subprocess.run(["git", "rev-parse", "HEAD"], cwd=ROOT, capture_output=True, text=True).stdout.strip()
    dirty = bool(subprocess.run(["git", "status", "--porcelain", "--", "."], cwd=ROOT, capture_output=True, text=True).stdout.strip())
    write("export_manifest.json", {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"), "git_commit": commit,
        "git_worktree": "dirty" if dirty else "clean", "generator": rel(Path(__file__)),
        "provenance": {"rfam_release": cfg["reference"]["rfam_release"], "seed_sha256": cfg["reference"]["seed_sha256"],
                       "star3d": "original STAR3D v1.2, defaults, one forward alignment per pair",
                       "star3d_sha256": cfg["sources"]["star3d_sha256"], "fr3d": cfg["annotation"]["tool"],
                       "cohort": "2.0_natural"},
        "sources": SOURCES, "unavailable": UNAVAILABLE})
    print(f"wrote {len(list(DATA.glob('*.json')))} JSON files; {len(SOURCES)} sources; unavailable: {UNAVAILABLE}")


if __name__ == "__main__":
    main()
