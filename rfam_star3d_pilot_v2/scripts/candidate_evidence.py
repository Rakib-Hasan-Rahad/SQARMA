"""Section 7/9 (v2.1): residue-level evidence for the RF00522 7REX-row candidate, ligand context, and validation
of an EXPLORATORY local adjustment of the 7REX row. Never modifies Rfam.seed.gz.

Outputs (review/candidate_RF00522/):
  structure_facts.tsv           per RNA: deposited seq, interval, row id, missing/modified residues, source evidence,
                                ligands and residues within 4.0 A of each ligand (heavy atoms, model 1)
  numbering_chain.tsv           seed column -> row index -> mmCIF label_seq_id -> author residue, per RNA
  p1_raw_fr3d_lines.txt         raw FR3D lines (unnormalized) for the five 6VUI P1 pairs and both 7REX registers
  residue_evidence_<pair>.tsv   per source residue: column, Rfam / STAR3D fwd / STAR3D rev / adjusted partners,
                                source FR3D interactions and their preservation under each mapping, anchor distances
  adjustment_validation.json    checks on the proposed shifted 7REX row
  adjustment_interactions.tsv   preservation on IDENTICAL eligible sets: seed vs adjusted vs STAR3D forward
"""
import csv
import gzip
import json
import os
import sys
from collections import defaultdict

import gemmi

sys.path.insert(0, os.path.dirname(__file__))
import interactions as it  # noqa: E402
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
OUT = P("review/candidate_RF00522")
FAM = "RF00522"
REPS = {"3FU2_A": "RF00522__3FU2_A", "6VUI_A": "RF00522__6VUI_A", "7REX_A": "RF00522__7REX_A"}
PAIRS = ["RF00522__6VUI_A__7REX_A", "RF00522__3FU2_A__7REX_A"]
SHIFT = dict(row="URS00023119CB_2126436/1-34", residues=(15, 22), delta=-1)   # proposal: 7REX A15..A22 one column left
IONS = {"MG", "MN", "CA", "NA", "K", "ZN", "CL", "SO4", "HOH"}


def R(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))


def W(path, rows, fields=None):
    fields = fields or list(rows[0].keys())
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) in (None, "") else r[k]) for k in fields})


def shifted_row(s, lo, hi, delta):
    """Move residues lo..hi (1-based row indices) by `delta` columns; refuse if a target column is occupied by a
    residue outside the moved block."""
    cols = stockholm.residue_columns(s)
    moved = {cols[k - 1]: cols[k - 1] + delta for k in range(lo, hi + 1)}
    chars = list(s)
    block = {c: s[c] for c in moved}
    for c in moved:
        chars[c] = "-"
    for c, nc in moved.items():
        if chars[nc] not in "-.":
            raise SystemExit(f"column {nc + 1} already holds a residue; adjustment invalid")
        chars[nc] = block[c]
    return "".join(chars)


def ligand_contacts(pdb, chain, cutoff=4.0):
    st = gemmi.read_structure(P("inputs/structures/mmcif", f"{pdb}.cif.gz"))
    st.remove_hydrogens()
    model = st[0]
    ns = gemmi.NeighborSearch(model, st.cell, 5).populate()
    out = defaultdict(set)
    for ch in model:
        for res in ch:
            if res.het_flag != "H" or res.name in ("HOH",):
                continue
            for a in res:
                for m in ns.find_atoms(a.pos, "\0", radius=cutoff):
                    cra = m.to_cra(model)
                    if cra.chain.name == chain and cra.residue.het_flag != "H":
                        out[f"{res.name}{res.seqid.num}"].add(cra.residue.seqid.num)
    return {k: sorted(v) for k, v in out.items()}


