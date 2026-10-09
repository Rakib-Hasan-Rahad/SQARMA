# Weekly progress update — Rfam seed vs original STAR3D (2026-10-09)

*Prepared by an AI agent for Rakib Hasan Rahad; not yet reviewed by a human.*

**Done this week (verified this session unless marked)**
1. **Software repairs (5), 51/51 tests pass.**
   - Valid per-family Stockholm export.
   - A changed input now stops every dependent step in fresh reproduction.
   - FR3D provenance is read from the installed package, and cached outputs are reused only if their hashes match.
   - Stored STAR3D outputs are re-validated when read.
   - STAR3D intermediate files are checked, not just exit codes.

   No correspondence, interaction, region or candidate table changed (`repair_impact_report.md`).
2. **STAR3D audit against the paper and source** (`STAR3D_execution_audit.md`).
   - Package, JAR and default parameters match.
   - Three tool behaviours were documented:
     - non-canonical cis Watson–Crick/Watson–Crick pairs enter STAR3D's structure;
     - a pair-overwrite defect changes 7MLW;
     - coordinate gaps are treated as neighbours.
3. **Fresh reproduction of all 7 pilot pairs is now complete.** The 4 remaining pairs were rerun today. All re-downloads
   and rebuilt inputs were byte-identical, and every completed run matched. 2 runs crashed in the Java runtime under x86
   emulation.
4. **Screening of all 21 remaining families.** None yields a new primary pair: engineering, a single natural source,
   or low coverage. The selection was frozen empty before any STAR3D run, so no new comparison was made.
5. **Survey B: ordinary vs curated seed.** In Rfam 15.1 the curated file is byte-identical to the ordinary seed for all
   74 shared families, including all pilot families.
6. **7REX candidate strengthened and qualified** (`candidate_evidence_update.md`).
   - Reciprocal-direction counts were added.
   - The register shift is specific to the 7REX row among 43 preQ1-I seed rows (sequence check).
   - The second ligand contacts L1 and one residue of the candidate strand.

**Current conclusion.** One supported candidate remains: the P1 3′ strand of the 7REX row. It is a candidate for
curator review. The seed is better supported in loop L1.

**Open issues**
- Only emulated STAR3D is available. A native x86-64 host is needed.
- The ZMP-ZTP construct papers are inaccessible.
- 14 of 19 regions are uninspected.
- The pre-curation Rfam release comparison has not been done.

**Decision needed from the researcher and professor.** Whether to broaden scope beyond the explicit-link, natural-
construct criteria, for example masked engineered constructs as a separate tier, sequence-only links, or predicted
structures. Under the current criteria the experimental inventory is exhausted.
