# Candidate evidence update — RF00522 preQ1-I, 7REX row (2026-10-09)

*Prepared by an AI agent (Claude). No researcher, professor or curator has reviewed this. The 7REX observation is a
**candidate for curator review**. It is not a demonstrated Rfam error.*

**Status labels used below**
- **[V]** Verified this session (recomputed or byte-compared today).
- **[R]** Supported by retained pilot evidence; not rerun this session.
- **[X]** Exploratory.
- **[U]** Unresolved.

## 1. What is being compared
- **Reference.** The ordinary Rfam seed, `Rfam.seed.gz` release 15.1. The 7REX row is `URS00023119CB_2126436/1-34`
  (*Carnobacterium antarcticum*). It is compared with the rows for 6VUI (*T. tengcongensis*, `URS000080E32E_119072/1-33`)
  and 3FU2 (*B. subtilis*, `URS000080E020_32630/1-34`).
- **Structural aligner.** Original STAR3D v1.2 with default parameters, both directions, 3 replicates each. The
  replicates are identical.
- **Exploratory adjusted row [X].** The 7REX row with residues 15–22 moved one column to the left. Column 24 is an
  insert column (`#=GC RF` = `.`). The adjusted row was designed after looking at these data, so its counts below are
  development-set observations, not a prospective test. The original row is kept unchanged. No seed edit has been made
  or submitted.
- **Not two discoveries.** Both comparisons (6VUI→7REX and 3FU2→7REX) share the 7REX row, so they are one candidate
  observation, not two independent ones.

## 2. Side-by-side correspondence (6VUI P1 → 7REX) [V]
The source is `tables/candidate_7REX_correspondence.tsv`, recomputed today. `scripts/candidate_evidence.py` rerun
gives outputs byte-identical to the retained `review/candidate_RF00522/`.

| 6VUI pair (FR3D cWW in 6VUI) | Seed partner pair in 7REX | STAR3D partner pair in 7REX | Adjusted [X] |
|---|---|---|---|
| C1–G20 | U1–C21: no FR3D annotation detected | U1–A22: cWW | U1–A22: cWW |
| U2–A19 | G2–A20: no FR3D annotation detected | G2–C21: cWW | G2–C21: cWW |
| G3–C18 | U3–C19: no FR3D annotation detected | U3–A20: cWW | U3–A20: cWW |
| G4–C17 | G4–C18: no FR3D annotation detected | G4–C19: cWW | G4–C19: cWW |
| G5–C16 | G5–C17: no FR3D annotation detected | G5–C18: cWW | G5–C18: cWW |

"No FR3D annotation detected" means FR3D reported no interaction for that residue pair. It does not prove the pair is
physically impossible.

Figures:
- `figures/fig_7REX_correspondence_6VUI.png` is drawn only from the residue-evidence table and FR3D cWW annotations.
  Its x-axis is residue index, not coordinates.
- `figures/fig_RF00522_6VUI_7REX_P1.png` (retained) is a PyMOL superposition. 6VUI is grey and 7REX is teal. The fit
  uses C1′ atoms of the 16 residue pairs on which seed and STAR3D agree (6VUI 1–6↔7REX 1–6, 6VUI 24–33↔7REX 25–34).
  The labelled C1′ distances are 6VUI C16 to 7REX C18 (STAR3D partner, 0.6 Å) and to 7REX C17 (seed partner, 6.6 Å).

## 3. Interaction preservation on identical eligible sets [V]
The source is `tables/candidate_7REX_counts.tsv`, recomputed today from re-verified FR3D outputs. The eligible set is
the same for all three mappings: every interaction whose endpoints are unmasked and observed, and which every method
maps.

