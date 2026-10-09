#!/usr/bin/env python3
"""Export project tables to JSON for the static presentation site.

Writes deliverables/2026-10-09_v4/site/data/*.json, copies figures into site/assets/ and
download files into site/downloads/, and writes data/export_manifest.json with the
sha256, row count and path of every source read, the generation UTC time and git commit.

No numbers are invented here: every value is read from a project table. Missing optional
inputs are recorded as unavailable (never as zero).

Usage (from the study directory):  .venv/bin/python scripts/export_site_data.py
"""
from __future__ import annotations

import csv
import datetime as dt
import hashlib
import json
import re
import shutil
import subprocess
import sys
from collections import Counter, OrderedDict
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DELIV = ROOT / "deliverables" / "2026-10-09_v4"      # v4: live site; deliverables/2026-10-09/site is a v3 snapshot
V3T = ROOT / "deliverables" / "2026-10-09" / "tables"  # v3 session tables still current (7REX, Survey B, screening)
EXP = ROOT / "expansion_v4"                          # v4 prospective (non-curated family) workspace
SITE = DELIV / "site"
DATA = SITE / "data"
ASSETS = SITE / "assets"
DOWNLOADS = SITE / "downloads"
TABLES = DELIV / "tables"

csv.field_size_limit(sys.maxsize)
SOURCES: list[dict] = []
UNAVAILABLE: list[dict] = []


def rel(p: Path) -> str:
    try:
        return str(p.relative_to(ROOT))
    except ValueError:
        return str(p)


