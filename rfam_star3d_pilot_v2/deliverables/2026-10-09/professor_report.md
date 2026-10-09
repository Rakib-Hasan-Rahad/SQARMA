# Rfam seed vs original STAR3D: pilot status report (2026-10-09)

*Prepared by an AI research agent (Claude) for Rakib Hasan Rahad. No human has reviewed these results, and no approval
from the professor is implied.*

**Status tags used below**
- **[V]** Verified this session.
- **[R]** Supported by retained pilot evidence; not rerun this session.
- **[X]** Exploratory.
- **[U]** Unresolved.

Every number comes from a table named alongside it. Paths are relative to `rfam_star3d_pilot_v2/`.

## 1. One-page summary

**The question.** For two experimentally solved RNAs from the same Rfam family, from different organisms, does the
published Rfam seed alignment pair up the same nucleotides as the original STAR3D structural aligner? Where the two
disagree, what does the 3D structure say? Neither method is treated as ground truth.

**The dataset.** We compared 7 RNA pairs (5 families). These pairs were also used to debug the workflow and to design
one exploratory adjustment, so they are a *development set*.
- 4 pairs from 2 families are primary: preQ1-I RF00522 (3 pairs sharing 3 RNAs) and cobalamin RF00174 (1 pair).
- 3 are exploratory.
- This session we screened the remaining 21 families that had passed the first screen. **None yielded a new pair that
  passes every primary criterion** (two distinct natural sequences, no engineering in the compared motifs, coordinates
  ≥90% observed) [V] (`review/v3_screening/candidate_screening.tsv`). So no new prospective comparison was run. This
  answers part of the feasibility question: suitable natural, unengineered pairs are scarce.

**The main finding [V/R].**
- In preQ1-I, the seed places the 3′ strand of helix P1 in the *Carnobacterium antarcticum* row (PDB 7REX) one
  nucleotide out of register relative to the crystal structure.
- STAR3D's correspondence matches the Watson–Crick pairs observed in 7REX. The seed's does not: FR3D detects no
  annotation for the five seed-implied pairs.
- **The finding is row-specific, not family-wide (sequence-level check).** Of the 43 preQ1-I seed rows, only the 7REX
  row becomes fully complementary in P1 when shifted one residue (2/5 → 5/5 complementary pairs)
  (`tables/RF00522_P1_register_all_rows.tsv`).
- **It is one candidate observation, not two.** Both supporting comparisons share the 7REX row. It is a candidate for
  curator review, not a demonstrated error.

**The counter-example.**
- In loop L1 of the same RNA, the seed's correspondence fits the structure *better* than STAR3D's (section 4).
- In 7REX a second preQ1 molecule contacts L1 (computed from coordinates). That may explain the local difference.

**A new result on the professor's provenance question (Survey B) [V].**
- In Rfam 15.1 the structure-curated seed file (`Rfam.3d.seed.gz`, 74 families) is **byte-identical** to the
  corresponding 74 families in the ordinary `Rfam.seed.gz`.
- All five pilot families are among them. So for these families the "ordinary" seed already *is* the 3D-curated
  alignment.
- Comparing the two files cannot tell us which correspondences 3D curation changed. That needs an earlier release
  (`results/seed_collection_comparison/README.md`).

**Software reliability [V].**
- Five repairs were made this session (section 6); 51/51 tests pass.
- None of them changed any scientific table.
- All 7 pairs have now been freshly re-run from re-downloaded files. Every completed run matched exactly.
- Under x86 emulation on this Mac, 2 of today's 24 runs crashed in the Java runtime (section 6).

## 2. How the data were selected (funnel)

The first two rows come from `results/family_inventory.tsv`, the rest from `review/` and
`review/v3_screening/`.

| Stage | Count |
|---|---|
| Families in Rfam 15.1 with a PDB candidate (in `Rfam.pdb.gz` or via a seed `#=GR` link; all types) | 167 |
| … with explicit `#=GR` structure links in the ordinary seed | 74 (the same 74 families as the curated collection; see Survey B) |
| … with ≥2 explicitly linked distinct row sequences (54 if sequence-only proposals were counted) | 31 |
| Passed the automated screen (also model ≤300 nt and not rRNA) | 31 |
| Reviewed by hand (10 before, 21 today) | 31 |
| Primary families | 2 (RF00522, RF00174) |
| Exploratory, pilot | 3 (RF00059, RF00162, RF00442) |
| Exploratory only, newly reviewed, not run | 4 (THF, CPEB3, PrrB_RsmZ, ZMP-ZTP) |
| Excluded or redundant, newly reviewed | 17 |

