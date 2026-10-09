# STAR3D execution audit (2026-10-09)

Scope: the original STAR3D v1.2 as run by `scripts/star3d.py` for the 7 pilot pairs and the controls. This audit is read-only. **No new STAR3D preprocessing or alignment was run.** The only container commands were `uname`, `java -version`, `sha256sum`, `-h`/usage output and `ldd --version`. All paths below are relative to `rfam_star3d_pilot_v2/`.

The evidence falls into three groups, and each statement says which group it comes from:

- **[DOC]**: documentation checks (reading the paper, README or source; no execution).
- **[RERUN]**: computations re-run in this session. The commands and outputs are in `deliverables/2026-10-09/star3d_audit/`.
- **[RETAINED]**: evidence from earlier sessions. The path is cited and the evidence was **not rerun**.

## 0. Sources

| source | status | evidence |
|---|---|---|
| Paper: Ge & Zhang, NAR 2015;43:e137, doi:10.1093/nar/gkv697, PMC4787758 | **[RERUN]** fetched today from the Europe PMC REST fullTextXML endpoint (168,395 bytes), sha256 `b33f995aff0ca283a2e2c45aa06e7bda6f69a6cb5813bf1c73051cc01aa39acb`. Saved to `inputs/literature/STAR3D_PMC4787758.xml`, which is gitignored. | `star3d_audit/paper_fetch.txt`, `star3d_audit/paper_key_sentences.txt` |
| Package README and `src/*.java` (16 files, 1,595 lines) | [DOC] read from `runs/RF00522__3FU2_A__6VUI_A/attempt3/STAR3D_source/` | n/a |
| Wrapper, Dockerfile, prepare_inputs, config, tests | [DOC] read; tests re-executed [RERUN] (4 passed) | `star3d_audit/pytest_star3d.txt` |

Equations in the paper's XML are TeX blocks. The numeric gap, match and mismatch defaults could not be read from the paper text, so section 2 cites the source for those values.

## 1. Software identity and runtime

| item | paper statement | source implementation | our command/input | evidence | status/resolution |
|---|---|---|---|---|---|
| Tarball sha256 | n/a | n/a | `inputs/software/STAR3D_v1.2.tar.gz` | [RERUN] host and in-container `sha256sum` = `c9da4405…ed946`; `star3d_audit/env_checks.txt` | **Matches** config/expected |
| STAR3D.jar sha256 | n/a | prebuilt jar in tarball (dated 2016-10-17); manifest says "Created-By 1.8.0_91", Ant 1.9.6 | jar in every attempt dir | [RERUN] all 11 attempt-dir jars and a fresh in-container extraction = `e03ff7bc…58618`; `env_checks.txt` | **Consistent**. The jar is the authors' prebuilt binary, not recompiled by us. |
| jar vs shipped classes vs src | "implemented in Java" | 16 top-level classes; classfile major 52 (Java 8). README says Java 1.7. | n/a | [RERUN] `star3d_audit/jar_vs_source.txt`: jar classes byte-identical to `class/*.class`; 1:1 with `src/*.java`. Compiled `Preprocess.class` contains the rcsb URL and DATAPATH strings; `MCA.class` contains `--h`. | Equivalence of src to bytecode **not proven** (not recompiled or decompiled). String markers are consistent. |
| Image | n/a | `scripts/Dockerfile.star3d`: ubuntu:22.04 + openjdk-8-jre-headless, linux/amd64 | `star3d-runtime:1` | [RERUN] image Id `sha256:e1602e60…1b7e`, Architecture amd64, created 2026-10-08T21:54:39-05:00 | Matches manifest `image_id` |
| Java / arch | n/a | n/a | n/a | [RERUN] in-container `uname -m` = `x86_64`; OpenJDK 1.8.0_504 (8u504-ga-1ubuntu1~22.04.3); host `arm64` (QEMU emulation via colima, per `reports/environment.md` [RETAINED]); glibc 2.35 | OK. README warns that RemovePseudoknots was built against glibc 2.12. It ran here: every npk.ct was produced. |
| Bundled tools | MC-Annotate; RemovePseudoknots (RNAstructure) | `tools/MC-Annotate` (ELF32), `tools/RemovePseudoknots` (ELF64) | n/a | [RERUN] sha256 MC-Annotate `285b89a6…0139`, RemovePseudoknots `0ca3afc1…f316`, EJML `ee7840eb…2588`, commons-cli `e7cd8951…59d9` (`container_help_and_jar.txt`) | Recorded. These hashes were not in the manifest before. |

