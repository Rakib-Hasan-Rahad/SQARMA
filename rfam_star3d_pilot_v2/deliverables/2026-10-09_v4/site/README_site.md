# Presentation site (local, static)

Dependency-free HTML/CSS/JS. All numbers come from `data/*.json`, generated from the project tables by
`scripts/export_site_data.py`; nothing numeric is typed into the HTML or JS. Missing inputs show as
"unavailable"/"pending", never as 0.

## Regenerate data (from the study directory (live site: v4) `rfam_star3d_pilot_v2/`)

    .venv/bin/python scripts/export_site_data.py

This rewrites `data/*.json` (including `data/export_manifest.json`: source paths, sha256, row counts,
generation UTC time, git commit, unavailable optional inputs), copies figures into `assets/` and download
files into `downloads/`. Re-run it whenever a source table changes (e.g. when the session tables in
`deliverables/2026-10-09/tables/` are added).

## Launch

    cd deliverables/2026-10-09_v4/site && ../../../.venv/bin/python -m http.server 8765

then open http://localhost:8765 . (Opening `index.html` directly from disk will not work: browsers block
`fetch()` of local files.)

## Sections
Overview · Dataset (funnel, cohort, provenance, searchable family inventory, new screening) · Results
(development vs prospective pairs) · 7REX case (candidate for curator review; exploratory adjustment) ·
Validation · Downloads & next steps · Glossary. Provenance footer reads `export_manifest.json`.
