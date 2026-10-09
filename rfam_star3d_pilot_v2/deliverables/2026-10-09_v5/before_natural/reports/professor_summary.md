# Summary for the professor (current: v4, 2026-10-09)

*Prepared by an AI research agent; no human has reviewed these results yet. The previous version is archived in
`deliverables/2026-10-09_v4/baseline/reports_before_v4/professor_summary.md`. Full details are in
`deliverables/2026-10-09_v4/professor_report_v4.md`.*

**What was compared.** Nucleotide correspondences in the ordinary Rfam seed (release 15.1) versus original STAR3D v1.2
on pairs of experimentally solved RNAs from the same family and different organisms. Base pairs and stacking were
annotated with FR3D.
- **Development set.** 7 pairs in 5 families; 4 primary pairs in 2 families.
- **Prospective pair.** 1 exploratory pair from a new family.

**Main finding: a candidate, not a demonstrated error.** In preQ1-I (RF00522), the seed places the 3′ strand of helix P1
of the *Carnobacterium antarcticum* row (PDB 7REX) one nucleotide out of register.

| 6VUI P1 pair (cWW) | Seed partner pair in 7REX | STAR3D partner pair in 7REX |
|---|---|---|
| C1–G20 | U1–C21 (no FR3D annotation detected) | U1–A22 (cWW) |
| U2–A19 | G2–A20 (no FR3D annotation detected) | G2–C21 (cWW) |
| G3–C18 | U3–C19 (no FR3D annotation detected) | U3–A20 (cWW) |
| G4–C17 | G4–C18 (no FR3D annotation detected) | G4–C19 (cWW) |
| G5–C16 | G5–C17 (no FR3D annotation detected) | G5–C18 (cWW) |

**Supporting evidence:**
- **Geometry.** After superposition on agreed residues, the STAR3D partners are closer for every differing residue,
  under three anchor sets and two distance measures.
- **The 7REX authors' own description.** They call P1 a canonical A-form helix containing G5–C18, which is the STAR3D
  register.
- **Not an artefact of STAR3D's code.** The mapping is unchanged when STAR3D is restricted to the paper's pairing rule.
- **Specific to this row.** Of 43 preQ1-I seed rows, only this one becomes fully complementary when shifted.

**Counter-evidence and limits:**
- **One observation.** Both comparisons share the 7REX row.
- **Not independent.** STAR3D's own scoring uses base pairing.
- **L1 favours the seed.** In loop L1 the seed is better supported, including the "pocket ceiling" residues the 7REX
  authors describe.
- **Ligand context.** A second preQ1 ligand contacts L1 and one residue of the candidate strand.
- **Row history.** The row first appears in Rfam 15.0; how it was aligned is undocumented.

**Your seed question.**
- In every Rfam release that ships a structure-curated seed file, each of its family records is byte-identical to the
  ordinary seed record.
- All our families are curated families, so our baseline is the 3D-curated alignment.
- Our structure-link discovery rule can only find curated families.

**More data.**
- All 31 screen-passing families have been reviewed, giving 2 primary families.
- A pre-registered attempt to add a non-curated family (tRNA) found no primary-eligible pair. Native tRNAs carry
  modified nucleotides that original STAR3D cannot read. Two sequence-only links pointed to another species' sequence
  row.
- One exploratory tRNA pair agreed with the seed except in a region refolded by a bound enzyme.

**Decision needed.** Under the current rules the experimental inventory is exhausted. Options, each a declared scope
change:
- (a) modified tRNAs with a parent-mapped STAR3D input (a method change);
- (b) engineered constructs as a separate tier;
- (c) predicted structures with Smriti, as a separate study.

A native x86-64 machine for STAR3D is also needed.
