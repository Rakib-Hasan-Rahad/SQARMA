"""Phase 5: FR3D evaluation annotations and interaction-preservation comparison.

Evaluation annotations: fr3d-python (commit pinned in config), categories basepair+stacking, run on the
unchanged RCSB mmCIF (model 1 kept; other models/chains ignored after annotation). These are distinct
from STAR3D's own preprocessing annotations (MC-Annotate WWc pairs), but both describe canonical pairs,
so canonical-pair preservation is NOT independent validation of STAR3D.

Normalization: one record per unordered intrachain pair, ordered by row index (i<j); when an FR3D line
is reversed the two edge letters are swapped (e.g. tSH <-> tHS) and s35 <-> s53.
Canonical = cWW with identities AU/UA/GC/CG; cWW GU/UG = 'wobble'; everything else 'noncanonical'.

Outputs: annotations/normalized/<rep>.tsv, results/interaction_comparison.tsv, results/interaction_summary.tsv
Usage: interactions.py [pair_id ...]
"""
import csv
import gzip
import os
import subprocess
import sys
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))
CANON = {("A", "U"), ("U", "A"), ("G", "C"), ("C", "G")}
WOBBLE = {("G", "U"), ("U", "G")}


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def write_tsv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) is None or r.get(k) == "" else r[k]) for k in fields})


def reverse_label(label):
    """Reverse an FR3D interaction label for swapped endpoints."""
    neg = label.startswith("n")
    core = label[1:] if neg else label
    if core in ("s35", "s53"):
        core = "s53" if core == "s35" else "s35"
    elif len(core) == 3 and core[0] in "ct" and core[1] in "WHS" and core[2] in "WHS":
        core = core[0] + core[2] + core[1]
    elif len(core) == 4 and core[0] in "ct" and core[1] in "WHS" and core[2] in "WHSa" :
        core = core[0] + core[2] + core[1] + core[3:]
    return ("n" if neg else "") + core


def parse_unit(u):
    f = u.split("|")
    icode = f[7] if len(f) > 7 and f[7] else ""
    return dict(pdb=f[0], model=int(f[1]), chain=f[2], comp=f[3], num=int(f[4]), icode=icode)


