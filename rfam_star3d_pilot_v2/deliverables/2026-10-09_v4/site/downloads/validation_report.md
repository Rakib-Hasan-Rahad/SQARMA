# Validation report — pilot v2.1 (cohort v1.1)

## v4 (2026-10-09): see `deliverables/2026-10-09_v4/validation_v4.md`
- **Tests.** 64 pass. Mutation testing detects 16/16 re-introduced defects (`deliverables/2026-10-09_v4/tables/mutation_check.tsv`).
- **Fix.** Reverse-strand crosswalk coordinates; no pilot row is affected.
- **Validation gates.** See `deliverables/2026-10-09_v4/tables/validation_gates.tsv`.
- **Region review.** All 19 pilot regions and 2 prospective regions have been reviewed.
- **STAR3D.** Pair-selection audit and S1/S2 sensitivity; 22 alignment runs this session, 0 crashes, emulated.
- **Not done.** Independent human review, a second aligner and a native host.


Reviewer for all checks: **AI agent (Claude)**. No human review or approval is claimed. "External audit" refers to
the audit described in the repair brief (commit 7f94cba). That audit re-checked retained files but did not rerun
STAR3D or FR3D.

## Phase status (no unconditional passes)
| Phase | Status | What passed | What is incomplete |
|---|---|---|---|
| 1 Inventory | PASS | Rfam 15.1 pinned (seed sha256 41f014f4…, decompressed a6fc52d9…); parser gate on a real interleaved record; external audit re-checked checksums | 21 screen-passing families unreviewed (unknown) |
| 2 Eligibility | PASS with amendments | Cohort v1 frozen before runs; v1.1 tier relabel logged; exact-source genome checks for 9 RNAs | 3D2G and 7MLW sources not exact-verified; several construct papers inaccessible |
| 3 Seed reference | PASS | Membership hashes (external audit + 11/11 raw-line traces); manual trace of the first pair; all 7 mappings re-checked by the external audit | — |
| 4 STAR3D + comparison | PASS for the current 42 runs; fresh rerun PARTIAL | 41 completed + 1 recorded crash; summary rows match raw output (external audit); preQ1 fresh rerun identical (18 runs) | Fresh rerun of the other 4 pairs not done; runs under QEMU emulation |
| 5 Interactions + regions | PASS after repair | Masking and denominator defect fixed; symmetry-mate defect fixed; region eligibility fixed; candidate rebuilt from raw files; FR3D fresh rerun identical for 3 RNAs | FR3D output "not finalized"; canonical evidence not independent of STAR3D; only 5 regions inspected |
| 6 Report | Updated | report, professor summary, Q&A, evidence cards, scale-up note | No PDF; no researcher review |

## Regression tests: 33 passing (`.venv/bin/python -m pytest -q tests`)
These are the 13 original tests plus 20 new ones:
- **`test_interaction_masking.py` (9).** Masked STAR3D target excludes; masked Rfam target excludes; clean
  interaction stays eligible; masked source; reversed endpoint order; unobserved or unmapped; three-way denominator;
  symmetry classes; non-injective inversion fails.
- **`test_regions.py` (5).** Clean source with masked Rfam target is not eligible; same with masked STAR3D target;
  an intervening masked position counts; unobserved target is not eligible while a clean region is; interpretations
  carried, not reset.
- **`test_star3d_gate.py` (2).** A mount mismatch prevents alignment; stale intermediates fail the mount check. Both
  fail on the audited `star3d.py` and pass on the fix.
- **`test_compare_validation.py` (4).** An unmapped output line is a validation failure; non-injective output is a
  validation failure; clean output maps; author-ID collision is fatal.

## Before/after counts affected by each fix
| Fix | Affected | Before → after |
|---|---|---|
| Interaction masking | RF00442 target side, seed vs STAR3D-forward eligible set | 110 → 105 (canonical 17 → 16, stack 82 → 78); preserved seed 88 → 83, STAR3D 82 → 79 |
| Separate reverse denominators | RF00174 query; RF00522 3FU2–6VUI target | reverse eligible 1 → 0; 36 → 39 |
| FR3D symmetry operator | 4KQY source interactions | 181 → 180 (self-stack 10–10 from a symmetry mate removed) |
| Region eligibility | `RF00059__2GDI_X__3D2G_A__r17-23` | trustworthy yes → eligible no; 18 other regions unchanged |
| Preprocessing gate | current results | none (all 14 current preprocessing steps completed) |
| Validation failures, subset refusal, order | current results | none (0 unmapped lines, all injective); `replicate_consistency` row order only |

Tables: `audit/fix1_interaction_masking_before_after.tsv`, `audit/fix2_region_eligibility_before_after.tsv`.
Invariance check after cohort v1.1:
- 42/42 run input hashes still match;
- `correspondence_comparison`, `reference_*`, `standard_seed_membership` and `residue_crosswalk` are byte-identical
  to the snapshot;
- `pair_summary` differs only in the tier column.

## Fresh reproduction, preQ1 (`audit/fresh_repro/fresh_repro_summary.json`)
- **Downloads.** Re-downloaded 3FU2, 6VUI and 7REX mmCIF and the STAR3D v1.2 tarball: compressed and decompressed
  SHA-256 are identical to the pinned files.
- **STAR3D inputs.** Rebuilt inputs are byte-identical, with 0.0 Å maximum atom displacement.
- **STAR3D runs.** 18/18 runs completed through the new gate. Mappings, aligned counts, RMSDs and npk.ct files are
  identical to the retained runs.
- **FR3D.** Raw output files are byte-identical for all three structures, and normalized annotations are identical
  (49 / 48 / 49).

This is reproduction by the same agent, not independent external validation.

## Defects found earlier (v2.0) — unchanged record
These were the crosswalk author-number source, the wrapper output directory, the stale sshfs mount, the 5U3G mask
list, and the captcha pages. They are documented in `logs/changes.md`.

## Remaining known risks
- STAR3D runs under QEMU emulation (one JVM SIGILL crash).
- FR3D-python reports "annotations not yet finalized".
- Canonical-pair agreement is partly circular with STAR3D's preprocessing.
- 3FU2 C12 has only phosphate atoms.
- The 7REX second ligand changes local L1 context.
- Engineered constructs dominate the excluded and exploratory pairs.
