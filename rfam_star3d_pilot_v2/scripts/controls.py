"""TECHNICAL CONTROLS ONLY (not pilot results): check that original STAR3D aligns near-identical or
identical structures of the same fold completely, to separate tool/input defects from algorithmic
outcomes on cross-species pairs. Runs are written under runs/_controls/ and results/control_runs.tsv.

Usage: controls.py QUERY_KEY TARGET_KEY [FAMILY]   (keys: <PDB>_<chain> with explicit standard-seed links)
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import prepare_inputs  # noqa: E402
import star3d  # noqa: E402
import stockholm  # noqa: E402

ROOT = star3d.ROOT
P = star3d.P


def main(qk, tk):
    links = {f"{r['pdb_id']}_{r['chain_token']}": r for r in star3d.read_tsv(P("mappings/structure_sequence_map.tsv"))
             if r["link_basis"] == "explicit_GR_feature" and r["link_status"] == "verified"}
    fam = links[qk]["rfam_acc"]
    seed = {fam: next(stockholm.parse(P(star3d.CFG["reference"]["seed_path"]), only={fam}))}
    prepare_inputs.CFG = star3d.CFG
    reps, inputs = {}, {}
    for k in (qk, tk):
        r = dict(links[k], rep_id=f"CONTROL__{fam}__{k}", masked_label_seq_ids="")
        meta, _ = prepare_inputs.prepare(r, seed)
        reps[r["rep_id"]] = r
        inputs[r["rep_id"]] = meta
    pid = f"_controls/{fam}__{qk}__{tk}"
    pair = dict(pair_id=pid, rfam_acc=fam, query_rep=f"CONTROL__{fam}__{qk}", target_rep=f"CONTROL__{fam}__{tk}")
    os.makedirs(P("runs", "_controls"), exist_ok=True)
    os.makedirs(P("runs", "_superseded"), exist_ok=True)
    star3d.MANIFEST_PATH = P("results/control_runs.tsv")
    star3d.run_pair(pair, reps, inputs, 1)


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
