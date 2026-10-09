"""Survey B (v3, auxiliary; never modifies the primary baseline): ordinary Rfam.seed.gz vs structure-curated
Rfam.3d.seed.gz, BOTH from the Rfam 15.1 release directory. Compares residue correspondences of shared rows (not raw
column numbers), plus GF/GS/GR/GC annotations. Outputs: results/seed_collection_comparison/
  family_overlap.tsv, shared_rows.tsv, correspondence_differences.tsv, annotation_differences.tsv, provenance.json
Usage: survey_b.py"""
import csv
import hashlib
import itertools
import json
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
ORD = P("inputs/rfam/15.1/Rfam.seed.gz")
CUR = P("inputs/rfam_survey_b/Rfam.3d.seed.gz")
OUT = P("results/seed_collection_comparison")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def W(name, rows, fields):
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) in (None, "") else r[k]) for k in fields})


def corr(a, b):
    """Residue correspondences of two gapped rows: {(i, j)} for columns holding residues in both (1-based)."""
    out, ia, ib = set(), 0, 0
    for x, y in zip(a, b):
        ra, rb = x not in "-.", y not in "-."
        ia += ra
        ib += rb
        if ra and rb:
            out.add((ia, ib))
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    cur = {a.acc: a for a in stockholm.parse(CUR)}
    ordn_all = {}
    n_ord = 0
    for a in stockholm.parse(ORD):
        n_ord += 1
        if a.acc in cur:
            ordn_all[a.acc] = a
    fam, shared, cdiff, adiff = [], [], [], []
    for acc in sorted(set(cur) | set(ordn_all)):
        c, o = cur.get(acc), ordn_all.get(acc)
        sh = sorted(set(c.seqs) & set(o.seqs)) if c and o else []
        same_seq = [n for n in sh if c.ungapped(n) == o.ungapped(n)]
        n_changed_pairs = n_pairs = 0
        for n in sh:
            shared.append(dict(family=acc, row=n, ungapped_identical=c.ungapped(n) == o.ungapped(n),
                               aligned_identical=c.seqs[n] == o.seqs[n],
                               gr_features_ordinary=";".join(o.gr.get(n, {})), gr_features_curated=";".join(c.gr.get(n, {}))))
        # pairwise residue correspondences among shared identical-sequence rows (aligned-identical rows are skipped
        # only after confirming identity implies identical correspondences)
        diff_rows = [n for n in same_seq if c.seqs[n] != o.seqs[n]]
        for x, y in itertools.combinations(same_seq, 2):
            n_pairs += 1
            if x not in diff_rows and y not in diff_rows:
                continue          # both gapped strings identical -> correspondences identical by construction
            co, cc = corr(o.seqs[x], o.seqs[y]), corr(c.seqs[x], c.seqs[y])
            if co != cc:
                n_changed_pairs += 1
                mo, mc = dict(co), dict(cc)
                cdiff.append(dict(family=acc, row_a=x, row_b=y, same=len(co & cc),
                                  changed_partner=sum(1 for i in mo if i in mc and mo[i] != mc[i]),
                                  residue_gap_changes=len(set(mo) ^ set(mc))))
        # annotations
        for kind, od, cd in (("GC", o.gc, c.gc), ("GF", {k: "\n".join(v) for k, v in o.gf.items()},
                                                   {k: "\n".join(v) for k, v in c.gf.items()})):
            for k in sorted(set(od) | set(cd)):
                if od.get(k) != cd.get(k):
                    adiff.append(dict(family=acc, kind=kind, row="NA", feature=k, in_ordinary=k in od, in_curated=k in cd))
        for n in sh:
            og, cg = o.gr.get(n, {}), c.gr.get(n, {})
            for k in sorted(set(og) | set(cg)):
                if og.get(k) != cg.get(k):
                    adiff.append(dict(family=acc, kind="GR", row=n, feature=k, in_ordinary=k in og, in_curated=k in cg))
        fam.append(dict(family=acc, rfam_id=(c or o).id, in_ordinary=o is not None, in_curated=c is not None,
                        rows_ordinary=len(o.seqs) if o else None, rows_curated=len(c.seqs) if c else None,
                        shared_rows=len(sh), shared_rows_identical_sequence=len(same_seq),
                        shared_rows_aligned_identical=sum(c.seqs[n] == o.seqs[n] for n in sh),
                        width_ordinary=o.width if o else None, width_curated=c.width if c else None,
                        comparable_row_pairs=n_pairs, row_pairs_with_changed_correspondence=n_changed_pairs,
                        rows_only_ordinary=len(set(o.seqs) - set(c.seqs)) if c and o else None,
                        rows_only_curated=len(set(c.seqs) - set(o.seqs)) if c and o else None))
    W("family_overlap.tsv", fam, list(fam[0]))
    W("shared_rows.tsv", shared, list(shared[0]))
    W("correspondence_differences.tsv", cdiff, ["family", "row_a", "row_b", "same", "changed_partner", "residue_gap_changes"])
    W("annotation_differences.tsv", adiff, ["family", "kind", "row", "feature", "in_ordinary", "in_curated"])
    prov = dict(ordinary=dict(path=os.path.relpath(ORD, ROOT), sha256=sha(ORD), release="15.1",
                              url="https://ftp.ebi.ac.uk/pub/databases/Rfam/15.1/Rfam.seed.gz"),
                curated=dict(path=os.path.relpath(CUR, ROOT), sha256=sha(CUR), release="15.1",
                             url="https://ftp.ebi.ac.uk/pub/databases/Rfam/15.1/Rfam.3d.seed.gz",
                             retrieved_utc=open(P("inputs/rfam_survey_b/retrieved_utc.txt")).read().strip()),
                families_ordinary_total=n_ord, families_curated=len(cur),
                families_in_both=sum(f["in_ordinary"] and f["in_curated"] for f in fam),
                families_with_shared_row=sum(f["shared_rows"] > 0 for f in fam),
                families_with_two_shared_identical_rows=sum(f["shared_rows_identical_sequence"] >= 2 for f in fam),
                shared_rows=len(shared), shared_rows_aligned_identical=sum(r["aligned_identical"] for r in shared),
                comparable_row_pairs=sum(f["comparable_row_pairs"] for f in fam),
                row_pairs_with_changed_correspondence=len(cdiff), annotation_differences=len(adiff),
                note="Auxiliary survey; does not modify the primary ordinary-seed baseline.")
    json.dump(prov, open(os.path.join(OUT, "provenance.json"), "w"), indent=1)
    print(json.dumps(prov, indent=1))


if __name__ == "__main__":
    main()