**Why the new candidates failed** (`review/v3_screening/screening_notes.md`):
- **Engineering inside the family interval.** THF: tetraloop replacement and Watson–Crick conversions. CPEB3: a U1A
  module. ZMP-ZTP: internal changes, and its construct papers were inaccessible.
- **A single natural source.** Most of the remaining families have only one natural source, or only designed or
  evolved variants.
- **Low coordinate coverage.** mir-16 is only 63–74% observed.
- **NMR-only partners.**

Our discovery rule requires explicit `#=GR` links, and these exist only in the 74 3D-curated families. The pilot can
therefore only ever sample 3D-curated families. Several limits make this list incomplete:
- the explicit `#=GR` link rule;
- the 300 nt cap and the rRNA exclusion;
- 1,793 sequence-only chain–row proposals that still lack provenance review.

## 3. Results per pair (development set) [R; fresh rerun identical — V]

Counting unit: residue correspondences in one direction (forward, replicate 1), from `results/pair_summary.tsv`.
- "Assessable seed pairs" are those with coordinates on both sides and no engineering mask.
- "Reproduced" is the number of assessable seed pairs that STAR3D also produces.
- 1 − reproduced is **not** a disagreement rate, because it also counts residues STAR3D left unaligned.

| Pair | Tier | Assessable seed pairs | STAR3D pairs | Same partner | Different partner | Seed-only | STAR3D-only |
|---|---|---|---|---|---|---|---|
| RF00522 3FU2–6VUI | primary | 29 | 31 | 24 | 4 | 2 | 3 |
| RF00522 3FU2–7REX | primary | 30 | 32 | 17 | 13 | 1 | 2 |
| RF00522 6VUI–7REX | primary | 32 | 32 | 16 | 15 | 1 | 1 |
| RF00174 4GXY–6VMY | primary | 103 | 26 | 0 | 2 | 110 | 24 |
| RF00059 2GDI–3D2G | exploratory | 54 | 75 | 71 | 1 | 3 | 3 |
| RF00442 5U3G–7MLW | exploratory | 73 | 78 | 62 | 16 | 6 | 0 |
| RF00162 2GIS–4KQY | exploratory (engineered) | 81 | 25 | 0 | 21 | 68 | 4 |

Reading the table:
- **Agreement control.** TPP (RF00059) agrees almost completely: 71 same partners, 1 different.
- **Coverage limits, not disagreements.** In cobalamin and SAM-I, STAR3D aligned only one helical module (26 and 25
  nucleotides). Its default minimum stack size and RMSD cutoff can produce such short alignments.
- **Replicates.** Identical in every direction group. Forward and reverse differ by 2 pairs for 3FU2–6VUI and
  4GXY–6VMY (`results/replicate_consistency.tsv`).
- **A STAR3D tool defect** affects the exploratory guanidine-I pair: STAR3D's own structure for 7MLW loses the C16–G47
  pair (section 6).

## 4. The 7REX case in detail

The full write-up is `candidate_evidence_update.md`. Figures:
- `figures/fig_7REX_correspondence_6VUI.png` is drawn from the tables.
- `../../figures/fig_RF00522_6VUI_7REX_P1.png` is the retained 3D superposition.

| 6VUI pair (cWW in 6VUI) | Seed partner in 7REX | STAR3D partner in 7REX |
|---|---|---|
| C1–G20 | U1–C21: no FR3D annotation detected | U1–A22: cWW |
| U2–A19 | G2–A20: no FR3D annotation detected | G2–C21: cWW |
| G3–C18 | U3–C19: no FR3D annotation detected | U3–A20: cWW |
| G4–C17 | G4–C18: no FR3D annotation detected | G4–C19: cWW |
| G5–C16 | G5–C17: no FR3D annotation detected | G5–C18: cWW |

**Interaction preservation [V].** Each count is over one identical eligible set per row
(`tables/candidate_7REX_counts.tsv`).

| Direction | Eligible | Seed | STAR3D | Adjusted row [X] | Canonical (seed/STAR3D/adj.) | Noncanonical | Stacking |
|---|---|---|---|---|---|---|---|
| 6VUI → 7REX | 46 | 19 | 29 | 31 | 0/5/5 of 7 | 2/4/4 of 8 | 17/20/22 of 31 |
| 3FU2 → 7REX | 44 | 20 | 31 | 33 | 0/5/5 of 7 | 3/6/6 of 8 | 17/20/22 of 29 |
| 7REX → 6VUI (new) | 38 | 16 | 28 | 29 | 0/5/5 of 5 | 2/4/4 of 6 | 14/19/20 of 27 |
| 7REX → 3FU2 (new) | 39 | 19 | 31 | 30 | 0/4/4 of 4 | 3/6/6 of 8 | 16/21/20 of 27 |

