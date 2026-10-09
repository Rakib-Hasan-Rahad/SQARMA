# RF00522 / 7REX candidate: v4 re-check (2026-10-09)

*AI agent (Claude); no human review.* This updates `deliverables/2026-10-09/candidate_evidence_update.md` (v3). Every
count in v3 that was re-run gave the same value. The changes below are additions and corrections.

**Status tags used below**
- **[V]** Verified in this execution.
- **[R]** Retained evidence, not rerun.
- **[X]** Exploratory.

## Corrections
- v3 said "base-centroid distances … were not computed". **That was wrong.** `scripts/anchor_fit.py` has always written
  them. v4 reports both C1′ and base-centroid comparisons for every region.
- v3 said the row's "specific origin is unverified". It is now **partly documented**: the 7REX, 6VUI and 3FU2 rows first
  appear in RF00522 in release **15.0**. They are absent from 14.0–14.10, which had 35–36 rows; RF00522 has 43 rows in
  15.0 and 15.1. The 7REX aligned string is identical in 15.0 and 15.1, and the row carries the `#=GR` features
  `7REX_A_SS` and `8FB3_A_SS` (`results/rfam_history/rf00522_rows.tsv`). How the row was aligned is still undocumented.

## P1 3′ strand: supported candidate for curator review (moderate)

| Evidence | Seed | STAR3D | Status |
|---|---|---|---|
| Partner distance after superposition: 6VUI 14–21 and 3FU2 15–22; 3 anchor rules (shared, flank-excluded, local ±8); C1′ and base centroid | 3.6–9.7 Å | 0.4–4.3 Å; closer for every residue, rule and measure | [V] `results/region_evidence/` |
| FR3D canonical cWW pairs in the region, rfam-vs-STAR3D-forward eligible set (6VUI→7REX region) | 0/7 | 5/7 | [V] |
| Same, 3FU2→7REX region | 0/5 | 5/5 | [V] |
| Noncanonical pairs, 6VUI→7REX region / 3FU2→7REX region | 0/7 · 0/5 | 2/7 · 3/5 | [V] |
| Stacking, 6VUI→7REX region / 3FU2→7REX region | 7/18 · 4/9 | 10/18 · 9/9 | [V] |
| 7REX authors' own description of P1: "a canonical A-form helix … A28•G5-C18•A29 base-triple" (G5–C18 = STAR3D register) | contradicts G5–C17 | consistent | [V] PMC8752633 (local copy) |
| P1 cWW present in all 3 crystal copies (U1–A22 in 2). The authors report a break at the chain C P1–L3 junction, which explains the missing copy | — | consistent | [R] review/candidate_RF00522; paper |
| Paper-rule sensitivity S1 (canonical cis Ww/Ww pairs only) | — | 7REX mappings identical | [V] `results/sensitivity/S1_vs_default.tsv` |
| Sequence-level complementarity across all 43 RF00522 rows: only the 7REX row improves with a +1 shift | — | — | [V] v3 `tables/RF00522_P1_register_all_rows.tsv` |
| Exploratory adjusted row: 31/46 and 33/44 preserved, against seed 19/46 and 20/44 and STAR3D 29/46 and 31/44 | — | — | [X] designed on these data; not a test |

**Against, or limiting:**
- **One observation.** Both comparisons share the 7REX row.
- **Partly circular evidence.** STAR3D's objective uses pairing.
- **Ligand contact.** The additional preQ1, PRF101, contacts 7REX residue 16, which lies inside the strand. (Which of the paper's α/β sites PRF101 occupies was not mapped.)
- **Crystal contacts.** Chain B in the asymmetric unit contacts 7REX 21–22, and symmetry mates contact 6VUI 19–23.
- **Unresolved neighbour.** 6VUI U22: both partners are about 6 Å away.

## L1 (6VUI 7–12): seed better supported (low–moderate)

**For the seed:**
- Partner distances: G8 3.4 Å vs 10.0 Å; G11 3.3 Å vs 8.7 Å (shared fit).
- The seed preserves 3 L1 stacks that STAR3D loses.
- **New:** the seed maps the 6VUI C7–G11 pair (FR3D tWH) onto 7REX C8–A12 (FR3D tWW; a different class). The 7REX
  authors describe this as part of the "pocket ceiling" U32•A12•C8 triple. STAR3D maps 6VUI 7 and 11 to 7REX 7 and 13.

**For STAR3D:** C7 (3.3 Å vs 5.3 Å) and U12 (1.3 Å vs 4.7 Å).

**Context.** The two preQ1 molecules are stacked in one pocket (paper). PRF101 contacts L1 residues 7, 8 and 12, so
ligand-context variation is plausible.

## Dependence
- This is one candidate observation. The 3FU2–7REX and 6VUI–7REX comparisons share the 7REX row, and their counts are
  not added together.
- FR3D annotation absence is reported as "no FR3D annotation detected", not as the absence of a physical interaction.
