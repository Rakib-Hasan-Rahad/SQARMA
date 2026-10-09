# v4 expansion pre-registration (written 2026-10-09 before any structure in this list was aligned)

**Scientific need.** All primary comparisons so far come from families whose ordinary 15.1 seed is the 3D-curated
alignment (Survey B). This expansion asks whether a family whose seed was *not* 3D-curated can supply an eligible
natural pair, and if so whether seed and STAR3D correspondences agree there. It does not aim to increase counts.

**Source.** Sequence-only chain-to-row proposals (`metadata/chain_row_candidates.tsv`,
`sequence_match_only_pending_provenance`). These rows have no explicit `#=GR` structure link. An exact match of a natural
genomic seed row inside a PDB chain only *proposes* a link; provenance must be verified.

**Family choice (deterministic).** Families outside the 74 curated families, model length ≤300, not rRNA, ranked by
the number of distinct matched seed rows. Rank 1 is RF00005 (tRNA, 43 rows). Only this family is attempted in this
session; the remaining 16 are listed as not reviewed.

**Eligibility per structure.** All of the following must hold:
1. **Natural row in the chain.** The seed row is a natural genomic interval, and its ungapped sequence occurs exactly
   once in the chain's SEQRES.
2. **Source organism.** The RNA entity's source organism matches the organism of the row's accession. This is
   verified from the mmCIF and NCBI records, not inferred from the accession string.
3. **Coordinates.** X-ray diffraction at ≤3.0 Å, with at least 90% of the family interval observed.
4. **Modifications.** Modified nucleotides inside the interval are allowed only if parent-mapped. They are recorded,
   and STAR3D's handling of them is checked.
5. **Context.** Free tRNA is preferred over protein- or ribosome-bound tRNA. If no free tRNA qualifies, a complex is
   accepted and recorded as a context confound.
6. **Distinct sources.** The two RNAs must have distinct sequences and come from different species.

**Representative rule.**
- Group structures by exact interval sequence.
- Within a group, choose: free tRNA > complex; then resolution; then PDB ID.
- Pair the two best groups from different species, ranked by group representative resolution.

**Analysis.** Use the unchanged pipeline:
- the reference phase;
- crosswalk and STAR3D inputs;
- original STAR3D in both directions × 3 replicates;
- comparison;
- FR3D interactions;
- regions.

**Reporting and stopping.**
- Results are reported as *prospective, non-curated-family* evidence, separately from the development set.
- Stop if no pair qualifies, or if any gate fails, and report that outcome.
