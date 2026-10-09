"""v4 SENSITIVITY ANALYSIS S1 ('paper pairing rule'). NOT the primary method and NOT unmodified STAR3D preprocessing.

Declared before running (2026-10-09):
  Question: do the pilot's STAR3D correspondences depend on STAR3D v1.2's source-level pair selection, which differs
  from the paper (all cis W-edge MC-Annotate pairs, incl. non-canonical identities and Wh/Ws sub-edges, and a
  last-written-wins overwrite for residues with two such partners)?
  Variant S1: the .ct given to the ORIGINAL RemovePseudoknots contains only cis 'Ww/Ww' MC-Annotate pairs with
  identity AU/UA/GC/CG/GU/UG (built by scripts/star3d_preproc_audit.py; conflict-free for all 11 RNAs).
  Everything else is unchanged and original: same PDB inputs, same MC-Annotate .mca (used by loop scoring), same
  RemovePseudoknots invocation as Preprocess.java, same STAR3D.jar, defaults + -p, same container.
  Runs: 7 pilot pairs x 2 directions x 1 replicate (default-run replicates were identical in every group).
  A run killed by a JVM signal (exit >= 128) is retried at most twice; every attempt is recorded.
Outputs: runs_sensitivity/S1_paper_rule/<pair>/attemptN/, results/sensitivity/S1_run_manifest.tsv,
         results/sensitivity/S1_vs_default.tsv
Usage: star3d_sensitivity.py"""
import csv
import os
import shutil
import sys
import tarfile

sys.path.insert(0, os.path.dirname(__file__))
import compare  # noqa: E402
import star3d  # noqa: E402

ROOT, P = star3d.ROOT, star3d.P
S1DIR = P("deliverables", "2026-10-09_v4", "star3d_sensitivity")
OUT = P("results", "sensitivity")


def R(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))


