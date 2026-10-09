"""Phase 4: run ORIGINAL STAR3D v1.2 (defaults) for frozen pairs and parse its raw .aln output.

v5 single-run policy: for each selected RNA pair, one forward alignment from original STAR3D v1.2 with default
parameters, following the package's preprocessing procedure (README):
    java -cp STAR3D.jar Preprocess <query_id> <query_chain>
    java -cp STAR3D.jar Preprocess <target_id> <target_chain>
    java -jar STAR3D.jar -o <output.aln> -p <query_id> <query_chain> <target_id> <target_chain>
Order is the frozen query -> target order of results/selected_pairs.tsv (query = lexicographically smaller stable
ID). Steps per pair: prepared-input validation -> Preprocess once per RNA (bundled MC-Annotate + RemovePseudoknots)
-> preprocessing-product validation -> ONE alignment -> raw-output preservation + parse validation. No replicate
loop, no reverse-direction run and no automatic retry: a failure is recorded as a failure. Fresh, never-reused
attempt directories and in-container checksums are file-management safeguards, not repetitions.

Usage: star3d.py run PAIR_ID [PAIR_ID ...]      (append rows to results/run_manifest.tsv)
       star3d.py parse FILE                      (print parsed mapping)
Run layout: runs/<pair_id>/STAR3D_source (fresh extraction of the verified tarball)
            runs/<pair_id>/logs/<step>.{stdout,stderr}   runs/<pair_id>/out/<run_id>.aln[.pdb]
"""
import csv
import datetime as dt
import hashlib
import os
import re
import shutil
import subprocess
import sys
import tarfile
import time

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))
TARBALL = P("inputs/software/STAR3D_v1.2.tar.gz")
MAP_RE = re.compile(r"^(?P<c1>\S):(?P<n1>-?\d+)(?P<i1>[A-Za-z]?)<->(?P<c2>\S):(?P<n2>-?\d+)(?P<i2>[A-Za-z]?)$")
MANIFEST_FIELDS = ["run_id", "pair_id", "rfam_acc", "direction", "replicate", "query_rep", "target_rep",
                   "query_star3d_id", "target_star3d_id", "query_chain", "target_chain", "command", "image",
                   "image_id", "star3d_tarball_sha256", "query_input_sha256", "target_input_sha256",
                   "query_npk_ct_sha256", "target_npk_ct_sha256", "query_mca_sha256", "target_mca_sha256",
                   "parameters", "started_utc", "duration_s", "exit_code", "stdout", "stderr", "output_aln",
                   "output_sha256", "aligned_n", "rmsd", "status", "note", "reference_source", "rfam_release",
                   "seed_sha256", "code_commit"]


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest() if path and os.path.exists(path) else None


def parse_aln(path):
    """Return dict(aligned_n, rmsd, parameters, pairs=[((c,n,i),(c,n,i)), ...], header_lines)."""
    out = dict(aligned_n=None, rmsd=None, parameters={}, pairs=[], bad_lines=[])
    in_map = False
    for line in open(path):
        line = line.rstrip("\n")
        if line.startswith("#Aligned nucleotide:"):
            out["aligned_n"] = int(line.split(":")[1])
        elif line.startswith("#Alignment RMSD:"):
            out["rmsd"] = float(line.split(":")[1].strip().rstrip("A"))
        elif line.startswith("#Nucleotide mapping:"):
            in_map = True
        elif line.startswith("#") and ":" in line and not in_map:
            k, v = line[1:].split(":", 1)
            out["parameters"][k.strip()] = v.strip()
        elif in_map and line.strip():
            m = MAP_RE.match(line.strip())
            if not m:
                out["bad_lines"].append(line)
                continue
            out["pairs"].append(((m["c1"], int(m["n1"]), m["i1"]), (m["c2"], int(m["n2"]), m["i2"])))
    if out["aligned_n"] is not None and out["aligned_n"] != len(out["pairs"]):
        out["bad_lines"].append(f"declared {out['aligned_n']} != parsed {len(out['pairs'])}")
    return out


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


MANIFEST_PATH = None


