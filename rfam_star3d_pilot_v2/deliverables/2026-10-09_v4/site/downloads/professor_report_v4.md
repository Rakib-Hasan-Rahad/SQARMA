# Rfam seed vs original STAR3D: validated status (v4, 2026-10-09)

*Prepared by an AI research agent (Claude) for Rakib Hasan Rahad. No human has reviewed these results, and no approval
from the professor is implied.*

This report supersedes the conclusions of `deliverables/2026-10-09/professor_report.md` (v3) wherever they differ. Those
differences are listed in `tables/conclusions_changed.tsv`. Paths are relative to `rfam_star3d_pilot_v2/`.

**Status tags used below**
- **[V]** Verified in this execution.
- **[R]** Retained evidence, not rerun.
- **[X]** Exploratory.
- **[U]** Unresolved.

## 1. The question and what counts as an answer

**The question.** For distinct homologous RNAs with suitable experimental structures, where do the ordinary Rfam seed
correspondences (release 15.1) and original STAR3D v1.2 correspondences differ, and what evidence explains the
differences?

**Possible answers per region.** Each region gets one of these:
- a supported candidate for curator review;
- a STAR3D limitation;
- structural or ligand-context variation;
- a construct or coordinate confound;
- insufficient evidence.

Neither method is treated as ground truth. Agreement is a valid result.

**What the professor asked for.** The list comes from the 8 Oct research plan, which records the meeting transcript;
the transcript itself is not on disk. See `tables/requirements_matrix.tsv`:
1. Count families with at least two eligible distinct sequences.
2. Link each chain to its exact row.
3. Remove redundant and engineered constructs.
4. Compare the ordinary seed with the curated seed.
5. Run original STAR3D and investigate motif disagreements.
6. If suitable experimental cases cannot be found, bring the search to Smriti and ask about predicted structures.

## 2. Findings that survived review

**1. One supported candidate (moderate confidence).** The P1 3′ strand of the *Carnobacterium antarcticum* row
(PDB 7REX) in preQ1-I (RF00522) is one nucleotide out of register in the seed.
- **[V] Geometry.** For every differing residue of the strand, the STAR3D partner is closer than the seed partner.
  The strand is 6VUI 14–21 against 7REX, and 3FU2 15–22 against 7REX. This holds under three anchor sets
  (shared / flank-excluded / local) and for both C1′ and base-centroid distances. Across both pairs, STAR3D partners lie 0.4–4.3 Å away and seed partners 3.6–9.7 Å; the residue-by-residue comparison always favours STAR3D.
  The adjacent 6VUI U22 is ambiguous, with both partners about 6 Å away (`results/region_evidence/`).
- **[V] Interactions.** FR3D canonical pairs in the strand are 0/7 under the seed and 5/7 under STAR3D
  (6VUI→7REX region).
- **[V] Literature.** The 7REX authors describe P1 as "a canonical A-form helix" with an A28•G5-C18•A29 triple. G5–C18
  is the STAR3D register; the seed implies G5–C17 (PMC8752633).
- **[V] Robustness.** The mapping is unchanged when STAR3D is given only canonical Watson–Crick pairs (sensitivity S1).
- **[V] Row-specific.** Of 43 preQ1-I seed rows, only this row becomes fully complementary when shifted
  (sequence-level check).
- **[V] Provenance fact.** The row first appears in Rfam 15.0, with the same aligned string as in 15.1. How it was
  aligned is not documented, and we do not infer it.
- **Caveats.** Both comparisons share the 7REX row, so this is one observation. STAR3D's objective uses pairing. A
  second preQ1 ligand contacts residue 16 of the strand.

**2. The seed is better supported in loop L1 of the same RNA (low to moderate confidence) [V].**
- The seed partners fit better after superposition.
- The seed maps the 6VUI C7–G11 pair onto 7REX C8–A12. These are the residues the 7REX authors describe as the
  "pocket ceiling" base triple; STAR3D maps them elsewhere.
- The second preQ1 ligand contacts L1, so ligand-context variation is plausible.

**3. Most other differences are not alignment disagreements [V].** All 19 pilot regions were reviewed with the same
evidence tables, giving 20 sub-region verdicts (`review/region_review_v4.tsv`):

| Verdict | Count | Where |
|---|---|---|
| Supported candidate | 2 | both the 7REX P1 strand |
| Possible STAR3D issue | 1 | L1 |
| Construct or coordinate confound | 2 | 3FU2 missing residues 13–14 and partial C12 |
| STAR3D coverage limitation | 2 | cobalamin |
| Insufficient evidence | 7 | — |
| Ineligible, not adjudicated | 6 | engineered or masked |

**4. Ordinary vs curated seed (precise wording) [V].**
- The compressed archives differ, and so do the decompressed files: the curated file contains only 74 families.
- The 74 extracted family records, however, are byte-identical to the ordinary records.
- The same holds in every release that ships a curated file (14.9, 14.10, 15.0, 15.1;
  `results/rfam_history/curated_vs_ordinary.tsv`).
- For our families, the "ordinary" baseline is therefore the 3D-curated alignment.
- In 15.1, the families our discovery rule can find (explicit `#=GR` links) are exactly these 74. The pilot therefore
  samples only curated families, which is a selection bias.

**5. A non-curated family was tested prospectively. There is no primary result, and one exploratory agreement case
[V/X].**
- **Pre-registration.** We pre-registered a screen of tRNA (RF00005), the top-ranked family outside the curated set
  (`review/v4_expansion/PREREGISTRATION.md`).
