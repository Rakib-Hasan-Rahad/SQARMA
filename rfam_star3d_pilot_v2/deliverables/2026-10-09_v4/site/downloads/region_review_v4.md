# Region review: all regions (v4, 2026-10-09)

*Generated from `review/region_review_v4.tsv`, `expansion_v4/review/region_review_v4.tsv` and `results/region_evidence/summary.tsv` by `deliverables/2026-10-09_v4/scripts/render_region_review.py`. Reviewer: AI agent (Claude); no human review.*

How to read the evidence columns:

- **Interactions:** canonical / noncanonical / stacking counts on the rfam-vs-STAR3D-forward eligible set, written as n / seed preserved / STAR3D preserved.
- **Closer (C1′):** for the residues whose partners differ, how many had the seed partner closer and how many the STAR3D partner, after the shared-anchor fit.
- **Local fit:** the same comparison using anchors within ±8 positions of the region.

| Region | Sub-span | Classification (confidence) | Residues: categories | Interactions can/nc/stack | Closer (C1′, shared) | Local fit | Fwd=Rev |
|---|---|---|---|---|---|---|---|
| RF00522 6VUI_A 7REX_A r7-23 | 6VUI 13-21 (P1 3' strand + J) | supported_candidate_Rfam_correspondence_issue (moderate) | different_partner:15;star3d_only:1;rfam_only:1 | 7/0/5 · 7/0/2 · 18/7/10 | rfam 4 / star3d 10 / tie 1 / NA 0 | rfam 2 / star3d 12 / tie 1 / NA 0 | 17/17 |
| RF00522 6VUI_A 7REX_A r7-23 | 6VUI 7-12 (L1) | possible_STAR3D_correspondence_issue (low-moderate) | different_partner:15;star3d_only:1;rfam_only:1 | 7/0/5 · 7/0/2 · 18/7/10 | rfam 4 / star3d 10 / tie 1 / NA 0 | rfam 2 / star3d 12 / tie 1 / NA 0 | 17/17 |
| RF00522 3FU2_A 7REX_A r15-22 | 3FU2 15-22 (P1 3' strand) | supported_candidate_Rfam_correspondence_issue (moderate) | star3d_only:1;different_partner:7 | 5/0/5 · 5/0/3 · 9/4/9 | rfam 0 / star3d 7 / tie 0 / NA 0 | rfam 0 / star3d 7 / tie 0 / NA 0 | 8/8 |
| RF00522 3FU2_A 7REX_A r9-12 | 3FU2 9-12 (L1) | construct_or_coordinate_confound (low) | different_partner:4 | 2/0/0 · 1/0/0 · 4/1/0 | rfam 1 / star3d 2 / tie 0 / NA 1 | rfam 1 / star3d 2 / tie 0 / NA 1 | 4/4 |
| RF00522 3FU2_A 7REX_A r32-34 | 3' terminal 32-34 | insufficient_evidence (low) | star3d_only:1;different_partner:2 | 1/0/0 · 0/0/0 · 2/1/0 | rfam 1 / star3d 1 / tie 0 / NA 0 | rfam 1 / star3d 1 / tie 0 / NA 0 | 3/3 |
| RF00522 3FU2_A 6VUI_A r32-34 | 3' terminal 32-34 | insufficient_evidence (low) | star3d_only:1;different_partner:1;rfam_only:1 | 1/0/1 · 0/0/0 · 1/0/1 | rfam 0 / star3d 1 / tie 0 / NA 0 | rfam 1 / star3d 0 / tie 0 / NA 0 | 1/3 |
| RF00522 3FU2_A 6VUI_A r23-24 | 3FU2 23-24 (J/L3) | insufficient_evidence (low) | different_partner:2 | 0/0/0 · 0/0/0 · 2/0/0 | rfam 1 / star3d 1 / tie 0 / NA 0 | rfam 2 / star3d 0 / tie 0 / NA 0 | 2/2 |
| RF00522 3FU2_A 6VUI_A r7-8 | 3FU2 7-8 (L1 start) | insufficient_evidence (low) | star3d_only:1;different_partner:1 | 0/0/0 · 0/0/0 · 1/0/0 | rfam 0 / star3d 1 / tie 0 / NA 0 | rfam 0 / star3d 1 / tie 0 / NA 0 | 2/2 |
| RF00522 3FU2_A 6VUI_A r15-15 | 3FU2 C15 | construct_or_coordinate_confound (moderate) | star3d_only:1 | 0/0/0 · 0/0/0 · 0/0/0 | rfam 0 / star3d 0 / tie 0 / NA 0 | rfam 0 / star3d 0 / tie 0 / NA 0 | 1/1 |
| RF00059 2GDI_X 3D2G_A r76-76 | 2GDI A85 (row 76; P1 3' end) | insufficient_evidence (low) | different_partner:1 | 0/0/0 · 0/0/0 · 2/0/1 | rfam 0 / star3d 1 / tie 0 / NA 0 | rfam 0 / star3d 1 / tie 0 / NA 0 | 1/1 |
| RF00174 4GXY_A 6VMY_A r26-82 | 4GXY 26-82 (P2-P6) | STAR3D_coverage_limitation (high) | rfam_only:54;neither:1;different_partner:2 | 0/0/0 · 0/0/0 · 1/1/1 | rfam 0 / star3d 0 / tie 0 / NA 2 | rfam 0 / star3d 0 / tie 0 / NA 2 | 55/57 |
| RF00174 4GXY_A 6VMY_A r85-88 | 4GXY 85-88 | STAR3D_coverage_limitation (high) | rfam_only:4 | 0/0/0 · 0/0/0 · 0/0/0 | rfam 0 / star3d 0 / tie 0 / NA 0 | rfam 0 / star3d 0 / tie 0 / NA 0 | 4/4 |
| RF00174 4GXY_A 6VMY_A r102-112 | 4GXY 102-112 (P7-P12 region) | insufficient_evidence (low) | star3d_only:11 | 0/0/0 · 0/0/0 · 0/0/0 | rfam 0 / star3d 0 / tie 0 / NA 0 | rfam 0 / star3d 0 / tie 0 / NA 0 | 11/11 |
| RF00174 4GXY_A 6VMY_A r117-129 | 4GXY 117-129 | insufficient_evidence (low) | star3d_only:13 | 0/0/0 · 0/0/0 · 0/0/0 | rfam 0 / star3d 0 / tie 0 / NA 0 | rfam 0 / star3d 0 / tie 0 / NA 0 | 13/13 |
| RF00162 2GIS_A 4KQY_A r1-93 | whole row | not_adjudicated_ineligible (n/a) | rfam_only:68;different_partner:21;star3d_only:4 | 5/5/4 · 1/0/0 · 20/16/15 | rfam 0 / star3d 0 / tie 0 / NA 21 | rfam 0 / star3d 0 / tie 0 / NA 21 | 93/93 |
| RF00442 5U3G_B 7MLW_F r41-55 | 5U3G 41-55 (P2) | not_adjudicated_ineligible (n/a) | different_partner:12;rfam_only:3 | 5/3/2 · 0/0/0 · 11/5/5 | rfam 3 / star3d 9 / tie 0 / NA 0 | rfam 3 / star3d 8 / tie 1 / NA 0 | 15/15 |
| RF00442 5U3G_B 7MLW_F r17-23 | 5U3G 17-23 (P1) | not_adjudicated_ineligible (n/a) | rfam_only:3;different_partner:4 | 1/1/0 · 0/0/0 · 1/0/0 | rfam 0 / star3d 4 / tie 0 / NA 0 | rfam 0 / star3d 4 / tie 0 / NA 0 | 7/7 |
| RF00059 2GDI_X 3D2G_A r17-23 | 2GDI 17-23 (P3) | not_adjudicated_ineligible (n/a) | rfam_only:3;neither:1;star3d_only:3 | 0/0/0 · 0/0/0 · 0/0/0 | rfam 0 / star3d 0 / tie 0 / NA 0 | rfam 0 / star3d 0 / tie 0 / NA 0 | 7/7 |
| RF00174 4GXY_A 6VMY_A r1-19 | 4GXY 1-19 | not_adjudicated_ineligible (n/a) | rfam_only:18;neither:1 | 0/0/0 · 0/0/0 · 0/0/0 | rfam 0 / star3d 0 / tie 0 / NA 0 | rfam 0 / star3d 0 / tie 0 / NA 0 | 19/19 |
| RF00174 4GXY_A 6VMY_A r145-172 | 4GXY 145-172 | not_adjudicated_ineligible (n/a) | rfam_only:28 | 0/0/0 · 0/0/0 · 0/0/0 | rfam 0 / star3d 0 / tie 0 / NA 0 | rfam 0 / star3d 0 / tie 0 / NA 0 | 28/28 |
| RF00005 5CCB_N 7EQJ_B r15-21 | 5CCB 15-21 (D-loop) | structural_variation_or_ligand_context (moderate) | rfam_only:6;different_partner:1 | 0/0/0 · 0/0/0 · 1/0/0 | rfam 0 / star3d 1 / tie 0 / NA 0 | rfam 0 / star3d 1 / tie 0 / NA 0 | 7/7 |
| RF00005 5CCB_N 7EQJ_B r54-60 | 5CCB 54-60 (T-loop, incl. A58 target) | structural_variation_or_ligand_context (moderate) | rfam_only:3;different_partner:4 | 0/0/0 · 0/0/0 · 1/0/0 | rfam 0 / star3d 4 / tie 0 / NA 0 | rfam 2 / star3d 2 / tie 0 / NA 0 | 2/7 |

## Evidence and confounds, region by region

**RF00522__6VUI_A__7REX_A__r7-23 — 6VUI 13-21 (P1 3' strand + J): supported_candidate_Rfam_correspondence_issue (moderate)**

- For the seed: none at 13-21; at 22 seed partner marginally closer (C1' 5.6 vs 6.2 A)
- For STAR3D: C1' after shared fit: STAR3D partners 0.6-3.2 A vs seed 6.1-8.6 A for 14-21 (same under flank-excluded and local-anchor fits); FR3D within span: canonical cWW 0/7 seed vs 5/7 STAR3D, noncanonical 0/7 vs 2/7, stacks 7/18 vs 10/18 (rfam-vs-STAR3D-forward eligible set); 7REX P1 cWW present in all 3 crystal copies (U1-A22 in 2); the 7REX authors describe P1 as a canonical A-form helix with an A28*G5-C18*A29 triple (G5-C18 = STAR3D register, seed implies G5-C17) (PMC8752633)
- Confounds and limits: STAR3D builds stacks from pairing (partly circular); same 7REX row as r15-22 (one observation); 7REX ligand PRF101 contacts residue 16 and PRF102 contacts 16-18; crystal/ASU contacts at 7REX 21-22 (chain B) and 6VUI 19-23 (symmetry); 6VUI U22-A23 unresolved (both partners ~5-6 A)

**RF00522__6VUI_A__7REX_A__r7-23 — 6VUI 7-12 (L1): possible_STAR3D_correspondence_issue (low-moderate)**

- For the seed: C1' after shared fit: G8 3.4 vs 10.0 A, G11 3.3 vs 8.7 A; seed preserves 3 L1 stacks STAR3D loses (s35 7-8, ns33 8-10, s35 9-10); the seed maps the 6VUI C7-G11 tWH pair onto 7REX C8-A12 (FR3D tWW, different class), the residues the 7REX authors describe as the U32*A12*C8 pocket-ceiling triple (Schroeder et al. 2022, PMC8752633); STAR3D maps it to 7REX 7-13
- For STAR3D: C7 3.3 vs 5.3 A, U12 1.3 vs 4.7 A; STAR3D preserves s35 6-7
- Confounds and limits: 7REX L1 residues contact a SECOND preQ1 (PRF101) and Mg (MG103) absent from 6VUI's single site -> genuine structural/ligand-context variation is plausible; crystal contacts at 7REX 8-12; residue-level mixed evidence

**RF00522__3FU2_A__7REX_A__r15-22 — 3FU2 15-22 (P1 3' strand): supported_candidate_Rfam_correspondence_issue (moderate)**

- For the seed: none
- For STAR3D: STAR3D partner closer for 7/7 different-partner residues under shared, flank-excluded and local-anchor fits (C1' and base centroid); canonical 0/5 seed vs 5/5 STAR3D, noncanonical 0/5 vs 3/5, stacks 4/9 vs 9/9; same published G5-C18 description of 7REX P1
- Confounds and limits: not independent of r7-23 (same 7REX row); STAR3D pairing circularity; ligand contacts at 7REX 16-18

**RF00522__3FU2_A__7REX_A__r9-12 — 3FU2 9-12 (L1): construct_or_coordinate_confound (low)**

- For the seed: G11 seed partner 3.8 vs 10.3 A (shared fit); seed preserves 1 of 4 eligible stacks vs 0
- For STAR3D: U9 5.9 vs 7.1 A, A10 2.7 vs 5.7 A
- Confounds and limits: 3FU2 C12 has only P/O5' (no C1'), U13-A14 unobserved; STAR3D's parser treats 3FU2 12 and 15 as sequence neighbours (STAR3D audit); 7REX L1 contacts second preQ1; canonical eligible 0/2 for both

**RF00522__3FU2_A__7REX_A__r32-34 — 3' terminal 32-34: insufficient_evidence (low)**

- For the seed: A34 seed partner 5.1 vs 7.9 A
- For STAR3D: A33 STAR3D partner 1.9 vs 4.3 A; U32 STAR3D-only (1.3 A)
- Confounds and limits: 3' end of crystallised constructs; Ca2+ and crystal-symmetry contacts at 3FU2 33-34; 1 canonical eligible preserved by neither

**RF00522__3FU2_A__6VUI_A__r32-34 — 3' terminal 32-34: insufficient_evidence (low)**

- For the seed: none decisive (A34 seed partner 11.4 A)
- For STAR3D: A33: C1' favours STAR3D (4.5 vs 5.7 A) but base centroid favours the seed (4.0 vs 4.9 A); U32 STAR3D-only
- Confounds and limits: terminal; STAR3D forward and reverse disagree here (1 of 3 positions identical) -> direction-unstable STAR3D output; Mn2+/Ca2+ and symmetry contacts

**RF00522__3FU2_A__6VUI_A__r23-24 — 3FU2 23-24 (J/L3): insufficient_evidence (low)**

- For the seed: U24 seed partner 4.9 vs 6.2 A (C1'); A23 base centroid favours seed
- For STAR3D: A23 C1' 4.0 vs 4.9 A
- Confounds and limits: 3FU2 A23 contacts another chain in the asymmetric unit and symmetry mates; mixed C1' vs base-centroid evidence; 2 eligible stacks preserved by neither

**RF00522__3FU2_A__6VUI_A__r7-8 — 3FU2 7-8 (L1 start): insufficient_evidence (low)**

- For the seed: none
- For STAR3D: C8 STAR3D partner 6.9 vs 8.7 A (both far); U7 STAR3D-only 3.0 A
- Confounds and limits: both partners poorly superposed; 3FU2 C8 forms a non-canonical C-A WWc pair with A34 in STAR3D's raw structure (removed before stacks)

**RF00522__3FU2_A__6VUI_A__r15-15 — 3FU2 C15: construct_or_coordinate_confound (moderate)**

- For the seed: seed leaves C15 unaligned (gap)
- For STAR3D: STAR3D maps C15 to 6VUI 13 (5.1 A)
- Confounds and limits: 3FU2 13-14 unobserved; STAR3D treats 12 and 15 as neighbours, so its local loop scoring here spans a coordinate gap

**RF00059__2GDI_X__3D2G_A__r76-76 — 2GDI A85 (row 76; P1 3' end): insufficient_evidence (low)**

- For the seed: none
- For STAR3D: STAR3D partner 0.6 A vs seed 7.5 A (C1', 53-anchor fit; same with local anchors)
- Confounds and limits: exploratory pair; adjacent to the redesigned/masked 3D2G P1 end; single residue

**RF00174__4GXY_A__6VMY_A__r26-82 — 4GXY 26-82 (P2-P6): STAR3D_coverage_limitation (high)**

- For the seed: seed aligns 54 residues STAR3D leaves unaligned
- For STAR3D: 2 different-partner residues without usable geometry
- Confounds and limits: STAR3D (default stack cutoff/min size) aligned only one 26-nt module of this 160-nt pair; local anchor fit refused (too few shared anchors); not a correspondence disagreement

**RF00174__4GXY_A__6VMY_A__r85-88 — 4GXY 85-88: STAR3D_coverage_limitation (high)**

- For the seed: seed-only (4)
- For STAR3D: none
- Confounds and limits: coverage only

**RF00174__4GXY_A__6VMY_A__r102-112 — 4GXY 102-112 (P7-P12 region): insufficient_evidence (low)**

- For the seed: seed leaves these 11 4GXY residues opposite gaps in the 6VMY row (no seed partner)
- For STAR3D: STAR3D aligns all 11 (star3d_only)
- Confounds and limits: no anchor geometry (local fit refused); 13 of STAR3D's 26 forward pairs for this pair change under the paper-rule sensitivity S1; insertion-region correspondences are weakly constrained in both methods

**RF00174__4GXY_A__6VMY_A__r117-129 — 4GXY 117-129: insufficient_evidence (low)**

- For the seed: seed gap
- For STAR3D: STAR3D aligns 13 (star3d_only)
- Confounds and limits: as r102-112

**RF00162__2GIS_A__4KQY_A__r1-93 — whole row: not_adjudicated_ineligible (n/a)**

- For the seed: n/a
- For STAR3D: n/a
- Confounds and limits: both constructs engineered inside the interval; STAR3D aligned only the engineered P3 module; pair exploratory_engineered_technical (justification partly outcome-informed); S1 sensitivity changes 9 of 25 STAR3D pairs

**RF00442__5U3G_B__7MLW_F__r41-55 — 5U3G 41-55 (P2): not_adjudicated_ineligible (n/a)**

- For the seed: seed-only 3
- For STAR3D: STAR3D C1' closer for 9 of 12 different-partner residues
- Confounds and limits: source span overlaps masked 5U3G engineering; STAR3D's 78-nt alignment of this pair collapses to 25 nt under S1 (it depends on non-canonical WWc pairs in STAR3D's stack input); overwrite defect isolated by S2: no effect

**RF00442__5U3G_B__7MLW_F__r17-23 — 5U3G 17-23 (P1): not_adjudicated_ineligible (n/a)**

- For the seed: seed preserves 1 canonical eligible pair STAR3D loses
- For STAR3D: STAR3D C1' closer 4/4
- Confounds and limits: source engineering overlap; S1-sensitive as above

**RF00059__2GDI_X__3D2G_A__r17-23 — 2GDI 17-23 (P3): not_adjudicated_ineligible (n/a)**

- For the seed: n/a
- For STAR3D: n/a
- Confounds and limits: both target partner sets overlap masked 3D2G engineering; coverage differences only

**RF00174__4GXY_A__6VMY_A__r1-19 — 4GXY 1-19: not_adjudicated_ineligible (n/a)**

- For the seed: n/a
- For STAR3D: n/a
- Confounds and limits: masked terminal residues; coverage only

**RF00174__4GXY_A__6VMY_A__r145-172 — 4GXY 145-172: not_adjudicated_ineligible (n/a)**

- For the seed: n/a
- For STAR3D: n/a
- Confounds and limits: masked terminal residues; coverage only

**RF00005__5CCB_N__7EQJ_B__r15-21 — 5CCB 15-21 (D-loop): structural_variation_or_ligand_context (moderate)**

- For the seed: seed aligns 6 residues STAR3D leaves unaligned; 1 eligible stack preserved by the seed only
- For STAR3D: the 1 different-partner residue is closer under STAR3D in all anchor fits
- Confounds and limits: 5CCB tRNA3Lys is bound to the m1A58 methyltransferase TRMT6/61A, whose paper reports refolding of the substrate tRNA; the D-loop/T-loop elbow is the refolded region; the confound was declared before alignment

**RF00005__5CCB_N__7EQJ_B__r54-60 — 5CCB 54-60 (T-loop, incl. A58 target): structural_variation_or_ligand_context (moderate)**

- For the seed: local-anchor fit favours the seed for 2 residues; 1 eligible stack preserved by the seed only
- For STAR3D: global C1' fits favour STAR3D for 4 of 4 different-partner residues
- Confounds and limits: STAR3D forward and reverse agree at only 2 of 7 positions here (direction-unstable); enzyme-bound refolded T-loop; anchor-dependent geometry -> no correspondence conclusion
