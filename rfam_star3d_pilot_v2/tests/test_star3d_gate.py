"""INVENTED TEST DATA ONLY: a preprocessing mount mismatch must stop the pair before any alignment (fix v2.1)."""
import csv
import hashlib
import io
import os
import sys
import tarfile

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import star3d  # noqa: E402


def _setup(tmp_path, monkeypatch):
    root = tmp_path
    (root / "inputs/software").mkdir(parents=True)
    (root / "runs/_superseded").mkdir(parents=True)
    (root / "results").mkdir()
    tb = root / "inputs/software/STAR3D_v1.2.tar.gz"
    with tarfile.open(tb, "w:gz") as t:
        data = b"fake jar"
        ti = tarfile.TarInfo("STAR3D_source/STAR3D.jar")
        ti.size = len(data)
        t.addfile(ti, io.BytesIO(data))
    pdbs = {}
    for name in ("q1aa", "t2bb"):
        f = root / f"{name}.pdb"
        f.write_text(f"ATOM fake {name}\n")
        pdbs[name] = hashlib.sha256(f.read_bytes()).hexdigest()
    monkeypatch.setattr(star3d, "ROOT", str(root))
    monkeypatch.setattr(star3d, "P", lambda *a: os.path.join(str(root), *a))
    monkeypatch.setattr(star3d, "TARBALL", str(tb))
    monkeypatch.setattr(star3d, "MANIFEST_PATH", str(root / "results/run_manifest.tsv"))
    monkeypatch.setitem(star3d.CFG["sources"], "star3d_sha256", hashlib.sha256(tb.read_bytes()).hexdigest())
    monkeypatch.setattr(star3d, "image_id", lambda: "sha256:test")
    monkeypatch.setattr(star3d, "code_commit", lambda: "test")
    reps = {"Q": dict(rep_id="Q", auth_asym_id="A"), "T": dict(rep_id="T", auth_asym_id="B")}
    inputs = {"Q": dict(file="q1aa.pdb", sha256=pdbs["q1aa"], star3d_id="q1aa"),
              "T": dict(file="t2bb.pdb", sha256=pdbs["t2bb"], star3d_id="t2bb")}
    pair = dict(pair_id="TEST__q__t", rfam_acc="RFTEST", query_rep="Q", target_rep="T")
    return root, reps, inputs, pair, pdbs


def test_mount_mismatch_prevents_alignment(tmp_path, monkeypatch):
    root, reps, inputs, pair, pdbs = _setup(tmp_path, monkeypatch)
    issued = []

    def fake_docker(work, cmd, logbase):
        issued.append(cmd)
        if cmd.startswith("sha256sum PDB"):
            return 0, 0.1, "t", "".join(f"{h}  PDB/{n}.pdb\n" for n, h in pdbs.items()) + "0\n"
        if "Preprocess" in cmd:
            sid, ch = cmd.split()[-2:]
            d = os.path.join(work, "STAR3D_struct_info")
            os.makedirs(d, exist_ok=True)
            open(os.path.join(d, f"{sid}_{ch}.npk.ct"), "w").write("3 x\n1 G 0 2 0 1\n")
            return 0, 0.1, "t", ""
        if cmd.startswith("sha256sum STAR3D_struct_info"):
            return 0, 0.1, "t", "0" * 64 + "  file\n"         # container sees different bytes -> mismatch
        return 0, 0.1, "t", ""

    monkeypatch.setattr(star3d, "docker", fake_docker)
    star3d.run_pair(pair, reps, inputs, 3)
    assert not any("STAR3D.jar -o" in c for c in issued), "alignment must not run after a mount mismatch"
    rows = list(csv.DictReader(open(root / "results/run_manifest.tsv"), delimiter="\t"))
    assert [r["status"] for r in rows] == ["failed_mount_mismatch"]
    assert all(r["direction"] == "preprocess" for r in rows)


def test_stale_intermediates_fail_mount_check(tmp_path, monkeypatch):
    root, reps, inputs, pair, pdbs = _setup(tmp_path, monkeypatch)
    issued = []

    def fake_docker(work, cmd, logbase):
        issued.append(cmd)
        if cmd.startswith("sha256sum PDB"):
            return 0, 0.1, "t", "".join(f"{h}  PDB/{n}.pdb\n" for n, h in pdbs.items()) + "4\n"   # stale files
        return 0, 0.1, "t", ""

    monkeypatch.setattr(star3d, "docker", fake_docker)
    star3d.run_pair(pair, reps, inputs, 3)
    assert not any("Preprocess" in c or "STAR3D.jar -o" in c for c in issued)
    rows = list(csv.DictReader(open(root / "results/run_manifest.tsv"), delimiter="\t"))
    assert [r["status"] for r in rows] == ["failed_mount_check"]
