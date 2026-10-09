# Questions the professor is likely to ask

*Answers trace to files in this study. Prepared by an AI agent; not yet reviewed by the researcher.*

**Why these families and pairs?**
The rule was declared before any run, in `config.yaml`. A family qualified if it had at least two explicitly
structure-linked rows with distinct sequences in `Rfam.seed.gz`, a model length of 300 nt or less, and was not rRNA.
Families were ranked by the number of non-synthetic source taxa, then by distinct sequences. The top 10 were reviewed
manually, and representatives were picked by a fixed rule order: verified row, no target-motif engineering,
cognate-ligand-bound state, coverage, method, resolution, ID. All eligible pairs within a family were run.

**Are the sequences really distinct and natural?**
Yes, for the primary RNAs, as far as could be checked. Each one was compared with its source genome by NCBI BLAST
(`review/natural_sequence_comparison.tsv`). 3FU2, 7REX and 6VMY match their genomes over the family interval; 6VUI
matches a related *Thermoanaerobacter* genome and is described as *T. tengcongensis* in its papers (the restricted
check timed out). 2GIS and 4KQY differ from their genomes only in peripheral loops (P3 apex, P4 apex), which are
masked. 4GXY matches its genome except at its terminal residues. Exact-string diversity and natural-source diversity
are reported separately (`results/sequence_groups.tsv`).

**Organism or expression host?**
Source comes from the RNA entity's own records and the papers, never from a protein or the expression host. Two
metadata problems were caught:
- 4GMA's "marine metagenome" label contradicts both papers, which say *T. tengcongensis*.
- 4GXY has no organism recorded; BLAST gives *S. thermophilum* at 169/169.

*T. tengcongensis* is the same organism as *Caldanaerobacter subterraneus* subsp. *tengcongensis*.

**What engineering was found?**
It is extensive, and recorded per structure in `review/construct_review.tsv` and `review/decisions.yaml`. Examples:
- SAM-I k-turn swaps (5FK series, 4AOB, 7EAF).
- Noncanonical pairs converted to Watson–Crick in THF (3SUH: U14A, U65C, U85A).
- An engineered tandem G·U in guanidine-I (5T83).
- A GAAA tetraloop in 4KQY P3.
- A redesigned 5′ end in 3D2G.
- P1/P2 and P6 replacements in 4GMA.

"Mutation: No" in PDB metadata was never taken as proof of a native construct.

**How exactly does a chain map to a row?**
The chain-row link is an explicit `#=GR <PDB>_<chain>_SS` feature on a row in `Rfam.seed.gz`. The sequence must match
exactly at the row's coordinates. Membership is proved by the row's raw decompressed line numbers and a sha256 of its
gapped string (`results/standard_seed_membership.tsv`). Residues are joined through `results/residue_crosswalk.tsv`:
row index, original column, `label_seq_id`, author number and insertion code, and STAR3D index. For a complete traced
example, see `logs/phase3_manual_trace_RF00522__3FU2_A__6VUI_A.txt`.

**Why the standard seed, and doesn't it already contain structural information?**
It is the published alignment that most users rely on, and the user-approved scope makes it the sole reference. It
does carry structure-derived content: the PDB-linked rows and their `#=GR` secondary structures. The Rfam
3D-curation pipeline adds rows with cmalign (its README). This is therefore not a "sequence-only versus 3D"
benchmark; it asks whether the published correspondences agree with an independently run structural aligner.

**Why is the curated-seed check deferred?**
The user changed the scope (prompt V2). The check was requested by the professor and is deferred, not withdrawn or
done. `Rfam.3d.seed.gz` was not used in V2.

**Is this really the original STAR3D?**
Yes. STAR3D v1.2 was downloaded from genome.ucf.edu on 2026-10-09 (sha256 c9da4405…), identical to the earlier local
copy. It was run with default parameters in an Ubuntu container with OpenJDK 8 (`star3d-runtime:1`), because its
bundled MC-Annotate and RemovePseudoknots binaries are Linux-only. LocalSTAR3D and CircularSTAR3D were not used.

**What are the denominators?**
Every table states them (`results/pair_summary.tsv`):
- seed pairs, total and structurally assessable;
- STAR3D pairs;
- shared pairs;
- reproduced assessable pairs;
- per-residue categories that sum to the row length.

Interaction comparisons use the same common-assessable source set for both methods.

**Does disagreement mean Rfam is wrong?**
No. Most disagreements are explained by STAR3D aligning only one module (SAM-I, cobalamin), by engineered regions, or
by loop register uncertainty. Only one region reaches "supported candidate": the 7REX row's P1 3′ strand in RF00522.
There, four kinds of evidence converge: the seed's own SS_cons implies non-Watson–Crick pairs, the structure shows
Watson–Crick pairs, base-pair preservation favours STAR3D, and a method-neutral fit agrees. Even that is a candidate
for curator review, not proof.

**What are the limits?**
- Three primary families and seven pairs that share RNAs.
- Engineering is pervasive, and several construct papers were inaccessible.
- STAR3D runs under emulation, and its preprocessing overlaps the canonical-pair evaluation.
- FR3D labels its output as not finalized.
- 21 shortlisted-eligible families are still unreviewed.
- No rates can be extrapolated to Rfam.

**Questions for Smriti (not contacted)**
1. Does her workflow use predicted structures for families without two natural experimental structures? If so, from
   which source, and with what confidence filter?
2. Has she seen STAR3D align only one helical module on multi-domain riboswitches? Does she change the stack RMSD
   cutoff or minimum stack size?
3. Does she have a preferred way to handle engineered loops (masking versus excluding)?
