"""Section 8 (v2.1): fresh reproduction by THIS agent of the preQ1 candidate (not independent external validation).

Steps (outputs only under audit/fresh_repro/; retained study files are never overwritten):
 1. re-download mmCIF (3FU2, 6VUI, 7REX) and the STAR3D tarball from the recorded URLs; compare compressed AND
    decompressed sha256 with the pinned/recorded values; a mismatch writes a diagnostic, quarantines the bytes and
    BLOCKS every dependent step (v3 repair B); the run then exits nonzero;
 2. rebuild the STAR3D coordinate inputs from the fresh mmCIF with the unchanged prepare() policy; compare bytes,
    residue identities and coordinates with the retained inputs;
 3. rerun ORIGINAL STAR3D (fresh tarball, star3d-runtime:1, defaults) for the 3 preQ1 pairs, both directions x 3;
    compare parsed mappings with the retained runs;
 4. rerun FR3D (pinned commit) on the fresh mmCIF; compare normalized annotations with the retained ones.
Usage: fresh_repro.py
"""
import csv
import gzip
import hashlib
import json
import os
import shutil
import sys
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import fetch  # noqa: E402
import interactions  # noqa: E402
import prepare_inputs  # noqa: E402
import star3d  # noqa: E402

ROOT = star3d.ROOT
FR = os.path.join(ROOT, "audit", "fresh_repro")
PDBS = ["3FU2", "6VUI", "7REX"]
PAIRS = ["RF00522__3FU2_A__6VUI_A", "RF00522__3FU2_A__7REX_A", "RF00522__6VUI_A__7REX_A"]
REPS = ["RF00522__3FU2_A", "RF00522__6VUI_A", "RF00522__7REX_A"]


def sha_bytes(b):
    return hashlib.sha256(b).hexdigest()


def sha(path):
    return sha_bytes(open(path, "rb").read())


def get(url, dest, tries=4):
    """Fresh download into audit/fresh_repro (cached there after the first success; bounded retries)."""
    import time
    if os.path.exists(dest) and os.path.getsize(dest) > 0:
        return open(dest, "rb").read()
    last = None
    for k in range(tries):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": fetch.UA})
            data = urllib.request.urlopen(req, timeout=120, context=fetch.SSL_CTX).read()
            break
        except (OSError, ConnectionError) as e:
            last = e
            time.sleep(5 * (k + 1))
    else:
        raise RuntimeError(f"download failed after {tries} tries: {url}: {last}")
    if not data:
        raise RuntimeError(f"empty response {url}")
    os.makedirs(os.path.dirname(dest), exist_ok=True)
    open(dest, "wb").write(data)
    return data


class InputMismatch(RuntimeError):
    pass


