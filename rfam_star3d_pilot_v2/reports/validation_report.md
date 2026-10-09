# Validation report — pilot cohort v1 (prompt V2.0)

Reviewer for every check: **AI agent (Claude)**. "Manual" = raw files viewed directly by the agent. No human
approval has been given or is claimed.

## Phase gates

| Phase | Gate | Status | Evidence |
|---|---|---|---|
| 1 Inventory | snapshots explicit; parser checked on a real interleaved record | **PASS** | Rfam 15.1 pinned via versioned URL == CURRENT bytes (seed sha256 41f014f4…, decompressed a6fc52d9…, gzip -t OK); `logs/parser_gate_RF00162.txt` (2 blocks, raw assembly == parser, all 457 rows + 5 #=GC tracks == Rfam.seed.gz) |
| 2 Eligibility | every selected RNA has evidence record, decision, traceable row link; pairs frozen | **PASS** | `review/decisions.yaml`, `review/construct_review.tsv`, `reports/evidence_cards.md`, `metadata/cohort_v1_freeze.json` (+ initial freeze kept) |
| 3 Seed reference | rows traced to archive; ≥5 pairs + gap traced manually; residues match structure; no aligner used | **PASS** | `results/standard_seed_membership.tsv` (11/11 verified: raw-line trace == parsed, sha256 == Phase-2 record); `logs/phase3_manual_trace_RF00522__3FU2_A__6VUI_A.txt` (independent awk: 30/30 pairs, 7/7 gaps identical); crosswalk identity check 986/986 rows |
| 4 STAR3D | correspondences trace to raw output + coordinates; all pair status rows exist | **PASS** | `results/run_manifest.tsv` (7 pairs × 6 runs: 41 completed, 1 failed + preprocessing); `logs/phase4_independent_check_RF00522__3FU2_A__6VUI_A.txt`; `logs/reconciliation_check.txt` |
| 5 Interactions | one consistent annotation method; same common-assessable denominators | **PASS (with caveats)** | FR3D-python 288f98cc on unchanged mmCIF model 1; `results/interaction_summary.tsv`; caveats below |
| 6 Report | deliverables + audit | **PASS** | this file, `reports/report.md`, `reports/professor_QA.md` |

## Focused tests (`tests/`, invented data only) — 13 passed
1 interleaved assembly incl. GR/GC + gaps · 2 all-gap columns leave correspondences unchanged · 3 trimmed-interval
offset reconciliation · prompt's A-CGU/AUCGU example · malformed/duplicate-name/unknown-GR rejection · 7 STAR3D parser
(icode, negative, digit chain, count mismatch) · 8 edge-label reversal (tSH↔tHS, s35↔s53, involution) · unit-ID parsing ·
9 common-denominator rule. Tests 4, 5, 6, 10 are covered by pipeline hard checks rather than unit tests:
4 missing residues keep label numbering (crosswalk `observed`; 3FU2 13-14 unobserved, no renumbering); 5 author/label/
icode join hard-checked against the written aligner input for all 11 RNAs; 6 identical-sequence rows kept ambiguous
(`sequence_match_only` → ambiguous; duplicate URS rows in RF00059/RF00174 retained); 10 `logs/reconciliation_check.txt`.

## Defects found and fixed (all logged in `logs/changes.md`)
1. **Crosswalk author numbering** taken from `pdbx_poly_seq_scheme.auth_seq_num` instead of coordinate-record
   `auth_seq_id` (= pdb_seq_num). Affected 6VMY_A (130 residues) and 2GDI_X (1). Detected because 26 STAR3D lines for
   RF00174 failed to join. Fixed + hard check added; aligner inputs byte-identical, so STAR3D runs stayed valid; Phases 3-5 recomputed.
2. **STAR3D wrapper**: output dir outside STAR3D_source (attempt 1) and **stale colima/sshfs view** of a moved directory
   (attempt 2) for the first pair. Both attempts preserved in `runs/_superseded/`; wrapper now uses never-reused paths and
   checksums inputs/preprocessing outputs inside the container.
3. **First-pair premise line** in the independent-check log used wrong columns; corrected in place with a note.
4. **5U3G mask list** missed positions 37 and 70 (organism-restricted BLAST arrived after first freeze); amended
   before any run, re-frozen, initial freeze kept.
5. Literature: 3 PMC captcha pages had been stored as successes (V1); quarantined with manifest correction rows.

## STAR3D behaviour checks
- Determinism: all completed replicates identical within direction (14/14 direction groups; RF00442 reverse shows
  "2 distinct outputs" only because replicate 1 crashed — JVM SIGILL under QEMU emulation — not nondeterminism).
- Direction sensitivity: forward ≠ reverse for RF00522 3FU2–6VUI and RF00174 (2 pairs each); identical for 4 pairs.
- Positive controls (`results/control_runs.tsv`; not results): 2GIS vs 3IQR 94/94 RMSD 0.63; 4GXY self 163/163;
  6VMY self 130/130 → short cross-species alignments (RF00162 25 nt, RF00174 26 nt) are algorithmic outcomes.
- STAR3D preprocessing (MC-Annotate WWc → RemovePseudoknots) produced 5-46 nested pairs per RNA (checked per file).

## Caveats that limit claims
- FR3D-python reports "annotations are not yet finalized"; repository has no license file (local use only).
- STAR3D's own preprocessing uses canonical (MC-Annotate WWc) pairs, so canonical-pair preservation is not independent
  validation of STAR3D; noncanonical and stacking classes are the more independent part of the evaluation.
- Engineered positions are masked from interpretation but remain in all tables (`engineered_masked`).
- Several primary construct papers are not open access (2GIS, 2CKY/3D2G, 4GXY): engineering inferred from genome
  comparison only; design statements unreviewed.
- 6VUI organism-restricted BLAST timed out; 7MLW source strain genome absent from nt.

## Audit answers
- Every conclusion cites a file in this study (tables, logs, raw runs, raw seed lines). ✔
- Global automated counts (`metadata/inventory_stage_counts.json`) are kept separate from reviewed counts
  (`results/family_inventory.tsv` review columns; 10 reviewed, 21 passing families unreviewed = unknown). ✔
- Every primary row exists unchanged in the pinned Rfam.seed.gz; nothing borrowed/added/replaced; Rfam.3d.seed.gz not used. ✔
- Trimming/engineering/missing residues/numbering were checked for each inspected region (masking, BLAST, crosswalk). ✔
- Every STAR3D result is from v1.2 (sha256 c9da4405…), defaults, recorded inputs (sha256 in manifest). ✔
- All 7 pairs and the failed run are reported regardless of outcome. ✔
- One full chain→row→residue→partner example: `logs/phase3_manual_trace_…`, `logs/phase4_independent_check_…`
  and `results/correspondence_comparison.tsv` rows for RF00522__3FU2_A__6VUI_A. ✔
