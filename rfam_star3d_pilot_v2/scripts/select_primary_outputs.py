"""v5 single-run policy: select ONE primary original-STAR3D output per pair and write
results/primary_star3d_outputs.tsv.

Rule (fixed; no outcome-based choice):
  For each pair, walk its FORWARD alignment records in execution order (attempt number, then replicate) and take the
  first one from a VALID execution with the intended inputs and original defaults. Validity checks:
    - status completed, exit code 0;
    - STAR3D tarball sha256 = pinned value; parameters = defaults + '-p' only;
    - query/target input sha256 recorded at run time = current prepared input files (mappings/aligner_inputs.tsv);
    - the attempt's preprocessing steps completed; npk.ct/.mca sha256 recorded = files on disk; preprocessing products
      pass star3d.preprocessing_problems() (no fatal problem);
    - output exists, sha256 = recorded, parses without bad lines, declared aligned count = parsed count = recorded;
    - every output residue maps through the residue crosswalk and the mapping is one-to-one.
  Earlier records that fail are listed with the reason. Reverse runs, later replicates and modified-method outputs are
  never substituted. Agreement with Rfam, interaction preservation and RMSD are NOT consulted.
  If no valid record exists the pair is written with status 'unavailable'.
Pinned: RF00522__6VUI_A__7REX_A must resolve to runs/RF00522__6VUI_A__7REX_A/attempt1/STAR3D_source/out/
RF00522__6VUI_A__7REX_A__a1__forward__rep1.aln (stop otherwise).
Usage: select_primary_outputs.py        (SQARMA_STUDY_ROOT may point to an isolated workspace)"""
import csv
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import compare  # noqa: E402
import star3d  # noqa: E402

