# Running status — Rfam standard seed vs ORIGINAL STAR3D (prompt V2.0, mode=pilot)

Reviewer for all checks: AI agent (Claude). No human approval has been given or claimed.
Last update: 2026-10-09 (pilot cohort v1 complete).

| Phase | State | Gate |
|---|---|---|
| 1 Inventory | done | PASS |
| 2 Eligibility | done; cohort v1 frozen (7 pairs: 5 primary, 2 exploratory) | PASS |
| 3 Seed reference | done for all 7 pairs | PASS (manual trace on first pair) |
| 4 STAR3D + comparison | done: 42 alignment runs (41 completed, 1 JVM crash), 3 technical controls | PASS (independent check on first pair) |
| 5 Interactions + regions | done: FR3D for 11 RNAs, 19 candidate regions, 5 inspected + 1 agreement example | PASS with caveats |
| 6 Report | done: `reports/report.md`, `professor_QA.md`, `validation_report.md`, `evidence_cards.md`, `scale_up_readiness.md`, `blockers.md` | PASS |

## Open items
- RF02340 (DENV/ZIKV SLA, tRNA-scaffold constructs): review pending (unknown, not excluded).
- 21 screen-passing families not reviewed.
- PDF version of the report not produced (no converter checked).
- Researcher review of construct decisions and the RF00522 7REX finding.

## Resume
See README.md "Rerun by stage". The V1 directory was deleted at the user's request after V2 completed; its provenance is kept in `archive_v1_provenance/`.
