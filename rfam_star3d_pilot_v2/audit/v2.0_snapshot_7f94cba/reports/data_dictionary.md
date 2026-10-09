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
- **results/interaction_comparison.tsv / interaction_summary.tsv** — per source FR3D interaction and method:
  exact_class_preserved, different_class, no_annotated_target_pair, unmapped_endpoint,
  target_endpoint_unobserved; `common_assessable_*` marks the shared denominator.
- **results/region_review.tsv** — all candidate disagreement regions, ranking inputs, inspection status,
  classification ∈ agreement, technical_mapping_or_input_defect, possible_STAR3D_correspondence_issue,
  structural_biological_experimental_difference, supported_candidate_Rfam_correspondence_issue, unresolved.
