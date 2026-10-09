# Archived multi-run history (v4, archived 2026-10-09 by the v5 single-run refactor)

**Primary policy from v5 onward.** For each selected RNA pair, we use one forward alignment from original STAR3D v1.2
with default parameters, following the package's preprocessing procedure.

**What was archived here.** Earlier sessions also ran each pair in the reverse direction and as three replicates. They
also ran two separately labelled sensitivity analyses (S1 and S2). Those results were not used to select or combine
the primary mapping. They are kept here unchanged, as evidence:

- `results/*_v4_multi_run.tsv` — the v4 active tables, which still carry the replicate and reverse columns;
- `results/replicate_consistency.tsv` — replicate and forward-versus-reverse agreement;
- `results/sensitivity/` — the S1 and S2 tables and run manifests;
- `results/run_manifest_all_runs_v4.tsv` — every STAR3D step ever recorded, including failed and superseded attempts
  (this is a copy; the original `results/run_manifest.tsv` stays as the historical execution log);
- `scripts/star3d_sensitivity*.py` — the sensitivity runners. They are no longer part of the active workflow.

**What was not moved.** The raw outputs stay where they were written (`runs/`, `runs_sensitivity/`,
`expansion_v4/runs/`) and are not modified.

**Observations made in the earlier runs, still valid as limitations:**
- Replicates were identical within every direction group.
- Forward and reverse runs differed by 2 pairs for 3FU2–6VUI and for 4GXY–6VMY, and by 4/4 positions for the tRNA pair.
- 3 JVM crashes occurred under emulation.
