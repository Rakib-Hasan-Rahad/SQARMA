# Weekly progress update (v4, 2026-10-09)

*AI agent for Rakib Hasan Rahad; no human review.*

**Done and verified in this session**
1. **Repairs re-validated.** 64 tests pass. Each of 16 earlier defects was put back into a scratch copy of the code, and
   each was caught by its test. One new fix: reverse-strand row coordinates (no pilot data affected).
2. **STAR3D checked against its paper.**
   - The code keeps non-canonical pairs, and when one residue has two partners it silently keeps the last one written.
     That overwrite happens once, in 7MLW.
   - Two labelled sensitivity runs:
     - preQ1 results are unchanged;
     - the exploratory guanidine-I alignment is strongly affected (78 → 25 nt);
     - the overwrite alone has no effect.
3. **Every region reviewed.** All 19 pilot regions, previously 5, now have evidence tables and a classification. The 7REX
   P1 candidate survived and gained independent literature support. L1 favours the seed.
4. **Seed provenance.** Curated and ordinary seed records are identical in every release that ships a curated file. The
   7REX row first appears in Rfam 15.0.
5. **Expansion (pre-registered, tRNA).** 0 primary pairs. One exploratory pair agrees with the seed outside an
   enzyme-refolded region.

**Conclusions changed:** see `tables/conclusions_changed.tsv`. One earlier statement was withdrawn: that base-centroid
distances had not been computed. Several others were made more precise.

**Open:**
- the scope decision for further data;
- a native host;
- a curator contact about 7REX, which is the user's decision;
- a second aligner (optional).