def main():
    os.makedirs(OUT, exist_ok=True)
    if star3d.sha(star3d.TARBALL) != star3d.CFG["sources"]["star3d_sha256"]:
        raise SystemExit("STAR3D tarball checksum mismatch")
    reps = {r["rep_id"]: r for r in R(P("results/selected_representatives.tsv"))}
    inputs = {r["rep_id"]: r for r in R(P("mappings/aligner_inputs.tsv"))}
    summ = {r["rna"]: r for r in R(os.path.join(S1DIR, "preproc_summary.tsv"))}
    pairs = R(P("results/selected_pairs.tsv"))
    man = []
    for pair in pairs:
        pid = pair["pair_id"]
        k = 1
        while os.path.exists(P("runs_sensitivity", "S1_paper_rule", pid, f"attempt{k}")):
            k += 1
        base = P("runs_sensitivity", "S1_paper_rule", pid, f"attempt{k}")
        os.makedirs(os.path.join(base, "logs"))
        with tarfile.open(star3d.TARBALL) as t:
            t.extractall(base, filter="data")
        work = os.path.join(base, "STAR3D_source")
        for sub in ("PDB", "out", "STAR3D_struct_info"):
            os.makedirs(os.path.join(work, sub), exist_ok=True)
        ids = {}
        ok = True
        for rid in (pair["query_rep"], pair["target_rep"]):
            meta, ch = inputs[rid], reps[rid]["auth_asym_id"]
            sid = meta["star3d_id"]
            if star3d.sha(P(meta["file"])) != meta["sha256"]:
                raise SystemExit(f"input {meta['file']} changed")
            shutil.copyfile(P(meta["file"]), os.path.join(work, "PDB", sid + ".pdb"))
            src = P(summ[f"{sid}_{ch}"]["source_dir"])
            shutil.copyfile(os.path.join(src, sid + ".mca"), os.path.join(work, "STAR3D_struct_info", sid + ".mca"))
            shutil.copyfile(os.path.join(S1DIR, f"{sid}_{ch}.S1.ct"), os.path.join(work, "STAR3D_struct_info", f"{sid}_{ch}.ct"))
            cmd = f"tools/RemovePseudoknots -m STAR3D_struct_info/{sid}_{ch}.ct STAR3D_struct_info/{sid}_{ch}.npk.ct"
            rc, dur, st, so = star3d.docker(work, cmd, os.path.join(base, "logs", f"removepk_{sid}"))
            fatal, warn = star3d.preprocessing_problems(work, sid, ch)
            man.append(dict(run_id=f"{pid}__S1__removepk_{sid}", pair_id=pid, direction="preprocess_S1", replicate="NA",
                            command=cmd, exit_code=rc, duration_s=dur, started_utc=st,
                            status="failed_intermediate_invalid" if (rc != 0 or fatal) else "completed",
                            note="; ".join(fatal + warn) or "NA",
                            output_sha256=star3d.sha(os.path.join(work, "STAR3D_struct_info", f"{sid}_{ch}.npk.ct"))
                            if os.path.exists(os.path.join(work, "STAR3D_struct_info", f"{sid}_{ch}.npk.ct")) else "NA",
                            output_aln="NA", aligned_n="NA", rmsd="NA"))
            ok &= man[-1]["status"] == "completed"
            ids[rid] = (sid, ch)
        if not ok:
            print(pid, "S1 preprocessing invalid -> no alignment")
            continue
        flags = " ".join(star3d.CFG["star3d"]["extra_flags"])
        for direction, (a, b) in (("forward", (pair["query_rep"], pair["target_rep"])),
                                  ("reverse", (pair["target_rep"], pair["query_rep"]))):
            (sa, ca), (sb, cb) = ids[a], ids[b]
            for attempt in range(1, 4):
                run_id = f"{pid}__S1__{direction}__try{attempt}"
                out = f"out/{run_id}.aln"
                cmd = f"java -jar STAR3D.jar -o {out} {flags} {sa} {ca} {sb} {cb}"
                rc, dur, st, so = star3d.docker(work, cmd, os.path.join(base, "logs", run_id))
                outp = os.path.join(work, out)
                if rc != 0:
                    status, n, rmsd = "failed", None, None
                elif not os.path.exists(outp):
                    status, n, rmsd = "no_alignment", 0, None
                else:
                    pa = star3d.parse_aln(outp)
                    status = "completed" if not pa["bad_lines"] else "parse_error"
                    n, rmsd = pa["aligned_n"], pa["rmsd"]
                man.append(dict(run_id=run_id, pair_id=pid, direction=direction, replicate="1", command=cmd,
                                exit_code=rc, duration_s=dur, started_utc=st, status=status, note="NA",
                                output_aln=os.path.relpath(outp, ROOT) if os.path.exists(outp) else "NA",
                                output_sha256=star3d.sha(outp) if os.path.exists(outp) else "NA",
                                aligned_n=n, rmsd=rmsd))
                print(run_id, status, n, rmsd, f"{dur}s", flush=True)
                if not (rc >= 128 or rc < 0):
                    break
    with open(os.path.join(OUT, "S1_run_manifest.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(man[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(man)
    compare_to_default(man, pairs)


def compare_to_default(man, pairs):
    cw = compare.crosswalks()
    default = {(r["pair_id"], r["direction"]): r for r in R(P("results/run_manifest.tsv"))
               if r["replicate"] == "1" and r["direction"] in ("forward", "reverse") and not r["run_id"].startswith("attempt")
               and r["status"] == "completed"}
    # retained default reverse rep1 for RF00442 crashed: fall back to rep2 (replicates identical)
    for r in R(P("results/run_manifest.tsv")):
        key = (r["pair_id"], r["direction"])
        if key not in default and r["status"] == "completed" and not r["run_id"].startswith("attempt") \
                and r["direction"] in ("forward", "reverse"):
            default[key] = r
    refs = {}
    for r in R(P("results/reference_pairs.tsv")):
        refs.setdefault(r["pair_id"], {})[int(r["row_A_index"])] = int(r["row_B_index"])
    rows = []

    def mapping(path, q, t, direction):
        pa = star3d.parse_aln(P(path))
        left, right = (q, t) if direction == "forward" else (t, q)
        il, ir = compare.resid_index(cw[left]), compare.resid_index(cw[right])
        m = {}
        for l, r in pa["pairs"]:
            a, b = il[l], ir[r]
            if direction == "reverse":
                a, b = b, a
            m[a] = b
        return m
    for pair in pairs:
        pid, q, t = pair["pair_id"], pair["query_rep"], pair["target_rep"]
        for direction in ("forward", "reverse"):
            s1 = [m for m in man if m["pair_id"] == pid and m["direction"] == direction and m["status"] == "completed"]
            d = default.get((pid, direction))
            if not s1 or not d:
                rows.append(dict(pair_id=pid, direction=direction, status="unavailable"))
                continue
            ms, md, rf = mapping(s1[-1]["output_aln"], q, t, direction), mapping(d["output_aln"], q, t, direction), refs[pid]
            same = sum(1 for i in ms if md.get(i) == ms[i])
            rows.append(dict(pair_id=pid, tier=pair["tier"], direction=direction, status="completed",
                             default_aligned=len(md), S1_aligned=len(ms), identical_mapping=ms == md,
                             shared_with_default=same, only_default=len(set(md.items()) - set(ms.items())),
                             only_S1=len(set(ms.items()) - set(md.items())),
                             default_same_as_rfam=sum(1 for i in md if rf.get(i) == md[i]),
                             S1_same_as_rfam=sum(1 for i in ms if rf.get(i) == ms[i]),
                             default_rmsd=d["rmsd"], S1_rmsd=s1[-1]["rmsd"],
                             S1_attempts=len([m for m in man if m["pair_id"] == pid and m["direction"] == direction])))
    with open(os.path.join(OUT, "S1_vs_default.tsv"), "w", newline="") as f:
        fields = list(next(r for r in rows if r["status"] == "completed"))
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", restval="NA")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print(r)


if __name__ == "__main__":
    main()
