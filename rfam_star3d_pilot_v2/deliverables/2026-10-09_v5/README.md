# Session deliverables, 2026-10-09 (v5: single-run policy + natural-sequence dataset)

*AI-agent work; no human review. Branch `v5-single-run-natural-dataset`, local commits only (not pushed or merged).*

**Method.** For each selected RNA pair, we use one forward alignment from original STAR3D v1.2 with default
parameters, following the package's preprocessing procedure.

**Dataset policy.** The active analysis includes only experimental structures of verified natural RNA sequences.
Confirmed engineered constructs and unresolved cases are excluded from the accepted cohort.

**Start here:** `professor_report_v5.md`. Then read:
- `validation_v5.md`;
- `meeting_script_v5.md`;
- `../../review/natural_sequence_eligibility.tsv`;
- `../../results/dataset_chains.md`;
- `../../results/derived_alignment_views.md`.

**Tables** (`tables/`):
- `before_after_single_run.tsv`;
- `before_after_natural_dataset.tsv`;
- `mutation_check_v5.tsv`;
- `test_results_v5.tsv`.

**Architecture guide:** `architecture/SQARMA_Project_Architecture_and_Pipeline_Guide.{docx,pdf,md}`, with sources in
`diagrams/*.mmd`.

**Website (local only).**
```
cd rfam_star3d_pilot_v2 && .venv/bin/python scripts/export_site_data.py
cd deliverables/2026-10-09_v5/site && ../../../.venv/bin/python -m http.server 8765   # open http://localhost:8765
```

**History** (superseded, kept):
- `deliverables/2026-10-09/` and `deliverables/2026-10-09_v4/` — earlier sessions and sites;
- `before/` and `before_natural/` — this session's starting tables and reports;
- `../../archive/` — multi-run history, cohort v1.1, region evidence of excluded pairs, legacy scripts;
- `../../expansion_v4/ARCHIVED.md` — the tRNA workspace.

**Other contents:**
- `MANIFEST.tsv`;
- `repro_package_v5_2026-10-09.tar.gz` and its `.sha256`.