class InputGate:
    """v3 repair B: strict pinned-input policy. A changed download or rebuilt input is never adopted: a diagnostic is
    written FIRST, the unexpected bytes are quarantined, and every dependent rep/pair is blocked so that no
    preprocessing, annotation or alignment runs on rejected inputs. Compressed-container-only changes are
    distinguished in the diagnostic but are also rejected (a later explicit source-version decision is required)."""

    def __init__(self, root):
        self.root = root
        self.diag_dir = os.path.join(root, "diagnostics")
        self.q_dir = os.path.join(root, "quarantine")
        self.blocked = {}            # key ('rep:<rep_id>' or 'software') -> reason
        self.records = []

    def _reject(self, key, rel, data, diag):
        os.makedirs(self.diag_dir, exist_ok=True)
        name = rel.replace("/", "__")
        with open(os.path.join(self.diag_dir, name + ".mismatch.json"), "w") as f:   # diagnostic before anything else
            json.dump(diag, f, indent=1, default=str)
        if data is not None:
            os.makedirs(self.q_dir, exist_ok=True)
            open(os.path.join(self.q_dir, name + ".rejected"), "wb").write(data)
        for k in key if isinstance(key, (list, tuple)) else [key]:
            self.blocked[k] = diag["verdict"]

    def check_download(self, key, rel, data, recorded_sha, pinned_path=None, fresh_path=None):
        rec = dict(file=rel, recorded_sha256=recorded_sha, fresh_sha256=sha_bytes(data),
                   compressed_identical=sha_bytes(data) == recorded_sha)
        if pinned_path and rel.endswith(".gz"):
            try:
                fd = gzip.decompress(data)
            except OSError:
                fd = None
            pd = gzip.open(pinned_path).read()
            rec.update(fresh_decompressed_sha256=sha_bytes(fd) if fd is not None else "not_gzip",
                       pinned_decompressed_sha256=sha_bytes(pd), decompressed_identical=fd == pd)
        ok = rec["compressed_identical"] and rec.get("decompressed_identical", True)
        if ok:
            rec["verdict"] = "accepted_identical"
        else:
            rec["verdict"] = ("rejected_container_only_change" if rec.get("decompressed_identical")
                              else "rejected_content_change")
            self._reject(key, rel, data, rec)
            if fresh_path and os.path.exists(fresh_path):
                os.remove(fresh_path)        # never leave rejected bytes where a later run would reuse them
        self.records.append(rec)
        return rec

    def check_rebuilt(self, key, rel, fresh_bytes, retained_bytes):
        rec = dict(file=rel, retained_sha256=sha_bytes(retained_bytes), fresh_sha256=sha_bytes(fresh_bytes),
                   bytes_identical=fresh_bytes == retained_bytes)
        rec["verdict"] = "accepted_identical" if rec["bytes_identical"] else "rejected_rebuilt_input_differs"
        if not rec["bytes_identical"]:
            self._reject(key, rel, fresh_bytes, rec)
        self.records.append(rec)
        return rec

    def allowed_pair(self, pair):
        return not ("software" in self.blocked or f"rep:{pair['query_rep']}" in self.blocked
                    or f"rep:{pair['target_rep']}" in self.blocked)

    def allowed_rep(self, rep_id):
        return f"rep:{rep_id}" not in self.blocked


def run_allowed_pairs(gate, pairs, runner):
    """Run `runner(pair)` only for pairs whose inputs passed the gate; return per-pair status."""
    out = {}
    for pid, pair in pairs.items():
        if gate.allowed_pair(pair):
            runner(pair)
            out[pid] = "run"
        else:
            out[pid] = "blocked_input_mismatch"
    return out


