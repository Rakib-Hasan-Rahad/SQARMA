# Version-1 provenance (V1 study directory deleted at the user's request, 2026-10-09)

The V1 study (`../rfam_star3d_pilot/`, prompt V1.0, built on Rfam.3d.seed.gz) was removed after V2 was complete.
V2 does not depend on it: every V1 download reused by V2 was copied into `../inputs/` after SHA-256
re-verification (see `note` column of `../metadata/sources_manifest.tsv`). Kept here for provenance only:
- `V1_ARCHIVE_STATUS.md` — what V1 contained and why it was superseded.
- `v1_sources_manifest.tsv` — original retrieval URLs/times/checksums of the reused files.
- `sources_manifest_failed_attempt1_ssl.tsv` — the failed first download attempt (SSL CA issue).
- `v1_quarantined_captcha_pages.txt` — PMC captcha pages that had been stored as successes and were quarantined.
No V1 derived table was ever used as a V2 result. scripts/import_v1_evidence.py and the reuse path in
scripts/fetch.py now find no previous study and are inert.
