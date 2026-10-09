"""Phase 4 comparison: standard-seed reference pairs vs ORIGINAL STAR3D correspondences.

v5 single-run policy: consumes exactly ONE selected original-STAR3D output per pair
(results/primary_star3d_outputs.tsv, written by select_primary_outputs.py; forward = query -> target). No replicate,
reverse-run or cross-run consensus logic remains in the active comparison.
Index system: row residue index (1-based) of each selected standard-seed row (crosswalk joins
STAR3D author residue IDs -> row index).
Outputs: results/correspondence_comparison.tsv (per pair x source residue)
         results/pair_summary.tsv            (per pair, with explicit denominators)
Usage: compare.py
"""
import csv
import hashlib
import os
import sys
from collections import defaultdict

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import star3d  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def write_tsv(path, rows, fields):
    """Atomic write (tmp + rename) so an interrupted stage never leaves a truncated table in place."""
    tmp = path + ".tmp"
    with open(tmp, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) is None or r.get(k) == "" else r[k]) for k in fields})
    os.replace(tmp, path)


def crosswalks():
    cw = defaultdict(dict)
    for r in read_tsv(P("results/residue_crosswalk.tsv")):
        cw[r["rep_id"]][int(r["row_index1"])] = r
    return cw


def resid_index(cwrep):
    """(chain, auth_seq, icode) -> row index, observed residues only; collisions are fatal."""
    out = {}
    for k, r in cwrep.items():
        if r["observed"] != "yes":
            continue
        key = (r["auth_asym_id"], int(r["auth_seq_id"]), "" if r["ins_code"] in ("NA", "") else r["ins_code"])
        if key in out:
            raise SystemExit(f"author residue ID collision {key}")
        out[key] = k
    return out


VALIDATION_FAILURES = []


def stored_alignment_problems(run, pa, path):
    """v3 repair C: re-validate STORED STAR3D output when it is consumed. A manifest saying 'completed' never
    overrules malformed or changed current bytes."""
    probs = list(pa["bad_lines"])                          # unparsable mapping lines, declared != parsed count
    if pa["aligned_n"] is None:
        probs.append("no '#Aligned nucleotide' header")
    cur = hashlib.sha256(open(path, "rb").read()).hexdigest()
    if run.get("output_sha256") not in (None, "", "NA") and run["output_sha256"] != cur:
        probs.append(f"output bytes changed since run (manifest {run['output_sha256'][:12]} != current {cur[:12]})")
    if run.get("aligned_n") not in (None, "", "NA") and int(run["aligned_n"]) != len(pa["pairs"]):
        probs.append(f"manifest aligned_n {run['aligned_n']} != parsed {len(pa['pairs'])}")
    return probs