| Direction | Class | Eligible n | Seed | STAR3D | Adjusted [X] |
|---|---|---|---|---|---|
| 6VUI → 7REX | all | 46 | 19 | 29 | 31 |
|  | canonical (cWW AU/GC) | 7 | 0 | 5 | 5 |
|  | wobble | 0 | 0 | 0 | 0 |
|  | noncanonical | 8 | 2 | 4 | 4 |
|  | stacking | 31 | 17 | 20 | 22 |
| 3FU2 → 7REX | all | 44 | 20 | 31 | 33 |
|  | canonical | 7 | 0 | 5 | 5 |
|  | noncanonical | 8 | 3 | 6 | 6 |
|  | stacking | 29 | 17 | 20 | 22 |
| **Reciprocal, new today:** 7REX → 6VUI | all | 38 | 16 | 28 | 29 |
|  | canonical / noncanonical / stacking | 5 / 6 / 27 | 0 / 2 / 14 | 5 / 4 / 19 | 5 / 4 / 20 |
| **Reciprocal, new today:** 7REX → 3FU2 | all | 39 | 19 | 31 | **30** |
|  | canonical / noncanonical / stacking | 4 / 8 / 27 | 0 / 3 / 16 | 4 / 6 / 21 | 4 / 6 / **20** |

**Why the denominators differ.**
- The earlier two-method comparison (seed vs STAR3D forward) has 47 eligible interactions for 6VUI→7REX
  (`results/interaction_summary.tsv`). The three-method set has 46.
- The adjusted row leaves two 6VUI interactions without a mapped endpoint: cSH 20–21 and s55 21–23. The adjusted row
  moves 7REX A22 so that 6VUI U21 has no partner (`tables/candidate_7REX_excluded_from_common_set.tsv`). Because one
  set excludes that interaction and the other doesn't, the 46 and 47 sets are not interchangeable.
- For 3FU2→7REX, 5 interactions are excluded. In 4 of them the seed itself leaves an endpoint unmapped.

**Where the seed does better: L1, 6VUI residues 7–10** (`tables/candidate_7REX_method_differences.tsv`)
- Four stacks are preserved by the seed (and by the adjusted row, which does not move L1) but **not** by STAR3D:
  s35 7–8, ns33 8–10 and s35 9–10 in 6VUI→7REX, and s35 9–10 in 3FU2→7REX.
- STAR3D does better at only one L1 stack (s35 6–7).
- In the retained anchor fit (`results/anchor_fit/…_shared.tsv`), 6VUI G8's seed partner is 3.4 Å away (C1′) and its
  STAR3D partner 10.0 Å away.
- So the L1 evidence favours the seed. The candidate concerns only the P1 3′ strand.

**Losses.**
- Inside the common set, the adjusted row loses no interaction that the seed preserved
  (`adjustment_validation.json`: `interactions_lost_by_adjustment = []`).
- Outside the common set, the adjusted row cannot score cSH 20–21 and s55 21–23. The seed does not preserve them
  either (`different_class` and `no_annotated_target_pair`).
- In the reciprocal 7REX→3FU2 direction, the adjusted row preserves one stack fewer than STAR3D (30 vs 31).

## 4. Geometry: what was measured, and with which anchors [R]
- **Anchor fit.** The shared-correspondence anchor fit (`scripts/anchor_fit.py`) is a Kabsch fit on C1′ atoms of
  residue pairs where the seed and STAR3D *agree*.
  - **Rule `shared`:** 16 anchors (6VUI 1–6↔7REX 1–6; 6VUI 24–33↔7REX 25–34), fit RMSD 2.64 Å.
  - **Rule `shared_flank_excl`:** drops 2 anchors on each side of the disputed span, leaving 12 anchors
    (1–4↔1–4; 26–33↔27–34), fit RMSD 1.89 Å.
  - **Rule `shared_canonical`:** only 5 anchors, 1–5. It was **refused** as degenerate (smallest singular value
    0.19 Å).
- **Results.** Distances are C1′–C1′ after the fit.
  - On the P1 3′ strand, the STAR3D partners are 0.2–3.2 Å from the superposed 6VUI residue and the seed partners
    4–9 Å. Both admissible anchor sets give the same answer.
  - These are C1′ distances. They are a different measure from STAR3D's own reported RMSD, which uses backbone-centroid
    stacks over all aligned residues, and the two are not compared as scores.
- **Not measured.** Base-centroid distances and heavy-atom base orientation were not computed this session [U].