**Evidence for the candidate.**
- **Seed consensus [R].** The seed's own consensus structure, applied to the 7REX row, implies three non-Watson–Crick
  P1 pairs.
- **Crystal copies [R].** The STAR3D register is present in all three copies of the RNA in the crystal (U1–A22 in two
  of the three).
- **Anchor fits [R].** In the fits on agreed residues, the STAR3D partners lie 0.2–3.2 Å away (C1′) and the seed
  partners 4–9 Å, under two different anchor sets.
- **Sequence provenance [R].** Each RNA matches its source genome exactly over the checked interval.

**Evidence against, or caveats.**
- **Circularity.** STAR3D builds its alignment from pairing information, so pair preservation is partly circular.
  Today's code audit found it keeps any cis Watson–Crick/Watson–Crick pair, including non-canonical ones.
- **One observation.** The 3FU2 and 6VUI comparisons share the 7REX row.
- **L1 favours the seed.** The seed preserves 3 L1 stacks that STAR3D loses.
- **Ligand confound.** The second 7REX ligand contacts L1 *and* residue 16 inside the candidate strand [V].
- **Adjustment not independent.** The adjusted row was designed on these data. In the reciprocal 7REX→3FU2 direction
  it preserves one stack fewer than STAR3D.

## 5. Professor-requested work: status

`tables/requirements_status.tsv` has the full table with evidence paths.

| Requirement | Status |
|---|---|
| Families with ≥2 distinct natural sources | partial: all 31 screened families reviewed; 2 primary |
| PDB-to-Rfam row correspondence | completed for pilot rows |
| Construct and engineering review | completed for reviewed families (some papers inaccessible) |
| Original STAR3D comparison | completed (7 pairs, freshly reproduced) |
| Interaction and motif interpretation | partial (5 of 19 regions inspected) |
| Ordinary vs curated seed | completed for 15.1: identical; the pre-curation comparison is outstanding |
| Predicted structures (Smriti) | not started; fallback only, no message sent |

## 6. Validation and limitations

**Repairs** (`repair_impact_report.md`). Each change below came with a regression test.
1. **Derived Stockholm file.** It is now valid, with one record per family.
2. **Input checks in fresh reproduction.** A changed input now stops every step that depends on it.
3. **FR3D provenance.** The FR3D version is now read from the installed package, and cached outputs are reused only
   if their hashes match.
4. **Stored STAR3D outputs.** These are re-validated when read.
5. **STAR3D preprocessing.** Its intermediate files are now checked, not just its exit code.

**Wording.** Overstated claims were corrected:
- "no base pair" now reads "no FR3D annotation detected";
- the unsupported statement about the 7REX row's history was removed;
- evidence-card wording was fixed.

**What changed in the results.** No correspondence, interaction, region or candidate table changed.

**STAR3D audit** (`STAR3D_execution_audit.md`):
- **Identity.** Package, JAR and default parameters match the README and source.
- **Paper vs code.** The paper says A-U, C-G and G-U pairs, but the code keeps all cis Watson–Crick/Watson–Crick pairs.
- **Overwrite defect.** When a residue has two such partners, the later one overwrites the earlier. This affects 7MLW.
- **Coordinate gaps.** These are scored as neighbours (3FU2 residues 12 and 15), so 3FU2 L1 geometry is low
  confidence.

**Platform.** STAR3D runs under QEMU x86-64 emulation on an arm64 Mac.
- There have been 3 Java runtime crashes in 84 emulated runs, in different runs each time.
- Every completed run is reproducible.
- A native Linux x86-64 host would remove this confound.

**Not done this session:**
- base-centroid and heavy-atom orientation geometry;
- a second structural aligner;
- inspection of 14 pending regions;
- a pre-curation Rfam comparison;
- curator contact.

## 7. Is further expansion justified?

**Not with the current criteria and sources.**
- Every screen-passing family has now been reviewed, and none added a primary pair.
- More data would need an explicitly revised scope, decided by the researcher and professor. Options include:
  - reviewing the 1,793 sequence-only links;
  - relaxing the 300 nt cap or the rRNA exclusion by a declared decision;
  - accepting masked engineered constructs as a separate tier;
  - predicted structures, as a separate study.
- **Checks still needed first:**
  - a native x86-64 STAR3D host;
  - the inaccessible ZMP-ZTP construct papers;
  - a pre-curation Rfam release, to ask how the 7REX row's register arose.