def R(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def main():
    os.makedirs(FR, exist_ok=True)
    man = {r["local_path"]: r for r in R(os.path.join(ROOT, "metadata/sources_manifest.tsv")) if r["status"] == "ok"}
    # 1. downloads (strict gate; v3 repair B)
    gate = InputGate(FR)
    rep_of_pdb = {rid.split("__")[1].split("_")[0]: rid for rid in REPS}
    dl = []
    for pdb in PDBS:
        rel = f"inputs/structures/mmcif/{pdb}.cif.gz"
        url = man[rel]["url"]
        fresh = os.path.join(FR, rel)
        data = get(url, fresh)
        rec = gate.check_download(f"rep:{rep_of_pdb[pdb]}", rel, data, man[rel]["sha256"],
                                  pinned_path=os.path.join(ROOT, rel), fresh_path=fresh)
        rec["url"] = url
        dl.append(rec)
    rel = "inputs/software/STAR3D_v1.2.tar.gz"
    fresh_tar = os.path.join(FR, rel)
    data = get(man[rel]["url"], fresh_tar)
    rec = gate.check_download("software", rel, data, man[rel]["sha256"], fresh_path=fresh_tar)
    rec["url"] = man[rel]["url"]
    dl.append(rec)
    rec = {"note": "reproduction by the same AI agent; not independent external validation", "downloads": dl}
    _write_partial(rec, gate)
    print(json.dumps(dl, indent=1))

    # fresh root: copy only the small tables the unchanged code needs; coordinates come from FRESH downloads
    for f in ("config.yaml", "results/selected_representatives.tsv", "results/selected_pairs.tsv",
              "results/residue_crosswalk.tsv"):
        os.makedirs(os.path.dirname(os.path.join(FR, f)), exist_ok=True)
        shutil.copyfile(os.path.join(ROOT, f), os.path.join(FR, f))
    os.makedirs(os.path.join(FR, "runs", "_superseded"), exist_ok=True)
    fp = lambda *a: os.path.join(FR, *a)  # noqa: E731

    # 2. rebuild coordinate inputs from fresh mmCIF
    prepare_inputs.P = fp
    prepare_inputs.CFG = star3d.CFG
    reps = {r["rep_id"]: r for r in R(os.path.join(ROOT, "results/selected_representatives.tsv"))}
    retained = {r["rep_id"]: r for r in R(os.path.join(ROOT, "mappings/aligner_inputs.tsv"))}
    inp, comp_inputs = [], []
    for rid in REPS:
        if not gate.allowed_rep(rid):
            comp_inputs.append(dict(rep_id=rid, status="blocked_input_mismatch"))
            continue
        meta, conv = prepare_inputs.prepare(reps[rid], None)
        meta["file"] = os.path.relpath(os.path.join(ROOT, meta["file"]), FR)   # prepare() returns study-root-relative
        inp.append(meta)
        old = os.path.join(ROOT, retained[rid]["file"])
        new = fp(meta["file"])
        same_bytes = sha(old) == sha(new)
        gate.check_rebuilt(f"rep:{rid}", meta["file"], open(new, "rb").read(), open(old, "rb").read())
        import gemmi
        a, b = gemmi.read_structure(old), gemmi.read_structure(new)
        ra, rb = [(r.seqid.num, r.seqid.icode, r.name) for r in a[0][0]], [(r.seqid.num, r.seqid.icode, r.name) for r in b[0][0]]
        maxd = 0.0
        if ra == rb:
            for x, y in zip(a[0][0], b[0][0]):
                pa = {at.name: at.pos for at in x}
                for at in y:
                    if at.name in pa:
                        maxd = max(maxd, at.pos.dist(pa[at.name]))
        comp_inputs.append(dict(rep_id=rid, retained_sha256=sha(old), fresh_sha256=sha(new), bytes_identical=same_bytes,
                                residue_ids_and_names_identical=ra == rb, n_residues=len(rb),
                                max_atom_displacement_A=round(maxd, 4)))
    inp = [m for m in inp if gate.allowed_rep(m["rep_id"])]      # rejected rebuilt inputs are never handed on
    if inp:
        with open(fp("mappings/aligner_inputs.tsv"), "w", newline="") as f:
            w = csv.DictWriter(f, fieldnames=list(inp[0].keys()), delimiter="\t", lineterminator="\n")
            w.writeheader()
            w.writerows(inp)
    rec["inputs"] = comp_inputs
    _write_partial(rec, gate)
    print(json.dumps(comp_inputs, indent=1))

    # 3. original STAR3D rerun with the FRESH tarball
    star3d.ROOT, star3d.P = FR, fp
    star3d.TARBALL = fp("inputs/software/STAR3D_v1.2.tar.gz")
    star3d.MANIFEST_PATH = fp("results/run_manifest.tsv")
    pairs = {p["pair_id"]: p for p in R(fp("results/selected_pairs.tsv"))}
    inputs = {r["rep_id"]: r for r in inp}
    rec["star3d_gate"] = run_allowed_pairs(
        gate, {pid: pairs[pid] for pid in PAIRS},
        lambda p: star3d.run_pair(p, reps, inputs, star3d.CFG["star3d"]["replicates"]))
    _write_partial(rec, gate)
    runs_new = ([r for r in R(fp("results/run_manifest.tsv")) if r["direction"] in ("forward", "reverse")]
                if os.path.exists(fp("results/run_manifest.tsv")) else [])
    runs_old = {r["run_id"]: r for r in R(os.path.join(ROOT, "results/run_manifest.tsv"))
                if r["pair_id"] in PAIRS and r["direction"] in ("forward", "reverse") and not r["run_id"].startswith("attempt")}
    star = []
    for r in runs_new:
        old = next((o for o in runs_old.values() if o["pair_id"] == r["pair_id"]
                    and o["direction"] == r["direction"] and o["replicate"] == r["replicate"]), None)
        new_map = star3d.parse_aln(fp(r["output_aln"]))["pairs"] if r["status"] == "completed" else None
        old_map = star3d.parse_aln(os.path.join(ROOT, old["output_aln"]))["pairs"] if old and old["status"] == "completed" else None
        star.append(dict(pair_id=r["pair_id"], direction=r["direction"], replicate=r["replicate"],
                         fresh_status=r["status"], retained_status=old["status"] if old else None,
                         fresh_aligned_n=r["aligned_n"], retained_aligned_n=old["aligned_n"] if old else None,
                         fresh_rmsd=r["rmsd"], retained_rmsd=old["rmsd"] if old else None,
                         mapping_identical=(new_map == old_map) if new_map is not None else False,
                         fresh_npk_query_identical=r["query_npk_ct_sha256"] == (old or {}).get("query_npk_ct_sha256"),
                         fresh_npk_target_identical=r["target_npk_ct_sha256"] == (old or {}).get("target_npk_ct_sha256")))
    rec["star3d"] = star
    for s in star:
        print(s)

    # 4. FR3D rerun on fresh mmCIF
    interactions.P = fp
    interactions.CFG = star3d.CFG
    cw = {}
    for r in R(fp("results/residue_crosswalk.tsv")):
        cw.setdefault(r["rep_id"], {})[int(r["row_index1"])] = r
    fr3d = []
    for rid in REPS:
        if not gate.allowed_rep(rid):
            fr3d.append(dict(rep_id=rid, status="blocked_input_mismatch"))
            continue
        rep = reps[rid]
        out, _ = interactions.normalized(rid, rep, cw[rid])
        old = R(os.path.join(ROOT, "annotations/normalized", f"{rid}.tsv"))
        key = lambda r: (int(r["i"]), int(r["j"]), r["label"])  # noqa: E731
        so, sn = {key(r) for r in old}, {(r["i"], r["j"], r["label"]) for r in out}
        raw_same = all(sha(fp("annotations/raw", f"{rep['pdb_id']}_{k}.txt")) ==
                       sha(os.path.join(ROOT, "annotations/raw", f"{rep['pdb_id']}_{k}.txt")) for k in ("basepair", "stacking"))
        fr3d.append(dict(rep_id=rid, retained_n=len(so), fresh_n=len(sn), normalized_identical=so == sn,
                         only_retained=sorted(so - sn)[:10], only_fresh=sorted(sn - so)[:10],
                         raw_files_byte_identical=raw_same))
    rec["fr3d"] = fr3d
    print(json.dumps(fr3d, indent=1))
    rec["status"] = "complete" if not gate.blocked else "stopped_on_input_mismatch"
    _write_partial(rec, gate, final=True)
    if gate.blocked:
        raise SystemExit(f"INPUT MISMATCH: dependent steps blocked: {gate.blocked} (see {gate.diag_dir})")


def _write_partial(rec, gate, final=False):
    rec["gate"] = {"blocked": gate.blocked, "records": gate.records}
    name = "fresh_repro_summary.json" if final else "fresh_repro_summary.partial.json"
    tmp = os.path.join(FR, name + ".tmp")
    json.dump(rec, open(tmp, "w"), indent=1, default=str)
    os.replace(tmp, os.path.join(FR, name))


def configure(pair_ids, out_dir):
    """v3: generalize beyond the preQ1 trio (outputs in a separate directory; retained files never overwritten)."""
    global FR, PAIRS, REPS, PDBS
    FR = os.path.join(ROOT, out_dir)
    PAIRS = list(pair_ids)
    REPS = sorted({f"{p.split('__')[0]}__{x}" for p in PAIRS for x in p.split("__")[1:]})
    PDBS = sorted({r.split("__")[1].split("_")[0] for r in REPS})


if __name__ == "__main__":
    import argparse
    ap = argparse.ArgumentParser()
    ap.add_argument("--pairs", help="comma-separated pair_ids (default: the preQ1 trio)")
    ap.add_argument("--out", default="audit/fresh_repro")
    a = ap.parse_args()
    if a.pairs:
        configure(a.pairs.split(","), a.out)
    main()
