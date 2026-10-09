# Data dictionary

Conventions: UTF-8 TSV with header; `NA` = not applicable or not available (never zero); statuses are
`pending, verified, excluded, ambiguous, blocked, failed, not_applicable` plus the stage-specific values
listed below. Every derived table carries `reference_source=Rfam.seed.gz`, `rfam_release`, `seed_sha256`
where it depends on the alignment. Index systems are never mixed without a named column:

| Name | Meaning |
|---|---|
| `row_index`, `row_A_index`, `source_row_index` | 1-based position among real residues of a standard-seed row |
| `original_column` | 1-based column of the pinned Rfam.seed.gz family record (never renumbered) |
| `row_coordinate` | coordinate in the row's own sequence system (`name/start-end`) |
| `label_seq_id` | mmCIF label sequence position of the deposited entity (includes unobserved residues) |
| `auth_seq_id` + `ins_code` | author residue number (what STAR3D and FR3D print) |
| `star3d_index0` | 0-based residue order inside the STAR3D input file |
| `<PDB>_<chain>` key / `rep_id` | `<family>__<PDB>_<author chain>`; pair_id = `<family>__<query>__<target>` |

## Tables
- **metadata/sources_manifest.tsv** — source_id, url, local_path, retrieved_utc, http_status, last_modified, etag,
  content_length_header, bytes, sha256, release, purpose, status (ok/failed/invalid), note (V1 reuse, corrections).
- **results/family_inventory.tsv** — per family: mapping entries/chain regions, candidate chain sequence groups,
  explicit GR links, explicitly linked rows/distinct sequences/taxa, sequence-only proposals, screen status.
  Automated availability only; `review_status=pending` unless reviewed.
- **metadata/chain_row_candidates.tsv** — every candidate chain: `candidate_status` ∈ explicit_gr_link,
  sequence_match_only_pending_provenance, no_standard_seed_row_candidate, no_seqres.
- **mappings/structure_sequence_map.tsv** — link (family, row, PDB, chain) with membership proof
  (`seed_row_aligned_sha256`, `seed_row_lines` = decompressed line numbers), chain IDs, entity, sequence match
  (`exact_at_row_coordinates`, `exact_elsewhere`, `match_except_unknown_residues`, `no_exact_match`), coverage,
  modifications (with parent-mapping source), source/host records, engineering fields, method, ligands,
  `link_status` (verified / ambiguous / failed / no_verified_standard_seed_row).
- **review/construct_review.tsv** — per reviewed representative: source + evidence, construct changes,
  `masked_label_seq_ids`, relevance, ligand state, alternatives, decision, reviewer.
- **results/sequence_groups.tsv** — exact family-region sequence groups (hash), members, representative, decision.
- **results/selected_representatives.tsv / selected_pairs.tsv** — frozen cohort; `tier` primary/exploratory;
  `primary_direction` = sorted stable IDs.
- **results/standard_seed_membership.tsv** — proof each selected row's gapped string equals the raw archive lines.
- **results/reference_pairs.tsv** — every original column with residues in both rows; `structural_assessability`
  ∈ assessable, missing_coordinates, engineered_position_masked, no_crosswalk.
- **results/reference_gap_assignments.tsv** — residue–gap columns, `partner=gap`.
- **results/residue_crosswalk.tsv** — row index ↔ column ↔ label/auth/icode ↔ STAR3D index; `observed`,
  `engineered_masked`, `modified`, `identity_check`.
- **results/run_manifest.tsv** — every STAR3D step: command, image id, tarball/input/preprocessing checksums,
  parameters, start, duration, exit code, output checksum, aligned_n, RMSD; status ∈ completed, failed,
  no_alignment, parse_error.
- **results/correspondence_comparison.tsv** — per run × source residue: Rfam partner, STAR3D partner,
  `category` ∈ same_partner, different_partner, rfam_only, star3d_only, neither,
  technical_failure_or_no_alignment; `rfam_missing_reason`, `star3d_missing_reason` ∈ alignment_gap_in_standard_seed,
  missing_coordinates_source, rfam_partner_missing_coordinates, algorithm_omission, no_alignment, technical_failure.
- **results/pair_summary.tsv** — per run: lengths, observed/masked counts, Rfam pairs (all / structurally
  assessable), STAR3D pairs, shared pairs, fraction of assessable Rfam pairs reproduced, Jaccard (unmasked),
  category counts + `category_sum_check`, injectivity.
- **results/interaction_comparison.tsv** (v2.1) — per source FR3D interaction: for each method m ∈ {rfam,
  star3d_forward, star3d_reverse}: `m_status` ∈ exact_class_preserved, different_class, no_annotated_target_pair,
  unmapped_endpoint, target_endpoint_unobserved; `m_target`; `m_target_masked` (yes/no/NA). For each comparison
  c ∈ {rfam_vs_star3d_forward, rfam_vs_star3d_reverse, all_three_methods}: `eligible_c` and `exclusion_c`
  (source_endpoint_masked, <m>_unmapped_endpoint, <m>_target_unobserved, <m>_target_masked). Nothing is dropped.
