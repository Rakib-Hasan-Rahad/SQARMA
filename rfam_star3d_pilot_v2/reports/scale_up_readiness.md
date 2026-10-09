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
- **Downstream analysis.** `compare.py`, `interactions.py`, `regions.py`, `neutral_fit.py` and the plotting scripts.

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
