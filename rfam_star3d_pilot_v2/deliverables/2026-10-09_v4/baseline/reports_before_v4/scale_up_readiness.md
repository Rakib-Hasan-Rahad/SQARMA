# Scale-up readiness

Mode `scale` in `config.yaml` changes only the cohort caps (`max_families_to_review: null`,
`max_pairs_per_family: null`). The reference policy (pinned Rfam.seed.gz 15.1), the eligibility rules and the
validation standard stay the same. The pilot is a development set: results on newly added families must be reported
separately from these 7 pairs, which were used to debug the workflow. Running the pipeline without crashing does not
validate it independently.

## Reusable as-is (automated, with hard checks)
- **Inventory and seed membership.** `inventory.py` runs the stage counts across all families in about 5 s.
- **Structure-link evidence.** `structures.py` extracts mmCIF evidence and parent-maps modified residues.
- **Phase 3 reference.** `reference.py` does the raw-archive trace and fails the stage if a row is absent or its hash differs.
- **Inputs and crosswalk.** `prepare_inputs.py` hard-checks author IDs against the written input files.
- **STAR3D runs.** `star3d.py` uses unique attempt paths, checks checksums inside the container, and records every run.
- **Downstream analysis.** `compare.py` (validation failures fatal), `interactions.py` (per-method masking, separate
  denominators, symmetry-operator filter, provenance sidecars), `regions.py` (span and target eligibility),
  `anchor_fit.py` (shared-correspondence anchor fit with degeneracy check) and the plotting scripts.
- **Exact-source genome check.** `exact_source_check.py` (full interval and trimmed core). This should run
  automatically for every candidate before construct review starts.
- **Fresh reproduction.** `fresh_repro.py` can be extended to any pair list.

## Still requires manual review (the bottleneck)
- **Construct and source review** took most of the pilot effort. Engineering was found in most candidate families,
  and PDB metadata was wrong or empty for several entries (4GMA, 4GXY, 2GIS).
- **Genome comparison** has to be checked against the *claimed* organism. Unrestricted BLAST hit lists fill up with PDB
  entries (2GIS got no natural hit), and organism-restricted queries can take more than 15 minutes or time out (6VUI).
- **Paper access.** Some construct papers are not open access, and PMC sometimes serves captcha pages.
- **Region adjudication** needs a human-level reading of geometry and interactions.

## Bottlenecks and costs observed
- STAR3D under QEMU emulation: about 2–4 s per alignment and 2 s per preprocessing step; one JVM SIGILL crash in 42
  alignment runs. A native x86-64 Linux host is recommended for scale.
- colima/sshfs can serve stale views of reused paths; this is now guarded.
- NCBI BLAST throughput is about one query every 1–15 minutes. A local BLAST database or Rfamseq-based genome lookups
  would be needed for hundreds of RNAs.

## Missing data and changes needed before a broad survey
1. Review the 21 screen-passing families that were not reviewed, then lift the model-length cap or the rRNA exclusion
   only by a new, declared decision.
2. Resolve the 1,793 sequence-only chain–row proposals by checking their provenance. They are not eligible today.
3. Settle a masking-versus-exclusion policy for engineered loops. The SAM-I result shows that engineered regions can
   steer STAR3D's choice of module.
4. Pre-register any secondary STAR3D parameter experiment (stack RMSD cutoff, minimum stack size), separate from the
   defaults.
5. Decide whether to use a release newer than 15.1. That would be a new, versioned study with links revalidated, not a
   silent mix of releases.
6. Report per family; pairs that share RNAs are not independent.

## Recommendation (v2.1)
**Do not scale yet.** First complete:
1. Researcher review of the RF00522 candidate and the cohort v1.1 reclassification.
2. A fresh rerun of the 4 pairs not yet rerun (cobalamin, SAM-I, TPP, guanidine-I).
3. Automated exact-source checks as a screening gate, because construct engineering removed most candidates.
4. Review of the 21 unreviewed families in rank order.
5. A native x86-64 STAR3D host.

After that, scale mode can reuse every automated stage unchanged. Construct review stays manual.

## Update 2026-10-09 (v3)
- Items 2 and 4 of the recommendation are done:
  - the fresh rerun covers all 7 pairs;
  - all 21 unreviewed families are reviewed, with 0 new primary pairs.
- Item 3 was applied to the new candidates (`review/v3_screening/exact_source_v3.tsv`).
- Still open:
  - item 1, researcher review;
  - item 5, a native host.
- Under the current criteria there is nothing eligible to scale to. Further growth needs a declared scope change
  (`deliverables/2026-10-09/readiness.json`).