- **Screen outcome.** No different-species pair met all rules:
  - natural tRNAs carry modified nucleotides, which original STAR3D reads as "N";
  - two sequence-only links pointed to a seed row from another species;
  - the two clean structures are both from *E. coli*.
- **The exploratory pair.** Free *E. coli* tRNA-Val (7EQJ) and human tRNA3Lys (5CCB). In 5CCB the tRNA is bound to an
  enzyme whose paper reports that it refolds the tRNA. This confound was declared before alignment.
- **Result.** Of 64 STAR3D-aligned positions, 59 have the same partner as the seed; all 5 differences lie in the
  refolded elbow. Interaction preservation is equal: 81/97 for each method (`expansion_v4/results/`).

## 3. Results per pair (development set; forward direction, replicate 1)

| Pair | Tier | Assessable seed pairs | STAR3D pairs | Same | Different | Seed-only | STAR3D-only |
|---|---|---|---|---|---|---|---|
| RF00522 3FU2–6VUI | primary | 29 | 31 | 24 | 4 | 2 | 3 |
| RF00522 3FU2–7REX | primary | 30 | 32 | 17 | 13 | 1 | 2 |
| RF00522 6VUI–7REX | primary | 32 | 32 | 16 | 15 | 1 | 1 |
| RF00174 4GXY–6VMY | primary | 103 | 26 | 0 | 2 | 110 | 24 |
| RF00059 2GDI–3D2G | exploratory | 54 | 75 | 71 | 1 | 3 | 3 |
| RF00442 5U3G–7MLW | exploratory | 73 | 78 | 62 | 16 | 6 | 0 |
| RF00162 2GIS–4KQY | exploratory (engineered) | 81 | 25 | 0 | 21 | 68 | 4 |
| *Prospective:* RF00005 5CCB–7EQJ | exploratory (refolded substrate) | 73 | 64 | 59 | 5 | 9 | 0 |

Source: `results/pair_summary.tsv` and `expansion_v4/results/pair_summary.tsv`. The unit is one source residue.
- **Reading the "reproduced" fraction.** One minus the fraction of seed pairs that STAR3D reproduces is not a
  disagreement rate, because it also counts residues STAR3D did not align.
- **Shared RNAs.** Pairs that share an RNA are not independent.

## 4. How original STAR3D actually works here [V]

- **Paper vs code.** The paper builds stacks from A-U, C-G and G-U pairs. The released code keeps every cis W-edge pair
  that MC-Annotate reports, including non-canonical ones; 8 of 11 RNAs have such pairs in STAR3D's stack input.
- **Overwrite defect.** When one residue has two such partners, the code keeps the last one written. This happens once,
  at 7MLW residue 16 in the exploratory guanidine-I pair. Preprocessing is deterministic: 3 fresh runs plus the
  retained run are identical.
- **Two sensitivity analyses.** These are separately versioned and are not the primary method
  (`results/sensitivity/`).
  - **S1 (paper rule):** preQ1 mappings are identical. Guanidine-I falls from 78 to 25 aligned nucleotides, while
    cobalamin (13/26) and SAM-I (16/25) keep about half their pairs. TPP keeps 72 of 75.
  - **S2 (overwrite corrected only):** guanidine-I is identical to the default. The overwrite does not affect any
    result.
- **What this means.** The preQ1 conclusions do not depend on this paper-versus-code difference. The guanidine-I result
  does, and it was already exploratory.

## 5. Software validation [V]

- **Tests.** 64 tests pass.
- **Mutation tests.** Each of 16 historical defects was put back into a scratch copy of the code, and each was caught by
  its test (`tables/mutation_check.tsv`). The defects covered:
  - masking;
  - denominators;
  - symmetry mates;
  - region eligibility;
  - reuse of old interpretations;
  - stored-output validation;
  - injectivity;
  - subset reruns;
  - preprocessing contents;
  - checksum gate;
  - FR3D provenance;
  - multi-family Stockholm.
- **New fix.** Reverse-strand row coordinates in the crosswalk. It does not affect pilot rows.
- **Runs.** STAR3D runs under x86-64 emulation. This session made 22 alignment runs, with 0 crashes; 3 crashes in 84
  earlier runs remain on record.
- **Same agent.** Reruns by the same agent are reproduction, not independent validation.

## 6. Limitations

- **Small dataset.** There are 2 primary families, and the 3 preQ1 pairs share RNAs.
- **Narrow sampling.** Only curated families could be found by the explicit-link rule.
- **Interaction evidence is partly circular.** STAR3D's objective uses pairing, and FR3D is a separate program run on
  the same coordinates.
- **Review status.** The region classifications are an AI agent's judgement.
- **Not run.** A second structural aligner, and native x86-64 execution.

## 7. Recommendation for the next stage

**Do not scale up under the current rules: the eligible experimental inventory is exhausted.** Ask the professor to
choose one of these, each a declared scope change:
- **(a) Modified natural tRNAs.** Add parent-mapped residue names to the STAR3D input. This is a method change and would
  need its own validation.
- **(b) Engineered constructs** as a separately reported tier.
- **(c) Predicted structures** with Smriti, as a separate study.

**Independently of that choice:**
- Send the 7REX P1 candidate to an Rfam curator. This is the user's decision, and nobody has been contacted.
- Obtain a native x86-64 host.
