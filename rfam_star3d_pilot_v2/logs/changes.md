# Change log (cohort / configuration)

- 2026-10-09T03:35Z cohort v1 frozen (metadata/cohort_v1_freeze_initial_20261009T033536.json).
- 2026-10-09T03:35:47Z amendment BEFORE any research STAR3D run or Phase-3 extraction: 5U3G_B masked list
  extended with 37 and 70 after the organism-restricted BLAST (txid204038, D. dadantii 3937) finished.
  Exploratory pair only; pair list unchanged. Re-frozen as metadata/cohort_v1_freeze.json.
- 2026-10-09 decisions before freeze: 4GMA_Z excluded (construct replaces P1/P2 5' segment and P6 extension);
  3D2G_A exploratory (5' 21 nt redesigned across P1/P2/P3) -> RF00059 pair exploratory.
- 2026-10-09T03:37Z STAR3D wrapper defect: out/ created outside STAR3D_source -> all 6 alignment steps of RF00522__3FU2_A__6VUI_A attempt1 failed (FileNotFoundException). Attempt preserved in runs/_superseded/, manifest rows relabelled failed_wrapper_defect/superseded_completed with run_id prefix attempt1__. Fixed in scripts/star3d.py; rerun.
- 2026-10-09T03:37Z attempt2 of RF00522__3FU2_A__6VUI_A: container saw a stale sshfs view of the moved attempt1 path (Preprocess skipped, nothing written). Preserved in runs/_superseded/. Wrapper now uses never-reused attemptN paths and checksums inputs/preprocessing outputs inside the container.
- 2026-10-09T03:43Z DEFECT FIXED: residue_crosswalk auth_seq_id came from pdbx_poly_seq_scheme.auth_seq_num instead of coordinate-record auth_seq_id (= pdb_seq_num). Affected 6VMY_A (130 residues) and 2GDI_X (1 residue); STAR3D output for RF00174 could not be joined (26 unmapped lines). Crosswalk now uses coordinate IDs (scheme value kept as scheme_auth_seq_num) and hard-checks against the written aligner input. Aligner input bytes unchanged -> STAR3D runs remain valid; Phase 3/4/5 tables recomputed.
- 2026-10-09T03:46Z TECHNICAL CONTROLS (not results; results/control_runs.tsv, runs/_controls/): 2GIS_A vs 3IQR_A (same Tte construct, A94G) 94/94 RMSD 0.63; 4GXY self 163/163; 6VMY self 130/130. Conclusion: short cross-species alignments for RF00162 (25 nt) and RF00174 (26 nt) are STAR3D algorithmic outcomes, not input/tool defects. (Control attempt1 dirs failed on wrapper run_id path bug; preserved.)
- 2026-10-09T03:52Z decisions.yaml post-freeze label edit: RF02340 'pending_blast' -> 'pending' (family never selected; no effect on frozen pairs). Freeze checksum for decisions.yaml therefore differs from metadata/cohort_v1_freeze.json by this line only.
- 2026-10-09T04:03Z User requested removal of the V1 directory ../rfam_star3d_pilot (502 MB). V2 has no runtime dependency on it (all reused inputs copied with sha256 re-verification). V1 provenance (archive note, V1 sources manifest, failed SSL attempt, captcha quarantine list) copied to archive_v1_provenance/ before deletion; doc references updated.
