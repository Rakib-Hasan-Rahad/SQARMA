"""v4: audit of ORIGINAL STAR3D preprocessing products (read-only).
Re-implements STAR3D's MCA.java/Preprocess.java pair selection in Python to quantify:
  - which MC-Annotate pairs STAR3D labels 'WWc' (first edge letter W on both sides, cis), incl. non-canonical ones;
  - residues with >1 'WWc' partner, where Preprocess.java keeps only the last-written partner (overwrite);
  - which pairs survive RemovePseudoknots into npk.ct.
Also builds, for the separately versioned SENSITIVITY variant S1 ('paper rule'), a .ct with only cis Ww/Ww pairs of
identity AU/UA/GC/CG/GU/UG. S1 is NOT original STAR3D; it is reported only as a sensitivity analysis.
Usage: star3d_preproc_audit.py OUT_DIR"""
import csv
import os
import re
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CANON = {"AU", "UA", "GC", "CG", "GU", "UG"}
BP_RE = re.compile(r"(([a-zA-Z])|('\d'))(-)*(\d)+(\.[a-zA-Z])*")


def mca_pairs(path):
    """Base-pair lines of the FIRST Base-pairs section, parsed as MCA.java does."""
    out, in_bp = [], False
    for line in open(path):
        if line.startswith("Residue conformations"):
            if in_bp:
                break
        elif line.startswith("Adjacent stackings") or line.startswith("Non-Adjacent stackings"):
            in_bp = False
        elif line.startswith("Base-pairs"):
            in_bp = True
        elif in_bp and line.strip():
            line = line.strip()
            bp, info = line.split(" : ", 1)
            m1 = BP_RE.search(bp)
            r1 = bp[:m1.end()]
            m2 = BP_RE.search(bp[m1.end() + 1:])
            r2 = bp[m1.end() + 1:m1.end() + 1 + m2.end()]
            o = "c" if "cis" in info else ("t" if "trans" in info else "n")
            tok = info.split()
            ids, edge = tok[0], tok[1]
            if "/" not in edge:
                v = "--h"
            else:
                e1, e2 = edge.split("/")[0][0], edge.split("/")[1][0]
                v = f"{e1}{e2}{o}" if e1 in "WSH" and e2 in "WSH" and o != "n" else "--h"
            out.append(dict(r1=r1, r2=r2, ids=ids, edge=edge, orient=o, v=v, line=line))
    return out


def resid(token):
    """'F16' / 'A12.B' / "'1'23" -> (chain, num, icode) like ResID.java (chain = first char or quoted)."""
    if token.startswith("'"):
        chain, rest = token[1], token[3:]
    else:
        chain, rest = token[0], token[1:]
    icode = ""
    if "." in rest:
        rest, icode = rest.split(".", 1)
    return chain, int(rest), icode


def pdb_chain_residues(path, chain):
    seen, out = set(), []
    for l in open(path):
        if l.startswith(("ATOM", "HETATM")) and l[21] == chain:
            key = (int(l[22:26]), l[26].strip())
            if key not in seen:
                seen.add(key)
                out.append((key, l[17:20].strip()))
    return out


def read_ct(path):
    rows = [l.split() for l in open(path) if l.strip()]
    return rows[0][0], {int(r[0]): (r[1], int(r[4])) for r in rows[1:]}


