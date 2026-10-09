> **SUPERSEDED (2026-10-09, v5).** This folder is a dated historical record. Current: `deliverables/2026-10-09_v5/README.md` (single-run policy; natural-sequence dataset). Conclusions here that rely on engineered constructs or multi-run STAR3D output are withdrawn from the active results.

# Session deliverables, 2026-10-09 (v3)

AI-agent work; no human review. All paths are relative to `rfam_star3d_pilot_v2/`.

**Start here:** `professor_report.md`. Then read:
- `weekly_progress_update.md`
- `meeting_script.md`
- `candidate_evidence_update.md`
- `repair_impact_report.md`
- `STAR3D_execution_audit.md`
- `readiness.json`

**Website (local only).**
```
cd rfam_star3d_pilot_v2/deliverables/2026-10-09/site
../../../.venv/bin/python -m http.server 8765        # then open http://localhost:8765
```
To regenerate the site data from the tables, run `.venv/bin/python scripts/export_site_data.py` from the study
directory. Opening `index.html` directly from disk will not load the data; serve the folder over HTTP instead.

**Folder contents.**
| Folder | Contents |
|---|---|
| `tables/` | Machine-readable session tables (data dictionary: `reports/data_dictionary.md`, section "v3 additions") |
| `figures/` | Session figures |
| `logs/` | Test and execution logs |
| `start_state/` | Checksums and test baseline at the starting commit ac6ff55 |
| `before_repairs/` | Pre-repair copies of changed scripts and regenerated tables |
| `scripts/` | Session analysis scripts |
| `star3d_audit/` | STAR3D audit evidence |
| `MANIFEST.tsv` | Each output with its generator, inputs, software and sha256 |
| `repro_package_v3_2026-10-09.tar.gz` (+ `.sha256`) | Reproducibility package (third-party binaries excluded; retrieval instructions inside) |
