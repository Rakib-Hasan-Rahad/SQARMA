# Audit-repair log (v2.1)

- Starting commit: 7f94cba5c7d7956f0f4fa27698e488a2f63063cf (merge of PR #1); tree identical to 3a6778b
  (`git diff 3a6778b 7f94cba` empty). No commits after the audited commit; working tree clean.
- Repair branch: audit-repair-v2.1 (from 7f94cba). Not pushed/merged.
- Snapshot of pre-repair results/reports/decisions/annotations: audit/v2.0_snapshot_7f94cba/ (+ .sha256).
- Reviewer: AI agent (Claude). No human review or professor approval claimed.

## Fix 1 — interaction masking / denominators (scripts/interactions.py)
- Defect confirmed: "unmasked" filter excluded masked source and masked Rfam-target endpoints but not masked
  STAR3D-target endpoints; reverse-run preservation was reported on the forward-vs-Rfam denominator.
- Change: per-method target flags (status, targets, target_masked) for rfam / star3d_forward / star3d_reverse;
  per-comparison eligibility (source unmasked AND every compared method maps both endpoints AND all mapped
  targets observed AND no mapped target masked under any compared method) for rfam_vs_star3d_forward,
  rfam_vs_star3d_reverse and all_three_methods; every interaction kept with `exclusion_<comparison>` reason;
  injective check before inverting maps; subset runs refused (would overwrite global tables).
- Before/after (audit/fix1_interaction_masking_before_after.tsv): RF00442 target side, all classes, common
  denominator 110 -> 105 (5 interactions with masked STAR3D targets; canonical 17->16, stack 82->78); preserved
  Rfam 88->83, STAR3D-forward 82->79. Reverse comparisons now have their own denominators (differ from forward for
  RF00174 query: 1->0 and RF00522 3FU2-6VUI target: 36->39). All other counts unchanged.
- Additional defect found while auditing (observed, not hypothetical): FR3D symmetry operator ignored. 4KQY raw
  annotations contain a symmetry-generated copy (operator 4_555): 360 copy-duplicate lines (harmless after dedup)
  and 2 inter-copy lines = one stack between residue 10 and its symmetry mate, previously normalized as an
  intrachain self-stack `10-10 s33`. Now excluded and counted (annotations/normalized/_symmetry_lines_excluded.tsv).
  4KQY source interactions 181 -> 180 (stack 137 -> 136). No other structure has symmetry-operator lines.
- Tests added: tests/test_interaction_masking.py (9 tests).

## Fix 2 — region eligibility and ranking (scripts/regions.py)
- Defect confirmed: "trustworthy" checked only the disagreement residues themselves; intervening span positions
  and Rfam/STAR3D target partners were not checked; coverage differences and correspondence disagreements were
  merged; regeneration reset reviewed regions to "pending".
- Change: `trustworthy` replaced by explicit fields (source_engineering_overlap, rfam_target_engineering_overlap,
  star3d_target_engineering_overlap, source_unobserved_in_span, rfam_target_unobserved, star3d_target_unobserved)
  and `eligible_for_structural_adjudication` (= eligible for investigation, not correctness);
  n_correspondence_disagreements and n_coverage_differences counted separately; coverage-only regions rank after
  regions with correspondence disagreements; interaction differences counted on the v2.1 eligible set; manual
  interpretations carried forward (exact id, else overlapping span, with `interpretation_source`). Region-forming
  rule unchanged (merge_gap 2) so ids are comparable.
- Before/after (audit/fix2_region_eligibility_before_after.tsv): 1 of 19 regions changed eligibility —
  RF00059__2GDI_X__3D2G_A__r17-23 trustworthy=yes -> eligible=no (Rfam AND STAR3D target partners are masked
  engineered 3D2G positions). All 6 previously inspected regions carried exactly. Pre-fix table kept:
  audit/region_review_v2.0_pre_fix2.tsv.
- Tests added: tests/test_regions.py (5 tests).

## Fix 3 — preprocessing failure handling (scripts/star3d.py)
- Defect confirmed: preprocessing status `failed_mount_mismatch` was recorded but the wrapper returned only on
  `failed`, so alignment runs would proceed; the initial mount check raised without a manifest record.
- Change: `preprocess_and_gate()` (injectable runner): mount check (host==container input bytes AND no pre-existing
  intermediates) recorded as `failed_mount_check` on failure; each preprocessing step must be `completed` incl. an
  in-container checksum of its npk.ct; ANY other status stops the pair's attempt before alignment.
- Observed impact on current results: none (all 14 preprocessing steps of the current attempts are `completed`).
- Tests: tests/test_star3d_gate.py (2 tests; both FAIL against the audited star3d.py and PASS after the fix).
- Denominators: the 42 current comparison runs (7 pairs x 2 directions x 3 replicates, run_id without `attempt`
  prefix) are reported separately from historical attempts (`attempt1__`/`attempt2__` rows, 16 rows, statuses
  failed_wrapper_defect / failed_stale_mount / superseded_completed) which stay in the manifest for provenance only.

## Section 6 — related safeguards (observed vs gap)
| Item | Finding | Action |
|---|---|---|
| Malformed STAR3D mapping lines | parse_aln flags bad lines -> status parse_error (tested) | none needed |
| Author-ID numbering collisions | compare.resid_index raises (now tested) | test added |
| Output-to-crosswalk failures | GAP: unmapped lines were only counted (current data: 0 in 41 runs) | now validation_failed + stage exit nonzero; tests |
| One-to-one before inversion | GAP: checked after building dict; interaction target-side inversion unchecked (current data: all injective) | checked before; invert_injective(); tests |
| Subset reruns overwrite global tables | GAP in compare.py, reference.py, interactions.py (no damaged table observed: final tables are full-cohort) | subset arguments refused |
| Cached annotation traceability | GAP: raw FR3D files reused without provenance | sidecars (source sha, CIF sha, FR3D commit); reuse refused on mismatch; 11 backfilled after verifying CIF bytes identical to pinned mmCIF |
| FR3D symmetry identifiers | DEFECT (see Fix 1): 4KQY inter-copy stack counted as intrachain | fixed |
| Model/chain/icode/altloc policies | preserved (model 1; first altloc via gemmi for aligner inputs; FR3D annotates full mmCIF, model 1 kept) | none |
| Structural-fit anchors | GAP: target-side masks not checked, no degeneracy check, wording "method-neutral" overstated | scripts/anchor_fit.py (shared-correspondence anchor fit; target masks; >=4 anchors & min singular value >=1 A); old neutral_fit outputs kept |
| replicate_consistency row order | nondeterministic (set order); content identical | sorted |
- Anchor sensitivity (audit/anchor_fit_sensitivity.tsv): shared (16/17 anchors) vs flank-excluded (12/13 anchors) —
  direction of support unchanged for every residue except 6VUI A10 (Rfam-closer -> within 1 A). canonical-only
  anchor set refused as degenerate (single strand; smallest singular value ~0.2 A).
