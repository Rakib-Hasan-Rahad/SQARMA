# Rfam standard seed vs ORIGINAL STAR3D — pilot (prompt Version 2.0)

Compares nucleotide correspondences in the **standard Rfam seed (`Rfam.seed.gz`, release 15.1)** with
correspondences produced by **original STAR3D v1.2** from experimental structures, then checks base-pair
and stacking preservation (FR3D). The ordinary-versus-structure-curated seed comparison is **deferred**.
`Rfam.3d.seed.gz` is not used by this study. Version-1 work was deleted after V2 completed; its provenance records are in `archive_v1_provenance/`.

Status: see `STATUS.md` (v2.1 audit-repair: `audit/AUDIT_LOG.md`; professor summary: `reports/professor_summary.md`). Validation: `reports/validation_report.md`. Blockers: `reports/blockers.md`.

## Layout
`inputs/` unchanged downloads (checksummed in `metadata/sources_manifest.tsv`; mmCIF, wwPDB seqres, papers and the STAR3D tarball are git-ignored — re-download from the recorded URLs) ·
`metadata/` inventories · `mappings/` structure-row links, conversion maps · `review/` construct evidence and
`decisions.yaml` · `runs/` one directory per STAR3D pair · `annotations/` FR3D raw + normalized ·
`results/` tables · `figures/` · `reports/` · `scripts/` · `tests/` · `logs/`.

## Environment
- Python venv: `python3.13 -m venv .venv && .venv/bin/pip install -r requirements.lock.txt`
  (fr3d from `git+https://github.com/BGSU-RNA/fr3d-python.git@288f98cc…`).
- STAR3D needs Linux (bundled i386/x86-64 binaries): `docker build --platform linux/amd64 -t star3d-runtime:1 -f scripts/Dockerfile.star3d scripts/`
  (on Apple silicon via colima x86_64/QEMU). Details: `reports/environment.md`.

**Latest validated state: `deliverables/2026-10-09_v4/README.md` (v4).**

## Rerun by stage (all stages are resumable; downloads are cached and never overwritten)
```
.venv/bin/python scripts/inventory.py                      # Phase 1 (pins + verifies Rfam.seed.gz sha256)
.venv/bin/python scripts/parser_gate.py inputs/rfam/web/RF00162_web_stockholm.sto RF00162 "URS000080DF35_32630/1-94" 2GIS_A_SS
.venv/bin/python scripts/structures.py                     # Phase 2a: mmCIF evidence for shortlisted links
.venv/bin/python scripts/literature.py <PDB_CHAIN ...>     # Phase 2b: paper excerpts (Europe PMC / PMC)
.venv/bin/python scripts/blast_natural.py <PDB_CHAIN[:TAXID] ...>; .venv/bin/python scripts/blast_summary.py
.venv/bin/python scripts/cohort.py [--freeze]              # Phase 2 close-out (reads review/decisions.yaml)
.venv/bin/python scripts/prepare_inputs.py                 # Phase 4a: aligner inputs + residue crosswalk
.venv/bin/python scripts/reference.py                      # Phase 3: standard-seed reference pairs
.venv/bin/python scripts/star3d.py run <PAIR_ID ...>       # Phase 4: original STAR3D, both directions x3
.venv/bin/python scripts/compare.py                        # Phase 4: correspondence comparison
.venv/bin/python scripts/interactions.py                   # Phase 5: FR3D + interaction preservation
.venv/bin/python scripts/regions.py                        # Phase 5: disagreement regions
.venv/bin/python scripts/exact_source_check.py KEY:ACC[:org] ...  # v2.1 exact-source genome check (full + trimmed core)
.venv/bin/python scripts/anchor_fit.py PAIR START END [shared|shared_flank_excl|shared_canonical] [flank]
.venv/bin/python scripts/candidate_evidence.py             # v2.1 RF00522 candidate evidence + exploratory adjustment checks
.venv/bin/python scripts/fresh_repro.py                    # v2.1 fresh re-download + STAR3D/FR3D rerun (preQ1) under audit/fresh_repro/
.venv/bin/python -m pytest -q tests                        # 33 focused correctness tests (invented data only)
```
`mode: pilot|scale` lives in `config.yaml`; scale mode changes only cohort caps, never the reference policy.

## Key policies (see config.yaml)
- Sole alignment reference: pinned `Rfam.seed.gz` (sha256 41f014f4…); every derived row carries
  `reference_source`, `rfam_release`, `seed_sha256`. Rows must already exist in that file.
- STAR3D input: family interval of one chain, model 1, first altloc, author numbering, written from mmCIF
  (conversion maps in `mappings/conversion/`). Defaults only; `-p` adds a superposition PDB.
- Engineered construct positions are kept but masked from interpretation (`review/decisions.yaml`).

## Licenses
STAR3D: authors' page states free for research/educational/commercial use and modification. FR3D-python:
no license declared in its repository — used locally, not redistributed. Paper texts are kept locally for
review only and are git-ignored.
