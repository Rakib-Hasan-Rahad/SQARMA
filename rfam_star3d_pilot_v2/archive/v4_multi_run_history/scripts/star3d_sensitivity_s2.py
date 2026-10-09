"""v4 SENSITIVITY S2 (isolates the Preprocess.java overwrite; NOT unmodified STAR3D preprocessing).
Declared before running: for 7MLW chain F only, the original .ct is changed at ONE residue conflict: residue 16 keeps
its cis Ww/Ww partner (index 44 = auth 47, C-G) instead of the last-written Wh/Wh partner (index 41 = auth 44);
index 41 becomes unpaired. Every other pair, 5U3G's .ct, the .mca files, RemovePseudoknots and STAR3D.jar are the
original ones. Runs: RF00442 pair, both directions, 1 replicate (retry <=2 on JVM signal)."""
import csv
import os
import shutil
import sys
import tarfile

sys.path.insert(0, os.path.dirname(__file__))
import star3d  # noqa: E402
import star3d_sensitivity as s1  # noqa: E402

P = star3d.P
PID = "RF00442__5U3G_B__7MLW_F"
SRC = P("runs", PID, "attempt1", "STAR3D_source", "STAR3D_struct_info")


def main():
    k = 1
    while os.path.exists(P("runs_sensitivity", "S2_overwrite_fix", PID, f"attempt{k}")):
        k += 1
    base = P("runs_sensitivity", "S2_overwrite_fix", PID, f"attempt{k}")
    os.makedirs(os.path.join(base, "logs"))
    with tarfile.open(star3d.TARBALL) as t:
        t.extractall(base, filter="data")
    work = os.path.join(base, "STAR3D_source")
    si = os.path.join(work, "STAR3D_struct_info")
    for sub in ("PDB", "out", "STAR3D_struct_info"):
        os.makedirs(os.path.join(work, sub), exist_ok=True)
    for stem in ("5u3gb", "7mlwf"):
        shutil.copyfile(P("runs", "_inputs", stem + ".pdb"), os.path.join(work, "PDB", stem + ".pdb"))
        shutil.copyfile(os.path.join(SRC, stem + ".mca"), os.path.join(si, stem + ".mca"))
    shutil.copyfile(os.path.join(SRC, "5u3gb_B.ct"), os.path.join(si, "5u3gb_B.ct"))
    rows = [l.split() for l in open(os.path.join(SRC, "7mlwf_F.ct")) if l.strip()]
    assert rows[16][4] == "41" and rows[41][4] == "16" and rows[44][4] == "16", "unexpected original .ct state"
    rows[16][4], rows[41][4], rows[44][4] = "44", "0", "16"
    with open(os.path.join(si, "7mlwf_F.ct"), "w") as f:
        f.write("\t".join(rows[0]) + "\n")
        for r in rows[1:]:
            f.write("\t".join(r) + "\n")
    man = []
    for stem, ch in (("5u3gb", "B"), ("7mlwf", "F")):
        cmd = f"tools/RemovePseudoknots -m STAR3D_struct_info/{stem}_{ch}.ct STAR3D_struct_info/{stem}_{ch}.npk.ct"
        rc, dur, st, so = star3d.docker(work, cmd, os.path.join(base, "logs", f"removepk_{stem}"))
        fatal, warn = star3d.preprocessing_problems(work, stem, ch)
        if rc or fatal:
            raise SystemExit(f"S2 preprocessing invalid: {fatal}")
        man.append(dict(run_id=f"{PID}__S2__removepk_{stem}", pair_id=PID, direction="preprocess_S2", replicate="NA",
                        command=cmd, exit_code=rc, duration_s=dur, started_utc=st, status="completed",
                        note="; ".join(warn) or "NA", output_aln="NA",
                        output_sha256=star3d.sha(os.path.join(si, f"{stem}_{ch}.npk.ct")), aligned_n="NA", rmsd="NA"))
    flags = " ".join(star3d.CFG["star3d"]["extra_flags"])
    for direction, (a, b) in (("forward", (("5u3gb", "B"), ("7mlwf", "F"))), ("reverse", (("7mlwf", "F"), ("5u3gb", "B")))):
        for attempt in range(1, 4):
            run_id = f"{PID}__S2__{direction}__try{attempt}"
            out = f"out/{run_id}.aln"
            cmd = f"java -jar STAR3D.jar -o {out} {flags} {a[0]} {a[1]} {b[0]} {b[1]}"
            rc, dur, st, so = star3d.docker(work, cmd, os.path.join(base, "logs", run_id))
            outp = os.path.join(work, out)
            pa = star3d.parse_aln(outp) if rc == 0 and os.path.exists(outp) else None
            status = "failed" if rc else ("no_alignment" if pa is None else ("completed" if not pa["bad_lines"] else "parse_error"))
            man.append(dict(run_id=run_id, pair_id=PID, direction=direction, replicate="1", command=cmd, exit_code=rc,
                            duration_s=dur, started_utc=st, status=status, note="NA",
                            output_aln=os.path.relpath(outp, star3d.ROOT) if os.path.exists(outp) else "NA",
                            output_sha256=star3d.sha(outp) if os.path.exists(outp) else "NA",
                            aligned_n=pa["aligned_n"] if pa else "NA", rmsd=pa["rmsd"] if pa else "NA"))
            print(run_id, status, man[-1]["aligned_n"], man[-1]["rmsd"], flush=True)
            if not (rc >= 128 or rc < 0):
                break
    out = P("results", "sensitivity", "S2_run_manifest.tsv")
    with open(out, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(man[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(man)
    s1.OUT = P("results", "sensitivity")
    pairs = [p for p in s1.R(P("results/selected_pairs.tsv")) if p["pair_id"] == PID]
    import io  # noqa: F401
    orig = os.path.join(s1.OUT, "S1_vs_default.tsv")
    keep = open(orig).read()
    s1.compare_to_default(man, pairs)
    os.replace(orig, os.path.join(s1.OUT, "S2_vs_default.tsv"))
    open(orig, "w").write(keep)


if __name__ == "__main__":
    main()
