# Validation and repair status (v4, 2026-10-09)

*AI agent (Claude); no human review.* Each kind of evidence below is kept separate.

## A. Software behaviour [V]
- **Tests.** `.venv/bin/python -m pytest -q tests` gives **64 passed, 0 failed** (`logs/pytest_final_v4.txt`). There
  were 51 at the start of v4. The 13 new tests cover:
  - subset-run refusal for compare, interactions and reference (3);
  - FR3D provenance and cache reuse (9: four refusal cases, installed-package check, three cache refusals, one valid
    reuse);
  - reverse-strand row coordinates (1).
- **Do the tests catch the defects?** Each previously reported defect was re-inserted into a scratch copy of the
  current code, and the relevant test file was run (`tables/mutation_check.tsv`, `scripts/mutation_check.py`).
  **16/16 were detected.**
  - On the pre-v2.1 code (7f94cba), the v2.1 tests failed mostly because the new functions were missing
    (AttributeError) rather than because of the old behaviour (`logs/defects_vs_pre_v21_code.txt`). That is why mutation
    testing was used.

| Defect (previously reported) | Present in current code? | Test detects it when re-introduced |
|---|---|---|
| Multi-family Stockholm record | no (fixed v3) | yes |
| Checksum mismatch not stopping dependent work | no (fixed v3) | yes |
| Configured instead of installed FR3D commit | no (fixed v3) | yes |
| Cached FR3D output reused without raw-hash check | no (fixed v3) | yes |
| Stored STAR3D output not re-validated / non-injective output accepted | no (fixed v3/v2.1) | yes / yes |
| Preprocessing contents not validated | no (fixed v3) | yes |
| Shared denominators across comparisons | no (fixed v2.1) | yes |
| Masked residues (target or source) ignored | no (fixed v2.1) | yes / yes |
| Crystal-symmetry interactions counted as intrachain | no (fixed v2.1) | yes |
| Region eligibility ignoring targets or intervening positions | no (fixed v2.1) | yes / yes |
| Review history auto-accepted after an eligibility change | no (fixed v3) | yes |
| Partial (subset) reruns overwriting complete tables | no (refused since v2.1; test added v4) | yes |
| **New in v4:** reverse-strand row coordinates written as increasing | yes; fixed in `prepare_inputs.row_coordinate` | test added; no pilot row is reverse-strand, so no pilot output changed |

## B. Reproduction [V/R]
- **Pipeline tables.** Re-running the region stage over the v4 tables changes only the new review columns. The scripts
  touched in v4 (`anchor_fit.py` new rule, `prepare_inputs.py` coordinate fix, `region_evidence.py` new) did not change
  any retained correspondence, interaction or anchor-fit table. Retained anchor-fit files are unchanged (git diff
  empty); new files were added.
- **Fresh reruns from re-downloaded inputs.** These cover all 7 pilot pairs, from v3 and earlier [R]. They were not
  repeated in v4.
- **Preprocessing.** It is deterministic (4/4 identical) [V].
- **Status.** Every rerun was done by the same agent. **None of this is independent validation.**

## C. Mapping validity [V]
- **Crosswalks.** 0 identity mismatches for 11 pilot and 2 prospective RNAs. The IDs in every STAR3D input file match
  the crosswalk.
- **Stored outputs.** Validated on read: counts, hashes and injectivity for all 41 completed pilot runs and the 6
  prospective runs.

## D. Biological interpretation [V, AI judgement]
All 19 pilot regions and the 2 prospective regions have a dated review with evidence for each method
(`review/region_review_v4.tsv`; `expansion_v4/review/region_review_v4.tsv`). These are an AI agent's judgements on
retained structures, not independent biological validation.

## E. Independent corroboration
- **Literature.** The 7REX authors' description of P1 (a G5–C18 pair) and of the pocket-ceiling triple (C8, A12, U32)
  comes from the structure paper. It is independent of STAR3D and FR3D, but describes the same coordinates.
- **Not done:** a second structural aligner, independent human review, and native-host execution.

## Validation gates
See `tables/validation_gates.tsv`. The quarantined or limited cases are listed there. No failed case was converted into
a negative biological result.