def annotate(pdb):
    raw = P("annotations/raw", f"{pdb}_basepair.txt")
    if not os.path.exists(raw):
        os.makedirs(P("annotations/_cif"), exist_ok=True)
        cif = P("annotations/_cif", f"{pdb}.cif")
        with gzip.open(P("inputs/structures/mmcif", f"{pdb}.cif.gz"), "rb") as fi, open(cif, "wb") as fo:
            fo.write(fi.read())
        cmd = [sys.executable, "-m", "fr3d.classifiers.NA_pairwise_interactions", "-i", P("annotations/_cif"),
               "-o", P("annotations/raw"), "-c", "basepair,stacking", f"{pdb}.cif"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        open(P("annotations/raw", f"{pdb}.log"), "w").write(" ".join(cmd) + "\n" + p.stdout + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"FR3D failed for {pdb}")
    return [P("annotations/raw", f"{pdb}_basepair.txt"), P("annotations/raw", f"{pdb}_stacking.txt")]


def normalized(rep_id, rep, cw):
    """Intrachain interactions with both endpoints in the row interval, model 1, normalized."""
    by_auth = {(r["auth_asym_id"], int(r["auth_seq_id"]), "" if r["ins_code"] in ("NA", "") else r["ins_code"]): int(r["row_index1"])
               for r in cw.values() if r["observed"] == "yes"}
    nt = {int(r["row_index1"]): r["parent_nt"] for r in cw.values()}
    out, interchain, seen = [], 0, set()
    for path in annotate(rep["pdb_id"]):
        for line in open(path):
            f = line.rstrip("\n").split("\t")
            if len(f) < 3:
                continue
            u1, lab, u2 = parse_unit(f[0]), f[1], parse_unit(f[2])
            if u1["model"] != 1 or u2["model"] != 1:
                continue
            ch = rep["auth_asym_id"]
            if (u1["chain"] == ch) != (u2["chain"] == ch):
                interchain += 1
                continue
            if u1["chain"] != ch:
                continue
            i = by_auth.get((ch, u1["num"], u1["icode"]))
            j = by_auth.get((ch, u2["num"], u2["icode"]))
            if i is None or j is None:
                continue
            if i > j:
                i, j, lab = j, i, reverse_label(lab)
            key = (i, j, lab)
            if key in seen:
                continue
            seen.add(key)
            kind = "stack" if lab.lstrip("n").startswith("s") else "basepair"
            if kind == "basepair" and lab == "cWW" and (nt[i], nt[j]) in CANON:
                cls = "canonical"
            elif kind == "basepair" and lab == "cWW" and (nt[i], nt[j]) in WOBBLE:
                cls = "wobble"
            elif kind == "basepair":
                cls = "noncanonical"
            else:
                cls = "stack"
            out.append(dict(rep_id=rep_id, i=i, j=j, label=lab, kind=kind, pair_class=cls,
                            nt_i=nt[i], nt_j=nt[j], crossing=f[3] if len(f) > 3 else None))
    write_tsv(P("annotations/normalized", f"{rep_id}.tsv"), out,
              ["rep_id", "i", "j", "label", "kind", "pair_class", "nt_i", "nt_j", "crossing"])
    return out, interchain


def primary_replicates(comp):
    """(pair_id, direction) -> lowest-numbered replicate whose run completed (failed replicates stay in tables)."""
    ok = {}
    for r in comp:
        if r["category"] != "technical_failure_or_no_alignment":
            key = (r["pair_id"], r["direction"])
            ok[key] = min(ok.get(key, 99), int(r["replicate"]))
    return ok


def main(only):
    reps = {r["rep_id"]: r for r in read_tsv(P("results/selected_representatives.tsv"))}
    pairs = [p for p in read_tsv(P("results/selected_pairs.tsv")) if not only or p["pair_id"] in only]
    cw = defaultdict(dict)
    for r in read_tsv(P("results/residue_crosswalk.tsv")):
        cw[r["rep_id"]][int(r["row_index1"])] = r
    comp_all = read_tsv(P("results/correspondence_comparison.tsv"))
    prim = primary_replicates(comp_all)
    comp = [r for r in comp_all if prim.get((r["pair_id"], r["direction"])) == int(r["replicate"])]
    ann, interch = {}, {}
    rows, summ = [], []
    for p in pairs:
        for rid in (p["query_rep"], p["target_rep"]):
            if rid not in ann:
                ann[rid], interch[rid] = normalized(rid, reps[rid], cw[rid])
        fwd = {int(r["source_row_index"]): r for r in comp if r["pair_id"] == p["pair_id"] and r["direction"] == "forward"}
        rev = {int(r["source_row_index"]): r for r in comp if r["pair_id"] == p["pair_id"] and r["direction"] == "reverse"}
        maps = {
            "rfam": {i: int(r["rfam_partner"]) for i, r in fwd.items() if r["rfam_partner"] != "NA"},
            "star3d_forward": {i: int(r["star3d_partner"]) for i, r in fwd.items() if r["star3d_partner"] != "NA"},
            "star3d_reverse": {i: int(r["star3d_partner"]) for i, r in rev.items() if r["star3d_partner"] != "NA"},
        }
        for src_side in ("query", "target"):
            src = p["query_rep"] if src_side == "query" else p["target_rep"]
            tgt = p["target_rep"] if src_side == "query" else p["query_rep"]
            m = maps if src_side == "query" else {k: {b: a for a, b in v.items()} for k, v in maps.items()}
            tix = defaultdict(set)
            for t in ann[tgt]:
                tix[(t["i"], t["j"])].add(t["label"])
            tobs = {k for k, r in cw[tgt].items() if r["observed"] == "yes"}
            tmask = {k for k, r in cw[tgt].items() if r["engineered_masked"] == "yes"}
            smask = {k for k, r in cw[src].items() if r["engineered_masked"] == "yes"}
            per = defaultdict(dict)
            for s in ann[src]:
                for meth, mp in m.items():
                    a, b = mp.get(s["i"]), mp.get(s["j"])
                    if a is None or b is None:
                        st = "unmapped_endpoint"
                    elif a not in tobs or b not in tobs:
                        st = "target_endpoint_unobserved"
                    else:
                        x, y = (a, b) if a < b else (b, a)
                        lab = s["label"] if a < b else reverse_label(s["label"])
                        labs = tix.get((x, y), set())
                        st = "exact_class_preserved" if lab in labs else ("different_class" if labs else "no_annotated_target_pair")
                    per[(s["i"], s["j"], s["label"])][meth] = (st, a, b)
            for (i, j, lab), d in per.items():
                s = next(x for x in ann[src] if (x["i"], x["j"], x["label"]) == (i, j, lab))
                assess = {k: v[0] not in ("unmapped_endpoint", "target_endpoint_unobserved") for k, v in d.items()}
                rows.append(dict(pair_id=p["pair_id"], source_side=src_side, source_rep=src, target_rep=tgt, i=i, j=j,
                                 label=lab, pair_class=s["pair_class"], kind=s["kind"],
                                 source_masked="yes" if (i in smask or j in smask) else "no",
                                 **{f"{k}_status": v[0] for k, v in d.items()},
                                 **{f"{k}_target": f"{v[1]}-{v[2]}" for k, v in d.items()},
                                 common_assessable_rfam_vs_star3d_forward="yes" if assess["rfam"] and assess["star3d_forward"] else "no",
                                 target_masked_rfam="yes" if (d["rfam"][1] in tmask or d["rfam"][2] in tmask) else "no",
                                 reference_source="Rfam.seed.gz", rfam_release=CFG["reference"]["rfam_release"]))
            sel = [r for r in rows if r["pair_id"] == p["pair_id"] and r["source_side"] == src_side]
            for cls in ("all", "canonical", "wobble", "noncanonical", "stack"):
                for masked_ok in ("all", "unmasked_only"):
                    ss = [r for r in sel if (cls == "all" or r["pair_class"] == cls)
                          and (masked_ok == "all" or (r["source_masked"] == "no" and r["target_masked_rfam"] == "no"))]
                    common = [r for r in ss if r["common_assessable_rfam_vs_star3d_forward"] == "yes"]
                    summ.append(dict(
                        pair_id=p["pair_id"], source_side=src_side, interaction_class=cls, masking=masked_ok,
                        source_interactions=len(ss),
                        rfam_assessable=sum(r["rfam_status"] not in ("unmapped_endpoint", "target_endpoint_unobserved") for r in ss),
                        star3d_fwd_assessable=sum(r["star3d_forward_status"] not in ("unmapped_endpoint", "target_endpoint_unobserved") for r in ss),
                        rfam_preserved_all=sum(r["rfam_status"] == "exact_class_preserved" for r in ss),
                        star3d_fwd_preserved_all=sum(r["star3d_forward_status"] == "exact_class_preserved" for r in ss),
                        common_assessable=len(common),
                        rfam_preserved_common=sum(r["rfam_status"] == "exact_class_preserved" for r in common),
                        star3d_fwd_preserved_common=sum(r["star3d_forward_status"] == "exact_class_preserved" for r in common),
                        star3d_rev_preserved_common=sum(r["star3d_reverse_status"] == "exact_class_preserved" for r in common),
                        interchain_lines_excluded=interch[src]))
    fields = list(rows[0].keys())
    write_tsv(P("results/interaction_comparison.tsv"), rows, fields)
    write_tsv(P("results/interaction_summary.tsv"), summ, list(summ[0].keys()))
    for s in summ:
        if s["masking"] == "unmasked_only" and s["interaction_class"] in ("all", "noncanonical"):
            print(s["pair_id"], s["source_side"], s["interaction_class"], "n", s["source_interactions"], "common",
                  s["common_assessable"], "rfam", s["rfam_preserved_common"], "star3d", s["star3d_fwd_preserved_common"])


if __name__ == "__main__":
    main(sys.argv[1:])
