# Summary for the professor (current: v5, 2026-10-09)

*Prepared by an AI research agent; no human has reviewed these results. Previous versions are archived in
`deliverables/2026-10-09_v5/before_natural/reports/` and `deliverables/2026-10-09_v4/baseline/reports_before_v4/`. Full details:
`deliverables/2026-10-09_v5/professor_report_v5.md`.*

**What we compare.** Nucleotide correspondences in the ordinary Rfam seed (release 15.1) versus original STAR3D on
pairs of experimentally solved RNAs from the same family.

**Method.** For each selected RNA pair, we use one forward alignment from original STAR3D v1.2 with default parameters, following the package's preprocessing procedure.

**Dataset policy.** The active analysis includes only experimental structures of verified natural RNA sequences. Confirmed engineered constructs and unresolved cases are excluded from the accepted cohort.

**Dataset now.** Re-reviewing all 13 previously analysed chains left 3 verified-natural RNAs in one family, the preQ1-I
riboswitch: *B. subtilis* (3FU2), *T. tengcongensis* (6VUI) and *C. antarcticum* (7REX). They form 3 pairs.
- Every other pair used at least one engineered construct and is excluded. The engineering ranged from added terminal
  nucleotides and cloning artefacts to loop replacements, internal deletions and an artificial 5′ G on a tRNA.

**Main finding: a candidate, not a demonstrated error.** In the seed row for 7REX, the 3′ strand of helix P1 is shifted
by one position.

| 6VUI P1 pair (cWW) | Seed partner pair in 7REX | STAR3D partner pair in 7REX |
|---|---|---|
| C1–G20 | U1–C21 (no FR3D annotation detected) | U1–A22 (cWW) |
| U2–A19 | G2–A20 (no FR3D annotation detected) | G2–C21 (cWW) |
| G3–C18 | U3–C19 (no FR3D annotation detected) | U3–A20 (cWW) |
| G4–C17 | G4–C18 (no FR3D annotation detected) | G4–C19 (cWW) |
| G5–C16 | G5–C17 (no FR3D annotation detected) | G5–C18 (cWW) |

**Supporting evidence:**
- **Geometry.** STAR3D's partners are closer after superposition on agreed residues.
- **The authors' own description.** The 7REX paper describes a G5–C18 pair, which is the STAR3D register.
- **Specific to this row.** Of 43 preQ1-I seed rows, only this one becomes fully complementary when shifted.

**Counter-evidence and limits:**
- **One observation.** Both comparisons share the 7REX row.
- **Not independent.** STAR3D's scoring uses base pairing.
- **L1 favours the seed.** The seed is better supported in loop L1.
- **Ligand context.** A second preQ1 ligand contacts L1 and one residue of the strand.
- **Row history.** The row first appears in Rfam 15.0; how it was aligned is undocumented.

**Your seed question.** For these families the ordinary seed records are byte-identical to the 3D-curated seed records.

**Decision needed.** With natural constructs only, the explicitly linked inventory yields one family. Options:
- review sequence-only links in non-curated families for natural constructs;
- or ask Smriti about predicted structures, as a separate study.
