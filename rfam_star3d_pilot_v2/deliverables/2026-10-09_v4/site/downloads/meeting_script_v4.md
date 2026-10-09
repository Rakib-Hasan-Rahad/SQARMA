# Two-minute meeting script (v4; completed work only)

1. "We compare which nucleotides the Rfam seed pairs up between related RNAs with what the original STAR3D aligner
   pairs up from their crystal structures. Neither is assumed correct."
2. "I re-checked the software by re-inserting each earlier bug into a copy of the code. All 16 were caught by the
   tests, and 64 tests pass."
3. "STAR3D's code is broader than its paper: it also uses non-canonical pairs to build helices. When I re-ran it with
   the paper's rule, our preQ1 result didn't change at all. One exploratory family changed a lot, so I treat that
   family's result as method-dependent."
4. "The main finding still stands as a candidate. One preQ1 row, the Carnobacterium RNA from PDB 7REX, has its P1
   3-prime strand shifted by one in Rfam. The structure, STAR3D and the authors' own paper all put G5 opposite C18, not
   C17. But in the neighbouring loop, Rfam fits better, and both comparisons share the same row, so it's one
   observation."
5. "On your seed question: in every Rfam release, the 3D-curated seed records are identical to the ordinary seed
   records for those families. So our baseline is already 3D-curated, and our search could only find curated
   families."
6. "I tried one non-curated family, tRNA, with rules fixed in advance. No pair qualified as primary. Natural tRNAs carry
   modified bases that STAR3D can't read. One exploratory pair agreed with Rfam except where a bound enzyme refolds the
   tRNA."
7. "Question for you: should we widen the scope? The options are modified tRNAs with a STAR3D input fix, engineered
   constructs as a separate tier, or predicted structures with Smriti."
