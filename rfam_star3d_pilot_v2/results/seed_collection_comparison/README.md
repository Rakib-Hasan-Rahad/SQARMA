# Survey B: ordinary vs structure-curated Rfam seed (release 15.1) — one-page explanation

*Generated 2026-10-09 by an AI agent (Claude), using `scripts/survey_b.py`. This is an auxiliary survey: it does not
modify the primary ordinary-seed baseline.*

**Question (professor-requested).** For families that appear in both collections, do the residue correspondences in
the ordinary seed differ from those in the structure-curated seed?

**Inputs.** Both files come from the same release directory, `https://ftp.ebi.ac.uk/pub/databases/Rfam/15.1/`, so the
releases are matched.
- `Rfam.seed.gz`: the pinned primary reference, sha256 41f014f4….
- `Rfam.3d.seed.gz`: retrieved 2026-10-09T05:38:55Z, sha256 4055ce87…, Last-Modified 2026-01-04. The release README
  describes it as "annotated seed alignments with 3D structure".

**Method.**
- Families and rows were matched by exact accession and exact row name (`acc/start-end`), with the ungapped sequence
  checked as well.
- For every pair of shared rows, the residue correspondences were derived from each collection and compared, rather
  than comparing raw column numbers.
- GF, GR and GC annotations were compared.
- Each Stockholm record was then compared byte for byte.

**Results** (`provenance.json`, `family_overlap.tsv`, `record_byte_identity.txt`)

| Count | Value |
|---|---|
| Families in the ordinary seed | 4,227 |
| Families in the curated seed | 74 |
| In both | 74 |
| With ≥1 shared row | 74 |
| With ≥2 shared identical-sequence rows | 74 |
| Shared rows | 7,808 (all with identical aligned strings) |
| Comparable row pairs | 1,304,970 |
| Row pairs with any changed correspondence | **0** |
| Annotation differences | **0** |
| Curated records byte-identical to the ordinary record | **74 / 74** |

**Interpretation.**
- In release 15.1, `Rfam.3d.seed.gz` is a byte-identical subset of `Rfam.seed.gz`. It contains the 74 families whose
  seeds Rfam has integrated with 3D structures.
- **All five pilot families (RF00059, RF00162, RF00174, RF00442, RF00522) are among the 74.** So for these families the
  "ordinary" seed used as the primary baseline *is* the structure-curated alignment. This is not a "sequence-only
  versus 3D" comparison.
- For 15.1, there is nothing to compare between the collections. The files do not show which rows or columns were
  changed by 3D curation, or when. This survey does **not** establish the history of the 7REX row.

**What would answer the provenance question.** Compare these 74 families against an earlier release that predates
their 3D update, for example the release before each family's update. Each family would need its own release and
version labels. That comparison was not done this session.

**Consequence for the main pilot (checked).** The 74 families that carry explicit `#=GR <PDB>_<chain>_SS` links in the
ordinary seed are exactly these 74 curated families (set comparison against `results/family_inventory.tsv`: 0
differences). The pilot's explicit-link discovery rule can therefore only find 3D-curated families.
