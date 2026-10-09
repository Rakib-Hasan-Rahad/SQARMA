> **SUPERSEDED (2026-10-09, v5).** This folder is a dated historical record. Current: `deliverables/2026-10-09_v5/README.md` (single-run policy; natural-sequence dataset). Conclusions here that rely on engineered constructs or multi-run STAR3D output are withdrawn from the active results.

# Session deliverables, 2026-10-09 (v4: scientific validation)

*AI-agent work; no human review. Branch `v4-validation-2026-10-09`, pushed to GitHub (not merged into main).*

**Start here:** `professor_report_v4.md`, which supersedes the v3 conclusions. Then read:
- `candidate_evidence_update_v4.md` — the 7REX candidate;
- `region_review_v4.md` — all 19 pilot regions and 2 prospective regions;
- `method_audit_v4.md` — STAR3D pair selection and the S1/S2 sensitivity analyses;
- `dataset_and_provenance_v4.md` — Survey B in precise terms, Rfam release history, and the tRNA expansion;
- `validation_v4.md` — tests, mutation check and validation gates;
- `weekly_progress_update_v4.md`;
- `meeting_script_v4.md`.

**Tables** (`tables/`):
- `requirements_matrix.tsv`;
- `validation_gates.tsv`;
- `conclusions_changed.tsv`;
- `mutation_check.tsv`;
- `test_results.tsv`;
- `results_status.tsv`.

**Architecture guide** (`architecture/`):
- `SQARMA_Project_Architecture_and_Pipeline_Guide.docx`, `.pdf` and `.md`, with the Mermaid sources in `diagrams/`.
- The PDF was checked page by page.
- The .docx was checked structurally: 7 embedded figures, each ≤ 8.3 in tall. Microsoft Word did not respond to an
  automated export, so its Word rendering was not visually inspected.

**Website (local only).** Data is regenerated with `.venv/bin/python scripts/export_site_data.py`. To launch it:
```
cd rfam_star3d_pilot_v2/deliverables/2026-10-09_v4/site
../../../.venv/bin/python -m http.server 8765        # open http://localhost:8765
```
`deliverables/2026-10-09/site/` is the v3 snapshot.

**Other contents:**
- `baseline/` — start-of-session checksums and archived reports;
- `logs/`;
- `scripts/` — session scripts;
- `star3d_sensitivity/`;
- `MANIFEST.tsv`;
- `repro_package_v4_2026-10-09.tar.gz` and its `.sha256`.