def sha256(p: Path) -> str:
    h = hashlib.sha256()
    with open(p, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def record(p: Path, rows, role: str) -> None:
    SOURCES.append({"path": rel(p), "sha256": sha256(p), "rows": rows, "role": role})


def read_tsv(p: Path, role: str = "required", optional: bool = False):
    """Return list of dict rows, or None if missing (optional) — comment lines (#) kept aside."""
    if not p.exists():
        if optional:
            UNAVAILABLE.append({"path": rel(p), "role": role, "status": "unavailable"})
            return None
        raise FileNotFoundError(p)
    comments = []
    lines = []
    with open(p, newline="", encoding="utf-8") as fh:
        for line in fh:
            if line.startswith("#"):
                comments.append(line.rstrip("\n"))
            elif line.strip():
                lines.append(line)
    rows = list(csv.DictReader(lines, delimiter="\t"))
    record(p, len(rows), role)
    for r in rows:  # normalise None keys/values
        for k in list(r):
            if r[k] is None:
                r[k] = ""
        r.pop(None, None)
    if comments:
        rows = rows  # comments returned separately via read_tsv_with_comments
    return rows


def read_tsv_with_comments(p: Path, role: str):
    if not p.exists():
        UNAVAILABLE.append({"path": rel(p), "role": role, "status": "unavailable"})
        return None, []
    comments = [l.rstrip("\n") for l in open(p, encoding="utf-8") if l.startswith("#")]
    return read_tsv(p, role), comments


def table_payload(rows, source: Path):
    if rows is None:
        return {"available": False, "source": rel(source), "columns": [], "rows": []}
    cols = list(rows[0].keys()) if rows else []
    return {"available": True, "source": rel(source), "columns": cols, "rows": rows}


def write(name: str, obj) -> None:
    with open(DATA / name, "w", encoding="utf-8") as fh:
        json.dump(obj, fh, indent=1, ensure_ascii=False)


def git_commit() -> str:
    try:
        return subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
    except Exception:
        return "unavailable"


def git_dirty() -> str:
    try:
        out = subprocess.check_output(["git", "status", "--porcelain"], cwd=ROOT, text=True)
        return "dirty" if out.strip() else "clean"
    except Exception:
        return "unavailable"


def config_provenance() -> dict:
    p = ROOT / "config.yaml"
    prov = {}
    if not p.exists():
        UNAVAILABLE.append({"path": "config.yaml", "role": "provenance", "status": "unavailable"})
        return prov
    txt = p.read_text(encoding="utf-8")
    record(p, len(txt.splitlines()), "provenance (lines)")

    def grab(key):
        m = re.search(rf"^\s*{key}:\s*\"?([^\"#\n]+?)\"?\s*(#.*)?$", txt, re.M)
        return m.group(1).strip() if m else "unavailable"

    for k in ["reference_source", "rfam_release", "seed_url", "seed_sha256", "star3d_url",
              "star3d_sha256", "cohort_version", "prompt_version"]:
        prov[k] = grab(k)
    m = re.search(r"fr3d-python.*?commit\s+([0-9a-f]{7,40})", txt)
    prov["fr3d_commit"] = m.group(1) if m else "unavailable"
    m = re.search(r"STAR3D_v([0-9.]+)\.tar", txt)
    prov["star3d_version"] = m.group(1) if m else "unavailable"
    return prov


def to_int(v):
    try:
        return int(v)
    except (TypeError, ValueError):
        return None


def main() -> int:
    for d in (DATA, ASSETS, DOWNLOADS):
        d.mkdir(parents=True, exist_ok=True)

    R = ROOT / "results"
    RV = ROOT / "review"

    # ---------------------------------------------------------------- families / funnel
    fam_p = R / "family_inventory.tsv"
    fam = read_tsv(fam_p)
    funnel = OrderedDict()
    funnel["families_in_inventory"] = len(fam)
    funnel["screen_status"] = dict(Counter(r["screen_status"] for r in fam))
    funnel["shortlisted"] = dict(Counter(r["shortlisted"] for r in fam))
    funnel["review_status"] = dict(Counter(r["review_status"] for r in fam))
    funnel["review_decision"] = dict(Counter(r["review_decision"] for r in fam))
    keep = ["rfam_acc", "rfam_id", "type", "model_length_RF", "seed_rows", "explicit_gr_links",
            "explicit_linked_distinct_sequences", "explicit_linked_taxa_nonsynthetic",
            "screen_status", "shortlisted", "review_status", "review_decision"]
    write("families.json", {"source": rel(fam_p), "unit": "Rfam family",
                            "columns": keep, "rows": [{k: r.get(k, "") for k in keep} for r in fam]})
    # v3 screening (2026-10-09): families reviewed this session, from the screening table (not in family_inventory)
    scr_p = ROOT / "review" / "v3_screening" / "candidate_screening.tsv"
    scr = read_tsv(scr_p, optional=True, role="v3 screening") or []
    v3fam = sorted({r["family"] for r in scr})
    acc = lambda d: sorted({r["family"] for r in scr if r["decision"] == d})  # noqa: E731
    funnel["v3_reviewed_families"] = len(v3fam) if scr else None
    funnel["v3_accepted_primary_families"] = len(acc("accepted_primary")) if scr else None
    funnel["v3_exploratory_only_families"] = len(acc("exploratory")) if scr else None
    funnel["reviewed_total"] = (funnel["review_status"].get("verified", 0) + len(v3fam)) if scr else None
    write("funnel.json", {"source": rel(fam_p), "v3_source": rel(scr_p), "unit": "Rfam family", "counts": funnel})

    # ---------------------------------------------------------------- cohort
    sp_p, rep_p = R / "selected_pairs.tsv", R / "selected_representatives.tsv"
    pairs = read_tsv(sp_p)
    reps = read_tsv(rep_p)
    write("pairs.json", table_payload(pairs, sp_p))
    rep_cols = ["rep_id", "rfam_acc", "family_decision", "decision", "source", "pdb_id", "auth_asym_id",
                "row_name", "masked_label_seq_ids", "observed_fraction", "link_status", "seed_row_lines"]
    write("representatives.json", {"source": rel(rep_p), "columns": rep_cols,
                                   "rows": [{k: r.get(k, "") for k in rep_cols} for r in reps]})
    for name, p in [("construct_review.json", RV / "construct_review.tsv"),
                    ("exact_source_check.json", RV / "exact_source_check.tsv")]:
        write(name, table_payload(read_tsv(p, optional=True, role="review"), p))

    # ---------------------------------------------------------------- runs
    rm_p = R / "run_manifest.tsv"
    rm = read_tsv(rm_p)
    cur = [r for r in rm if not r["run_id"].startswith("attempt")]
    hist = [r for r in rm if r["run_id"].startswith("attempt")]
    write("run_status.json", {
        "source": rel(rm_p), "unit": "STAR3D step (run_manifest row)",
        "current_rows": len(cur), "historical_attempt_rows_excluded": len(hist),
        "current_status_counts": dict(Counter(r["status"] for r in cur)),
        "current_direction_counts": dict(Counter(r["direction"] for r in cur)),
    })

    # ---------------------------------------------------------------- pair summary
    ps_p = R / "pair_summary.tsv"
    ps = [r for r in read_tsv(ps_p) if not r["run_id"].startswith("attempt")]
    rc_p = R / "replicate_consistency.tsv"
    rc = read_tsv(rc_p, optional=True, role="replicates") or []
    rc += read_tsv(EXP / "results" / "replicate_consistency.tsv", optional=True, role="prospective replicates") or []
    rc_idx = {(r["pair_id"], r["direction"]): r for r in rc}
    tier_by_pair = {p["pair_id"]: p["tier"] for p in pairs}
    tier_by_pair.update({p["pair_id"]: p["tier"] for p in (read_tsv(EXP / "results" / "selected_pairs.tsv", optional=True,
                                                                     role="prospective pairs") or [])})

    def summarise(rows, src):
        out = OrderedDict()
        for r in rows:
            key = (r["pair_id"], r["direction"])
            g = out.setdefault(key, {"pair_id": r["pair_id"], "direction": r["direction"],
                                     "tier": r.get("tier") or tier_by_pair.get(r["pair_id"], ""),
                                     "runs": 0, "completed_runs": 0, "status_counts": Counter(),
                                     "values": None})
            g["runs"] += 1
            g["status_counts"][r["status"]] += 1
            if r["status"] == "completed":
                g["completed_runs"] += 1
                if g["values"] is None:
                    g["values"] = {k: r[k] for k in r if k not in ("run_id",)}
        res = []
        for (pid, d), g in out.items():
            g["status_counts"] = dict(g["status_counts"])
            c = rc_idx.get((pid, d))
            g["replicates_identical"] = c["identical_across_replicates"] if c else "unavailable"
            g["distinct_outputs"] = c["distinct_outputs"] if c else "unavailable"
            res.append(g)
        return {"source": rel(src), "unit": "residue of the source row (per STAR3D run direction)",
                "note": "values from the first completed replicate; replicate identity from replicate_consistency.tsv",
                "rows": res}

    write("pair_summary.json", summarise(ps, ps_p))

    new_ps_p = EXP / "results" / "pair_summary.tsv"
    new_ps = read_tsv(new_ps_p, optional=True, role="prospective pairs")
    if new_ps is None:
        write("new_pair_summary.json", {"available": False, "source": rel(new_ps_p), "rows": []})
    else:
        s = summarise([r for r in new_ps if not r.get("run_id", "").startswith("attempt")], new_ps_p)
        s["available"] = True
        write("new_pair_summary.json", s)

    # ---------------------------------------------------------------- interactions / regions
    is_p = R / "interaction_summary.tsv"
    is_rows = read_tsv(is_p) + (read_tsv(EXP / "results" / "interaction_summary.tsv", optional=True,
                                         role="prospective interactions") or [])
    write("interactions.json", dict(table_payload(is_rows, is_p),
                                    unit="FR3D-annotated intrachain interaction of the source structure"))
    rr_p = R / "region_review.tsv"
    rr = read_tsv(rr_p) + (read_tsv(EXP / "results" / "region_review.tsv", optional=True, role="prospective regions") or [])
    rr_cols = ["inspection_rank", "region_id", "pair_id", "tier", "n_correspondence_disagreements",
               "n_coverage_differences", "seed_elements", "eligible_for_structural_adjudication",
               "inspected", "classification"]
    write("regions.json", {"source": rel(rr_p), "columns": rr_cols,
                           "rows": [{k: r.get(k, "") for k in rr_cols} for r in rr]})

    # ---------------------------------------------------------------- 7REX candidate
    cand = RV / "candidate_RF00522"
    adj_p = cand / "adjustment_interaction_summary.tsv"
    if not adj_p.exists():
        adj_p = cand / "adjustment_interactions_summary.tsv"
    adj = read_tsv(adj_p, optional=True, role="7REX adjustment summary")
    val_p = cand / "adjustment_validation.json"
    val = None
    if val_p.exists():
        val = json.loads(val_p.read_text(encoding="utf-8"))
        record(val_p, len(val), "7REX adjustment validation (keys)")
    else:
        UNAVAILABLE.append({"path": rel(val_p), "role": "7REX validation", "status": "unavailable"})
    anchor = []
    for p in sorted((R / "anchor_fit").glob("*.tsv")):
        rows, comments = read_tsv_with_comments(p, "anchor fit")
        header = " ".join(c.lstrip("# ") for c in comments)
        m = re.search(r"fit RMSD ([0-9.]+)", header)
        n = re.search(r"(\d+) anchors", header)
        rule = re.search(r"rule=(\S+?);", header)
        anchor.append({"file": rel(p), "header": header,
                       "fit_rmsd_A": m.group(1) if m else "unavailable",
                       "n_anchors": n.group(1) if n else "unavailable",
                       "rule": rule.group(1) if rule else "unavailable",
                       "columns": list(rows[0].keys()) if rows else [], "rows": rows or []})
    corr_p = V3T / "candidate_7REX_correspondence.tsv"
    cnt_p = V3T / "candidate_7REX_counts.tsv"
    seven = [r for r in rr if "7REX" in r["pair_id"] and r["inspected"].startswith("inspected")]
    write("candidate_7rex.json", {
        "adjustment_summary": table_payload(adj, adj_p),
        "validation": {"available": val is not None, "source": rel(val_p), "data": val},
        "anchor_fits": anchor,
        "correspondence": table_payload(read_tsv(corr_p, optional=True, role="7REX correspondence"), corr_p),
        "counts": table_payload(read_tsv(cnt_p, optional=True, role="7REX counts"), cnt_p),
        "regions": [{k: r.get(k, "") for k in rr_cols + ["interpretation", "interpretation_source"]}
                    for r in seven],
    })

    # ---------------------------------------------------------------- session tables (optional)
    opt = {
        "candidate_screening": [V3T / "candidate_screening.tsv",
                                ROOT / "review" / "v3_screening" / "candidate_screening.tsv"],
        "requirements_status": [TABLES / "requirements_matrix.tsv"],
        "test_results": [TABLES / "test_results.tsv"],
        "validation_checks": [TABLES / "validation_gates.tsv"],
        "results_status": [TABLES / "results_status.tsv"],
        "survey_b": [V3T / "survey_b_summary.tsv"],
        "rf00522_rows": [V3T / "RF00522_P1_register_all_rows.tsv"],
        "fresh_repro_other4": [V3T / "fresh_repro_other4.tsv"],
        "method_differences": [V3T / "candidate_7REX_method_differences.tsv"],
    }
    for name, cands in opt.items():
        found = next((c for c in cands if c.exists()), None)
        if found is None:
            for c in cands:
                UNAVAILABLE.append({"path": rel(c), "role": name, "status": "unavailable"})
            write(f"{name}.json", table_payload(None, cands[0]))
        else:
            write(f"{name}.json", table_payload(read_tsv(found, role=name), found))

    # ---------------------------------------------------------------- v4 tables (generic, per section)
    v4 = [
        ("validation", "Repairs re-checked by re-introducing each defect (mutation test)", TABLES / "mutation_check.tsv",
         "Each historical defect was re-inserted into a scratch copy of the code; DETECTED = its regression test failed."),
        ("validation", "Conclusions changed, refined or withdrawn in v4", TABLES / "conclusions_changed.tsv", ""),
        ("method", "How original STAR3D selects base pairs for its stacks (per RNA)",
         DELIV / "star3d_sensitivity" / "preproc_summary.tsv",
         "STAR3D labels any cis W-edge MC-Annotate pair 'WWc' (incl. non-canonical identities); one residue can keep "
         "only the last-written partner (overwrite)."),
        ("method", "Sensitivity S1: STAR3D with the paper's pairing rule (NOT the primary method)",
         R / "sensitivity" / "S1_vs_default.tsv", "Columns named S1_* are the sensitivity run; default = original STAR3D."),
        ("method", "Sensitivity S2: only the overwrite corrected (7MLW residue 16; NOT the primary method)",
         R / "sensitivity" / "S2_vs_default.tsv", "Columns named S1_* here hold the S2 values (shared comparison code)."),
        ("results", "Evidence summary for every region (anchor-fit geometry, interactions, contacts)",
         R / "region_evidence" / "summary.tsv", "closer_* = number of different-partner residues whose seed or STAR3D "
         "partner is closer after superposition on shared anchors (tie = within 0.5 A)."),
        ("results", "Manual review of every region (v4, AI agent)", ROOT / "review" / "region_review_v4.tsv", ""),
        ("dataset", "Rfam release history: RF00522 rows across releases 14.0-15.1", R / "rfam_history" / "rf00522_rows.tsv",
         "p1_6vui_16_to_7rex = the 7REX residue the seed pairs with 6VUI C16."),
        ("dataset", "Curated vs ordinary seed records in every release that ships a curated file",
         R / "rfam_history" / "curated_vs_ordinary.tsv", ""),
        ("dataset", "Prospective expansion: tRNA (RF00005) candidate structures screened",
         ROOT / "review" / "v4_expansion" / "candidate_structures.tsv", "Pre-registered in review/v4_expansion/PREREGISTRATION.md."),
        ("results", "Prospective tRNA pair: interaction preservation (FR3D)", EXP / "results" / "interaction_summary.tsv", ""),
    ]
    v4_out = []
    for sec, title, p, note in v4:
        rows = read_tsv(p, optional=True, role=title)
        payload = table_payload(rows, p) if rows is not None else {"available": False, "source": rel(p), "rows": []}
        v4_out.append({"section": sec, "title": title, "note": note, "table": payload})
    write("v4_tables.json", {"tables": v4_out})

    # ---------------------------------------------------------------- figures
    figs = []
    fig_src = [ROOT / "figures" / "fig_RF00522_6VUI_7REX_P1.png"]
    fig_src += sorted((ROOT / "figures").glob("*anchorfit*.png"))
    fig_src += sorted((V3T.parent / "figures").glob("*.png")) if (V3T.parent / "figures").exists() else []
    fig_src += sorted((DELIV / "figures").glob("*.png")) if (DELIV / "figures").exists() else []
    for p in fig_src:
        if not p.exists():
            UNAVAILABLE.append({"path": rel(p), "role": "figure", "status": "unavailable"})
            continue
        shutil.copy2(p, ASSETS / p.name)
        SOURCES.append({"path": rel(p), "sha256": sha256(p), "rows": None, "role": "figure"})
        figs.append({"file": f"assets/{p.name}", "source": rel(p)})
    write("figures.json", {"figures": figs})

    # ---------------------------------------------------------------- downloads
    dl_p = TABLES / "downloads.tsv"
    dl_rows = read_tsv(dl_p, optional=True, role="downloads list")
    default = [
        ("Professor summary", ROOT / "reports" / "professor_summary.md", "Plain-language summary (v2.1)"),
        ("Full report", ROOT / "reports" / "report.md", "Technical report"),
        ("Validation report", ROOT / "reports" / "validation_report.md", "Validation details"),
        ("Data dictionary", ROOT / "reports" / "data_dictionary.md", "Column meanings for every table"),
        ("Evidence cards", ROOT / "reports" / "evidence_cards.md", "Per-claim evidence"),
        ("Blockers", ROOT / "reports" / "blockers.md", "Open blockers"),
        ("Pair summary", R / "pair_summary.tsv", "Per-run correspondence summary"),
        ("Interaction summary", R / "interaction_summary.tsv", "Interaction preservation by class"),
        ("Region review", R / "region_review.tsv", "Candidate disagreement regions"),
        ("Family inventory", R / "family_inventory.tsv", "Screening funnel per family"),
        ("Selected pairs", R / "selected_pairs.tsv", "Frozen cohort"),
        ("7REX adjustment summary", adj_p, "Interaction preservation under the adjusted row"),
        ("7REX adjustment validation", val_p, "Checks on the one-column adjustment"),
        ("Export manifest", None, "Sources, checksums and row counts of this site"),
    ]
    downloads = []
    seen = set()
    if dl_rows:
        for r in dl_rows:
            path = r.get("path", "")
            src = (SITE / path).resolve() if path else None
            # the coordinator's paths are relative to the site; try a project-relative fallback
            cand_srcs = [src] if src else []
            if path:
                cand_srcs += [DELIV / path, ROOT / path, TABLES / Path(path).name]
            hit = next((c for c in cand_srcs if c and c.exists()), None)
            entry = {"label": r.get("label", ""), "description": r.get("description", ""),
                     "href": None, "status": "unavailable"}
            if hit is not None:
                if SITE.resolve() in hit.resolve().parents:
                    entry["href"] = str(hit.resolve().relative_to(SITE.resolve()))
                else:
                    shutil.copy2(hit, DOWNLOADS / hit.name)
                    entry["href"] = f"downloads/{hit.name}"
                entry["status"] = "available"
            downloads.append(entry)
            seen.add(entry.get("href"))
    for label, p, desc in default:
        if p is None:
            href = "data/export_manifest.json"
            if href not in seen:
                downloads.append({"label": label, "description": desc, "href": href, "status": "available"})
            continue
        if not p.exists():
            downloads.append({"label": label, "description": desc, "href": None, "status": "unavailable"})
            continue
        shutil.copy2(p, DOWNLOADS / p.name)
        href = f"downloads/{p.name}"
        if href in seen:
            continue
        seen.add(href)
        downloads.append({"label": label, "description": desc, "href": href, "status": "available",
                          "source": rel(p)})
    # copy every session table that exists, so it can be downloaded
    if TABLES.exists():
        for p in sorted(TABLES.glob("*.tsv")):
            shutil.copy2(p, DOWNLOADS / p.name)
            href = f"downloads/{p.name}"
            if href not in seen:
                seen.add(href)
                downloads.append({"label": p.name, "description": "Session table (deliverables/2026-10-09_v4/tables)",
                                  "href": href, "status": "available", "source": rel(p)})
    write("downloads.json", {"downloads": downloads})

    # ---------------------------------------------------------------- manifest
    manifest = {
        "generated_utc": dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ"),
        "git_commit": git_commit(),
        "git_worktree": git_dirty(),
        "generator": rel(Path(__file__)),
        "provenance": config_provenance(),
        "sources": SOURCES,
        "unavailable_optional_inputs": UNAVAILABLE,
    }
    write("export_manifest.json", manifest)
    print(f"wrote {len(list(DATA.glob('*.json')))} JSON files to {rel(DATA)}; "
          f"{len(SOURCES)} sources; {len(UNAVAILABLE)} unavailable optional inputs")
    for u in UNAVAILABLE:
        print("  unavailable:", u["path"])
    return 0


if __name__ == "__main__":
    sys.exit(main())