def compare_run(run, pair, cw, ref):
    qrep, trep = pair["query_rep"], pair["target_rep"]
    cq, ct = cw[qrep], cw[trep]
    if run["status"] != "completed":
        smap, injective, unmapped = None, None, None
    else:
        aln_path = P(run["output_aln"])
        if not os.path.exists(aln_path):
            pa, probs = dict(pairs=[], bad_lines=[], aligned_n=None), [f"output missing: {run['output_aln']}"]
        else:
            pa = star3d.parse_aln(aln_path)
            probs = stored_alignment_problems(run, pa, aln_path)
        left_rep, right_rep = (qrep, trep) if run["direction"] == "forward" else (trep, qrep)
        il, ir = resid_index(cw[left_rep]), resid_index(cw[right_rep])
        pairs, unmapped = [], []
        for l, r in pa["pairs"]:
            if l not in il or r not in ir:
                unmapped.append((l, r))
                continue
            a, b = il[l], ir[r]
            pairs.append((a, b) if run["direction"] == "forward" else (b, a))
        qs = [a for a, _ in pairs]
        ts = [b for _, b in pairs]
        injective = len(set(qs)) == len(qs) and len(set(ts)) == len(ts)   # checked BEFORE building the map
        if probs:
            VALIDATION_FAILURES.append((run["run_id"], "stored_output_invalid", "; ".join(probs)))
            smap = None
        elif unmapped or not injective:
            # unexplained output-to-crosswalk failure or many-to-one mapping = validation failure, never a silent drop
            VALIDATION_FAILURES.append((run["run_id"], len(unmapped), injective))
            smap = None
        else:
            smap = dict(pairs)
    rmap = {int(r["row_A_index"]): int(r["row_B_index"]) for r in ref}
    rows = []
    for i, c in sorted(cq.items()):
        jr = rmap.get(i)
        js = smap.get(i) if smap is not None else None
        masked_q = c["engineered_masked"] == "yes"
        if smap is None and run["status"] == "completed":
            cat = "validation_failed"
        elif smap is None:
            cat = "technical_failure_or_no_alignment"
        elif jr is not None and js is not None:
            cat = "same_partner" if jr == js else "different_partner"
        elif jr is not None:
            cat = "rfam_only"
        elif js is not None:
            cat = "star3d_only"
        else:
            cat = "neither"
        why_r = None if jr is not None else "alignment_gap_in_standard_seed"
        if js is None:
            if smap is None:
                why_s = ("validation_failed" if run["status"] == "completed" else
                         "no_valid_primary_output" if run["status"] == "unavailable" else
                         "technical_failure" if run["status"] == "failed" else "no_alignment")
            elif c["observed"] != "yes":
                why_s = "missing_coordinates_source"
            elif jr is not None and ct[jr]["observed"] != "yes":
                why_s = "rfam_partner_missing_coordinates"
            else:
                why_s = "algorithm_omission"
        else:
            why_s = None
        assess = (c["observed"] == "yes" and not masked_q and jr is not None and ct[jr]["observed"] == "yes"
                  and ct[jr]["engineered_masked"] != "yes")
        rows.append(dict(pair_id=pair["pair_id"], star3d_run_id=run["run_id"], source_rep=qrep, source_row_index=i, source_nt=c["row_nt"],
                         source_label_seq_id=c["label_seq_id"], source_auth=f"{c['auth_asym_id']}:{c['auth_seq_id']}",
                         source_observed=c["observed"], source_masked=c["engineered_masked"],
                         original_column=c["original_column"],
                         rfam_partner=jr, rfam_partner_nt=ct[jr]["row_nt"] if jr else None,
                         rfam_partner_auth=f"{ct[jr]['auth_asym_id']}:{ct[jr]['auth_seq_id']}" if jr else None,
                         star3d_partner=js, star3d_partner_nt=ct[js]["row_nt"] if js else None,
                         star3d_partner_auth=f"{ct[js]['auth_asym_id']}:{ct[js]['auth_seq_id']}" if js else None,
                         category=cat, rfam_missing_reason=why_r, star3d_missing_reason=why_s,
                         rfam_pair_structurally_assessable="yes" if assess else "no",
                         partner_offset=(js - jr) if (js and jr) else None,
                         reference_source="Rfam.seed.gz", rfam_release=CFG["reference"]["rfam_release"],
                         seed_sha256=CFG["reference"]["seed_sha256"]))
    return rows, smap, rmap, injective, unmapped


