# v3 biological screening notes (Agent B, 2026-10-09, about 05:15–05:45 UTC)

**Outcome: 0 accepted primary pairs.** `frozen_selection_v3.json` has an empty list and was frozen before any STAR3D run. STAR3D was not run.

## What was checked
- **Scope.** All 21 families with screen_status=pass and "not reviewed", in the declared rank order. Ranks 1–3 were THF, CPEB3 and PrrB_RsmZ (as expected), followed by the taxa=1 list.
- **mmCIF facts (48 chains).** For each chain: method, resolution, entity, `pdbx_entity_src_syn` / `entity_src_gen`, `struct_ref`, `struct_ref_seq_dif`, ligands, observed fraction, missing and modified residues, and author numbering. Source: `scripts/v3_facts.py`, output in `facts_raw*.jsonl` and `structure_facts.tsv`.
  - The chain's `#=GR` link comes from `metadata/seed_gr_structure_links.tsv`.
  - The ungapped row matched the deposited canonical sequence exactly at row coordinates for every chain checked.
  - Every examined interval has monotonic author numbering and no insertion codes. A crosswalk is feasible wherever coverage passes.
- **Exact-source genome checks.** `scripts/v3_exact_source.py` searches both strands. Results are in `exact_source_v3.tsv`.
  - For multi-contig files (AAWL01, AAYI02), contigs are joined with `N` and positions are in that concatenated coordinate system.
- **Downloads.** URL, sha256 and UTC time for each file are in `download_manifest.tsv`. Files went only to gitignored `inputs/`. `metadata/sources_manifest.tsv` was not touched.
- **Papers.**
  - Read: PMC7981257 (7KD1), PMC3935398 (4LVV), PMC10066318 (7YR6/7), PMC3518761 (4FRG/4FRN), and the abstract of the CPEB3 7QR3/7QR4 paper (Europe PMC; no PMID or PMCID).
  - Inaccessible (PMC returned captcha pages, which were deleted and not used): PMC4685959 (4ZNP) and PMC4557640 (4XW7/4XWF).
  - Europe PMC fullTextXML returned HTTP 500 for 3 non-OA papers.

## Key findings
- **THF (RF01831).** Both natural groups have internal engineering:
  - S. mutans construct (4LVV, 4LVW–4LW0, 6Q57, 7KD1): the 7KD1 methods state that the P1 terminal pairs were changed to GG/CC and that P4 was replaced by a tetraloop. The genome check against UA159 (AE014133.2) agrees: differences at 1–2, 59–61 and 87–89.
  - E. siraeum (3SUH, 3SUX, 3SUY): 14, 65 and 85 differ from both E. siraeum genomes, plus the termini.
  - 3SD3 is a U25C ligand-site mutant.
  - Result: exploratory only.
- **CPEB3 (RF00622).** The human construct matches AL158040.14 only at 1–41. Positions 42–55 are a U1A-binding module in P4, consistent with U1A being in the crystal. The paper reports P1.1 replaced by symmetry-mate dimerization. Chimp and human differ at one position (30). Result: exploratory.
- **PrrB_RsmZ (RF00166).**
  - 2MF0 is exact in P. protegens CHA0 (CP003190.1), but it is an NMR fragment (1–72) with two conformer entries (L/R) of 20 models each.
  - 7YR6/7YR7 (cryo-EM, 4.8 and 3.8 Å) have one extra C at 61 compared with PAO1 (and 2 differences compared with PA14). The accessible paper text does not explain it.
  - Result: exploratory.
- **ZMP-ZTP (RF01750).** This is the strongest candidate family, but it is not eligible.
  - F. ulcerans chains have observed fraction 0.83–0.85.
  - 4ZNP_A (T. carboxydivorans) and 4XWF_A (A. odontolyticus) both differ internally from their source WGS. Both carry the same loop `GUGGGAAACCAC`, and 4XWF has an internal deletion of about 11 nt.
  - The papers were inaccessible, so a motif effect cannot be ruled out. Result: exploratory.
- **AdoCbl-II (RF01689).** Both structures derive from env8. The paper lists the 4FRN mutations and the 4FRG P13 deletion. Result: excluded.
- **mir-16 (RF00254).** Observed fraction is 0.63–0.74. Result: excluded.
- **Remaining families.** Excluded or redundant because they have a single natural source, consist of designed variants or artificial sequences (5DI2 hammerhead), or are NMR-only partners.
  - The review of Corona_FSE, c-di-GMP-I-GGC, Tymo, HIV_PBS, pRNA, K10_TLS, Gammaretro_CES, PreQ1-III, HIV_FE and Guanidine-III used `seed_gr_structure_links.tsv` sequences and taxids only. Their mmCIFs were not opened.
  - Statements based on "sequence inspection" (for example U1A-type loops) are flagged as unverified in the TSV.

## Uncertainties
- The chimp CPEB3 genome was not checked.
- For RsmZ, the CHA0 source is assigned from the Rfam row taxid (294) plus an exact genome hit. The mmCIF has no source annotation.
- The 6Q57 `src_gen` (S. mutans UA159, host E. coli K-12) is metadata only. Its sequence is identical to the engineered 4LVV construct.
- ZTP could become eligible only if the 4ZNP and 4XW7 papers (or their supplements) show that the loop and deletion changes are outside any compared motif. That has not been shown.