ROOT = os.environ.get("SQARMA_STUDY_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
PINNED = {"RF00522__6VUI_A__7REX_A":
          "runs/RF00522__6VUI_A__7REX_A/attempt1/STAR3D_source/out/RF00522__6VUI_A__7REX_A__a1__forward__rep1.aln"}
FIELDS = ["pair_id", "rfam_acc", "status", "alignment_order", "query_rep", "target_rep", "query_star3d_id",
          "query_chain", "target_star3d_id", "target_chain", "selected_run_id", "output_aln", "output_sha256",
          "aligned_n", "rmsd", "command", "parameters", "star3d_tarball_sha256", "image_id", "query_input_sha256",
          "target_input_sha256", "query_npk_ct_sha256", "target_npk_ct_sha256", "query_mca_sha256", "target_mca_sha256",
          "preprocessing_run_ids", "selection_rule", "earlier_records_not_selected", "checks_passed"]
RULE = "first forward record of the earliest valid original-default execution (attempt, then replicate order)"


def R(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def order_key(r):
    m = re.search(r"__a(\d+)__", r["run_id"]) or re.match(r"attempt(\d+)__", r["run_id"])
    return (int(m.group(1)) if m else 0, int(r["replicate"]) if str(r["replicate"]).isdigit() else 0)


def attempt_dir(output_aln):
    return os.path.dirname(os.path.dirname(P(output_aln)))      # .../STAR3D_source


def problems(run, inputs, cw, man, q, t):
    out = []
    if run["status"] != "completed" or str(run["exit_code"]) != "0":
        return [f"status {run['status']} exit {run['exit_code']}"]
    if run["star3d_tarball_sha256"] != star3d.CFG["sources"]["star3d_sha256"]:
        out.append("tarball sha differs from pinned")
    if not run["parameters"].startswith("defaults") or run["parameters"].split("+")[-1].strip() != "-p":
        out.append(f"non-default parameters: {run['parameters']}")
    if run["query_input_sha256"] != inputs[q]["sha256"] or run["target_input_sha256"] != inputs[t]["sha256"]:
        out.append("prepared input sha256 at run time != current prepared inputs")
    for rid in (q, t):
        f = P(inputs[rid]["file"])
        if not os.path.exists(f) or sha(f) != inputs[rid]["sha256"]:
            out.append(f"prepared input file missing or changed: {inputs[rid]['file']}")
    work = attempt_dir(run["output_aln"]) if run.get("output_aln") not in (None, "", "NA") else None
    if work is None or not os.path.exists(P(run["output_aln"])):
        return out + ["output missing"]
    si = os.path.join(work, "STAR3D_struct_info")
    for side, sid, ch in (("query", run["query_star3d_id"], run["query_chain"]),
                          ("target", run["target_star3d_id"], run["target_chain"])):
        npk, mca = os.path.join(si, f"{sid}_{ch}.npk.ct"), os.path.join(si, f"{sid}.mca")
        if not os.path.exists(npk) or sha(npk) != run[f"{side}_npk_ct_sha256"]:
            out.append(f"{side} npk.ct missing or differs from record")
        if not os.path.exists(mca) or sha(mca) != run[f"{side}_mca_sha256"]:
            out.append(f"{side} .mca missing or differs from record")
        fatal, _warn = star3d.preprocessing_problems(work, sid, ch)
        if fatal:
            out.append(f"{side} preprocessing invalid: {'; '.join(fatal)}")
    att = re.search(r"__a(\d+)__", run["run_id"])
    pre = [m for m in man if m["pair_id"] == run["pair_id"] and m["direction"] == "preprocess"
           and att and f"__a{att.group(1)}__" in m["run_id"]]
    if len(pre) != 2 or any(m["status"] != "completed" for m in pre):
        out.append("preprocessing records for this attempt not 2 x completed")
    if sha(P(run["output_aln"])) != run["output_sha256"]:
        out.append("output sha256 differs from record")
    pa = star3d.parse_aln(P(run["output_aln"]))
    if pa["bad_lines"] or pa["aligned_n"] is None or pa["aligned_n"] != len(pa["pairs"]) or \
            str(pa["aligned_n"]) != str(run["aligned_n"]):
        out.append(f"parse problems {pa['bad_lines'][:2]} declared {pa['aligned_n']} parsed {len(pa['pairs'])}")
    il, ir = compare.resid_index(cw[q]), compare.resid_index(cw[t])
    mapped = [(il.get(a), ir.get(b)) for a, b in pa["pairs"]]
    if any(x is None or y is None for x, y in mapped):
        out.append("output residue not in crosswalk")
    qs, ts = [x for x, _ in mapped], [y for _, y in mapped]
    if len(set(qs)) != len(qs) or len(set(ts)) != len(ts):
        out.append("mapping not one-to-one")
    return out


def choose(runs, check):
    """Pure selection: forward records only, in execution order; first record for which check(r) returns no problems.
    Returns (chosen_or_None, [rejection strings]). Reverse records are ignored, never substituted."""
    fwd = sorted([r for r in runs if r["direction"] == "forward"], key=order_key)
    rejected = []
    for r in fwd:
        why = check(r)
        if why:
            rejected.append(f"{r['run_id']}: {'; '.join(why)}")
            continue
        return r, rejected
    return None, rejected


def main():
    pairs = R(P("results/selected_pairs.tsv"))
    inputs = {r["rep_id"]: r for r in R(P("mappings/aligner_inputs.tsv"))}
    man = R(P("results/run_manifest.tsv"))
    cw = compare.crosswalks() if ROOT == compare.ROOT else None
    if cw is None:
        compare.P = P
        cw = compare.crosswalks()
    rows = []
    for p in pairs:
        q, t = p["query_rep"], p["target_rep"]
        chosen, rejected = choose([r for r in man if r["pair_id"] == p["pair_id"]],
                                  lambda r: problems(r, inputs, cw, man, q, t))
        if p["pair_id"] in PINNED and (chosen is None or chosen["output_aln"] != PINNED[p["pair_id"]]):
            raise SystemExit(f"STOP: {p['pair_id']} did not resolve to the pinned primary output")
        base = dict(pair_id=p["pair_id"], rfam_acc=p["rfam_acc"], query_rep=q, target_rep=t,
                    alignment_order=f"{p['query']} -> {p['target']} (query = lexicographically smaller stable ID)",
                    selection_rule=RULE, earlier_records_not_selected=" | ".join(rejected) or "none")
        if chosen is None:
            rows.append(dict(base, status="unavailable"))
            continue
        pre = [m["run_id"] for m in man if m["pair_id"] == p["pair_id"] and m["direction"] == "preprocess"
               and re.search(r"__a(\d+)__", chosen["run_id"]).group(0) in m["run_id"]]
        rows.append(dict(base, status="selected", **{k: chosen[k] for k in (
            "query_star3d_id", "query_chain", "target_star3d_id", "target_chain", "output_aln", "output_sha256",
            "aligned_n", "rmsd", "command", "parameters", "star3d_tarball_sha256", "image_id", "query_input_sha256",
            "target_input_sha256", "query_npk_ct_sha256", "target_npk_ct_sha256", "query_mca_sha256", "target_mca_sha256")},
            selected_run_id=chosen["run_id"], preprocessing_run_ids=";".join(pre),
            checks_passed="status+exit; tarball; default params; input sha; npk/mca sha; preprocessing contents; "
                          "output sha; parse+counts; crosswalk mapping; one-to-one"))
    tmp = P("results/primary_star3d_outputs.tsv.tmp")
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t", lineterminator="\n", restval="NA")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, P("results/primary_star3d_outputs.tsv"))
    for r in rows:
        print(r["pair_id"], r["status"], r.get("selected_run_id"), "| not selected:", r["earlier_records_not_selected"][:160])


if __name__ == "__main__":
    main()
