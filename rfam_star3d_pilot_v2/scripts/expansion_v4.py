"""v4 prospective expansion (pre-registered: review/v4_expansion/PREREGISTRATION.md).
Builds an ISOLATED workspace expansion_v4/ (the frozen pilot tables are never touched), freezes the selection, then
runs the UNCHANGED pipeline stages there: reference -> prepare_inputs -> original STAR3D (both directions x 3) ->
compare -> FR3D interactions -> regions.
Usage: expansion_v4.py freeze | run [--downstream-only]
  (attempt 1 ran reference before prepare_inputs; its STAR3D runs do not depend on reference tables and are kept;
   --downstream-only re-runs prepare_inputs, reference, compare, interactions, regions in the documented order)"""
import csv
import datetime as dt
import hashlib
import json
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402
import structures as S  # noqa: E402

ROOT = S.ROOT
P = S.P
WS = P("expansion_v4")
fp = lambda *a: os.path.join(WS, *a)  # noqa: E731
FAM = "RF00005"
REPS = [("5CCB", "N", "AP000442.6/2022-1950"), ("7EQJ", "B", "X17321.1/66-138")]
TIER = "prospective_exploratory_conformational_context"
RATIONALE = ("non-curated family (RF00005 not in Rfam.3d.seed 15.1); E. coli tRNA-Val (free, 7EQJ) vs human tRNA3Lys "
             "bound to the m1A58 methyltransferase TRMT6/61A (5CCB; paper: substrate tRNA is refolded) -> conformational "
             "context confound declared BEFORE alignment; no primary-eligible different-species pair exists under the rules")


def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()


def W(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) in (None, "") else r[k]) for k in fields})


def freeze():
    if os.path.exists(fp("results/selected_pairs.tsv")):
        raise SystemExit("already frozen; never re-freeze over an existing selection")
    for d in ("results", "review/evidence", "runs/_superseded", "mappings/conversion", "annotations"):
        os.makedirs(fp(d), exist_ok=True)
    if not os.path.exists(fp("inputs")):
        os.symlink(P("inputs"), fp("inputs"))
    open(fp("config.yaml"), "w").write(open(P("config.yaml")).read())
    seed = next(stockholm.parse(P(S.CFG["reference"]["seed_path"]), only={FAM}))
    fields = open(P("results/selected_representatives.tsv")).readline().rstrip("\n").split("\t")
    reps = []
    for pdb, chain, row in REPS:
        path = S.get_mmcif(pdb)
        ev, b = S.extract_entry(pdb, path)
        obs, nmod, st = S.observed_atoms(path)
        ung = seed.ungapped(row)
        acc, rs, re_ = stockholm.split_name(row)
        srow = dict(row_name=row, ungapped_row=ung, gr_feature="NA (sequence-only proposal)", pdb_id=pdb, chain=chain,
                    urs="NA", row_taxid="NA", row_start=1, row_end=len(ung), row_len=len(ung),
                    row_seq_hash=hashlib.sha256(ung.encode()).hexdigest()[:16], in_mapping_file="yes")
        link, scheme = S.build_link(FAM, srow, ev, obs, nmod, b)
        if link["link_status"] != "verified" or link.get("mods_in_family_interval"):
            raise SystemExit(f"{pdb}_{chain}: link not verified or modified residues in interval")
        json.dump({"link": link, "scheme_chain": scheme},
                  open(fp("review/evidence", f"{pdb}_{chain}_{FAM}_{re.sub('[^A-Za-z0-9]', '_', row)}.json"), "w"), indent=1)
        reps.append(dict(rep_id=f"{FAM}__{pdb}_{chain}", key=f"{pdb}_{chain}", rfam_acc=FAM, family_decision=TIER,
                         decision="accept_prospective_exploratory", source=link["entity_source_records"],
                         masked_label_seq_ids="NA", row_name=row,
                         seed_row_aligned_sha256=hashlib.sha256(seed.seqs[row].encode()).hexdigest(),
                         seed_row_lines=",".join(map(str, seed.seq_lines[row])), pdb_id=pdb, chain_token=chain,
                         label_asym_id=link["label_asym_id"], auth_asym_id=link["auth_asym_id"], entity_id=link["entity_id"],
                         row_start=rs, row_end=re_, row_offset_in_deposited=link["row_offset_in_deposited"],
                         family_label_seq_start=link["family_label_seq_start"], family_label_seq_end=link["family_label_seq_end"],
                         deposited_seq_parent_mapped=link["deposited_seq_parent_mapped"],
                         observed_fraction=link["observed_fraction"], link_status=link["link_status"],
                         reference_source="Rfam.seed.gz", rfam_release=S.CFG["reference"]["rfam_release"],
                         seed_sha256=S.CFG["reference"]["seed_sha256"]))
    W(fp("results/selected_representatives.tsv"), reps, fields)
    q, t = sorted(reps, key=lambda r: r["key"])
    pfields = open(P("results/selected_pairs.tsv")).readline().rstrip("\n").split("\t")
    pair = dict(pair_id=f"{FAM}__{q['key']}__{t['key']}", rfam_acc=FAM, tier=TIER, query_rep=q["rep_id"],
                target_rep=t["rep_id"], query=q["key"], target=t["key"], primary_direction=f"{q['key']}->{t['key']}",
                run_both_directions="yes", rationale=RATIONALE, reference_source="Rfam.seed.gz",
                rfam_release=S.CFG["reference"]["rfam_release"], seed_sha256=S.CFG["reference"]["seed_sha256"],
                cohort_version="v4_prospective_1")
    W(fp("results/selected_pairs.tsv"), [pair], pfields)
    frz = dict(frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
               statement="frozen before any STAR3D run on these structures", preregistration="review/v4_expansion/PREREGISTRATION.md",
               files={f: sha(fp(f)) for f in ("results/selected_representatives.tsv", "results/selected_pairs.tsv", "config.yaml")},
               preregistration_sha256=sha(P("review/v4_expansion/PREREGISTRATION.md")))
    json.dump(frz, open(fp("cohort_v4_prospective_freeze.json"), "w"), indent=1)
    print(json.dumps(frz, indent=1))


def run():
    frz = json.load(open(fp("cohort_v4_prospective_freeze.json")))
    for f, h in frz["files"].items():
        if sha(fp(f)) != h:
            raise SystemExit(f"frozen file changed: {f}")
    import compare
    import interactions
    import prepare_inputs
    import reference
    import regions
    import star3d
    for m in (reference, prepare_inputs, star3d, compare, interactions, regions):
        m.P = fp
        m.ROOT = WS
    star3d.MANIFEST_PATH = fp("results/run_manifest.tsv")
    prepare_inputs.main()          # documented order (README): Phase 4a crosswalk BEFORE Phase 3 reference
    reference.main([])
    if len(sys.argv) > 2 and sys.argv[2] == "--downstream-only":
        compare.main([])
        interactions.main([])
        regions.main()
        return
    reps = {r["rep_id"]: r for r in csv.DictReader(open(fp("results/selected_representatives.tsv")), delimiter="\t")}
    inputs = {r["rep_id"]: r for r in csv.DictReader(open(fp("mappings/aligner_inputs.tsv")), delimiter="\t")}
    for pair in csv.DictReader(open(fp("results/selected_pairs.tsv")), delimiter="\t"):
        star3d.run_pair(pair, reps, inputs, star3d.CFG["star3d"]["replicates"])
    compare.main([])
    interactions.main([])
    regions.main()


if __name__ == "__main__":
    {"freeze": freeze, "run": run}[sys.argv[1]]()
