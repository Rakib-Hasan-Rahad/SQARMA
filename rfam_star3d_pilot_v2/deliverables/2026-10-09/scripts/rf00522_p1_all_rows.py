"""Sequence-level check of the P1 helix (SS_cons columns 6-10 : 27-31) for ALL 43 RF00522 rows of the pinned
ordinary seed. For each row: pairs at the SS_cons columns (WC/GU or not), and the same with the 3' strand partner
taken one residue later / earlier in that row (a +1/-1 register shift). Sequence complementarity only; no structure."""
import os
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import stockholm  # noqa: E402

OK = {"AU", "UA", "GC", "CG", "GU", "UG"}
a = next(stockholm.parse(os.path.join(ROOT, "inputs/rfam/15.1/Rfam.seed.gz"), only={"RF00522"}))
ss = a.gc["SS_cons"]
stack, pairs = [], []
for i, c in enumerate(ss):
    if c in "<([{":
        stack.append(i)
    elif c in ">)]}":
        pairs.append((stack.pop(), i))
p1 = sorted(p for p in pairs if p[0] < 12 and p[1] < 35)
print("# SS_cons P1 column pairs (1-based):", [(x + 1, y + 1) for x, y in p1])
print("row\tn_pairs_with_residues\twc_or_gu_as_aligned\twc_or_gu_3prime_shift_plus1\twc_or_gu_3prime_shift_minus1")
for name, s in a.seqs.items():
    cols = stockholm.residue_columns(s)
    pos = {c: k for k, c in enumerate(cols)}
    res = [s[c].upper().replace("T", "U") for c in cols]
    n = asis = plus = minus = 0
    for x, y in p1:
        if x in pos and y in pos:
            n += 1
            i, j = pos[x], pos[y]
            asis += res[i] + res[j] in OK
            plus += j + 1 < len(res) and res[i] + res[j + 1] in OK
            minus += j - 1 > i and res[i] + res[j - 1] in OK
    print(f"{name}\t{n}\t{asis}\t{plus}\t{minus}")
