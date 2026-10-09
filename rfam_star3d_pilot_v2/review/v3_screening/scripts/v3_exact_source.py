"""Exact-source check (v3 screening, standalone; does not touch review/exact_source_check.tsv).
Searches the deposited family-interval sequence in a claimed-source genome (both strands). If no exact hit,
locates the best region by 12-mer seeds and reports a query-global/genome-local alignment with differences
in construct (label_seq_id) numbering. Usage: v3_exact_source.py ROOT KEY SEQ ACC [KEY SEQ ACC ...]"""
import sys, os, collections
ROOT = sys.argv[1]
COMP = str.maketrans("ACGTN", "TGCAN")

def load(acc):
    L = open(os.path.join(ROOT, "inputs/ncbi/genomes", acc + ".fasta")).read().splitlines()
    return L[0], "N".join("".join(L[i] if not L[i].startswith(">") else "\n" for i in range(1, len(L))).split("\n")).upper()

def glocal(q, t):
    n, m = len(q), len(t)
    S = [[0]*(m+1) for _ in range(n+1)]
    for i in range(1, n+1): S[i][0] = -2*i
    for i in range(1, n+1):
        for j in range(1, m+1):
            S[i][j] = max(S[i-1][j-1] + (1 if q[i-1] == t[j-1] else -1), S[i-1][j]-2, S[i][j-1]-2)
    j = max(range(m+1), key=lambda j: S[n][j]); i = n; diffs = []; end = j
    while i > 0:
        if j > 0 and S[i][j] == S[i-1][j-1] + (1 if q[i-1] == t[j-1] else -1):
            if q[i-1] != t[j-1]: diffs.append(f"{i}{q[i-1]}>{t[j-1]}")
            i, j = i-1, j-1
        elif S[i][j] == S[i-1][j]-2:
            diffs.append(f"{i}{q[i-1]}>del"); i -= 1
        else:
            diffs.append(f"ins_before_{i+1}:{t[j-1]}"); j -= 1
    return diffs[::-1], j, end

args = sys.argv[2:]
print("key\taccession\tgenome_header\texact_plus\texact_minus\tverdict\tbest_strand\tbest_genome_start\tn_diff\tdifferences_construct_numbering")
for k in range(0, len(args), 3):
    key, seq, acc = args[k:k+3]
    q = seq.upper().replace("U", "T")
    head, g = load(acc); rc = g.translate(COMP)[::-1]
    ep = [i+1 for i in range(len(g)) if g.startswith(q, i)] if q in g else []
    em = [len(g)-i-len(q)+1 for i in range(len(rc)) if rc.startswith(q, i)] if q in rc else []
    if ep or em:
        print(f"{key}\t{acc}\t{head[1:80]}\t{ep}\t{em}\texact_source_verified\t\t\t0\t"); continue
    best = None
    for strand, s in (("+", g), ("-", rc)):
        idx = collections.Counter()
        kmers = {q[i:i+12]: i for i in range(len(q)-11)}
        for km, qi in kmers.items():
            p = s.find(km)
            while p != -1:
                idx[(p - qi)//50] += 1; p = s.find(km, p+1)
        if idx:
            d, c = idx.most_common(1)[0]
            if not best or c > best[0]: best = (c, strand, s, d*50)
    if not best:
        print(f"{key}\t{acc}\t{head[1:80]}\t[]\t[]\tNOT_found_no_seed_hit\t\t\t\t"); continue
    c, strand, s, d = best
    w0 = max(0, d-60); win = s[w0:d+len(q)+110]
    diffs, j0, j1 = glocal(q, win)
    gs = w0 + j0 + 1
    gpos = gs if strand == "+" else len(g) - gs + 1
    print(f"{key}\t{acc}\t{head[1:80]}\t[]\t[]\tNOT_found_exactly_in_claimed_genome\t{strand}\t{gpos}\t{len(diffs)}\t{';'.join(diffs)}")