- **results/interaction_summary.tsv** (v2.1) — per pair, source side, class and comparison: source_interactions,
  eligible_unmasked (the comparison's own denominator), and per method: coverage_all, preserved_all and
  preserved_eligible (NA for methods outside the comparison).
- **annotations/normalized/_symmetry_lines_excluded.tsv** — FR3D lines that involve non-identity symmetry copies
  (copy_duplicate, inter_copy); these are never counted as intrachain.
- **annotations/raw/<PDB>.provenance.json** — source mmCIF sha256, the sha256 of the decompressed CIF that FR3D read,
  FR3D commit, and categories; `provenance` = generated or reconstructed_v2.1.
- **results/region_review.tsv** (v2.1) — all candidate regions; n_correspondence_disagreements vs
  n_coverage_differences; source_engineering_overlap, rfam_target_engineering_overlap,
  star3d_target_engineering_overlap, source_unobserved_in_span, rfam_target_unobserved, star3d_target_unobserved;
  eligible_for_structural_adjudication (eligible for investigation, not correctness); interpretation_source (how a
  manual interpretation was carried forward); ranking inputs; inspection status;
  classification ∈ agreement, technical_mapping_or_input_defect, possible_STAR3D_correspondence_issue,
  structural_biological_experimental_difference, supported_candidate_Rfam_correspondence_issue, unresolved.

## v2.1 additions
- **review/exact_source_check.tsv** — exact search of the claimed source genome (both strands): full family interval,
  trimmed core (masked termini removed), internal masked positions, and verdict ∈ exact_source_verified,
  core_exact_source_verified_termini_differ, NOT_found_exactly_in_claimed_genome.
- **review/decisions.yaml** `evidence_strength` ∈ exact_source_genome, core_exact_source_genome,
  literature_supported_only, related_species_only, conflicting_metadata; `engineering_status` ∈ confirmed_absent,
  terminal_only, present_documented, unknown, not_applicable.
- **results/anchor_fit/<pair>_<range>_<rule>.tsv** — shared-correspondence anchor fit. The header records the rule,
  anchors, RMSD and singular values. Rules: shared, shared_flank_excl, shared_canonical. Degenerate sets are REFUSED.
- **review/candidate_RF00522/** — structure_facts, numbering_chain, p1_raw_fr3d_lines, residue_evidence_<pair>,
  adjustment_validation.json, adjustment_interactions(_summary).tsv.
- **results/selected_pairs.tsv** `tier` ∈ primary, exploratory, exploratory_engineered_technical.
- **results/run_manifest.tsv** statuses add failed_mount_check, failed_mount_mismatch and validation_failed
  (correspondence category). `attempt*__` run_ids are historical attempts and are excluded from current denominators.

## v3 additions (2026-10-09)
- **results/standard_seed_rows.sto**: now one complete Stockholm record per family (each with ID, AC, CC, rows,
  #=GS/#=GR and #=GC, ending `//`). Original columns are preserved.
- **annotations/raw/<PDB>.provenance.json**: `provenance` = verified_v3. Adds `raw_sha256` (the basepair and stacking
  raw files) and `fr3d_installed` (the commit from the installed distribution's direct_url.json, the RECORD hash check
  and the import path). Earlier versions are kept as `<PDB>.provenance.v2.1.json`.
- **results/run_manifest.tsv**: new preprocessing status `failed_intermediate_invalid`. The `note` column can carry
  `WARNING raw .ct non-reciprocal …`.
- **results/*.INVALID.tsv**: written by compare.py *instead of* the complete tables when stored STAR3D outputs fail
  validation. A file of this name means the stage failed.
- **results/region_review.tsv**: the `inspected` and `classification` columns can be `needs_reassessment`. The
  interpretation is then prefixed `HISTORICAL, not accepted (…)`.
- **audit/fresh_repro*/diagnostics/*.mismatch.json and quarantine/*.rejected**: written by the input gate. Verdict ∈
  accepted_identical, rejected_content_change, rejected_container_only_change, rejected_rebuilt_input_differs.
- **results/seed_collection_comparison/** (Survey B):
  - `family_overlap.tsv`: one row per family.
  - `shared_rows.tsv`: one row per shared row.
  - `correspondence_differences.tsv`: one row per row pair with changed residue correspondences.
  - `annotation_differences.tsv`: GF/GR/GC differences.
  - `provenance.json`, `record_byte_identity.txt` and `README.md`.
- **review/v3_screening/**:
  - `candidate_screening.tsv`; `decision` ∈ accepted_primary, exploratory, excluded, redundant, not_reviewed_time.
  - `structure_facts.tsv`, `exact_source_v3.tsv`, `frozen_selection_v3.json`, `download_manifest.tsv`.
- **deliverables/2026-10-09/tables/**: the 7REX tables are `candidate_7REX_correspondence`, `candidate_7REX_counts`,
  `candidate_7REX_excluded_from_common_set` and `candidate_7REX_method_differences`. The others are:
  - `RF00522_P1_register_all_rows`;
  - `fr3d_verify_regenerate`;
  - `fresh_repro_other4`;
  - `requirements_status`, `results_status` (classification ∈ verified_this_session, retained_not_rerun, exploratory,
    unresolved), `validation_checks`, `test_results`, `survey_b_summary`, `downloads`.

## v4 additions (2026-10-09)
- **results/region_evidence/<region_id>.tsv.** Per residue:
  - partners (seed, STAR3D forward, STAR3D reverse) and category;
  - 4 Å contacts for source, seed partner and STAR3D partner: `LIG:<comp><num>`, `CHAIN:<id>` (another chain in the
    asymmetric unit), `SYM:<chain>` (symmetry mate);
  - for each anchor rule (shared, shared_flank_excl, shared_local), C1′ and base-centroid distances of both partners.
  Comment lines at the end give each fit's anchors and RMSD.
- **results/region_evidence/summary.tsv.** Per region. `closer_*` = number of different-partner residues whose seed /
  STAR3D partner is closer (tie = within 0.5 Å). `*_eligible_rfam_star3d` = n / seed preserved / STAR3D preserved on the
  rfam-vs-STAR3D-forward eligible set. `star3d_fwd_rev_same` = positions where forward and reverse STAR3D agree.
- **results/anchor_fit/*_shared_local.tsv.** v4 anchor rule using only shared anchors within ±8 positions outside the
  region.
- **review/region_review_v4.tsv.** The manual review. `classification` ∈ supported_candidate_Rfam_correspondence_issue,
  possible_STAR3D_correspondence_issue, STAR3D_coverage_limitation, structural_variation_or_ligand_context,
  construct_or_coordinate_confound, insufficient_evidence, not_adjudicated_ineligible. `confidence` ∈ low,
  low-moderate, moderate, high, n/a.
- **results/sensitivity/S1_*, S2_*.** Sensitivity run manifests and comparisons. In `S2_vs_default.tsv` the `S1_*`
  columns hold the S2 values.
- **deliverables/2026-10-09_v4/star3d_sensitivity/preproc_pairs.tsv.** Per MC-Annotate pair: STAR3D label, whether it is
  STAR3D-"WWc", canonical identity, whether it passes the S1 paper rule, and whether it is in `.ct` / `npk.ct`.
- **results/rfam_history/.** `release_family_records.tsv` (record hash, rows, width and structure features per release
  and pilot family), `rf00522_rows.tsv`, `curated_vs_ordinary.tsv`.
- **expansion_v4/.** An isolated prospective workspace with the same table formats as the study root. tier
  `prospective_exploratory_conformational_context`.
- **review/v4_expansion/.** `PREREGISTRATION.md`, `candidate_structures.tsv`, `raw/` (RCSB GraphQL and NCBI esummary
  responses).

## v5 additions (2026-10-09)
- **results/primary_star3d_outputs.tsv** — one row per pair: `status` (selected / unavailable), `alignment_order`,
  `selected_run_id`, `output_aln`, `output_sha256`, aligned_n, rmsd, command, parameters, input/npk/mca sha256,
  `preprocessing_run_ids`, `selection_rule`, `earlier_records_not_selected` (each with its reason), `checks_passed`.
- **results/correspondence_comparison.tsv, pair_summary.tsv** — one STAR3D run per pair (`star3d_run_id`). The
  `direction` and `replicate` columns are removed. `star3d_missing_reason` can be `no_valid_primary_output`.
- **results/interaction_comparison.tsv, interaction_summary.tsv** — methods `rfam` and `star3d`; single comparison
  `rfam_vs_star3d`.
  - `source_side` = query (forward mapping) or target (inverted same mapping; not another run).
  - `source_side_meaning` spells this out. Each side has its own denominator.
- **results/region_review.tsv** — the column `reverse_run_same_star3d_partner` is removed.
- **review/natural_sequence_eligibility.tsv** — per chain:
  - `natural_sequence_status` ∈ verified_natural, confirmed_engineered, unresolved;
  - `analysis_eligibility` ∈ accepted, excluded, pending;
  - evidence, reason, reviewer and date.
- **results/dataset_chains.tsv/.md** — readable chain-level table generated from the eligibility table.
- **results/family_inventory.tsv** — old review columns renamed `historical_review_status_v1`,
  `historical_review_decision_v1_1` and `historical_shortlisted_v1`. `current_status_v5_natural_policy` gives the
  current status.
- **results/derived_alignment_views.tsv/.md** — a SQARMA-generated gapped display of the seed and STAR3D
  correspondences (not STAR3D raw output). Lower-case = residue without coordinates.
- **metadata/cohort_v2.0_natural_freeze.json** — the frozen natural cohort, with hashes.
- **archive/** — `v4_multi_run_history/` (replicate, reverse and sensitivity tables and scripts),
  `cohort_v1.1_pre_natural_policy/`, `v4_region_evidence_all_pairs/`, `legacy_scripts/`.