def main(out_dir):
    os.makedirs(out_dir, exist_ok=True)
    man = [r for r in csv.DictReader(open(os.path.join(ROOT, "results/run_manifest.tsv")), delimiter="\t")
           if r["direction"] == "preprocess" and not r["run_id"].startswith("attempt")]
    done, pairs_rows, summary = set(), [], []
    for r in man:
        npk = os.path.join(ROOT, r["output_aln"])
        d = os.path.dirname(npk)
        stem, chain = os.path.basename(npk)[:-7].rsplit("_", 1)
        if stem in done:
            continue
        done.add(stem)
        res = pdb_chain_residues(os.path.join(os.path.dirname(d), "PDB", stem + ".pdb"), chain)
        index = {(chain,) + k: i + 1 for i, (k, _) in enumerate(res)}
        _, ct = read_ct(os.path.join(d, f"{stem}_{chain}.ct"))
        _, nk = read_ct(npk)
        seq_ok = len(ct) == len(res)
        wwc, partners = [], {}
        for p in mca_pairs(os.path.join(d, stem + ".mca")):
            a, b = resid(p["r1"]), resid(p["r2"])
            if a[0] != chain or b[0] != chain or a not in index or b not in index:
                continue
            i, j = index[a], index[b]
            ident = p["ids"].replace("-", "")
            canon_ident = ident in CANON
            strict = p["edge"].split()[0] == "Ww/Ww" and p["orient"] == "c" and canon_ident
            rec = dict(rna=f"{stem}_{chain}", i=i, j=j, auth_i=f"{a[1]}{a[2]}", auth_j=f"{b[1]}{b[2]}", identity=ident,
                       mca_edge=p["edge"], orientation=p["orient"], star3d_label=p["v"],
                       star3d_WWc=p["v"] == "WWc", canonical_identity=canon_ident, paper_rule_S1=strict,
                       in_ct=ct[i][1] == j and ct[j][1] == i, in_npk=nk[i][1] == j and nk[j][1] == i)
            pairs_rows.append(rec)
            if p["v"] == "WWc":
                wwc.append(rec)
                partners.setdefault(i, []).append(j)
                partners.setdefault(j, []).append(i)
        multi = {k: v for k, v in partners.items() if len(v) > 1}
        nonrecip = [i for i, (_, j) in ct.items() if j and ct[j][1] != i]
        s1 = [x for x in wwc if x["paper_rule_S1"]]
        s1_part = {}
        for x in s1:
            s1_part.setdefault(x["i"], []).append(x["j"])
            s1_part.setdefault(x["j"], []).append(x["i"])
        s1_conf = {k: v for k, v in s1_part.items() if len(v) > 1}
        # S1 ct (sensitivity input; only written when conflict-free)
        if not s1_conf:
            with open(os.path.join(out_dir, f"{stem}_{chain}.S1.ct"), "w") as f:
                f.write(f"{len(ct)}\t{stem}_{chain}\n")
                pm = {}
                for x in s1:
                    pm[x["i"]], pm[x["j"]] = x["j"], x["i"]
                for k in range(1, len(ct) + 1):
                    f.write(f"{k}\t{ct[k][0]}\t{k - 1}\t{k + 1}\t{pm.get(k, 0)}\t{k}\n")
        summary.append(dict(rna=f"{stem}_{chain}", residues=len(ct), pdb_ct_length_match=seq_ok,
                            star3d_WWc_pairs=len(wwc),
                            WWc_noncanonical_identity=sum(not x["canonical_identity"] for x in wwc),
                            WWc_not_Ww_Ww_edges=sum(x["mca_edge"] != "Ww/Ww" for x in wwc),
                            residues_with_multiple_WWc_partners=";".join(f"{k}:{v}" for k, v in sorted(multi.items())) or "none",
                            ct_nonreciprocal=";".join(map(str, nonrecip)) or "none",
                            ct_pairs=sum(1 for i, (_, j) in ct.items() if j > i),
                            npk_pairs=sum(1 for i, (_, j) in nk.items() if j > i),
                            npk_noncanonical_identity=sum(1 for x in wwc if x["in_npk"] and not x["canonical_identity"]),
                            npk_not_Ww_Ww=sum(1 for x in wwc if x["in_npk"] and x["mca_edge"] != "Ww/Ww"),
                            S1_pairs=len(s1), S1_conflicts=";".join(f"{k}:{v}" for k, v in s1_conf.items()) or "none",
                            source_dir=os.path.relpath(d, ROOT)))
    for name, rows in (("preproc_pairs.tsv", pairs_rows), ("preproc_summary.tsv", summary)):
        with open(os.path.join(out_dir, name), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
    for s in summary:
        print({k: v for k, v in s.items() if k != "source_dir"})


if __name__ == "__main__":
    main(sys.argv[1])