## 2. Commands and parameters

| item | paper statement | source implementation | our command/input | evidence | status/resolution |
|---|---|---|---|---|---|
| Preprocess command | preprocessing obtains SS from coordinates | `Preprocess.main`: usage `java -cp STAR3D.jar Preprocess PDB chain`; lower-cases the PDB stem; chain is used as given | `java -cp STAR3D.jar Preprocess <stem> <chain>` ×2 per attempt (`star3d.py:126`) | [RETAINED] manifest `command` column; [RERUN] usage string (`container_help_and_jar.txt`) | **Matches README** |
| Alignment command | n/a | `STAR3D.main` (commons-cli BasicParser); 4 positional args | `java -jar STAR3D.jar -o out/<run>.aln -p q Cq t Ct` (`star3d.py:188`, `extra_flags: ["-p"]`) | [RETAINED] manifest; [RERUN] `-h` output | **Matches README** plus `-o` and `-p` |
| RMSD cutoff r_c | "default value is 4 Å" | `rmsd_cutoff=4.0` (STAR3D.java:17) | default, not passed | header of every `.aln`: `#RMSD cutoff: 4.0A` | Match |
| min stack size k | "default value of k is 3" | `min_stack_size=3` | default | `.aln` header | Match |
| gap open / ext | symbols only (in equations) | −5 / −2 | default | `.aln` header | Source = expected; paper values not verified |
| match / mismatch | "two different scores" for matched | `match_score=3`, `mismatch_score=0`. Base score is 3 if d<0.5·r_c, 1.5 if d<r_c, 0 if d<2·r_c, else forbidden (LoopAlign.java:156-159) | default | `.aln` header | Match; 1.5 tier = 0.5·match |
| threads | n/a | `thread_num=1` | default | manifest `parameters` | Match |
| `-p` | n/a | only writes `<out>.aln.pdb` superposition; does not change the alignment | passed | source STAR3D.java:385-424 | Not an algorithmic deviation |
| Deviations | n/a | n/a | n/a | n/a | **None in parameters.** Our only additions are `-o` and `-p`. |

## 3. Coordinate inputs and the PDB.java parser

Our input policy ([DOC] `scripts/prepare_inputs.py`): RCSB mmCIF → gemmi, model 1 only, `remove_alternative_conformations()` (first conformer), family label_seq interval of one chain, no ligands, waters or other chains, author chain/number/icode unchanged, PDB written with TER. [RERUN] All 11 input sha256 equal `mappings/aligner_inputs.tsv`. Each file was re-parsed exactly as PDB.java does (`star3d_audit/input_parse_audit.tsv`, script `audit_inputs.py`).

