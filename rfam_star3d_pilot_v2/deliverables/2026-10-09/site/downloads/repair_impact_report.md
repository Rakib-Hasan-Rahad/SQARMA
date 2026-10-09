# Repair impact report — session 2026-10-09 (branch `v3-session-2026-10-09`, from main `ac6ff55`)

Reviewer: AI agent (Claude); no human review. Passing tests show the code behaves as specified on test cases; they do
not prove biological correctness. Pre-repair copies of every changed script and of every regenerated table are kept in
`before_repairs/`; start-state checksums are in `start_state/SHA256SUMS_start_ac6ff55.txt` (90 files).

Test baseline at start: **33 passed**. After repairs: **51 passed, 0 failed**
(`.venv/bin/python -m pytest -q tests`; log `logs/pytest_final.txt`). New and changed tests were run against the
pre-repair scripts (`logs/new_tests_vs_old_code.txt`). The failures there were:

| Test file | Failures against the pre-repair script |
|---|---|
| Stockholm export | 1 of 3. The real-file round-trip test also failed on the pre-repair `.sto` excerpt before it was regenerated. |
| fresh-repro gate | 5 of 5 |
| compare validation | 5 failed. These are the 5 new stored-output tests; the 4 v2.1 tests and the atomic-write test pass on both versions. |
| STAR3D gate | 3 of 3 new |
| regions | 2: the changed carry test and the new eligibility test |

