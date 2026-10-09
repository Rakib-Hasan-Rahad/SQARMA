# Rfam seed vs original STAR3D: natural-sequence dataset, single-run policy (v5, 2026-10-09)

*Prepared by an AI research agent (Claude) for Rakib Hasan Rahad. No human has reviewed these results, and no approval
from the professor is implied.*

This report supersedes `deliverables/2026-10-09_v4/professor_report_v4.md` and all earlier summaries. Those remain as
dated historical records. Paths are relative to `rfam_star3d_pilot_v2/`.

## 1. What changed and why

Two changes, both explicit decisions by the researcher in this session:
1. **Single-run policy.** For each selected RNA pair, we use one forward alignment from original STAR3D v1.2 with
   default parameters, following the package's preprocessing procedure.
   - The reverse-direction runs, the extra replicates and the sensitivity analyses from earlier sessions are archived
     (`archive/v4_multi_run_history/`). They are not used to select or combine the primary mapping.
2. **Natural-sequence dataset.** The active analysis includes only experimental structures of verified natural RNA
   sequences. Confirmed engineered constructs and unresolved cases are excluded from the accepted cohort.
   - Masking engineered residues no longer makes a construct eligible.
   - This is the researcher's requirement, not a rule attributed to the professor.

## 2. Dataset under the natural-sequence policy

All 13 previously analysed chains were re-reviewed (`review/natural_sequence_eligibility.tsv`;
`results/dataset_chains.md`):

| Family | Chain | Status | Analysis | Key evidence |
|---|---|---|---|---|
| preQ1-I RF00522 | 3FU2 A | verified natural | **accepted** | whole 34-mer exact in *B. subtilis* 168 genome; paper: wild-type |
| preQ1-I RF00522 | 6VUI A | verified natural | **accepted** | whole 33-mer exact in *T. tengcongensis* MB4 genome; wild-type 33-mer chemically synthesised |
| preQ1-I RF00522 | 7REX A | verified natural | **accepted** | whole 34-mer exact in *C. antarcticum* CP1 genome; WT, chemically synthesised |
| Cobalamin RF00174 | 4GXY A | confirmed engineered | excluded | non-genomic terminal nucleotides (1, 171–172) |
| Cobalamin RF00174 | 6VMY A | confirmed engineered | excluded | 5′ G recorded as "cloning artifact" in the entry |
| TPP RF00059 | 2GDI X | confirmed engineered | excluded | non-genomic terminal nucleotides (1, 79–80) |
| TPP RF00059 | 3D2G A | confirmed engineered | excluded | 5′ region redesigned |
| Guanidine-I RF00442 | 5U3G B | confirmed engineered | excluded | internal substitutions and a deletion |
| Guanidine-I RF00442 | 7MLW F | confirmed engineered | excluded | P2 loop changed (authors) |
| SAM-I RF00162 | 2GIS A | confirmed engineered | excluded | internal deletion and loop changes |
| SAM-I RF00162 | 4KQY A | confirmed engineered | excluded | GAAA tetraloop replacement (paper) |
| tRNA RF00005 | 5CCB N | confirmed engineered | excluded | artificial 5′ G before the natural mature tRNA (also enzyme-refolded) |
| tRNA RF00005 | 7EQJ B | verified natural | accepted (no eligible partner) | T7 transcript of the natural mature tRNA-Val1 (paper Methods) |

**Revised counts** (`tables/before_after_natural_dataset.tsv`):

| Count | Previous | Now |
|---|---|---|
| Families with an analysed pair | 6 | **1** |
| Structures in pairs | 13 | **3** |
| Distinct sequences | 13 | **3** |
| Pairs | 8 | **3** |
| Verified-natural chains | — | 4 |
| Confirmed-engineered chains | — | 9 |
| Unresolved chains | — | 0 |

No STAR3D run was needed. The three accepted pairs reuse their existing original outputs unchanged, and their inputs
are byte-identical.