| item | paper statement | source (PDB.java / ResID.java) | our input | evidence [RERUN] | status/resolution |
|---|---|---|---|---|---|
| ATOM/HETATM | input is PDB atomic coordinates | both record types read; residue name = cols 18-20 | HETATM present only for terminal GTP/CCC (2gdix GTP10, CCC89; 4gxya GTP1, CCC172; 6vmya GTP202; 5u3gb GTP1) | `input_parse_audit.tsv` | Included as residues; sequence letter `N` |
| Modified residues | n/a | any non-A/C/G/U name → `N` in sequence/ct; coordinates still used | as above. No internal modified nt in the 11 inputs. | same | OK; `N` only at chain termini |
| TER / models | n/a | stops at first `ENDMDL`; after `TER`, further records of that chain are ignored | 1 TER per file, single model | same | OK |
| Residue order | n/a | file order; new residue whenever (chain, resSeq, iCode) changes; index = list position | written in label_seq order; `prepare_inputs.py` re-reads and asserts order | conversion maps `mappings/conversion/*.tsv`; [RETAINED] build-time assertion | OK |
| Insertion codes / negative numbers | n/a | icode = col 27; `Integer.valueOf` handles negatives; MC-Annotate ID parser handles `-` and `.icode` | none present in the 11 inputs | `input_parse_audit.tsv` (neg_or_icode = "-") | Handled in source and in wrapper regex (`tests/test_star3d_parser.py`); not exercised by data |
| Altlocs | n/a | **altloc column (col 17) ignored**: duplicate conformers would all enter the centroid | gemmi keeps first conformer (7MLW had 46 altloc atoms before) | altloc_nonblank_atoms = 0 in all inputs | OK because of our pre-filtering |
| Missing residues | n/a | **no gap detection**: consecutive list entries are neighbours | coordinate gaps: 3fu2a 12→15, 4gxya 19→26 and 113→117, 7mlwf 29→33 | `input_parse_audit.tsv` (last column) | See next row |
| Gap-adjacency in loop scoring | "uses 3-nt regions" for d_ij | `LoopAlign.base_superimpose` takes list indices i−1..i+1, so residues across a gap are treated as backbone neighbours. Stack detection (`FindStackmap`) also tests contiguity by list index. | n/a | [RERUN] `aln_crosswalk_audit.tsv`: aligned consecutive pairs spanning a gap occur only for 3FU2. 3FU2 A:12/A:15 is aligned to 6VUI A:12/A:13 and 7REX A:14/A:15 (all 6 replicates in each direction). | **Qualification:** the 3FU2 12–15 local scores use a non-physical "neighbour". No gap-spanning pairs were found for 4GXY or 7MLW alignments. |
| Partial residues | backbone centroid of "C3', C4', C5', O3', O5' and P" | centroid of whichever of the 6 atoms exist; zero atoms would give NaN (no guard) | 3FU2 C12 has only P, OP1, OP2, O5' (2 of 6 centroid atoms). 4GXY 113 also has 2/6. 5′ residues lack P (5/6). | `input_parse_audit.tsv`; `mappings/conversion/RF00522__3FU2_A.tsv` | **3FU2 C12 is aligned** (A:12↔6VUI A:12; A:12↔7REX A:14) using a 2-atom pseudo-centroid. It should be flagged as low-confidence. |
| Chain IDs | n/a | single char (`charAt(0)`) | auth chains A, X, B, F; enforced 1-char in prepare_inputs | `aligner_inputs.tsv` | OK |

## 4. Secondary structure: MC-Annotate → WWc → RemovePseudoknots

| item | paper statement | source implementation | evidence | status/resolution |
|---|---|---|---|---|
| SS origin | "All plausible pairing interactions are identified by using MC-Annotate" | Preprocess runs MC-Annotate on the PDB, then builds a ct file from MCA pairs. **No Rfam SS_cons is supplied anywhere** (wrapper passes only stem and chain). | [DOC] Preprocess.java, star3d.py | **Confirmed: SS is derived from coordinates** |
| Which pairs form the ct | "Watson–Crick base pairs (A↔U, C↔G) and wobble base pairs (G↔U) are retrieved" | `MCA.parse_MCA_BP_info` takes the **first letter** of each MC-Annotate face (e.g. `Wh`→W, `Ws`→W) plus cis/trans. Preprocess keeps every pair labelled `WWc`, **with no base-identity filter**. | [RERUN] `preprocessing_audit.tsv`: non-AU/CG/GU "WWc" entering the ct: 3FU2 C-A 8-34 (Wh/Ww), 2GIS U-U 26-67, 4KQY G-G 53-70 (Ww/Wh), 4GXY A-G 73-156, 6VMY G-A 246-308 and A-A 276-306, 2GDI G-A 19-47, 5U3G U-U 13-28, 7MLW C-A 5-58 and G-A 75-90 | **DISCREPANCY (paper vs code).** Non-canonical cis W/W pairs can define stacks. Some are later removed as pseudoknots (e.g. 3FU2 8-34), but others survive into npk.ct (e.g. 2GDI 19-47, where nothing is removed). |
| Multi-partner residues | n/a | if a residue has more than one WWc partner, the later one overwrites the partner column. `multi_pair` is collected but never used, so the ct can be non-reciprocal. | [RERUN] 7MLW F16 has F44 (C-G Wh/Wh, one_hbond) and F47 (C-G Ww/Ww, XIX). In `7mlwf_F.ct`, index 16→41 (F44) but index 44 (F47)→16 is non-reciprocal. In `7mlwf_F.npk.ct`, F16, F44 and F47 are **all unpaired**. | **Source defect with an effect on our data:** the canonical C16–G47 pair is missing from the 7MLW SS used for stack detection. All other ct files are reciprocal. |
| Pseudoknot removal | "eliminate the crossing base pairs … RemovePseudoknots" | `RemovePseudoknots -m ct npk.ct`. The `DATAPATH` env var is set on an unused ProcessBuilder (and points to a non-existent `tools/RNAstructure/data_tables`), so it is never passed. Exit code not checked. If 0 WWc pairs, ct is copied to npk.ct. | [RERUN] all 14 npk.ct files: reciprocal, subset of ct, length = PDB.java residue count, sequence identical to the PDB.java sequence. Removed pairs listed per RNA (e.g. 3FU2: 8-34, 9-33, 10-32, 11-31, i.e. the P2 pseudoknot helix). | Outputs consistent. Whether `-m` output depends on DATAPATH is **not verified**. |
| ct numbering | n/a | ct index = 1-based list position, **not** author number | 3fu2a_A.ct: author A22 is index 20 (gap 13–14) | OK; the crosswalk uses `star3d_index0` |
| Pairs used in loop scoring (β) | "Pseudoknots, non-canonical base pairs and canonical base pairs … are considered" | `Lib.get_seq_pairing_map` uses **all** MCA pairs with W/H/S faces (cis or trans, any identity, including pseudoknots). Bonus is +1 per matched pair whose local RMSD < r_c (`multi_pairing_align`). | [DOC] Lib.java, LoopAlign.java | Matches paper |
| Loop bonus carry-over | n/a | in `affine_gap_align`, `num_of_pair` is initialised once (line 148) and only updated when both residues are paired (161-162). An unpaired cell therefore **inherits the previous paired cell's bonus** (lines 164-166). | [DOC] LoopAlign.java | **Implementation quirk, not in paper.** It inflates match scores after paired cells. Its effect on our alignments was not quantified. |
| MCA files present | n/a | n/a | [RERUN] every mca has WWc pairs (5–48 per RNA) | OK |

