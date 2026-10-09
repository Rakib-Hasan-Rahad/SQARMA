"""Method-neutral local geometry check for a disagreement region.

Superposes target onto source using ONLY residues where the standard seed and STAR3D agree
(same_partner, both observed, unmasked) — so the fit is not built from either method's disputed
correspondences — then reports, for every source residue in the region, heavy-atom distances to its
seed partner and its STAR3D partner (C1' and base-centroid).
Usage: neutral_fit.py PAIR_ID START END [run_suffix]  -> results/neutral_fit_<pair>_<start>-<end>.tsv
"""
import csv
import os
import sys

import gemmi
import numpy as np

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
BASE_ATOMS = {"N1", "C2", "N3", "C4", "C5", "C6", "N7", "C8", "N9", "O2", "O4", "N4", "O6", "N6", "N2"}


def residues(rep_id):
    cw = {int(r["row_index1"]): r for r in csv.DictReader(open(P("results/residue_crosswalk.tsv")), delimiter="\t")
          if r["rep_id"] == rep_id}
    meta = next(r for r in csv.DictReader(open(P("mappings/aligner_inputs.tsv")), delimiter="\t") if r["rep_id"] == rep_id)
    st = gemmi.read_structure(P(meta["file"]))
    by = {(res.seqid.num, res.seqid.icode.strip()): res for res in st[0][0]}
    out = {}
    for k, r in cw.items():
        if r["observed"] == "yes":
            out[k] = by[(int(r["auth_seq_id"]), "" if r["ins_code"] in ("NA", "") else r["ins_code"])]
    return out


def atom(res, name):
    a = res.find_atom(name, "*")
    return np.array(a.pos.tolist()) if a else None


def base_centroid(res):
    xs = [a.pos.tolist() for a in res if a.name in BASE_ATOMS]
    return np.mean(xs, axis=0) if xs else None


def kabsch(X, Y):
    xc, yc = X.mean(0), Y.mean(0)
    H = (Y - yc).T @ (X - xc)
    U, S, Vt = np.linalg.svd(H)
    d = np.sign(np.linalg.det(Vt.T @ U.T))
    R = Vt.T @ np.diag([1, 1, d]) @ U.T
    return lambda Z: (R @ (Z - yc).T).T + xc


def main(pair_id, start, end):
    start, end = int(start), int(end)
    rows = [r for r in csv.DictReader(open(P("results/correspondence_comparison.tsv")), delimiter="\t")
            if r["pair_id"] == pair_id and r["direction"] == "forward" and r["replicate"] == "1"]
    pair = next(p for p in csv.DictReader(open(P("results/selected_pairs.tsv")), delimiter="\t") if p["pair_id"] == pair_id)
    S, T = residues(pair["query_rep"]), residues(pair["target_rep"])
    anchors = [(int(r["source_row_index"]), int(r["rfam_partner"])) for r in rows if r["category"] == "same_partner"
               and r["source_masked"] == "no" and int(r["source_row_index"]) in S and int(r["rfam_partner"]) in T]
    X, Y = [], []
    for i, j in anchors:
        a, b = atom(S[i], "C1'"), atom(T[j], "C1'")
        if a is not None and b is not None:
            X.append(a)
            Y.append(b)
    X, Y = np.array(X), np.array(Y)
    f = kabsch(X, Y)
    fit_rmsd = float(np.sqrt(((f(Y) - X) ** 2).sum(1).mean()))
    out = []
    for r in rows:
        i = int(r["source_row_index"])
        if not start <= i <= end or i not in S:
            continue
        rec = dict(pair_id=pair_id, source_row_index=i, source_nt=r["source_nt"], category=r["category"],
                   rfam_partner=r["rfam_partner"], star3d_partner=r["star3d_partner"])
        for lab, j in (("rfam", r["rfam_partner"]), ("star3d", r["star3d_partner"])):
            if j != "NA" and int(j) in T:
                tj = T[int(j)]
                a_t, a_s = atom(tj, "C1'"), atom(S[i], "C1'")
                b_t, b_s = base_centroid(tj), base_centroid(S[i])
                if a_t is not None and a_s is not None:     # missing atoms -> NA, never imputed
                    rec[f"{lab}_C1p_dist"] = round(float(np.linalg.norm(f(a_t[None])[0] - a_s)), 2)
                if b_t is not None and b_s is not None:
                    rec[f"{lab}_base_centroid_dist"] = round(float(np.linalg.norm(f(b_t[None])[0] - b_s)), 2)
        out.append(rec)
    path = P(f"results/neutral_fit_{pair_id}_{start}-{end}.tsv")
    fields = ["pair_id", "source_row_index", "source_nt", "category", "rfam_partner", "star3d_partner",
              "rfam_C1p_dist", "star3d_C1p_dist", "rfam_base_centroid_dist", "star3d_base_centroid_dist"]
    with open(path, "w", newline="") as fo:
        fo.write(f"# fit: C1' of {len(X)} agreed residue pairs (both methods same partner): {anchors}; fit RMSD {fit_rmsd:.2f} A\n")
        w = csv.DictWriter(fo, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow({k: r.get(k, "NA") for k in fields})
    for line in open(path):
        f_ = line.rstrip("\n").split("\t")
        print(line.rstrip()[:160] if line.startswith("#") else "  ".join(f"{x:>8}" for x in f_[1:]))


if __name__ == "__main__":
    main(*sys.argv[1:4])