## 3. Results (accepted pairs; one selected STAR3D output each)

**Correspondences** (`results/pair_summary.tsv`; unit: query-row residue). The STAR3D output file for each pair is
listed in `results/primary_star3d_outputs.tsv`.

| Pair | STAR3D output | Assessable seed pairs | STAR3D pairs | Same | Different | Seed-only | STAR3D-only |
|---|---|---|---|---|---|---|---|
| 3FU2–6VUI | attempt3 forward | 29 | 31 | 24 | 4 | 2 | 3 |
| 3FU2–7REX | attempt1 forward | 30 | 32 | 17 | 13 | 1 | 2 |
| 6VUI–7REX | attempt1 forward | 32 | 32 | 16 | 15 | 1 | 1 |

**FR3D interactions, query side** (eligible set shared by both methods; `results/interaction_summary.tsv`):

| Pair | Seed | STAR3D |
|---|---|---|
| 3FU2–6VUI | 31/40 | 33/40 |
| 3FU2–7REX | 20/44 | 31/44 |
| 6VUI–7REX | 19/47 | 29/47 |

Target-side interactions are evaluated through the same mapping, inverted, with their own denominators. That is not a
second STAR3D run.

**Regions:** 8 regions remain, each with a dated review (`results/region_review.tsv`).
- Supported candidate: 2 sub-regions, both the 7REX P1 strand.
- Possible STAR3D issue: 1 (L1).
- Coordinate confound: 2 (3FU2 missing residues 13–14).
- Insufficient evidence: 4.

## 4. Findings

**Unchanged: the 7REX P1 3′ strand is a supported candidate for curator review (moderate confidence).** All three
supporting RNAs pass the natural-sequence policy. The evidence:
- after superposition on agreed residues, STAR3D partners are closer for every differing residue of the strand;
- canonical cWW pairs are preserved 0/7 by the seed and 5/7 by STAR3D;
- the 7REX authors' own description of P1 gives a G5–C18 pair, which is the STAR3D register;
- among 43 seed rows, only this row becomes fully complementary when shifted.

It is one observation, because both comparisons share the 7REX row.

**Unchanged: in loop L1 the seed is better supported.**

**Withdrawn from active results, because they relied on excluded data:**
- the TPP agreement control;
- the cobalamin and SAM-I coverage-limitation examples;
- the guanidine-I pairing-rule sensitivity (78 → 25 nt);
- the tRNA exploratory agreement (59/64).

These remain in the archive as historical observations. Some still describe STAR3D's behaviour, for example its pair
selection and its one-module alignments.

## 5. Validation

- **Tests.** 81 pass. They include the new single-run and natural-policy tests. One of them checks that excluded pairs
  cannot appear in active tables or on the website.
- **Mutation check.** 18 of 18 re-inserted defects were detected (`tables/mutation_check_v5.tsv`).
- **Single-run refactor.** 0 changed values in correspondences, interactions, regions and candidate tables
  (`tables/before_after_single_run.tsv`). Only rows and columns for archived runs were removed.

## 6. Limitations

- **Size.** One family and three pairs, sharing RNAs. No rates can be generalised.
- **Seed provenance.** For preQ1-I the ordinary seed equals the 3D-curated alignment.
- **Execution.** STAR3D ran under emulation. Earlier observations of forward/reverse differences (3FU2–6VUI: 2 pairs)
  remain a documented limitation of single-run output.
- **Preparation evidence.** For 3FU2 the paper's preparation method was not found in the accessible text. Its whole
  sequence is exactly natural, and the paper calls it wild-type.
- **Review.** All decisions are an AI agent's review.

## 7. Next decision for the professor

Under the natural-sequence policy, the explicit-link experimental inventory yields one usable family. Expanding needs a
declared scope choice, for example:
- reviewing sequence-only links in non-curated families for natural constructs;
- or, as a separate study, predicted structures of natural sequences.

The 7REX candidate can be discussed now.