def main():
    os.makedirs(OUT, exist_ok=True)
    seed = next(stockholm.parse(P("inputs/rfam/15.1/Rfam.seed.gz"), only={FAM}))
    links = {f"{r['pdb_id']}_{r['chain_token']}": r for r in R(P("mappings/structure_sequence_map.tsv"))
             if r["link_basis"] == "explicit_GR_feature"}
    exact = {r["key"]: r for r in R(P("review/exact_source_check.tsv"))}
    cw = defaultdict(dict)
    for r in R(P("results/residue_crosswalk.tsv")):
        cw[r["rep_id"]][int(r["row_index1"])] = r
    import yaml
    dec = yaml.safe_load(open(P("review/decisions.yaml")))["families"][FAM]["representatives"]

    # ---- structure facts + numbering chain
    facts, chain_rows = [], []
    for key, rid in REPS.items():
        L = links[key]
        d = next(x for x in dec if x["key"] == key)
        lig = ligand_contacts(L["pdb_id"], L["auth_asym_id"])
        facts.append(dict(
            key=key, rep_id=rid, deposited_seq=L["deposited_seq_parent_mapped"], deposited_len=L["deposited_len"],
            family_interval_label=f"{L['family_label_seq_start']}-{L['family_label_seq_end']}",
            seed_row=L["row_name"], seed_row_lines=L["seed_row_lines"],
            missing_residues_label=L["missing_residue_seq_ids"] or "none",
            incomplete_backbone_label=L["incomplete_backbone_seq_ids"] or "none",
            modified_residues=L["modified_residues"] or "none (confirmed absent in mmCIF poly_seq_scheme)",
            source_literature=d.get("source"), exact_source_genome=f"{exact[key]['accession']} "
            f"{exact[key]['verdict']} at {exact[key]['family_interval_exact_hits']}",
            construct_vs_native="identical to native locus over full deposited length"
            if exact[key]["deposited_full_exact_hits"] != "none" else "differs from native",
            method_resolution=f"{L['exptl_method']} {L['resolution']}", ligands_mmCIF=L["ligands"],
            ligand_contacts_4A=json.dumps(lig)))
        for k, r in sorted(cw[rid].items()):
            chain_rows.append(dict(rep_id=rid, original_column=r["original_column"], row_index=k, row_nt=r["row_nt"],
                                   label_seq_id=r["label_seq_id"], auth=f"{r['auth_asym_id']}:{r['auth_seq_id']}",
                                   observed=r["observed"], comp_id=r["comp_id"]))
    W(os.path.join(OUT, "structure_facts.tsv"), facts)
    W(os.path.join(OUT, "numbering_chain.tsv"), chain_rows)

    # ---- raw FR3D lines for the P1 pairs (no normalization)
    with open(os.path.join(OUT, "p1_raw_fr3d_lines.txt"), "w") as f:
        for pdb, pairs_ in (("6VUI", [(1, 20), (2, 19), (3, 18), (4, 17), (5, 16)]),
                            ("7REX", [(1, 21), (2, 20), (3, 19), (4, 18), (5, 17), (1, 22), (2, 21), (3, 20), (4, 19), (5, 18)])):
            raw = open(P("annotations/raw", f"{pdb}_basepair.txt")).read().splitlines()
            for i, j in pairs_:
                hits = [l for l in raw if l.split("\t")[0].split("|")[4] == str(i) and l.split("\t")[2].split("|")[4] == str(j)]
                f.write(f"{pdb} {i}-{j}: " + (" | ".join(hits) if hits else "NO raw FR3D line") + "\n")

    # ---- exploratory adjustment of the 7REX row
    orig = seed.seqs[SHIFT["row"]]
    adj = shifted_row(orig, *SHIFT["residues"], SHIFT["delta"])
    oc, ac = stockholm.residue_columns(orig), stockholm.residue_columns(adj)
    ss = seed.gc["SS_cons"]
    checks = dict(
        nucleotides_preserved=stockholm.split_name and orig.replace("-", "").replace(".", "") == adj.replace("-", "").replace(".", ""),
        order_preserved=all(a < b for a, b in zip(ac, ac[1:])),
        width_unchanged=len(orig) == len(adj),
        columns_changed=[f"res{k + 1}:{oc[k] + 1}->{ac[k] + 1}" for k in range(len(oc)) if oc[k] != ac[k]],
        adjusted_row=adj, original_row=orig)
    pairs_ss = []
    stack = []
    for i, c in enumerate(ss):
        if c == "<":
            stack.append(i)
        elif c == ">":
            pairs_ss.append((stack.pop(), i))
    WC = {"AU", "UA", "GC", "CG", "GU", "UG"}
    checks["sscons_P1_pairs_original"] = [f"{orig[i]}{orig[j]}{'' if (orig[i] + orig[j]) in WC else '(nonWC)'}" for i, j in sorted(pairs_ss)]
    checks["sscons_P1_pairs_adjusted"] = [f"{adj[i]}{adj[j]}{'' if (adj[i] + adj[j]) in WC else '(nonWC)'}" for i, j in sorted(pairs_ss)]
    checks["column_24_RF"] = seed.gc["RF"][23]
    checks["other_rows_in_moved_columns"] = {n: s[23:32] for n, s in seed.seqs.items()
                                             if n in (links["6VUI_A"]["row_name"], links["3FU2_A"]["row_name"])}

    # ---- residue evidence + interaction preservation with the adjusted mapping
    comp = [r for r in R(P("results/correspondence_comparison.tsv")) if r["replicate"] == "1"]
    inter_rows = []
    fit = {}
    for rule in ("shared", "shared_flank_excl"):
        for pid, rng in (("RF00522__6VUI_A__7REX_A", "7-23"), ("RF00522__3FU2_A__7REX_A", "9-22")):
            path = P(f"results/anchor_fit/{pid}_{rng}_{rule}.tsv")
            if os.path.exists(path):
                for r in csv.DictReader([l for l in open(path) if not l.startswith("#")], delimiter="\t"):
                    fit[(pid, rule, int(r["source_row_index"]))] = r
    for pid in PAIRS:
        src_key = pid.split("__")[1]
        src_row = links[src_key]["row_name"]
        s_aln = seed.seqs[src_row]
        adj_map = {a + 1: b + 1 for a, b in stockholm.pairwise_correspondence(s_aln, adj)}
        assert len(set(adj_map.values())) == len(adj_map), "adjusted mapping not one-to-one"
        rows = {int(r["source_row_index"]): r for r in comp if r["pair_id"] == pid and r["direction"] == "forward"}
        rrev = {int(r["source_row_index"]): r for r in comp if r["pair_id"] == pid and r["direction"] == "reverse"}
        src_rep, tgt_rep = REPS[src_key], REPS["7REX_A"]
        ann_s = R(P("annotations/normalized", f"{src_rep}.tsv"))
        ann_t = R(P("annotations/normalized", f"{tgt_rep}.tsv"))
        tix = defaultdict(set)
        for t in ann_t:
            tix[(int(t["i"]), int(t["j"]))].add(t["label"])
        tobs = {k for k, r in cw[tgt_rep].items() if r["observed"] == "yes"}
        tmask = {k for k, r in cw[tgt_rep].items() if r["engineered_masked"] == "yes"}
        maps = {"rfam": {i: int(r["rfam_partner"]) for i, r in rows.items() if r["rfam_partner"] != "NA"},
                "adjusted": adj_map,
                "star3d_forward": {i: int(r["star3d_partner"]) for i, r in rows.items() if r["star3d_partner"] != "NA"}}
        per_int = []
        for s in ann_s:
            s2 = dict(i=int(s["i"]), j=int(s["j"]), label=s["label"])
            st = {m: it.method_status(s2, mp, tix, tobs, tmask) for m, mp in maps.items()}
            ok, why = it.comparison_eligibility("no", st, tuple(maps))
            per_int.append(dict(pair_id=pid, i=s2["i"], j=s2["j"], label=s2["label"], pair_class=s["pair_class"],
                                **{f"{m}_target": f"{v['a']}-{v['b']}" for m, v in st.items()},
                                **{f"{m}_status": v["status"] for m, v in st.items()},
                                eligible_all_three=("yes" if ok else "no"), exclusion=None if ok else why))
        inter_rows += per_int
        ev = []
        for i, r in sorted(rows.items()):
            mine = [x for x in per_int if i in (x["i"], x["j"])]
            ev.append(dict(
                source=src_key, source_row_index=i, source_nt=r["source_nt"], source_auth=r["source_auth"],
                seed_column=r["original_column"],
                rfam_partner=f"{r['rfam_partner_nt']}{r['rfam_partner']}" if r["rfam_partner"] != "NA" else "gap",
                star3d_fwd_partner=f"{r['star3d_partner_nt']}{r['star3d_partner']}" if r["star3d_partner"] != "NA" else "none",
                star3d_rev_partner=(rrev[i]["star3d_partner"] if i in rrev else "NA"),
                adjusted_partner=adj_map.get(i, "gap"), category=r["category"],
                source_interactions=" ".join(f"{x['label']}({x['i']}-{x['j']},{x['pair_class'][:5]}):R={x['rfam_status'][:5]}/A={x['adjusted_status'][:5]}/S={x['star3d_forward_status'][:5]}"
                                             for x in mine),
                C1p_rfam_shared=fit.get((pid, "shared", i), {}).get("rfam_C1p_dist"),
                C1p_star3d_shared=fit.get((pid, "shared", i), {}).get("star3d_C1p_dist"),
                C1p_rfam_flankexcl=fit.get((pid, "shared_flank_excl", i), {}).get("rfam_C1p_dist"),
                C1p_star3d_flankexcl=fit.get((pid, "shared_flank_excl", i), {}).get("star3d_C1p_dist")))
        W(os.path.join(OUT, f"residue_evidence_{pid}.tsv"), ev)
    W(os.path.join(OUT, "adjustment_interactions.tsv"), inter_rows)
    summ = []
    for pid in PAIRS:
        for cls in ("all", "canonical", "wobble", "noncanonical", "stack"):
            el = [x for x in inter_rows if x["pair_id"] == pid and x["eligible_all_three"] == "yes"
                  and (cls == "all" or x["pair_class"] == cls)]
            summ.append(dict(pair_id=pid, interaction_class=cls, eligible_same_set=len(el),
                             **{f"{m}_preserved": sum(x[f"{m}_status"] == "exact_class_preserved" for x in el)
                                for m in ("rfam", "adjusted", "star3d_forward")}))
    W(os.path.join(OUT, "adjustment_interaction_summary.tsv"), summ)
    # damage check: interactions preserved by the seed but NOT by the adjusted mapping
    checks["interactions_lost_by_adjustment"] = [f"{x['pair_id']}:{x['label']}({x['i']}-{x['j']})" for x in inter_rows
                                                 if x["eligible_all_three"] == "yes" and x["rfam_status"] == "exact_class_preserved"
                                                 and x["adjusted_status"] != "exact_class_preserved"]
    checks["mapping_one_to_one"] = True
    json.dump(checks, open(os.path.join(OUT, "adjustment_validation.json"), "w"), indent=1)
    for s in summ:
        print(s)
    print(json.dumps({k: v for k, v in checks.items() if k not in ("adjusted_row", "original_row")}, indent=1))


if __name__ == "__main__":
    main()
