# Running status — Rfam standard seed vs ORIGINAL STAR3D (prompt V2.0; audit-repair v2.1; cohort v1.1)

Reviewer for all checks: AI agent (Claude). No human review or professor approval has been given or claimed.
Last update: 2026-10-09 (v5) — branch v5-single-run-natural-dataset; local commits only (not pushed).

| Status | State |
|---|---|
| Execution completed | yes (7 pairs, 42 current runs, FR3D 11 RNAs) |
| Calculation reproduced | external audit re-checked retained files (no software rerun) |
| Fresh software rerun | all 7 pairs (preQ1 earlier; 4 others 2026-10-09): every completed run identical; 2 JVM crashes under emulation in today's rerun; FR3D 11/11 byte-identical |
| Candidate structurally supported | RF00522 7REX row P1 3' strand: supported candidate (not a demonstrated error) |
| Interpretation unresolved | L1 loop, ligand context, SAM-I and cobalamin (coverage), exploratory pairs |
| New families reviewed | all 21 remaining screen-passing families: 0 new primary pairs (review/v3_screening/) |
| Ordinary vs curated seed (Survey B) | identical in 15.1 for all 74 shared families |
| Ready for scaling | no new eligible data under current criteria (deliverables/2026-10-09/readiness.json) |

Audit log: audit/AUDIT_LOG.md; pre-repair snapshot: audit/v2.0_snapshot_7f94cba/.
Resume: README.md "Rerun by stage"; tests: `.venv/bin/python -m pytest -q tests` (51 passing).

## v4 (2026-10-09)
| Status | State |
|---|---|
| Tests | 64 pass; 16/16 re-introduced defects detected |
| Regions reviewed | 19/19 pilot + 2/2 prospective |
| Candidate | 7REX P1 3′ strand: supported candidate (moderate); L1 favours the seed |
| STAR3D method audit | pair-rule difference and overwrite quantified; S1/S2 sensitivity |
| Curated vs ordinary | records identical in all releases with a curated file; discovery rule samples curated families only |
| Expansion | tRNA pre-registered: 0 primary pairs; 1 exploratory pair run |
| Ready for scaling | no (scope decision needed) |

## v5 (2026-10-09): CURRENT
| Status | State |
|---|---|
| Method | one forward original-STAR3D v1.2 output per pair (results/primary_star3d_outputs.tsv) |
| Dataset | verified natural sequences only: 1 family, 3 structures, 3 pairs (RF00522) |
| Excluded | 9 confirmed-engineered chains; 7EQJ natural but unpaired |
| Candidate | 7REX P1 3′ strand: supported candidate (moderate); L1 favours the seed |
| Tests | 81 pass; mutation check 18/18 |
| Ready for scaling | no (scope decision needed) |
