"""v3 (2026-10-09) candidate update for RF00522 / 7REX. Reads retained, re-verified tables only; writes
deliverables/2026-10-09/tables/candidate_7REX_*.tsv. The adjusted row is EXPLORATORY (designed on these data)."""
import csv
import os
import sys
from collections import defaultdict

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
sys.path.insert(0, P("scripts"))
import interactions  # noqa: E402
OUT = P("deliverables", "2026-10-09", "tables")
PAIRS = ["RF00522__6VUI_A__7REX_A", "RF00522__3FU2_A__7REX_A"]
CLASSES = ("all", "canonical", "wobble", "noncanonical", "stack")


def R(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))


def W(name, rows, fields=None):
    fields = fields or list(rows[0].keys())
    with open(os.path.join(OUT, name), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) in (None, "") else r[k]) for k in fields})


def ann(rep):
    d = {}
    for r in R(P("annotations/normalized", f"{rep}.tsv")):
        d[(int(r["i"]), int(r["j"]))] = r
    return d


def main():
    os.makedirs(OUT, exist_ok=True)
    cw = defaultdict(dict)
    for r in R(P("results/residue_crosswalk.tsv")):
        cw[r["rep_id"]][int(r["row_index1"])] = r
    inter = R(P("review/candidate_RF00522/adjustment_interactions.tsv"))
    corr, counts, excluded, seedbetter = [], [], [], []
    for pid in PAIRS:
        fam, q, t = pid.split("__")
        qrep, trep = f"{fam}__{q}", f"{fam}__{t}"
        ev = R(P("review/candidate_RF00522", f"residue_evidence_{pid}.tsv"))
        A_t = ann(trep)
        rows = [x for x in inter if x["pair_id"] == pid]
        # ---- forward (source = q): identical three-way set, from the retained & re-run candidate table
        for cls in CLASSES:
            sel = [x for x in rows if x["eligible_all_three"] == "yes" and (cls == "all" or x["pair_class"] == cls)]
            counts.append(dict(pair=pid, source=q, direction="source_to_7REX", comparison="seed_vs_adjusted_vs_star3d_forward",
                               **{"class": cls}, eligible_n=len(sel),
                               rfam_preserved=sum(x["rfam_status"] == "exact_class_preserved" for x in sel),
                               star3d_preserved=sum(x["star3d_forward_status"] == "exact_class_preserved" for x in sel),
                               adjusted_preserved=sum(x["adjusted_status"] == "exact_class_preserved" for x in sel),
                               source_interactions_total=sum(cls == "all" or x["pair_class"] == cls for x in rows)))
        for x in rows:
            if x["eligible_all_three"] != "yes":
                excluded.append(dict(pair=pid, interaction=f"{x['label']}({x['i']}-{x['j']})", pair_class=x["pair_class"],
                                     exclusion=x["exclusion"], rfam=x["rfam_status"], adjusted=x["adjusted_status"],
                                     star3d=x["star3d_forward_status"]))
            r_ok = x["rfam_status"] == "exact_class_preserved"
            s_ok = x["star3d_forward_status"] == "exact_class_preserved"
            a_ok = x["adjusted_status"] == "exact_class_preserved"
            if r_ok != s_ok or r_ok != a_ok:
                seedbetter.append(dict(pair=pid, interaction=f"{x['label']}({x['i']}-{x['j']})", pair_class=x["pair_class"],
                                       eligible_all_three=x["eligible_all_three"],
                                       preserved_by=",".join(m for m, ok in (("seed", r_ok), ("adjusted", a_ok), ("star3d", s_ok)) if ok) or "none",
                                       seed_target=x["rfam_target"], adjusted_target=x["adjusted_target"],
                                       star3d_target=x["star3d_forward_target"]))
        # ---- correspondence table (per source residue)
        for e in ev:
            i = int(e["source_row_index"])
            ints = [x for x in rows if int(x["i"]) == i or int(x["j"]) == i]
            def lab(m):
                return "; ".join(f"{x['label']}({x['i']}-{x['j']})->{x[m + '_target']}:{x[m + '_status']}" for x in ints) or "NA"
            corr.append(dict(pair=pid, source_residue=f"{q.split('_')[0]}:{e['source_auth']}{e['source_nt']}",
                             seed_column=e["seed_column"], rfam_partner=e["rfam_partner"], star3d_partner=e["star3d_fwd_partner"],
                             star3d_reverse_partner=e["star3d_rev_partner"], adjusted_partner=e["adjusted_partner"],
                             category=e["category"], rfam_annotation=lab("rfam"), star3d_annotation=lab("star3d_forward"),
                             adjusted_annotation=lab("adjusted")))
        # ---- reciprocal: source = 7REX interactions mapped back to q by the inverted (injective) mappings,
        #      scored with the pipeline's own method_status/comparison_eligibility (scripts/interactions.py)
        def inv(col):
            fwd = {}
            for e in ev:
                v = e[col]
                digits = "".join(ch for ch in v if ch.isdigit())
                if digits:
                    fwd[int(e["source_row_index"])] = int(digits)
            return interactions.invert_injective(fwd, f"{pid} {col}")
        maps = {"rfam": inv("rfam_partner"), "adjusted": inv("adjusted_partner"), "star3d": inv("star3d_fwd_partner")}
        tix = defaultdict(set)
        for (i, j), b in ann(qrep).items():
            tix[(i, j)].add(b["label"])
        tobs = {k for k, c in cw[qrep].items() if c["observed"] == "yes"}
        tmask = {k for k, c in cw[qrep].items() if c["engineered_masked"] == "yes"}
        smask = {k for k, c in cw[trep].items() if c["engineered_masked"] == "yes" or c["observed"] != "yes"}
        recs = []
        for (i, j), a in A_t.items():
            s_ = dict(i=i, j=j, label=a["label"])
            per = {m: interactions.method_status(s_, mp, tix, tobs, tmask) for m, mp in maps.items()}
            ok, why = interactions.comparison_eligibility("yes" if (i in smask or j in smask) else "no", per, list(maps))
            recs.append((a, {m: per[m]["status"] for m in maps}, ok))
        for cls in CLASSES:
            sel = [(a, st) for a, st, e in recs if e and (cls == "all" or a["pair_class"] == cls)]
            counts.append(dict(pair=pid, source="7REX_A", direction=f"7REX_to_{q}", comparison="seed_vs_adjusted_vs_star3d_forward_inverted",
                               **{"class": cls}, eligible_n=len(sel),
                               rfam_preserved=sum(st["rfam"] == "exact_class_preserved" for _, st in sel),
                               star3d_preserved=sum(st["star3d"] == "exact_class_preserved" for _, st in sel),
                               adjusted_preserved=sum(st["adjusted"] == "exact_class_preserved" for _, st in sel),
                               source_interactions_total=sum(cls == "all" or a["pair_class"] == cls for a, _, _ in recs)))
    W("candidate_7REX_correspondence.tsv", corr)
    W("candidate_7REX_counts.tsv", counts)
    W("candidate_7REX_excluded_from_common_set.tsv", excluded)
    W("candidate_7REX_method_differences.tsv", seedbetter)
    for c in counts:
        if c["class"] == "all":
            print(c)


if __name__ == "__main__":
    main()
