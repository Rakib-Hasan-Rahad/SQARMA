"""Audit STAR3D preprocessing products (mca/ct/npk.ct) and raw .aln -> crosswalk mapping for current runs."""
import sys, csv, os, re, hashlib, collections
ROOT = sys.argv[1]
mode = sys.argv[2]
man = list(csv.DictReader(open(os.path.join(ROOT, "results/run_manifest.tsv")), delimiter="\t"))
def sha(p): return hashlib.sha256(open(p, "rb").read()).hexdigest()
def read_ct(p):
    L = open(p).read().splitlines()
    n = int(L[0].split()[0]); rows = [l.split() for l in L[1:] if l.strip()]
    return n, "".join(r[1] for r in rows), {int(r[0]): int(r[4]) for r in rows}
def pdb_res(p):
    res, cur = [], None
    for line in open(p):
        if line.startswith("ENDMDL") or line.startswith("TER"): break
        if line.startswith(("ATOM", "HETATM")):
            rid = (line[21], int(line[22:26]), line[26])
            if rid != cur: res.append((rid, line[17:20].strip())); cur = rid
    return res
MCA_RE = re.compile(r"^(?P<a>\S+?)-(?P<b>'?\w'?-?\d+(\.\w)?) : \S+ (?P<edge>\S+) .*?(?P<o>cis|trans)?\s*\S*\s*$")
def mca_wwc(p, chain):
    pairs, inbp = [], False
    for line in open(p):
        if line.startswith("Residue conformations") and inbp: break
        if line.startswith(("Adjacent stackings", "Non-Adjacent stackings")): inbp = False; continue
        if line.startswith("Base-pairs"): inbp = True; continue
        if inbp and line.strip():
            left, info = line.strip().split(" : ")
            tok = info.split()
            edge = tok[1]
            o = "c" if "cis" in info else ("t" if "trans" in info else "n")
            if "/" in edge and edge[0] == "W" and edge.split("/")[1][0] == "W" and o == "c":
                m = re.match(r"^([A-Za-z])(-?\d+)(?:\.(\w))?-([A-Za-z])(-?\d+)(?:\.(\w))?$", left)
                if m: pairs.append(((m[1], int(m[2]), m[3] or " "), (m[4], int(m[5]), m[6] or " "), tok[0], edge))
    return pairs
if mode == "preproc":
    seen = set()
    print("attempt_dir\tstem_chain\tct_len\tpdbjava_len\tseq_equal\tnpk_ct_sha256(host,now)\tmanifest_npk_sha_match\tmca_WWc_same_chain\tct_pairs\tct_reciprocal\tnpk_pairs\tnpk_reciprocal\tnpk_subset_of_ct\tremoved_by_RemovePseudoknots(author ids)\tnoncanonical_WWc_in_ct(identity@author)")
    for r in man:
        if r["direction"] != "preprocess" or r["status"] != "completed": continue
        npk = os.path.join(ROOT, r["output_aln"]); si = os.path.dirname(npk); work = os.path.dirname(si)
        stem_ch = os.path.basename(npk)[:-len(".npk.ct")]; stem, ch = stem_ch.rsplit("_", 1)
        key = (work, stem_ch)
        if key in seen: continue
        seen.add(key)
        res = pdb_res(os.path.join(work, "PDB", stem + ".pdb"))
        seq = "".join(s if s in ("A", "C", "G", "U") else "N" for _, s in res)
        n, ctseq, ct = read_ct(os.path.join(si, stem_ch + ".ct"))
        n2, npkseq, nk = read_ct(npk)
        recip = lambda d: all(d[j] == i for i, j in d.items() if j)
        prs = lambda d: {(i, j) for i, j in d.items() if j and i < j}
        removed = prs(ct) - prs(nk)
        idx2id = {i + 1: f"{rid[1]}{rid[2].strip()}" for i, (rid, _) in enumerate(res)}
        ww = [p for p in mca_wwc(os.path.join(si, stem + ".mca"), ch) if p[0][0] == ch and p[1][0] == ch]
        nonc = [f"{p[2]}@{p[0][1]}-{p[1][1]}({p[3]})" for p in ww if p[2] not in ("A-U", "U-A", "G-C", "C-G", "G-U", "U-G")]
        print("\t".join(map(str, [os.path.relpath(work, ROOT), stem_ch, n, len(res), seq == ctseq == npkseq, sha(npk)[:16],
              sha(npk) == r["output_sha256"], len(ww), len(prs(ct)), recip(ct), len(prs(nk)), recip(nk), prs(nk) <= prs(ct),
              ",".join(f"{idx2id[i]}-{idx2id[j]}" for i, j in sorted(removed)) or "-", ",".join(nonc) or "-"])))
elif mode == "aln":
    cw = list(csv.DictReader(open(os.path.join(ROOT, "results/residue_crosswalk.tsv")), delimiter="\t"))
    rep_by_sid = {}
    for m in csv.DictReader(open(os.path.join(ROOT, "mappings/aligner_inputs.tsv")), delimiter="\t"):
        rep_by_sid[m["star3d_id"]] = m["rep_id"]
    idx = collections.defaultdict(dict)
    for c in cw:
        if c["star3d_resid"] not in ("NA", ""): idx[c["rep_id"]][c["star3d_resid"]] = c
    print("run_id\tdeclared_n\tparsed_n\tmanifest_aligned_n\tall_q_in_crosswalk\tall_t_in_crosswalk\tq_injective\tt_injective\tq_order_monotonic\tt_order_monotonic\toutput_sha_match\tpairs_across_coordinate_gap\tpartial_residues_aligned")
    for r in man:
        if r["status"] != "completed" or r["direction"] not in ("forward", "reverse"): continue
        p = os.path.join(ROOT, r["output_aln"]); L = open(p).read().splitlines()
        decl = int([l for l in L if l.startswith("#Aligned nucleotide")][0].split(":")[1])
        pairs = [l.split("<->") for l in L[L.index("#Nucleotide mapping:") + 1:] if l.strip()]
        q, t = rep_by_sid[r["query_star3d_id"]], rep_by_sid[r["target_star3d_id"]]
        qi = [idx[q].get(a) for a, _ in pairs]; ti = [idx[t].get(b) for _, b in pairs]
        ok_q = all(qi); ok_t = all(ti)
        qx = [int(c["star3d_index0"]) for c in qi if c]; tx = [int(c["star3d_index0"]) for c in ti if c]
        gap = []
        for k in range(len(pairs) - 1):
            if qi[k] and qi[k+1] and ti[k] and ti[k+1] and qx[k+1] == qx[k] + 1 and tx[k+1] == tx[k] + 1:
                if int(qi[k+1]["label_seq_id"]) - int(qi[k]["label_seq_id"]) > 1 or int(ti[k+1]["label_seq_id"]) - int(ti[k]["label_seq_id"]) > 1:
                    gap.append(f"{pairs[k][0]}/{pairs[k+1][0]}<->{pairs[k][1]}/{pairs[k+1][1]}")
        part = [f"{a}<->{b}" for (a, b), cq, ct_ in zip(pairs, qi, ti) if (cq and cq["star3d_atoms_complete"] != "yes") or (ct_ and ct_["star3d_atoms_complete"] != "yes")]
        print("\t".join(map(str, [r["run_id"], decl, len(pairs), r["aligned_n"], ok_q, ok_t, len(set(qx)) == len(qx), len(set(tx)) == len(tx),
              qx == sorted(qx), tx == sorted(tx), sha(p) == r["output_sha256"], ";".join(gap) or "-", ";".join(part) or "-"])))