def summarize(run, pair, rows, smap, rmap, injective, unmapped, cw):
    cq, ct = cw[pair["query_rep"]], cw[pair["target_rep"]]
    R = set(rmap.items())
    S = set(smap.items()) if smap else set()
    Ra = {(i, j) for i, j in R if cq[i]["observed"] == "yes" and ct[j]["observed"] == "yes"
          and cq[i]["engineered_masked"] != "yes" and ct[j]["engineered_masked"] != "yes"}
    unmask = lambda s: {(i, j) for i, j in s if cq[i]["engineered_masked"] != "yes" and ct[j]["engineered_masked"] != "yes"}  # noqa
    common_src = {i for i, _ in R} & {i for i, _ in S}
    cats = defaultdict(int)
    for r in rows:
        cats[r["category"]] += 1
    Sa = unmask(S)
    return dict(pair_id=pair["pair_id"], tier=pair["tier"], star3d_run_id=run["run_id"],
                star3d_output=run.get("output_aln"), status=run["status"],
                source_row_len=len(cq), target_row_len=len(ct),
                source_observed=sum(c["observed"] == "yes" for c in cq.values()),
                target_observed=sum(c["observed"] == "yes" for c in ct.values()),
                source_masked=sum(c["engineered_masked"] == "yes" for c in cq.values()),
                target_masked=sum(c["engineered_masked"] == "yes" for c in ct.values()),
                rfam_pairs=len(R), rfam_pairs_structurally_assessable=len(Ra),
                star3d_pairs=len(S) if smap is not None else None, star3d_rmsd=run["rmsd"],
                star3d_unmapped_output_lines=len(unmapped) if unmapped is not None else None,
                star3d_injective=injective,
                common_source_mapped=len(common_src) if smap is not None else None,
                shared_pairs=len(R & S) if smap is not None else None,
                shared_pairs_unmasked=len(unmask(R) & Sa) if smap is not None else None,
                rfam_assessable_pairs_reproduced=len(Ra & S) if smap is not None else None,
                frac_rfam_assessable_reproduced=round(len(Ra & S) / len(Ra), 4) if (smap is not None and Ra) else None,
                jaccard_pairs_unmasked=round(len(unmask(R) & Sa) / len(unmask(R) | Sa), 4) if (smap is not None and (unmask(R) | Sa)) else None,
                same_partner=cats["same_partner"], different_partner=cats["different_partner"],
                rfam_only=cats["rfam_only"], star3d_only=cats["star3d_only"], neither=cats["neither"],
                failure_rows=cats["technical_failure_or_no_alignment"] + cats["validation_failed"],
                category_sum_check="ok" if sum(cats.values()) == len(cq) else "MISMATCH",
                reference_source="Rfam.seed.gz", rfam_release=CFG["reference"]["rfam_release"],
                seed_sha256=CFG["reference"]["seed_sha256"])


def primary_runs(pairs):
    """One selected run per pair from results/primary_star3d_outputs.tsv (missing or 'unavailable' -> unavailable)."""
    sel = {r["pair_id"]: r for r in read_tsv(P("results/primary_star3d_outputs.tsv"))}
    out = {}
    for pid in pairs:
        r = sel.get(pid)
        if r is None or r["status"] != "selected":
            out[pid] = dict(run_id=(r or {}).get("selected_run_id", "NA"), status="unavailable", direction="forward",
                            output_aln="NA", rmsd=None)
        else:
            out[pid] = dict(run_id=r["selected_run_id"], status="completed", direction="forward",
                            output_aln=r["output_aln"], output_sha256=r["output_sha256"], aligned_n=r["aligned_n"],
                            rmsd=r["rmsd"])
    return out


def main(only):
    if only:
        raise SystemExit("subset runs would overwrite the complete global tables; run without arguments")
    pairs = {p["pair_id"]: p for p in read_tsv(P("results/selected_pairs.tsv"))}
    runs = primary_runs(pairs)
    refs = defaultdict(list)
    for r in read_tsv(P("results/reference_pairs.tsv")):
        refs[r["pair_id"]].append(r)
    cw = crosswalks()
    allrows, summ = [], []
    for pid, pair in pairs.items():
        run = runs[pid]
        rows, smap, rmap, inj, un = compare_run(run, pair, cw, refs[pid])
        allrows += rows
        summ.append(summarize(run, pair, rows, smap, rmap, inj, un, cw))
    # on validation failure the recomputed tables are written ONLY as *.INVALID.tsv (complete tables untouched)
    out = (lambda n: P("results", n + (".INVALID.tsv" if VALIDATION_FAILURES else ".tsv")))  # noqa: E731
    write_tsv(out("correspondence_comparison"), allrows, list(allrows[0].keys()))
    write_tsv(out("pair_summary"), summ, list(summ[0].keys()))
    if VALIDATION_FAILURES:
        raise SystemExit(f"STAGE FAILED: STAR3D output validation failures {VALIDATION_FAILURES} (written only as results/*.INVALID.tsv)")
    for s in summ:
        print(s["pair_id"], s["star3d_run_id"], s["status"], "R", s["rfam_pairs"], "Ra", s["rfam_pairs_structurally_assessable"],
              "S", s["star3d_pairs"], "same", s["same_partner"], "diff", s["different_partner"], "inj", s["star3d_injective"],
              s["category_sum_check"])


if __name__ == "__main__":
    main(sys.argv[1:])
