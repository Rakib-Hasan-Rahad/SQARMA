# SQARMA: final report documentation (v5, 2026-10-09)

This folder holds the current final reports in one place. They cover the Rfam seed vs original STAR3D v1.2 study under
two policies: one STAR3D output per pair, and only verified natural RNA sequences.

These are **copies** of the files listed below. The working originals stay in `rfam_star3d_pilot_v2/`, and paths cited
inside the reports are relative to that directory. Earlier versions (v2–v4) are dated historical records in
`rfam_star3d_pilot_v2/deliverables/`.

## 1. Main reports (`1_main_reports/`)
| File | What it is |
|---|---|
| `professor_report_v5.md` | **Start here.** Dataset, results, findings, limitations, next decision |
| `validation_v5.md` | Tests (81 pass), mutation check (18/18), reproduction evidence |
| `meeting_script_v5.md` | Talking points for discussing the results |
| `deliverables_README_v5.md` | Index of the v5 deliverables folder (site, manifest, repro package) |

## 2. Architecture guide (`2_architecture_guide/`)
`SQARMA_Project_Architecture_and_Pipeline_Guide` as PDF (17 pages), Word and Markdown, plus its diagrams.

## 3. Supporting reports (`3_supporting_reports/`)
Full study report, professor summary and Q&A, validation report, scale-up readiness, blockers, data dictionary, and
the running `STATUS.md`.

## 4. Key results tables (`4_key_results_tables/`)
| File | Content |
|---|---|
| `natural_sequence_eligibility.tsv` | Eligibility decision and evidence for all 13 chains reviewed |
| `dataset_chains.md` | Readable table of the chains |
| `primary_star3d_outputs.tsv` | The one STAR3D output used for each pair, with hashes and command |
| `pair_summary.tsv` | Seed vs STAR3D correspondences per pair |
| `interaction_summary.tsv` | FR3D interactions preserved by each method |
| `region_review.tsv` | The 8 regions and their dated review |
| `derived_alignment_views.md` | Gapped side-by-side views (SQARMA visualisation, not STAR3D output) |
| `before_after_single_run.tsv`, `before_after_natural_dataset.tsv` | Effect of each policy change |
| `mutation_check_v5.tsv`, `test_results_v5.tsv` | Validation evidence |

All results and judgements were produced by an AI research agent (Claude); no human has reviewed them.
