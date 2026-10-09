# Version 1 study — archived (superseded by Version 2 on 2026-10-09)

This directory holds work done under prompt Version 1.0. Version 2.0 (standard Rfam.seed.gz as the
sole alignment reference; ordinary-vs-curated seed comparison deferred) supersedes it. Per V2 §14 this
directory is preserved unchanged as the V1 run; the active study is `../rfam_star3d_pilot_v2/`.

State at archival:
- Downloaded: Rfam 15.1 CURRENT files incl. Rfam.3d.seed.gz (V1 only), Rfam.pdb.gz, Rfam.seed.gz,
  133 mmCIF entries, RNAcentral records, literature metadata/excerpts, NCBI BLAST results (checksums in
  metadata/sources_manifest.tsv; 3 PMC captcha pages quarantined to logs/invalid_downloads/).
- Phase 1 inventory/shortlist and Phase 2 structure_sequence_map were built from Rfam.3d.seed.gz
  rows. These are NOT standard-seed results and must not be relabelled as such.
- V1-only observation (not reused as a V2 result): for all 74 families in Rfam.3d.seed.gz, row names,
  aligned strings and #=GR lines were identical to Rfam.seed.gz (metadata/seed_overlap_families.tsv).
- STAR3D: only a TECHNICAL preflight (yeast tRNA-Phe 1EHZ/1EVV, runs/_preflight_tRNA_TECHNICAL_TEST);
  no research pair was run under V1. No cohort was frozen under V1.