def append_manifest(row):
    path = MANIFEST_PATH or P("results/run_manifest.tsv")
    new = not os.path.exists(path)
    with open(path, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=MANIFEST_FIELDS, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        if new:
            w.writeheader()
        w.writerow({k: ("NA" if row.get(k) in (None, "") else row[k]) for k in MANIFEST_FIELDS})


def docker(workdir, cmd, logbase):
    full = ["docker", "run", "--rm", "--platform", CFG["star3d"].get("platform", "linux/amd64"),
            "-v", f"{workdir}:/run/STAR3D_source", "-w", "/run/STAR3D_source", CFG["star3d"]["image"], "bash", "-c", cmd]
    t0 = time.time()
    started = dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds")
    p = subprocess.run(full, capture_output=True, text=True, timeout=3600)
    dur = round(time.time() - t0, 2)
    open(logbase + ".stdout", "w").write(p.stdout)
    open(logbase + ".stderr", "w").write(p.stderr)
    return p.returncode, dur, started, p.stdout


def image_id():
    return subprocess.run(["docker", "image", "inspect", CFG["star3d"]["image"], "--format", "{{.Id}}"],
                          capture_output=True, text=True).stdout.strip()


def code_commit():
    p = subprocess.run(["git", "-C", ROOT, "rev-parse", "HEAD"], capture_output=True, text=True)
    return p.stdout.strip() or "uncommitted"


def preprocessing_problems(work, sid, ch):
    """v3: validate preprocessing CONTENTS, not only exit codes (STAR3D ignores its external tools' exit codes).
    Fatal: missing/empty MC-Annotate .mca or no 'Base-pairs' section; npk.ct header/row count mismatch, malformed
    rows, or non-reciprocal partners. Returned separately as warnings: a non-reciprocal raw .ct (a known STAR3D
    source behaviour when one residue has two WWc partners; the later overwrites the earlier)."""
    d = os.path.join(work, "STAR3D_struct_info")
    fatal, warn = [], []
    mca = os.path.join(d, f"{sid}.mca")
    if not os.path.exists(mca) or os.path.getsize(mca) == 0:
        fatal.append("MC-Annotate output missing or empty")
    elif "Base-pairs" not in open(mca, errors="replace").read():
        fatal.append("MC-Annotate output has no Base-pairs section")

    def ct_check(path, label, sink):
        if not os.path.exists(path):
            sink.append(f"{label} missing")
            return
        lines = [x.split() for x in open(path) if x.strip()]
        try:
            n = int(lines[0][0])
            rows = [(int(r[0]), int(r[4])) for r in lines[1:]]
        except (IndexError, ValueError):
            sink.append(f"{label} malformed")
            return
        if len(rows) != n or [i for i, _ in rows] != list(range(1, n + 1)):
            sink.append(f"{label} declares {n} residues, has {len(rows)}")
            return
        partner = dict(rows)
        bad = [i for i, j in rows if j and (j < 1 or j > n or partner.get(j) != i)]
        if bad:
            sink.append(f"{label} non-reciprocal partners at {bad[:6]}")
    ct_check(os.path.join(d, f"{sid}_{ch}.npk.ct"), "npk.ct", fatal)
    ct_check(os.path.join(d, f"{sid}_{ch}.ct"), "raw .ct", warn)
    return fatal, warn


def preprocess_and_gate(work, ids, rep_order, base, tag, k, common, runner=None):
    """Mount check + STAR3D preprocessing for both RNAs. Returns True only if EVERY step completed and passed its
    checks. Any failure (mount view mismatch, stale intermediates present, nonzero exit, missing/empty npk.ct,
    container/host checksum mismatch of the npk.ct) is recorded in the manifest and stops the pair's attempt."""
    runner = runner or docker
    # 1. container must see exactly the host input bytes and NO pre-existing intermediates
    rc, _, _, so = runner(work, "sha256sum PDB/*.pdb; ls STAR3D_struct_info 2>/dev/null | wc -l",
                          os.path.join(base, "logs", "mount_check"))
    seen = {l.split()[1].split("/")[-1][:-4]: l.split()[0] for l in so.splitlines() if l.strip().endswith(".pdb")}
    lines = so.strip().splitlines()
    bad = rc != 0 or not lines or any(seen.get(v[0]) != v[2] for v in ids.values()) or lines[-1].strip() != "0"
    if bad:
        append_manifest(dict(common, run_id=f"{tag}__a{k}__mount_check", direction="preprocess",
                             command="sha256sum PDB/*.pdb; ls STAR3D_struct_info | wc -l", exit_code=rc,
                             status="failed_mount_check", note=("container view differs from host or stale "
                                                                "intermediates present: " + so.strip())[:200],
                             stdout=os.path.relpath(os.path.join(base, "logs", "mount_check.stdout"), ROOT)))
        return False
    # 2. preprocessing, each followed by an in-container checksum of its product
    for rid in rep_order:
        sid, ch, _ = ids[rid]
        cmd = f"java -cp STAR3D.jar Preprocess {sid} {ch}"
        rc, dur, st, so = runner(work, cmd, os.path.join(base, "logs", f"preprocess_{sid}"))
        npk = os.path.join(work, "STAR3D_struct_info", f"{sid}_{ch}.npk.ct")
        status = "completed" if rc == 0 and os.path.exists(npk) and os.path.getsize(npk) > 0 else "failed"
        note = None
        if status == "completed":
            rc2, _, _, so2 = runner(work, f"sha256sum STAR3D_struct_info/{sid}_{ch}.npk.ct",
                                    os.path.join(base, "logs", f"post_check_{sid}"))
            if rc2 != 0 or not so2.split() or so2.split()[0] != sha(npk):
                status = "failed_mount_mismatch"
                note = f"container npk.ct sha {so2.split()[0] if so2.split() else 'NA'} != host {sha(npk)}"
            else:
                fatal, warn = preprocessing_problems(work, sid, ch)
                if fatal:
                    status = "failed_intermediate_invalid"
                note = "; ".join(fatal + [f"WARNING {w}" for w in warn]) or None
        append_manifest(dict(common, run_id=f"{tag}__a{k}__preprocess_{sid}", direction="preprocess", command=cmd,
                             started_utc=st, duration_s=dur, exit_code=rc, status=status, note=note,
                             stdout=os.path.relpath(os.path.join(base, "logs", f"preprocess_{sid}.stdout"), ROOT),
                             stderr=os.path.relpath(os.path.join(base, "logs", f"preprocess_{sid}.stderr"), ROOT),
                             output_aln=os.path.relpath(npk, ROOT), output_sha256=sha(npk)))
        if status != "completed":          # ANY non-completed preprocessing status stops the attempt
            return False
    return True


def run_pair(pair, reps, inputs):
    if sha(TARBALL) != CFG["sources"]["star3d_sha256"]:
        raise SystemExit("STAR3D tarball checksum mismatch")
    pid = pair["pair_id"]
    tag = os.path.basename(pid)
    # never reuse a host path: colima/sshfs can serve a cached view of a moved directory at the same path
    k = 1
    while os.path.exists(P("runs", pid, f"attempt{k}")) or os.path.exists(P("runs", "_superseded", f"{pid}__attempt{k}")) \
            or any(d.startswith(f"{os.path.basename(pid)}__attempt{k}_") for d in os.listdir(P("runs", "_superseded")) if os.path.isdir(P("runs", "_superseded", d))):
        k += 1
    base = P("runs", pid, f"attempt{k}")
    os.makedirs(os.path.join(base, "logs"))
    with tarfile.open(TARBALL) as t:
        t.extractall(base, filter="data")
    work = os.path.join(base, "STAR3D_source")
    os.makedirs(os.path.join(work, "PDB"))
    os.makedirs(os.path.join(work, "out"))
    q, t_ = reps[pair["query_rep"]], reps[pair["target_rep"]]
    ids = {}
    for r in (q, t_):
        meta = inputs[r["rep_id"]]
        src = P(meta["file"])
        if sha(src) != meta["sha256"]:
            raise SystemExit(f"input {src} changed since preparation")
        shutil.copyfile(src, os.path.join(work, "PDB", meta["star3d_id"] + ".pdb"))
        ids[r["rep_id"]] = (meta["star3d_id"], r["auth_asym_id"], meta["sha256"])
    img = image_id()
    common = dict(pair_id=pid, rfam_acc=pair["rfam_acc"], image=CFG["star3d"]["image"], image_id=img,
                  star3d_tarball_sha256=sha(TARBALL), reference_source="Rfam.seed.gz",
                  rfam_release=CFG["reference"]["rfam_release"], seed_sha256=CFG["reference"]["seed_sha256"],
                  code_commit=code_commit())
    if not preprocess_and_gate(work, ids, (q["rep_id"], t_["rep_id"]), base, tag, k, common):
        print(f"{pid}: preprocessing/mount gate FAILED -> no alignment for this attempt (see manifest)", flush=True)
        return None, "preprocessing_gate_failed"
    flags = " ".join(CFG["star3d"]["extra_flags"])
    a, b = q, t_                                   # fixed forward order: query -> target (recorded explicitly)
    sa, ca, ha = ids[a["rep_id"]]
    sb, cb, hb = ids[b["rep_id"]]
    run_id = f"{tag}__a{k}__forward"
    out = f"out/{run_id}.aln"
    cmd = f"java -jar STAR3D.jar -o {out} {flags} {sa} {ca} {sb} {cb}"
    rc, dur, st, so = docker(work, cmd, os.path.join(base, "logs", run_id))
    outp = os.path.join(work, out)
    if rc != 0:
        status, n, rmsd, note = "failed", None, None, "nonzero exit (not retried)"
    elif not os.path.exists(outp):
        status, n, rmsd = "no_alignment", 0, None
        note = "no output file; stdout: " + so.strip()[:120]
    else:
        pa = parse_aln(outp)
        status = "completed" if not pa["bad_lines"] else "parse_error"
        n, rmsd, note = pa["aligned_n"], pa["rmsd"], ";".join(pa["bad_lines"])[:200]
    si = os.path.join(work, "STAR3D_struct_info")
    append_manifest(dict(common, run_id=run_id, direction="forward", replicate="NA", query_rep=a["rep_id"],
                         target_rep=b["rep_id"], query_star3d_id=sa, target_star3d_id=sb, query_chain=ca,
                         target_chain=cb, command=cmd, query_input_sha256=ha, target_input_sha256=hb,
                         query_npk_ct_sha256=sha(os.path.join(si, f"{sa}_{ca}.npk.ct")),
                         target_npk_ct_sha256=sha(os.path.join(si, f"{sb}_{cb}.npk.ct")),
                         query_mca_sha256=sha(os.path.join(si, f"{sa}.mca")),
                         target_mca_sha256=sha(os.path.join(si, f"{sb}.mca")),
                         parameters="defaults (-r 4.0 -s 3 -g -5 -e -2 -m 3 -i 0 -t 1) + " + flags,
                         started_utc=st, duration_s=dur, exit_code=rc,
                         stdout=os.path.relpath(os.path.join(base, "logs", run_id + ".stdout"), ROOT),
                         stderr=os.path.relpath(os.path.join(base, "logs", run_id + ".stderr"), ROOT),
                         output_aln=os.path.relpath(outp, ROOT) if os.path.exists(outp) else None,
                         output_sha256=sha(outp), aligned_n=n, rmsd=rmsd, status=status,
                         note=f"single forward alignment; order {a['rep_id']} -> {b['rep_id']}" + (f"; {note}" if note else "")))
    print(run_id, status, n, rmsd, f"{dur}s", flush=True)
    return run_id, status


def main():
    if sys.argv[1] == "parse":
        pa = parse_aln(sys.argv[2])
        print(pa["aligned_n"], pa["rmsd"], pa["parameters"], pa["pairs"][:5], pa["bad_lines"])
        return
    pairs = {p["pair_id"]: p for p in read_tsv(P("results/selected_pairs.tsv"))}
    reps = {r["rep_id"]: r for r in read_tsv(P("results/selected_representatives.tsv"))}
    inputs = {r["rep_id"]: r for r in read_tsv(P("mappings/aligner_inputs.tsv"))}
    for pid in sys.argv[2:]:
        run_pair(pairs[pid], reps, inputs)


if __name__ == "__main__":
    main()
