# Dataset, provenance and expansion (v4, 2026-10-09)

*AI agent (Claude); no human review.*

## 1. Ordinary vs structure-curated seed: exactly what was compared [V]

| Object compared (release 15.1) | Result |
|---|---|
| Compressed archives (`Rfam.seed.gz` sha256 41f014f4… vs `Rfam.3d.seed.gz` 4055ce87…) | different (expected: different content) |
| Decompressed files | different: the curated file holds 74 family records, the ordinary file 4,227 |
| Extracted family records (bytes from the record header to `//`) | **74/74 byte-identical** |
| Sequence rows (names, aligned strings) | 7,808/7,808 identical |
| Residue correspondence of shared rows | 0 changed among 1,304,970 comparable row pairs |
| Consensus and per-row annotations (GF, GR, GC) | 0 differences |

Sources: `results/seed_collection_comparison/` and `results/rfam_history/curated_vs_ordinary.tsv`.

**Earlier releases** (server Last-Modified dates; these are not formal release dates):
- 14.9: 40 curated records, all byte-identical to the ordinary records.
- 14.10: 136 records, all identical.
- 15.0: 143 records, all identical.
- 15.1: 74 records, all identical.

Releases 14.0–14.8 ship no curated file. **In every release that ships a curated file, its records are byte-identical to
the ordinary records.**

**Consequences:**
- **Not a sequence-only baseline.** The pilot's "ordinary" baseline is the 3D-curated alignment for all five pilot
  families. It is not a structure-independent sequence alignment.
- **Selection bias.** In 15.1 the families with explicit `#=GR <PDB>_<chain>_SS` links in the ordinary seed are exactly
  the 74 curated families (0 differences). The pilot's discovery rule could therefore only sample curated families.
  This holds in 15.1 only: in 15.0, RF00522 already carried `#=GR` links but was not in that release's curated file.
- **Not curation history.** Survey B cannot show which correspondences curation changed. That needs a comparison
  against a release before each family's curation. For RF00522, the three pilot rows do not exist before 15.0, so no
  earlier version of the 7REX row exists to compare.

## 2. Release history of the 7REX row [V]

Source: `results/rfam_history/rf00522_rows.tsv`.

| Releases | RF00522 rows | 3FU2 / 6VUI / 7REX rows present | 7REX aligned string | 6VUI C16 → 7REX (seed) |
|---|---|---|---|---|
| 14.0–14.8 | 35 | no | — | — |
| 14.9–14.10 | 36 | no | — | — |
| 15.0 | 43 | yes | `-----UGUGGUUCGCAA--CC---AUCCCACA---…` | 17 |
| 15.1 | 43 | yes | identical to 15.0 | 17 |

The row carries `#=GR` features `7REX_A_SS` and `8FB3_A_SS`. **We document only these facts.** How the row was aligned
is not recorded in these files and is not inferred here.

## 3. Prospective expansion into a non-curated family

The rule was pre-registered in `review/v4_expansion/PREREGISTRATION.md` and fixed before screening.

**Scientific need.** Test whether a family whose seed is *not* 3D-curated can supply an eligible natural pair. This
addresses the selection bias in section 1.

**Route.**
- Use sequence-only chain-to-row proposals, i.e. the exact occurrence of a natural seed row inside a PDB chain.
- 17 non-curated families within the length cap and outside rRNA have ≥2 distinct matched rows.
- The deterministic rank-1 family is **RF00005 (tRNA)**, with 43 rows and 502 matched chains. The other 16 families
  were not reviewed in this session.

**Screen** (`review/v4_expansion/candidate_structures.tsv` and `raw/`). Of the 502 chains, 76 are X-ray structures at
≤3.0 Å, and 17 of those are protein-free.

