# Validation (v5, 2026-10-09)

*AI agent (Claude); no human review.*

**Software behaviour [verified]**
- **Tests.** 81 pass (`logs/pytest_final_v5.txt`), up from 64 at the start of the session. New tests:
  - `test_single_run_policy.py` (8): one alignment and one Preprocess per RNA; fixed query→target order; a failed
    alignment is not retried or substituted; the earliest valid forward record is chosen, not the best-scoring one; a
    failed first attempt is documented; there is no reverse substitution; an unavailable pair stays a failure; the
    pinned 6VUI–7REX output is reused byte-for-byte.
  - `test_natural_policy.py` (8): engineered, masked-engineered and unresolved cases cannot be accepted; one
    ineligible representative blocks its pair; synthesis, missing coordinates and native modifications are not
    engineering; excluded chains cannot leak into the active tables.
  - The interaction tests were updated for the single Rfam-vs-STAR3D comparison and target-side inversion.
- **Mutation check** (`tables/mutation_check_v5.tsv`): 18/18 re-inserted defects detected. These are the 16
  historical ones plus two new single-run defects: a replicate loop and reverse-run substitution.

**Essential checks kept after removing repetition:**
- structure, chain and interval (crosswalk identity);
- input, software and preprocessing checksums;
- malformed or missing preprocessing products;
- failed execution;
- declared vs parsed counts;
- unmapped identifiers;
- one-to-one mapping;
- masks;
- interaction denominators;
- subset-run refusal.

Each has a test, and each is exercised by the mutation check.

**Single-run refactor effect** (`tables/before_after_single_run.tsv`): every value was compared, and **0 changed** in
residue correspondences (532 + 73), interaction statuses and denominators (1,634 + 222), regions (19 + 2), region
evidence and candidate tables. Changes were structural only:
- archived rows and columns (reverse, replicates 2–3, the three-method comparison) removed from the active tables;
- exclusion labels renamed (`star3d_forward_*` → `star3d_*`).

**Natural-sequence cohort:**
- The prepared inputs of the 3 accepted pairs are byte-identical to the inputs used at run time, so their original
  STAR3D outputs are reused. Every output passed all selection checks.
- The 3 accepted pairs' correspondences, interactions and regions are unchanged from the earlier values for those
  pairs.

**Primary outputs** (`results/primary_star3d_outputs.tsv`):

| Pair | Selected file | Earlier records not selected |
|---|---|---|
| 3FU2–6VUI | `runs/RF00522__3FU2_A__6VUI_A/attempt3/…__a3__forward__rep1.aln` | attempt1 (×3): `failed_wrapper_defect` (output directory bug). Attempt2 never wrote a forward record (stale sshfs mount; Preprocess skipped; preserved in `runs/_superseded/`). |
| 3FU2–7REX | `runs/RF00522__3FU2_A__7REX_A/attempt1/…__a1__forward__rep1.aln` | none |
| 6VUI–7REX | `runs/RF00522__6VUI_A__7REX_A/attempt1/…__a1__forward__rep1.aln` (pinned) | none |

**Not done:** independent human review, a native x86-64 host, a second aligner, and a fresh v5 STAR3D run. None was
needed, because no accepted input changed.
