"""Phase 5: candidate disagreement regions (ALL kept) and predeclared ranking for inspection.

Rule (config regions.merge_gap): a source residue is a disagreement residue if, in the primary
direction replicate 1, its category is different_partner, or rfam_only/star3d_only where the absent
side is NOT explained by missing coordinates. Disagreement residues whose source-row indices are
within merge_gap of each other form one region. Regions are also annotated by whether the reverse
run reproduces the disagreement.
Ranking (v2.1): (1) eligible_for_structural_adjudication (no engineering mask or missing coordinate at ANY source
position in the span or at any Rfam/STAR3D target partner); (2) regions with >=1 correspondence disagreement before
coverage-only regions; (3) more interaction-status differences on the eligible Rfam-vs-STAR3D-forward set;
(4) not within 3 residues of a row terminus; (5) more correspondence disagreements; (6) pair_id, start.
Correspondence disagreements (both map, different partner) and coverage differences (only one maps) are counted
separately; a missing mapping is not an incorrect correspondence. Eligibility means eligible for investigation only.
Outputs results/region_review.tsv (interpretation columns filled by manual inspection later).
"""
import csv
import os
import sys
from collections import defaultdict

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import locate  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def primary_replicates(comp):
    """(pair_id, direction) -> lowest-numbered replicate whose run completed (failed replicates stay in tables)."""
    ok = {}
    for r in comp:
        if r["category"] != "technical_failure_or_no_alignment":
            key = (r["pair_id"], r["direction"])
            ok[key] = min(ok.get(key, 99), int(r["replicate"]))
    return ok


def region_eligibility(span, src_cw, tgt_cw, rfam_map, s3d_map):
    """Eligibility for structural adjudication of a region spanning source row indices `span` (inclusive list).
    Checks EVERY source position in the span (incl. intervening ones) and the Rfam and STAR3D target partners of
    those positions for engineering masks and missing coordinates. Passing = eligible for investigation only."""
    def flag(rows, key, val):
        return "yes" if any(r is not None and r[key] == val for r in rows) else "no"
    src = [src_cw.get(k) for k in span]
    rt = [tgt_cw.get(rfam_map[k]) for k in span if k in rfam_map]
    st = [tgt_cw.get(s3d_map[k]) for k in span if k in s3d_map]
    out = dict(source_engineering_overlap=flag(src, "engineered_masked", "yes"),
               rfam_target_engineering_overlap=flag(rt, "engineered_masked", "yes"),
               star3d_target_engineering_overlap=flag(st, "engineered_masked", "yes"),
               source_unobserved_in_span=flag(src, "observed", "no"),
               rfam_target_unobserved=flag(rt, "observed", "no"),
               star3d_target_unobserved=flag(st, "observed", "no"))
    out["eligible_for_structural_adjudication"] = "yes" if all(v == "no" for v in out.values()) else "no"
    return out


def carry_interpretations(out, previous):
    """Carry manual review fields from earlier region tables: exact region_id first, else same pair with
    overlapping span (noted). Nothing is reset to pending if it was reviewed before."""
    for r in out:
        r.update(inspected="pending", classification="not_inspected", interpretation=None, interpretation_source=None)
        exact = [p for p in previous if p["region_id"] == r["region_id"] and p["inspected"] not in ("pending", "NA")]
        over = [p for p in previous if p["pair_id"] == r["pair_id"] and p["inspected"] not in ("pending", "NA")
                and int(p["row_index_start"]) <= r["row_index_end"] and int(p["row_index_end"]) >= r["row_index_start"]]
        src = exact or over
        if src:
            r["inspected"] = ";".join(sorted({p["inspected"] for p in src}))
            r["classification"] = " || ".join(p["classification"] for p in src)
            r["interpretation"] = " || ".join(p["interpretation"] for p in src)
            r["interpretation_source"] = ("carried exact from " if exact else "carried by span overlap from ") + \
                ",".join(p["region_id"] for p in src)
    return out


