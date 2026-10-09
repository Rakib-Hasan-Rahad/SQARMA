# Blockers and attempted remedies

| # | Item | Effect | Attempted remedy | Needed |
|---|---|---|---|---|
| 1 | Python.org Python lacked a CA store (SSL verify failed on EBI) | first download attempt failed (recorded in archive_v1_provenance/sources_manifest_failed_attempt1_ssl.tsv) | certifi CA bundle in scripts/fetch.py | none (resolved) |
| 2 | No host Java; STAR3D bundles Linux-only MC-Annotate (i386) / RemovePseudoknots (x86-64) | cannot run natively on macOS/arm64 | docker image star3d-runtime:1 (ubuntu 22.04, OpenJDK 8) on colima x86_64/QEMU | none (resolved) |
| 3 | PMC returned reCAPTCHA pages for 3 articles (4LVV, 7KD1, 3K1V papers) | methods text for those papers unreviewed | pages quarantined (list: archive_v1_provenance/v1_quarantined_captcha_pages.txt), manifest correction rows; 3K1V paper reviewed via the 3FU2 copy | manual access if THF family is revisited |
| 4 | Non-open-access primary papers (2GIS Nature 2006, 2CKY Science 2006, 3D2G JACS 2008, 4GXY NSMB 2012, 2HOJ) | construct-design statements unreviewed; engineering inferred from genome comparison only | NCBI BLAST against claimed source genome | researcher library access to confirm construct design |
| 5 | NCBI BLAST organism-restricted query for 6VUI_A timed out (900 s) | Tte-genome-specific check for the PreQ1 33-mer missing | unrestricted BLAST already 33/33 to T. italicus; literature states T. tengcongensis origin | optional rerun |
| 6 | 7MLW_F source strain (Burkholderia sp. TJI49, txid987057) has no genome in NCBI nt | organism-specific natural comparison impossible | closest hit B. pseudomultivorans (125/129) + paper statement of P2-loop changes | exploratory pair only |
| 7 | JVM SIGILL (JIT code) under QEMU x86 emulation in 1 of 36 alignment runs (RF00442 reverse rep1) | that replicate has no output | recorded as failed; downstream uses lowest completed replicate; replicates 2-3 completed | native x86-64 Linux host would avoid emulation |

## v2.1 additions (audit-repair)
| # | Item | Effect | Attempted remedy | Needed |
|---|---|---|---|---|
| 8 | Fresh rerun limited to the preQ1 candidate | 4 pairs (SAM-I, cobalamin, TPP, guanidine-I) not rerun from fresh downloads | reproduction script is generic (`scripts/fresh_repro.py`, PDBS/PAIRS lists) | run with the remaining pairs if required |
| 9 | STAR3D author site reset a connection once during the fresh download | none (retry/cache added; tarball verified identical) | bounded retries | none |
| 10 | No exact-source genome check for 3D2G (plant locus; construct already redesigned) and 7MLW (strain genome absent from nt) | evidence_strength literature_supported_only / related_species_only | documented in evidence cards | strain genome or author confirmation |
| 11 | Node.js absent: palette validator not runnable | chart colours taken from the reference palette's documented validated slots; non-colour encoding added | — | none |
| 12 | Item 5 superseded: 6VUI source now exact-verified via direct genome search (AE008691.1) instead of BLAST | resolved | — | — |
