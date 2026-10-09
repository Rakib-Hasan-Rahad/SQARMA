# Two-minute meeting script (v5; completed work only)

1. "We compare which nucleotides the Rfam seed pairs up between related RNAs with what original STAR3D pairs up from
   their crystal structures. Neither is assumed to be right."
2. "I simplified the method: one forward STAR3D alignment per pair, run the way the package README describes, with
   defaults. Earlier reverse and replicate runs are archived and not used. The switch changed none of the results."
3. "I also made the dataset strictly natural sequences. I re-checked all 13 RNA chains we had used. Nine were
   engineered in some way: extra terminal nucleotides, loop swaps or deletions. Those are now excluded, even where we
   had masked the changes. That leaves three natural preQ1 riboswitches from three bacteria, so three pairs."
4. "The main finding survives. In the seed row for the Carnobacterium RNA, 7REX, the 3-prime strand of helix P1 is
   shifted by one nucleotide. The structure, STAR3D and the authors' own paper all put G5 opposite C18. In the
   neighbouring loop Rfam fits better, and both comparisons share that row, so it's one candidate observation."
5. "Results that came from engineered RNAs — TPP agreement, cobalamin coverage, the guanidine sensitivity, the tRNA
   pair — are withdrawn from the active results."
6. "Question: with natural constructs only we have one family. Should I look for natural pairs through sequence-only
   links in other families, or should we ask Smriti about predicted structures?"