def main():
    reps = {r["rep_id"]: r for r in read_tsv(P("results/selected_representatives.tsv"))}
    comp = read_tsv(P("results/correspondence_comparison.tsv"))
    prim = primary_replicates(comp)
    inter = read_tsv(P("results/interaction_comparison.tsv"))
    cw = defaultdict(dict)
    for r in read_tsv(P("results/residue_crosswalk.tsv")):
        cw[r["rep_id"]][int(r["row_index1"])] = r
    pairs = {p["pair_id"]: p for p in read_tsv(P("results/selected_pairs.tsv"))}
    previous = read_tsv(P("results/region_review.tsv")) if os.path.exists(P("results/region_review.tsv")) else []
    gap = CFG["regions"]["merge_gap"]
    fwd = defaultdict(list)
    rev = defaultdict(dict)
    for r in comp:
        if prim.get((r["pair_id"], r["direction"])) != int(r["replicate"]):
            continue
        if r["direction"] == "forward":
            fwd[r["pair_id"]].append(r)
        else:
            rev[r["pair_id"]][int(r["source_row_index"])] = r

    def kind(r):
        """correspondence disagreement (both map, different partner) vs coverage difference (one maps)."""
        if r["category"] == "different_partner":
            return "correspondence"
        if r["category"] == "rfam_only" and r["star3d_missing_reason"] == "algorithm_omission":
            return "coverage"
        if r["category"] == "star3d_only":
            return "coverage"
        return None

    out = []
    for pid, rows in sorted(fwd.items()):
        rows.sort(key=lambda r: int(r["source_row_index"]))
        n = len(rows)
        pair = pairs[pid]
        src_cw, tgt_cw = cw[pair["query_rep"]], cw[pair["target_rep"]]
        rmap = {int(r["source_row_index"]): int(r["rfam_partner"]) for r in rows if r["rfam_partner"] != "NA"}
        smap = {int(r["source_row_index"]): int(r["star3d_partner"]) for r in rows if r["star3d_partner"] != "NA"}
        dis = [r for r in rows if kind(r)]
        groups, cur = [], []
        for r in dis:
            if cur and int(r["source_row_index"]) - int(cur[-1]["source_row_index"]) > gap:
                groups.append(cur)
                cur = []
            cur.append(r)
        if cur:
            groups.append(cur)
        rep = reps[pair["query_rep"]]
        for g in groups:
            s, e = int(g[0]["source_row_index"]), int(g[-1]["source_row_index"])
            span = list(range(s, e + 1))
            labs = [int(src_cw[k]["label_seq_id"]) for k in span]
            loc = locate.locate(rep["rfam_acc"], rep["row_name"], rep["row_offset_in_deposited"], labs)
            el = region_eligibility(span, src_cw, tgt_cw, rmap, smap)
            ints = [x for x in inter if x["pair_id"] == pid and x["source_side"] == "query"
                    and (s <= int(x["i"]) <= e or s <= int(x["j"]) <= e)
                    and x["eligible_rfam_vs_star3d_forward"] == "yes"
                    and x["rfam_status"] != x["star3d_forward_status"]]
            rev_same = sum(1 for r in g if rev[pid].get(int(r["source_row_index"]), {}).get("star3d_partner") == r["star3d_partner"])
            out.append(dict(
                pair_id=pid, region_id=f"{pid}__r{s}-{e}", source_rep=rep["rep_id"], row_index_start=s, row_index_end=e,
                n_correspondence_disagreements=sum(1 for r in g if kind(r) == "correspondence"),
                n_coverage_differences=sum(1 for r in g if kind(r) == "coverage"),
                source_auth=f"{src_cw[s]['auth_asym_id']}:{src_cw[s]['auth_seq_id']}..{src_cw[e]['auth_seq_id']}",
                categories=";".join(sorted({r["category"] for r in g})),
                partner_offsets=";".join(sorted({r["partner_offset"] for r in g if r["partner_offset"] != "NA"})),
                seed_elements=";".join(sorted({x["element"] for x in loc})),
                ss_cons="".join(x.get("ss_cons", "?") for x in loc),
                motif_flags=";".join(sorted({f for x in loc for f in x.get("motif_flags", "").split(";") if f})),
                **el, near_terminus="yes" if (s <= 3 or e >= n - 2) else "no",
                interaction_status_differences_eligible=len(ints),
                reverse_run_same_star3d_partner=f"{rev_same}/{len(g)}", tier=pair["tier"]))
    out.sort(key=lambda r: (r["eligible_for_structural_adjudication"] != "yes", r["n_correspondence_disagreements"] == 0,
                            -r["interaction_status_differences_eligible"], r["near_terminus"] == "yes",
                            -r["n_correspondence_disagreements"], r["pair_id"], r["row_index_start"]))
    for i, r in enumerate(out, 1):
        r["inspection_rank"] = i
    out = carry_interpretations(out, previous)
    fields = ["inspection_rank", "region_id", "pair_id", "tier", "source_rep", "row_index_start", "row_index_end",
              "n_correspondence_disagreements", "n_coverage_differences", "source_auth", "categories",
              "partner_offsets", "seed_elements", "ss_cons", "motif_flags", "source_engineering_overlap",
              "rfam_target_engineering_overlap", "star3d_target_engineering_overlap", "source_unobserved_in_span",
              "rfam_target_unobserved", "star3d_target_unobserved", "eligible_for_structural_adjudication",
              "near_terminus", "interaction_status_differences_eligible", "reverse_run_same_star3d_partner",
              "inspected", "classification", "interpretation", "interpretation_source"]
    with open(P("results/region_review.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in out:
            w.writerow({k: ("NA" if r.get(k) in (None, "") else r[k]) for k in fields})
    print(len(out), "candidate regions")
    for r in out:
        print(r["inspection_rank"], r["region_id"], "corr", r["n_correspondence_disagreements"], "cov",
              r["n_coverage_differences"], "eligible", r["eligible_for_structural_adjudication"],
              "int", r["interaction_status_differences_eligible"], "|", (r["interpretation_source"] or "")[:60])


if __name__ == "__main__":
    main()
