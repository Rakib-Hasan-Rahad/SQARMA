# Summary for the professor (pilot v2.1)

*Prepared by an AI research agent; no human has reviewed these results yet.*

**What was compared.** We compared nucleotide correspondences in the standard Rfam seed alignment (release 15.1) with
those produced by original STAR3D v1.2 from experimental structures. The comparison covered seven pairs of RNAs from
the same family; four of those pairs are eligible for primary scientific interpretation. Base pairs and stacking
interactions were annotated with FR3D.

Standard seeds may already incorporate structural information. The separately requested ordinary-versus-curated seed
comparison is deferred.

**What discrepancy was found.** The clearest discrepancy is in the preQ1-I riboswitch family (RF00522), in the row for
*Carnobacterium antarcticum* (PDB 7REX). There, the seed places the 3′ strand of the P1 helix one nucleotide out of
register relative to the *Thermoanaerobacter tengcongensis* (6VUI) and *Bacillus subtilis* (3FU2) rows.

| 6VUI P1 pair (cWW in 6VUI) | Seed partner pair in 7REX | STAR3D partner pair in 7REX |
|---|---|---|
| C1–G20 | U1–C21 (no FR3D annotation) | U1–A22 (cWW) |
| U2–A19 | G2–A20 (none) | G2–C21 (cWW) |
| G3–C18 | U3–C19 (none) | U3–A20 (cWW) |
| G4–C17 | G4–C18 (none) | G4–C19 (cWW) |
| G5–C16 | G5–C17 (none) | G5–C18 (cWW) |

**Supporting evidence.** All of these points were checked directly from raw files.
- **The seed's own consensus.** Applied to the 7REX row, the seed's consensus secondary structure implies three
  non-Watson–Crick P1 pairs. A one-column shift of 7REX residues 15–22 makes all five Watson–Crick.
- **The crystal structure.** The register implied by STAR3D is the one present in the 7REX crystal. Four of the five
  pairs appear in all three RNA copies in the asymmetric unit; U1–A22 appears in two copies, as chain C has no
  annotation for it.
- **Superposition geometry.** After superposing on residues where both methods agree, the STAR3D partners are 0.2–3.2 Å
  away and the seed partners 4–9 Å. The result is unchanged when the anchors exclude the flanking residues.
- **Interaction preservation.** On the same eligible interaction set, the adjusted row preserves 31/46 interactions,
  including 5/7 canonical. The seed preserves 19/46 (0/7 canonical) and STAR3D 29/46. The adjustment loses no
  interaction that the seed preserved.
- **Sequence provenance.** All three RNAs match their source genomes exactly, with no engineering and no modified
  nucleotides.
- **Reproduction.** A fresh rerun of STAR3D and FR3D from re-downloaded files reproduced every mapping and annotation
  exactly. This rerun was done by the same agent; it is not independent validation.

**Alternative explanations that remain.**
1. Canonical-pair agreement partly overlaps STAR3D's own input: STAR3D uses canonical pairs during preprocessing.
2. The 3′ P1 region differs in local sequence between species. This is a candidate for a curator to assess, not a
   proven error.
3. Elsewhere STAR3D is less convincing. In loop L1 (6VUI residues 8 and 11) the seed's partners fit better. 7REX binds
   two preQ1 molecules, the second contacting L1, which plausibly changes that loop's local geometry.
4. Only two comparisons support the finding, and both involve the same 7REX row, so this is one observation.

**Next experiment.**
1. Have the Rfam row's alignment history checked; it was probably added by the cmalign-based 3D curation pipeline.
2. Test whether other preQ1-I sequences with different P1 lengths show the same register issue.
3. Repeat the analysis with a second structural aligner or a curated structural reference, to separate STAR3D-specific
   effects.

**Relation to the broader project.** The strongest signal concerns *canonical* P1 pairing. The noncanonical evidence
is supportive but limited: the adjusted mapping preserves 4/8 noncanonical interactions (6VUI→7REX) and 6/8
(3FU2→7REX), against 2/8 and 3/8 for the seed. This shows that alignment-register errors can mislabel which
nucleotides form noncanonical contacts, which matters for any future training labels. It is **not** a
noncanonical-pair prediction method: the pilot validates correspondences between known structures only.