| Structure | Organism (entity / row) | Decision | Reason |
|---|---|---|---|
| 1EHZ_A yeast tRNA-Phe 1.93 Å | S. cerevisiae / S. cerevisiae | excluded | native, with modified nucleotides in the interval; original STAR3D reads them as "N" (not parent-mapped); the rule-4 check was done before any alignment |
| 1VTQ_A yeast tRNA-Asp 3.0 Å | "synthetic construct" / S. cerevisiae | excluded | modified nucleotides (PSU, H2U, …), as above |
| 7EQJ_B E. coli tRNA-Val 2.04 Å | E. coli / E. coli K-12 | **eligible** | free tRNA, exact row at coordinates, no modifications, 100% observed |
| 9J4N_A E. coli tRNA-Leu 2.9 Å | E. coli K-12 / E. coli | eligible, but same species as 7EQJ | not a different-species partner |
| 9J4O_A B. subtilis tRNA-Leu 2.5 Å | B. subtilis / **Halalkalibacterium halodurans** | excluded | the sequence-only link points to a seed row from another species; an identical sequence does not make it this RNA's row |
| 6PMO_B G. kaustophilus tRNA-Gly 2.66 Å | G. kaustophilus / H. halodurans | excluded | organism mismatch; also bound to a T-box RNA |
| 5CCB_N human tRNA3Lys 2.0 Å | H. sapiens / H. sapiens | **eligible as exploratory** | no modifications, 100% observed; bound to the TRMT6/61A methyltransferase; the paper title reports refolding of the substrate tRNA (context confound declared before alignment) |
| 4YCP_B E. coli tRNA-Trp 2.55 Å | E. coli K-12 / E. coli O157:H7 | not used | same species as 7EQJ; 85% observed |
| 2FK6_R tRNA-Thr 2.9 Å | not recorded / B. subtilis | excluded | source organism not recorded in the entry; 73% observed |

**Outcome:**
- **No primary-eligible different-species pair** exists under the declared rules.
- One exploratory pair was frozen at 06:16:35 UTC, before any STAR3D run: **RF00005__5CCB_N__7EQJ_B**
  (`expansion_v4/cohort_v4_prospective_freeze.json`).
- It was run with the unchanged pipeline in the isolated workspace `expansion_v4/`. A first run executed two stages in
  the wrong order; that is recorded in `logs/expansion_v4_run_attempt1_wrong_stage_order.log`. STAR3D does not depend
  on those stages, and the downstream stages were re-run in the documented order.

**Result [V/X]** (`expansion_v4/results/`). This is one exploratory observation, not a primary result.
- **Mapped positions.** 73 seed pairs, all structurally assessable. STAR3D aligned 64 positions, identical across 3
  replicates in each direction.
- **Agreement.** 59 positions have the same partner as the seed, 5 a different partner, and 9 are aligned by the seed
  only. All 5 differences fall in the D-loop (15–21) and T-loop (54–60), the elbow the bound enzyme refolds.
- **Direction instability.** STAR3D forward and reverse agree at only 2 of 7 positions in the T-loop.
- **Interactions** (FR3D, eligible sets):

  | Class | Seed | STAR3D forward |
  |---|---|---|
  | All | 81/97 | 81/97 |
  | Canonical | 20/21 | 20/21 |
  | Non-canonical | 3/4 | 3/4 |
  | Stacking | 57/71 | 57/71 |

- **Interpretation.** In a family whose seed was not structure-curated, seed and STAR3D correspondences agree outside a
  region with a documented conformational confound. It does not test seed quality for tRNA in general.

## 4. Evidence cards: prospective RNAs [V]

**5CCB_N**
- **Molecule.** Human tRNA3Lys, entity source *Homo sapiens* (pdbx_entity_src_syn), 77-mer.
- **Seed row.** `AP000442.6/2022-1950` (reverse strand; chromosome 11 clone), exact at deposited offset 1.
- **Coordinates.** No modified residues; observed fraction 1.0.
- **Context.** Bound to TRMT6/TRMT61A with SAH.
- **Citation.** "Crystal Structure of the Human tRNA m(1)A58 Methyltransferase–tRNA3(Lys) Complex: Refolding of
  Substrate tRNA…". Its construct preparation was not reviewed beyond the entry and its title.

**7EQJ_B**
- **Molecule.** *E. coli* tRNA-Val, entity source *E. coli* (src_nat), 76-mer.
- **Seed row.** `X17321.1/66-138` (valU operon, E. coli K-12), exact at row coordinates.
- **Coordinates.** No modified residues in the deposited sequence; observed fraction 1.0.
- **Context.** Free tRNA with Mg²⁺ and Na⁺.
- **Citation.** Its title: "Unique anticodon loop conformation with the flipped-out wobble nucleotide…". That is a
  local anticodon feature; no region was flagged there.

**Not done for these two RNAs:** exact-source genome checks. Each seed row *is* a natural genomic interval found exactly
in the chain, which supports sequence provenance but says nothing about construct preparation.

## 5. Survey A inventory (unchanged counts, all retained)
- **Funnel.** 167 families with any PDB candidate → 74 with explicit links → 31 passing the screen → 31 reviewed by hand.
  2 primary families, 3 exploratory pilot families, 4 newly exploratory-only (v3), 0 new primary.
- **Sequence-only links.** These add 17 non-curated candidate families. One (tRNA) was reviewed, with 0 primary pairs;
  16 are unreviewed.
