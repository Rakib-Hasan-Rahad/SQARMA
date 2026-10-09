"""v4: uniform evidence extraction for EVERY region in results/region_review.tsv (no interpretation is written here).
Per region: span eligibility flags; per-residue Rfam / STAR3D forward / STAR3D reverse partners; FR3D interactions
touching the span, per class, on the rfam-vs-STAR3D-forward eligible set; shared-correspondence anchor fits under
three anchor rules (C1' and base-centroid distances); ligand, other-chain and crystal-symmetry contacts (<= 4 A)
of the source span and both partner sets; missing coordinates.
Outputs: results/region_evidence/<region_id>.tsv (per residue) and results/region_evidence/summary.tsv"""
import csv
import gzip
import io
import os
import statistics
import subprocess
import sys
from collections import Counter, defaultdict

import gemmi

ROOT = os.environ.get("SQARMA_STUDY_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # v4: workspace override
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
OUT = P("results", "region_evidence")
WATER = {"HOH", "DOD", "WAT"}


def R(p):
    return list(csv.DictReader(open(P(p), encoding="utf-8"), delimiter="\t"))


def contacts(pdb, chain, cutoff=4.0):
    """auth (num, icode) -> set of contact labels: LIG:<name><num>, CHAIN:<id>, SYM:<op>."""
    st = gemmi.read_structure(io.StringIO(gzip.open(P("inputs/structures/mmcif", f"{pdb}.cif.gz"), "rt").read()).getvalue()
                              if False else P("inputs/structures/mmcif", f"{pdb}.cif.gz"))
    st.setup_entities()
    model = st[0]
    ns = gemmi.NeighborSearch(model, st.cell, 6).populate()
    out = defaultdict(set)
    for res in model[chain]:
        key = (res.seqid.num, res.seqid.icode.strip())
        for at in res:
            for m in ns.find_atoms(at.pos, "\0", radius=cutoff):
                cra = m.to_cra(model)
                if cra.residue.name in WATER:
                    continue
                if m.image_idx != 0:
                    if cra.chain.name == chain and cra.residue.seqid == res.seqid:
                        continue
                    out[key].add(f"SYM:{cra.chain.name}")
                elif cra.chain.name != chain:
                    kind = "LIG" if cra.residue.het_flag == "H" else "CHAIN"
                    out[key].add(f"{kind}:{cra.residue.name}{cra.residue.seqid.num}" if kind == "LIG" else f"CHAIN:{cra.chain.name}")
                elif cra.residue.het_flag == "H" and cra.residue.seqid != res.seqid:
                    out[key].add(f"LIG:{cra.residue.name}{cra.residue.seqid.num}")
    return out


def run_fit(pid, s, e, rule, flank):
    subprocess.run([sys.executable, os.path.join(os.path.dirname(os.path.abspath(__file__)), "anchor_fit.py"), pid, str(s), str(e), rule, str(flank)],
                   capture_output=True, text=True)
    path = P(f"results/anchor_fit/{pid}_{s}-{e}_{rule}.tsv")
    lines = open(path).read().splitlines()
    if lines[0].startswith("# REFUSED"):
        return {"header": lines[0], "rows": {}}
    rows = {int(r["source_row_index"]): r for r in csv.DictReader(lines[1:], delimiter="\t")}
    return {"header": lines[0], "rows": rows}


def main():
    os.makedirs(OUT, exist_ok=True)
    reps = {r["rep_id"]: r for r in R("results/selected_representatives.tsv")}
    pairs = {p["pair_id"]: p for p in R("results/selected_pairs.tsv")}
    cw = defaultdict(dict)
    for r in R("results/residue_crosswalk.tsv"):
        cw[r["rep_id"]][int(r["row_index1"])] = r
    comp = defaultdict(dict)
    for r in R("results/correspondence_comparison.tsv"):
        if r["run_id"].startswith("attempt"):
            continue
        comp[(r["pair_id"], r["direction"], r["replicate"])][int(r["source_row_index"])] = r
    inter = [r for r in R("results/interaction_comparison.tsv") if r["source_side"] == "query"]
    cont = {}
    summary = []
    for reg in R("results/region_review.tsv"):
        pid, s, e = reg["pair_id"], int(reg["row_index_start"]), int(reg["row_index_end"])
        pair = pairs[pid]
        q, t = pair["query_rep"], pair["target_rep"]
        for rid in (q, t):
            if rid not in cont:
                cont[rid] = contacts(reps[rid]["pdb_id"], reps[rid]["auth_asym_id"])
        fwd = comp[(pid, "forward", "1")]
        # first COMPLETED reverse replicate (a crashed replicate has only technical-failure rows)
        rev = next((comp[(pid, "reverse", k)] for k in ("1", "2", "3") if (pid, "reverse", k) in comp and any(
            x["category"] != "technical_failure_or_no_alignment" for x in comp[(pid, "reverse", k)].values())), {})
        fits = {rule: run_fit(pid, s, e, rule, 8 if rule == "shared_local" else 2)
                for rule in ("shared", "shared_flank_excl", "shared_local")}
        rows = []
        for i in range(s, e + 1):
            c = fwd.get(i)
            if c is None:
                continue
            def ctc(rid, k):
                if k in (None, "NA", ""):
                    return "NA"
                x = cw[rid].get(int(k))
                if x is None or x["observed"] != "yes":
                    return "unobserved"
                key = (int(x["auth_seq_id"]), "" if x["ins_code"] in ("NA", "") else x["ins_code"])
                return ";".join(sorted(cont[rid].get(key, set()))) or "none"
            rec = dict(region_id=reg["region_id"], source_row_index=i, source_nt=c["source_nt"], source_auth=c["source_auth"],
                       rfam_partner=c["rfam_partner"], star3d_fwd_partner=c["star3d_partner"],
                       star3d_rev_partner=rev.get(i, {}).get("star3d_partner", "NA"), category=c["category"],
                       source_contacts=ctc(q, i), rfam_partner_contacts=ctc(t, c["rfam_partner"]),
                       star3d_partner_contacts=ctc(t, c["star3d_partner"]))
            for rule, f in fits.items():
                fr = f["rows"].get(i, {})
                for m in ("rfam", "star3d"):
                    rec[f"{rule}_{m}_C1p"] = fr.get(f"{m}_C1p_dist", "NA")
                    rec[f"{rule}_{m}_base"] = fr.get(f"{m}_base_centroid_dist", "NA")
            rows.append(rec)
        with open(os.path.join(OUT, f"{reg['region_id']}.tsv"), "w", newline="") as fo:
            w = csv.DictWriter(fo, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(rows)
            for rule, f in fits.items():
                fo.write(f"# {rule}: {f['header'][2:]}\n")
        # interactions with >=1 endpoint in span; rfam vs STAR3D forward, eligible set
        ints = [x for x in inter if x["pair_id"] == pid and (s <= int(x["i"]) <= e or s <= int(x["j"]) <= e)]
        el = [x for x in ints if x["eligible_rfam_vs_star3d_forward"] in ("yes", "True")]
        cls = {}
        for k in ("canonical", "wobble", "noncanonical", "stack"):
            sel = [x for x in el if x["pair_class"] == k]
            cls[k] = (len(sel), sum(x["rfam_status"] == "exact_class_preserved" for x in sel),
                      sum(x["star3d_forward_status"] == "exact_class_preserved" for x in sel))
        diff = [r for r in rows if r["category"] == "different_partner"]

        def closer(rule, kind):
            n_r = n_s = tie = na = 0
            for r in diff:
                a, b = r[f"{rule}_rfam_{kind}"], r[f"{rule}_star3d_{kind}"]
                if "NA" in (a, b):
                    na += 1
                elif abs(float(a) - float(b)) < 0.5:
                    tie += 1
                elif float(a) < float(b):
                    n_r += 1
                else:
                    n_s += 1
            return f"rfam {n_r} / star3d {n_s} / tie {tie} / NA {na}"
        cnt = lambda key: sum(1 for r in rows if r[key] not in ("none", "NA", "unobserved") and "LIG" in r[key])  # noqa: E731
        summary.append(dict(region_id=reg["region_id"], pair_id=pid, tier=reg["tier"], span=f"{s}-{e}",
                            n_residues=len(rows), categories=";".join(f"{k}:{v}" for k, v in Counter(r["category"] for r in rows).items()),
                            eligible=reg["eligible_for_structural_adjudication"],
                            star3d_fwd_rev_same=sum(1 for r in rows if r["star3d_fwd_partner"] == r["star3d_rev_partner"]),
                            interactions_touching=len(ints), interactions_eligible=len(el),
                            **{f"{k}_eligible_rfam_star3d": "%d/%d/%d" % v for k, v in cls.items()},
                            closer_C1p_shared=closer("shared", "C1p"), closer_base_shared=closer("shared", "base"),
                            closer_C1p_flank_excl=closer("shared_flank_excl", "C1p"),
                            closer_C1p_local=closer("shared_local", "C1p"), closer_base_local=closer("shared_local", "base"),
                            fit_local=("REFUSED" if not fits["shared_local"]["rows"] else "ok"),
                            source_ligand_contacts=cnt("source_contacts"), rfam_partner_ligand_contacts=cnt("rfam_partner_contacts"),
                            star3d_partner_ligand_contacts=cnt("star3d_partner_contacts"),
                            symmetry_contacts=sum(1 for r in rows for k in ("source_contacts", "rfam_partner_contacts", "star3d_partner_contacts") if "SYM:" in r[k]),
                            other_chain_contacts=sum(1 for r in rows for k in ("source_contacts", "rfam_partner_contacts", "star3d_partner_contacts") if "CHAIN:" in r[k])))
    with open(os.path.join(OUT, "summary.tsv"), "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=list(summary[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(summary)
    for x in summary:
        print(x)


if __name__ == "__main__":
    main()