## 5. Isolation and the legacy download fallback

| item | source | our mitigation | evidence | status |
|---|---|---|---|---|
| Auto-download | Preprocess downloads `http://www.rcsb.org/pdb/files/<id>.pdb` if `PDB/<stem>.pdb` is missing | wrapper copies the hash-checked input into `PDB/` first. Stems are `<pdb><chain>` (e.g. `3fu2a`), which are not real PDB IDs. | [RETAINED] preprocess stdout shows no "Downloading" line (e.g. `runs/RF00522__3FU2_A__6VUI_A/attempt3/logs/preprocess_3fu2a.stdout`) | Fallback not triggered. The container is **not** network-isolated (`docker run` has no `--network none`). |
| Cache reuse | mca and npk.ct are reused if present and non-empty | fresh tarball extraction per attempt (`attemptK` never reused, including `_superseded`). Mount check requires container-side input sha = host sha and `STAR3D_struct_info` count = 0. Post-check compares in-container npk.ct sha to host. | [RETAINED] `logs/mount_check.stdout` (sha lines + `0`), `post_check_*.stdout`; manifest rows `failed_stale_mount` (attempt2) and `failed_wrapper_defect` (attempt1) moved to `runs/_superseded/`. [RERUN] manifest npk sha = file sha now for all 14 (`preprocessing_audit.tsv`). | Effective |

## 6. Failure detection

