# Original STAR3D: pair selection, overwrite and sensitivity (v4, 2026-10-09)

*AI agent (Claude); no human review.* This extends `deliverables/2026-10-09/STAR3D_execution_audit.md` (v3), whose
identity, command and parameter checks still apply.

## 1. What the source does, verified by reading `src/*.java` of the pinned v1.2 package
- **`MCA.java`** reads only the first "Base-pairs" section of MC-Annotate output. It labels a pair `XYc` or `XYt` using
  only the **first letter** of each edge token. As a result:
  - Ww/Ws counts as WW;
  - Wh/Wh counts as WW;
  - pairs reported without cis or trans become `--h`.
- **`Preprocess.java`** writes every pair labelled `WWc` into a single partner slot per residue, whatever the base
  identity. A later pair overwrites an earlier one. The code collects a `multi_pair` list but never uses it.
- **The overwrite order is formally unspecified.** The pairs sit in a `HashSet` of a class (`Pair`) that defines
  neither `equals` nor `hashCode`, so iteration follows JVM identity hashes.
- **`DATAPATH` is never passed.** It is set on a `ProcessBuilder` that is never used; RemovePseudoknots is launched with
  `Runtime.exec`. The tool still produced valid output for all RNAs.
- **The aligner reads two files:**
  - `npk.ct` (pseudoknot-free), for stacks;
  - the full `.mca`, for the pairing bonus in loop scoring, including non-canonical pairs.
- **Modified nucleotides.** Any residue name other than A/C/G/U becomes "N" in STAR3D's sequence. The residue is not
  parent-mapped. This is relevant to native tRNAs.

**The paper differs.** It describes stacks formed from A-U, C-G and G-U pairs. The code's rule is broader, as listed
above.

## 2. Measured effect on the 11 pilot RNAs (`star3d_sensitivity/preproc_summary.tsv`) [V]
- **Re-implementation check.** STAR3D's rule, re-implemented in Python, is consistent with all 11 retained `.ct`
  files. Every partner recorded in a `.ct` is one of the re-implemented "WWc" partners, and no residue that has a
  "WWc" pair is left unpaired. This includes the one non-reciprocal case (7MLW F16 → 41; index 44 left pointing
  at 16).
- **Non-canonical pairs.** 8 of 11 RNAs have non-canonical-identity or non-Ww/Ww "WWc" pairs in the stack input
  (`npk.ct`). 6VUI and 7REX have none, and 3FU2 has none after pseudoknot removal.
- **Overwrite.** There is exactly **1 overwrite in 11 RNAs**: 7MLW chain F residue 16, which has a Wh/Wh partner at
  auth 44 and a Ww/Ww partner at auth 47. The kept partner is the Wh/Wh one. After pseudoknot removal, residue 16 and
  both partners are unpaired.
- **Repeatability.** Original preprocessing of 7MLW, rerun 3 times in fresh directories, gives identical `.mca`, `.ct`
  and `npk.ct`, and these match the retained run. The order is formally unspecified but was stable in practice.

## 3. Sensitivity analyses: separately versioned, NOT the primary method [V]

**Pre-declared.** The design is written in the header of `scripts/star3d_sensitivity.py` and
`scripts/star3d_sensitivity_s2.py`.

**What stays original.** Both variants use the original `.mca`, RemovePseudoknots, `STAR3D.jar`, default parameters and
container. Only the `.ct` given to RemovePseudoknots changes. Each run is 1 replicate per direction. JVM-signal retries
were allowed, and none occurred.

- **S1, paper rule.** Keep only cis Ww/Ww pairs with identity AU/UA/GC/CG/GU/UG. There are no conflicts in any RNA.
- **S2, overwrite only.** Change 7MLW residue 16 to its Ww/Ww partner. Everything else stays original.

**Results, forward direction** (`results/sensitivity/S1_vs_default.tsv`, `S2_vs_default.tsv`):

| Pair | Tier | Default aligned | S1 aligned | Shared with default | Same as seed (default → S1) |
|---|---|---|---|---|---|
| RF00522 3FU2–6VUI | primary | 31 | 31 | 31 (identical) | 24 → 24 |
| RF00522 3FU2–7REX | primary | 32 | 32 | 32 (identical) | 17 → 17 |
| RF00522 6VUI–7REX | primary | 32 | 32 | 32 (identical) | 16 → 16 |
| RF00174 4GXY–6VMY | primary | 26 | 27 | 13 | 0 → 0 |
| RF00059 2GDI–3D2G | exploratory | 75 | 76 | 72 | 71 → 68 |
| RF00162 2GIS–4KQY | exploratory (engineered) | 25 | 24 | 16 | 0 → 0 |
| RF00442 5U3G–7MLW | exploratory | 78 | 25 | 0 | 62 → 0 |
| RF00442 5U3G–7MLW, **S2** | exploratory | 78 | 78 | 78 (identical) | 62 → 62 |

**Interpretation:**
1. **The preQ1 findings do not depend on the pairing-rule difference.** All three preQ1 mappings are identical under S1.
2. **The overwrite affected nothing.** S2 is identical to the default.
3. **Guanidine-I's long alignment depends on STAR3D's broader pair rule.** The likely mechanism, not traced
   stack-by-stack, is that removing non-canonical and non-Ww/Ww pairs shortens or splits helices below the minimum
   stack size. Its long alignment is therefore a property of the released code, not of the method as the paper
   describes it. The pair was already exploratory.
4. **Cobalamin's STAR3D mapping is unstable.** Its one-module mapping shifts by half under S1. It was already treated as
   a coverage limitation.

## 4. Execution status this session [V]
- **Runs.** 22 alignment runs (S1 14, S2 2, prospective tRNA 6) and 21 preprocessing steps all completed, with
  **0 JVM crashes**. The preprocessing steps are 16 RemovePseudoknots steps for S1/S2, 2 Preprocess steps for tRNA and
  3 for the determinism check.
- **Earlier crash record.** 3 crashes in 84 earlier emulated alignment runs remain on record.
- **Platform.** All runs used x86-64 emulation (QEMU via colima) on an arm64 Mac. A native host was not available.
