# Two-minute meeting script (completed work only)

1. **Goal.** "We compare which nucleotides the Rfam seed pairs up between two related RNAs with which nucleotides
   the original STAR3D aligner pairs up, using experimental structures. Neither is treated as the truth."

2. **Reliability.** "This week I repaired five pipeline checks and added regression tests; 51 tests pass. None of the
   repairs changed any result. All seven pilot pairs have now been rerun from fresh downloads. Every run that completed
   matched exactly. Two runs crashed in the Java runtime because I am emulating x86 on a Mac."

3. **Data.** "I reviewed every remaining family that passed our first screen, 21 of them. None gives a new pair of two
   natural, unengineered RNAs from different sources. So I did not add comparisons. The usable experimental data under
   our current rules is exhausted."

4. **Your seed question.** "In Rfam 15.1 the 3D-curated seed file is byte-identical to the ordinary seed for all 74
   families they share, including all of ours. So our 'ordinary' baseline is already the 3D-curated alignment. To see
   what curation changed, we would need an older Rfam release."

5. **Main finding.** "In preQ1-I, the seed row for the Carnobacterium RNA, PDB 7REX, has the 3′ strand of helix P1 one
   nucleotide out of register. The crystal structure and STAR3D agree with each other there. Among all 43 rows of that
   family, only this row shows the problem. In loop L1, though, the seed fits better, and a second ligand sits there.
   I'd call it a candidate for curator review, not an error."

6. **Ask.** "Should we broaden the criteria, for example engineered constructs as a separate tier or predicted
   structures? And can we get access to a native Linux machine for STAR3D?"
