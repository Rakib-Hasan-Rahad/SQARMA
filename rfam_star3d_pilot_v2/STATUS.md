# Running status — Rfam standard seed vs ORIGINAL STAR3D (prompt V2.0; audit-repair v2.1; cohort v1.1)

Reviewer for all checks: AI agent (Claude). No human review or professor approval has been given or claimed.
Last update: 2026-10-09 — branch audit-repair-v2.1 (from 7f94cba); not pushed or merged.

| Status | State |
|---|---|
| Execution completed | yes (7 pairs, 42 current runs, FR3D 11 RNAs) |
| Calculation reproduced | external audit re-checked retained files (no software rerun) |
| Fresh software rerun | preQ1 candidate only (18 STAR3D runs + FR3D for 3 RNAs): identical |
| Candidate structurally supported | RF00522 7REX row P1 3' strand: supported candidate (not a demonstrated error) |
| Interpretation unresolved | L1 loop, ligand context, SAM-I and cobalamin (coverage), exploratory pairs |
| Ready for scaling | no (see reports/scale_up_readiness.md) |

Audit log: audit/AUDIT_LOG.md; pre-repair snapshot: audit/v2.0_snapshot_7f94cba/.
Resume: README.md "Rerun by stage"; tests: `.venv/bin/python -m pytest -q tests` (33 passing).
