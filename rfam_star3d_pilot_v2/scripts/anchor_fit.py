"""Shared-correspondence anchor fit (v2.1; replaces the 'neutral_fit' wording — the fit is NOT fully
independent: its anchors are residues where the standard seed and STAR3D give the SAME partner).

Anchor rules (all require: both methods give the same partner, C1' present in source AND target, source AND
target not engineering-masked, both observed):
  shared            all such residues
  shared_flank_excl shared, excluding anchors within `flank` source positions of the disputed region [start,end]
  shared_canonical  shared, restricted to residues in an FR3D canonical cWW pair in BOTH source and target
Degeneracy check: >= 4 anchors and smallest singular value of the centred anchor C1' cloud >= 1.0 A in both
structures; otherwise the fit is refused.

Usage: anchor_fit.py PAIR_ID START END [rule] [flank]  -> results/anchor_fit/<pair>_<start>-<end>_<rule>.tsv
"""
import csv
import os
import sys

import gemmi
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
BASE_ATOMS = {"N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9", "O2", "O4", "N4", "O6", "N6", "N2"}


def read_tsv(p):
    return list(csv.DictReader(open(P(p)), delimiter="\t"))


def residues(rep_id):
    cw = {int(r["row_index1"]): r for r in read_tsv("results/residue_crosswalk.tsv") if r["rep_id"] == rep_id}
    meta = next(r for r in read_tsv("mappings/aligner_inputs.tsv") if r["rep_id"] == rep_id)
    st = gemmi.read_structure(P(meta["file"]))
    by = {(res.seqid.num, res.seqid.icode.strip()): res for res in st[0][0]}
    out = {k: by[(int(r["auth_seq_id"]), "" if r["ins_code"] in ("NA", "") else r["ins_code"])]
           for k, r in cw.items() if r["observed"] == "yes"}
    return out, cw


def atom(res, name):
    a = res.find_atom(name, "*")
    return np.array(a.pos.tolist()) if a else None


def base_centroid(res):
    xs = [a.pos.tolist() for a in res if a.name in BASE_ATOMS]
    return np.mean(xs, axis=0) if xs else None


def nondegenerate(X, min_n=4, min_sv=1.0):
    if len(X) < min_n:
        return False, f"only {len(X)} anchors"
    sv = np.linalg.svd(X - X.mean(0), compute_uv=False)
    return (sv[-1] >= min_sv), f"singular values {np.round(sv, 2).tolist()}"


def kabsch(X, Y):
    xc, yc = X.mean(0), Y.mean(0)
    H = (Y - yc).T @ (X - xc)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return lambda Z: (R @ (Z - yc).T).T + xc


def canonical_residues(rep_id):
    return {int(x) for r in read_tsv(f"annotations/normalized/{rep_id}.tsv") if r["pair_class"] == "canonical"
            for x in (r["i"], r["j"])}


def select_anchors(rows, S, T, cs, ct, rule, start, end, flank):
    canon_s = canon_t = None
    out = []
    for r in rows:
        if r["category"] != "same_partner":
            continue
        i, j = int(r["source_row_index"]), int(r["rfam_partner"])
        if i not in S or j not in T or cs[i]["engineered_masked"] == "yes" or ct[j]["engineered_masked"] == "yes":
            continue
        if atom(S[i], "C1'") is None or atom(T[j], "C1'") is None:
            continue
        if rule == "shared_flank_excl" and start - flank <= i <= end + flank:
            continue
        if rule == "shared_canonical":
            if canon_s is None:
                canon_s, canon_t = canonical_residues(cs[i]["rep_id"]), canonical_residues(ct[j]["rep_id"])
            if i not in canon_s or j not in canon_t:
                continue
        out.append((i, j))
    return out


def main(pair_id, start, end, rule="shared", flank="2"):
    start, end, flank = int(start), int(end), int(flank)
    rows = [r for r in read_tsv("results/correspondence_comparison.tsv")
            if r["pair_id"] == pair_id and r["direction"] == "forward" and r["replicate"] == "1"]
    pair = next(p for p in read_tsv("results/selected_pairs.tsv") if p["pair_id"] == pair_id)
    (S, cs), (T, ct) = residues(pair["query_rep"]), residues(pair["target_rep"])
    anchors = select_anchors(rows, S, T, cs, ct, rule, start, end, flank)
    X = np.array([atom(S[i], "C1'") for i, _ in anchors])
    Y = np.array([atom(T[j], "C1'") for _, j in anchors])
    okx, why_x = nondegenerate(X) if len(X) else (False, "no anchors")
    oky, why_y = nondegenerate(Y) if len(Y) else (False, "no anchors")
    os.makedirs(P("results/anchor_fit"), exist_ok=True)
    path = P(f"results/anchor_fit/{pair_id}_{start}-{end}_{rule}.tsv")
    if not (okx and oky):
        open(path, "w").write(f"# REFUSED: degenerate anchor set ({why_x}; {why_y}); anchors {anchors}\n")
        print(open(path).read())
        return
    f = kabsch(X, Y)
    rmsd = float(np.sqrt(((f(Y) - X) ** 2).sum(1).mean()))
    recs = []
    for r in rows:
        i = int(r["source_row_index"])
        if not start <= i <= end or i not in S:
            continue
        rec = dict(pair_id=pair_id, source_row_index=i, source_nt=r["source_nt"], category=r["category"],
                   rfam_partner=r["rfam_partner"], star3d_partner=r["star3d_partner"])
        for lab, j in (("rfam", r["rfam_partner"]), ("star3d", r["star3d_partner"])):
            if j != "NA" and int(j) in T:
                a_t, a_s = atom(T[int(j)], "C1'"), atom(S[i], "C1'")
                b_t, b_s = base_centroid(T[int(j)]), base_centroid(S[i])
                if a_t is not None and a_s is not None:
                    rec[f"{lab}_C1p_dist"] = round(float(np.linalg.norm(f(a_t[None])[0] - a_s)), 2)
                if b_t is not None and b_s is not None:
                    rec[f"{lab}_base_centroid_dist"] = round(float(np.linalg.norm(f(b_t[None])[0] - b_s)), 2)
        recs.append(rec)
    fields = ["pair_id", "source_row_index", "source_nt", "category", "rfam_partner", "star3d_partner",
              "rfam_C1p_dist", "star3d_C1p_dist", "rfam_base_centroid_dist", "star3d_base_centroid_dist"]
    with open(path, "w", newline="") as fo:
        fo.write(f"# shared-correspondence anchor fit; rule={rule} flank={flank}; {len(anchors)} anchors {anchors}; "
                 f"fit RMSD {rmsd:.2f} A; source {why_x}; target {why_y}\n")
        w = csv.DictWriter(fo, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in recs:
            w.writerow({k: r.get(k, "NA") for k in fields})
    print(open(path).read())


if __name__ == "__main__":
    main(*sys.argv[1:])