| item | source behaviour | wrapper behaviour (`star3d.py`) | evidence | status/resolution |
|---|---|---|---|---|
| Exit codes | `STAR3D` exits 0 on `-h`, on wrong arg count, on CLI ParseException, and on "No similar stacks" (no output file). Preprocess exits 0 on wrong usage. | rc≠0 → `failed`; rc=0 with no file → `no_alignment` (stdout kept in note); file present → parsed; declared≠parsed count → `parse_error` | [RERUN] `-h` and usage exit=0 (`container_help_and_jar.txt`) | A CLI misuse would be logged as `no_alignment`, not `failed`. The command strings are fixed, so this is a low risk. |
| Empty alignment | if no clique gives score < 0, the file is written with 0 aligned and RMSD 256.00 | would be marked `completed` with aligned_n=0 | [DOC] | Not observed (min aligned_n = 25) |
| Preprocess validation | tool exit codes ignored; empty mca → 0 WWc → ct copied → valid-looking npk.ct | gate checks rc, non-empty npk.ct and in-container sha. It does **not** check that the mca is non-empty or has pairs. | [DOC] | **Gap in the gate.** Not triggered (section 4), but worth a check. |
| SIGILL | n/a | n/a | [RETAINED] `RF00442__5U3G_B__7MLW_F__a1__reverse__rep1`: exit 139, `SIGILL` in JIT-compiled `java.util.AbstractCollection.<init>` (`runs/RF00442__5U3G_B__7MLW_F/attempt1/logs/…reverse__rep1.stdout`). Recorded `failed`; rep2/rep3 completed with bodies identical to each other and, swapped, to forward. | 1 of 42 pilot alignment runs. Consistent with a JIT/QEMU emulation fault (not a STAR3D logic error), but **not proven**. Residue: 0-byte `core` and `hs_err_pid1.log` are in that attempt's STAR3D_source/. |
| Determinism | Bron–Kerbosch pivot uses unseeded `new Random()`; ties are broken by first clique encountered | 3 replicates per direction | [RERUN] `replicate_body_identity.txt`: 1 distinct body per direction for all 14 direction groups. [RETAINED] `results/replicate_consistency.tsv` agrees. | Deterministic in practice. Forward and reverse differ by 2 residue pairs for 3FU2/6VUI (3' end 32-33) and 4GXY/6VMY. Already recorded in replicate_consistency.tsv. |

## 7. Raw output → residue crosswalk

[RERUN] `star3d_audit/aln_crosswalk_audit.tsv` (script `audit_preproc_aln.py aln`) covers all 41 completed pilot alignment runs, not just one. For every run:

- declared `#Aligned nucleotide` = parsed lines = manifest `aligned_n`;
- every query and target residue ID resolves in `results/residue_crosswalk.tsv` (`star3d_resid`);
- the mapping is injective on both sides and monotonic in `star3d_index0`;
- the file sha256 equals manifest `output_sha256`.

Example: 3FU2→6VUI forward rep1 has 31 pairs, matching manifest 31. Partial-atom residues inside alignments: 3FU2 A:12 (both 3FU2 pairs) and 5′ P-less residues (A:1, X:10/A:2, B:1/F:2).

RMSD in `.aln` is computed on 6-atom backbone **pseudo-centroids** over all mapped residues after a single Kabsch fit (STAR3D.java:329). It is not an all-atom RMSD.

## 8. Scientific qualification

STAR3D's alignment depends on pairing information at two levels:

1. Stacks are built only from MC-Annotate "WWc" pairs that survive pseudoknot removal. In this code that includes some non-canonical cis W/W pairs.
2. The loop DP adds a β bonus for conserved pairs of any family. Per the paper: "Pseudoknots, non-canonical base pairs and canonical base pairs … are considered".

Agreement between STAR3D correspondences and FR3D interaction preservation is therefore **supporting, not independent**, evidence. Both are driven by annotated base pairing (different annotators, MC-Annotate vs FR3D, but overlapping signal). Claims of "interaction conservation" for STAR3D-aligned residues should be read as partly circular.

## 9. Discrepancies and actions (summary)

1. **Paper vs code, SS pair selection:** the paper says AU/CG/GU. The code takes any cis W/W face pair regardless of identity, and 10 non-canonical-identity pairs across 8 RNAs entered ct files (plus the identity-canonical but non-WC-geometry C-G Wh/Wh 7MLW 16-44). *Action:* disclose; optionally list npk.ct pairs per RNA with identity.
2. **Multi-partner overwrite (7MLW F16):** the canonical C16–G47 pair is lost from the SS used for stacks. *Action:* disclose for RF00442; consider whether it affects the stem containing F15–F48/F17–F45.
3. **Gap adjacency:** 3FU2 12→15 is treated as contiguous, and the 2-atom C12 is aligned. *Action:* flag 3FU2 C12 and its neighbours' correspondences as low-confidence in both RF00522 pairs.
4. **Loop-bonus carry-over** (`num_of_pair` not reset): disclose as an implementation property of STAR3D v1.2.
5. **Preprocess gate:** add a check that the `.mca` is non-empty and has at least 1 WWc pair. Optionally run with `--network none`.
6. Housekeeping: `core` (0 B) and `hs_err_pid1.log` from the SIGILL run sit inside `runs/RF00442__5U3G_B__7MLW_F/attempt1/STAR3D_source/` (left untouched).

## 10. Limitations / not verified

- The jar was not recompiled or decompiled. Equivalence of `src/` to the executed bytecode rests on byte-identical `class/` files and string markers only.
- The paper's numeric gap/match/mismatch defaults were not readable in the text (they are in TeX equations). The source values are reported.
- No STAR3D alignment or preprocessing was re-executed. Outputs were re-checked, not regenerated.
- The cause of the SIGILL (QEMU vs JVM) is not established.
- The effect of `DATAPATH` not being passed to RemovePseudoknots `-m` was not tested.
- The quantitative effect of the `num_of_pair` carry-over, of the gap adjacency and of the 7MLW lost pair on the final correspondences was not measured, because that would require rerunning a modified STAR3D.
- MC-Annotate face notation was interpreted from the source's first-letter rule. MC-Annotate's own semantics for `Wh`/`Ws` sub-faces were not independently checked.
- Controls (`results/control_runs.tsv`: self-alignments 4GXY 163/0.0 Å and 6VMY 130/0.0 Å; 2GIS vs 3IQR 94/0.63 Å) are [RETAINED], not rerun.

## Files written this session

- `deliverables/2026-10-09/STAR3D_execution_audit.md` (this file)
- `deliverables/2026-10-09/star3d_audit/`:
  - `paper_fetch.txt`
  - `paper_key_sentences.txt`
  - `env_checks.txt`
  - `container_help_and_jar.txt`
  - `jar_vs_source.txt`
  - `input_parse_audit.tsv`
  - `preprocessing_audit.tsv`
  - `aln_crosswalk_audit.tsv`
  - `replicate_body_identity.txt`
  - `pytest_star3d.txt`
  - scripts `audit_inputs.py`, `audit_preproc_aln.py`
- `inputs/literature/STAR3D_PMC4787758.xml` (paper; gitignored)

## Addendum (coordinator, same session): STAR3D computations that WERE rerun today
The audit above deliberately ran no alignments. Separately, the coordinator ran the following this session [RERUN].

**Fresh reproduction of the 4 pilot pairs not rerun before** (RF00059, RF00162, RF00174, RF00442).
- Command: `scripts/fresh_repro.py --pairs … --out audit/fresh_repro_v3_other4`. It used the new strict input gate and
  the new preprocessing-content validator.
- **Downloads.** All 8 mmCIFs and the STAR3D tarball were re-downloaded and are byte-identical to the pinned files
  (`accepted_identical`).
- **Rebuilt inputs.** All 8 rebuilt PDB inputs are byte-identical, with 0.0 Å maximum atom displacement.
- **Preprocessing.** 8/8 steps completed, and all npk.ct files are identical to the retained ones.
- **Alignments.** 24 runs: 4 pairs × 2 directions × 3 replicates.
  - 21 runs produced mappings identical to the retained runs.
  - Two runs crashed in the JVM. `RF00059 reverse rep1` died with SIGSEGV in a JIT-compiled `java.util.regex` frame.
    `RF00174 forward rep1` died with SIGILL in a JIT-compiled `java.util.Formatter` frame. Both runs had completed in
    the retained set.
  - `RF00442 reverse rep1` crashed in the retained set (SIGILL) and **completed** today. Its mapping is identical to
    retained rep2 and rep3.
- **What the crashes suggest.** There are 3 JVM crashes in 84 emulated alignment runs (42 retained, 18 preQ1 fresh,
  24 today). All are in JDK library code compiled by the JIT, and they hit different runs each time. That fits
  QEMU/JIT emulation instability rather than STAR3D logic, but this is not proven. A native x86-64 host, or a
  diagnostic `-Xint` run, would test it.
- **What was not affected.** Every completed run, fresh or retained, gives identical mappings across replicates and
  across sessions.
- **Tables:** `tables/fresh_repro_other4.tsv` and `audit/fresh_repro_v3_other4/fresh_repro_summary.json`.

**FR3D.** It was regenerated for these 8 RNAs, and for all 11 RNAs via `interactions.py --verify-regenerate`. Raw
outputs and normalized annotations are byte-identical.

**Gate repair (C3).** The `.mca` gap reported above is now closed (`star3d.preprocessing_problems`). All 14 retained
preprocessing products pass. One WARNING is recorded: the non-reciprocal raw `.ct` for 7MLW chain F at residue 44.