| Defect | Evidence | Repair | Regression test | Effect on results | Remaining limitation |
|---|---|---|---|---|---|
| **A. Invalid derived Stockholm** — `results/standard_seed_rows.sto` held 5 families (widths 70–461) in one record | repository parser: `unequal sequence lengths` (reproduced today) | `reference.py: write_family_excerpts` writes one complete record per family (ID, AC, CC, rows, #=GS/#=GR, all #=GC, `//`), original columns and strings verbatim, atomic write | `tests/test_stockholm_export.py` (3): unequal-width round trip; old combined layout rejected; real excerpt equals pinned seed rows/GR/GC for all 5 families | **None on correspondences**: `standard_seed_membership`, `reference_pairs`, `reference_gap_assignments`, all 7 `reference_example_*` byte-identical; only the `.sto` changed (now 5 valid records) | v2.1 repro package (`audit/repro_package_RF00522_v2.1`) still contains the old file; superseded by the v3 package |
| **B. Fresh reproduction continued after input mismatch** | `fresh_repro.py` recorded `compressed_identical=False` but continued to rebuild/align/annotate | `InputGate`: diagnostic JSON written first, unexpected bytes quarantined, fresh file removed from cache path; blocks every dependent rep/pair (STAR3D tarball mismatch blocks all alignments; rebuilt-input mismatch blocks its pairs; FR3D skipped); container-only (gzip header) changes distinguished but also rejected; partial summaries written atomically; nonzero exit | `tests/test_fresh_repro_gate.py` (5): altered download blocks dependent alignment+annotation; container-only change rejected; software mismatch blocks all; altered rebuilt input blocks; identical inputs pass | None on existing results (preQ1 rerun had no mismatches). Gate exercised for real in today's 4-pair rerun (see below) | Network fetches can still fail for other reasons (recorded, not adopted) |
| **C1. FR3D provenance was a config label** | sidecars wrote `fr3d_commit` from `config.yaml`; 10 of 11 were `reconstructed_v2.1` | `installed_fr3d_provenance()`: PEP 610 `direct_url.json` commit of the imported distribution, all 95 installed files re-hashed against RECORD, import path inside distribution; stops if not 288f98cc. Sidecars now store raw-output sha256; cache reuse requires matching raw hashes and complete, parseable raw lines | exercised by full rerun (below); invalid-cache paths are SystemExit branches (not unit-tested — see limitation) | All 11 RNAs regenerated in the verified environment: **raw outputs byte-identical** (`tables/fr3d_verify_regenerate.tsv`); sidecars upgraded to `verified_v3` (old kept as `*.provenance.v2.1.json`); `interaction_comparison` (1,634 rows) and `interaction_summary` (210 rows) byte-identical | No unit test for the reuse-refusal branches; FR3D still labels its output "not finalized" |
| **C2. Stored STAR3D outputs not re-validated when consumed** | `compare.py` ignored `parse_aln` bad lines and declared≠parsed counts; never compared output sha/aligned_n with manifest; wrote tables even when the stage then failed | `stored_alignment_problems()`: bad lines, missing header, missing file, output sha ≠ manifest, aligned_n ≠ parsed → `validation_failed` (never a primary replicate). Tables written atomically; on any failure written only as `results/*.INVALID.tsv`, complete tables untouched | `tests/test_compare_validation.py` +6: declared-count mismatch; malformed line; stale manifest vs changed bytes; manifest aligned_n mismatch; missing output; atomic write | 41/41 completed runs pass the stricter checks; `correspondence_comparison`, `pair_summary`, `replicate_consistency` byte-identical | — |
| **C3. Preprocessing gate trusted exit codes** (found by today's STAR3D audit) | STAR3D ignores MC-Annotate/RemovePseudoknots exit codes; empty `.mca` would yield a pair-free npk.ct that passed | `star3d.preprocessing_problems()`: fatal if `.mca` missing/empty/no Base-pairs section, or npk.ct count/format/reciprocity invalid → `failed_intermediate_invalid`, alignment not run. Non-reciprocal raw `.ct` recorded as WARNING | `tests/test_star3d_gate.py` +3: empty mca stops alignment; non-reciprocal npk.ct stops; valid preprocessing proceeds with raw-ct warning | Retained: 14/14 preprocessing products pass; 1 warning: `7mlwf_F` raw .ct non-reciprocal at 44 (STAR3D source overwrite, see audit) | The 7MLW defect is in original STAR3D; we record it, we do not patch the tool |
| **D1. Claims exceeding evidence** | professor_summary: "probably added by the cmalign-based 3D curation pipeline"; "(none)" for annotation absence; "no engineering" | text corrected and dated; "no FR3D annotation detected"; "no sequence changes detected over the checked interval" | n/a (text) | wording only | Other historical reports keep their dated text |
| **D2. Evidence-card vocabulary** | `confirmed_absent` displayed as "engineering confirmed absent" | cards distinguish none (checked) / unknown / not applicable / unavailable; exact-match caveat stated | n/a (regenerated `reports/evidence_cards.md`, 26 changed lines) | wording only | — |
| **D3. Old interpretations auto-accepted after boundary/eligibility change** | `carry_interpretations` copied conclusions by span overlap and ignored eligibility changes | exact id + unchanged eligibility → carried; otherwise `needs_reassessment` with the old text kept as HISTORICAL | `tests/test_regions.py` updated + 1 new (eligibility change) | `region_review.tsv` byte-identical (no current region affected) | — |

## Defects reported earlier that were re-checked and found already fixed
- Interaction masking per method, separate reverse denominators, symmetry-operator filter, region eligibility,
  mount-mismatch gate, subset-run refusal: tests from v2.1 still pass (33 of the 51).
- Injectivity and crosswalk coverage: re-verified for all 41 completed runs (also independently by the STAR3D audit,
  `star3d_audit/aln_crosswalk_audit.tsv`).

## Fresh reproduction of the 4 pilot pairs not previously rerun (new today)
`scripts/fresh_repro.py --pairs … --out audit/fresh_repro_v3_other4` (runs through the new input gate and the new
preprocessing validator). Result summary: `tables/fresh_repro_other4.tsv` and
`audit/fresh_repro_v3_other4/fresh_repro_summary.json` (see section in the main report).

## Scientific outputs changed by repairs
**None of the correspondence, interaction, region or candidate tables changed.** Changed files: the derived `.sto`
(format), FR3D provenance sidecars (verified provenance + raw hashes), evidence-card and professor-summary wording.
No cohort or analysis-version change was needed for the existing seven pairs.