## 5. Ligand context (new today, computed from coordinates) [V]
- **The two ligands.** 7REX has two preQ1 ligands (`structure_facts.tsv`, residues within 4 Å).
  - PRF102 contacts residues 5, 6, 16, 17, 18, 30 and 31.
  - PRF101 contacts residues 7, 8, 12, 16, 30, 31 and 32.
- **Which site matches 6VUI.** The single 6VUI preQ1 contacts 9 residues (5, 6, 7, 11, 14, 15, 16, 29, 30). Mapped
  into 7REX, the number landing on PRF102 contact residues is:
  - 7/9 under STAR3D;
  - 6/9 under the seed;
  - 7/9 under the adjusted row.

  Under every mapping, more contacts land on PRF102 than on PRF101 (4–5/9). So PRF102 corresponds to the conserved
  6VUI site, and PRF101 is the additional ligand. It contacts L1 (7, 8, 12). This calculation is in this document's
  build log (`logs/ligand_site_mapping.txt`).
- **What this means for the explanations.** This is consistent with the earlier explanation that the second ligand
  changes local L1 geometry. That explanation was previously stated without a contact calculation; it now has a
  measured basis but is still unconfirmed against the structure paper [U].
- **A new caveat.** PRF101 also contacts 7REX residue **16**, which lies inside the disputed P1 3′ strand. Ligand
  context is therefore a possible local confound for the candidate region too, not only for L1.

## 6. Provenance of the three RNAs [V/R]
- **Genome matches [R].** Each RNA matches its source genome exactly over the checked interval:
  - 6VUI: AE008691.1, minus strand at 1523221, 33 nt;
  - 3FU2: AL009126.3, plus strand at 1439279, 34 nt;
  - 7REX: CP010796, plus strand at 2093557, 34 nt.

  No sequence changes were detected over those intervals. An exact match does not prove every aspect of experimental
  preparation.
- **Raw-file checks [V].** Re-confirmed today from the raw files: no modified nucleotides in any of the three chains,
  and FR3D raw outputs byte-identical after regeneration with the verified installed FR3D commit.
- **Coordinate limits.**
  - 3FU2 residues 13 and 14 have no coordinates.
  - 3FU2 C12 has only P and O5′ (2 of the 6 atoms STAR3D uses for centroids).
  - STAR3D's parser treats 3FU2 residues 12 and 15 as neighbours (STAR3D execution audit), so 3FU2–7REX L1 geometry
    (region r9-12) is **low confidence** and not used for adjudication.

## 7. Independence and circularity
- STAR3D builds stacks from coordinate-derived Watson–Crick-edge pairs and adds pairing bonuses, including
  noncanonical and pseudoknot pairs, in loop scoring (Ge & Zhang 2015; execution audit).
- The audit also found that the code keeps any cis Watson–Crick/Watson–Crick pair from MC-Annotate, not only AU/GC/GU.
- So canonical **and** noncanonical preservation are partly circular with STAR3D's own objective. FR3D is a separate
  implementation, but it is not independent biological information.
- The improved counts of the adjusted row were obtained on the same data used to design it.

## 8. Classification
| Region | Classification | Strength |
|---|---|---|
| 7REX row, P1 3′ strand (6VUI 14–22 / 3FU2 15–22) | possible Rfam correspondence issue — **candidate for curator review** | moderate. For: within-row SS_cons pairing check, cWW in the 7REX crystal, anchor fits, interaction counts. Against: STAR3D circularity, one shared row, ligand PRF101 contacts residue 16 |
| L1, 6VUI 7–10 → 7REX | possible STAR3D issue / plausible structural variation (second ligand) | low–moderate; the seed is better supported here |
| 3FU2 L1, r9-12 | technical/coordinate confound (missing 13–14, partial C12, parser adjacency) | unresolved |
| SAM-I pair (RF00162) | unchanged: exploratory (engineered, technical). Part of the justification arose after observing the alignment | — |

**Still to do:**
- Check other preQ1-I seed rows with different P1 lengths, together with neighbouring rows, before suggesting any
  family-level change.
- Optionally corroborate with a second structural aligner, kept separate from the professor's original-STAR3D
  experiment.
- Have a curator check the row's alignment history. Its specific origin is unverified.
