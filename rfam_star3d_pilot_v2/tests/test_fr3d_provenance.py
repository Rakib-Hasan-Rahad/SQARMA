"""v4: FR3D provenance comes from the installed package, and cached raw outputs are reused only when verified."""
import gzip
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import interactions as it  # noqa: E402

GOOD = dict(installed_commit=None, record_files_mismatched=0, record_files_checked=5, import_inside_distribution=True)


def _prov(monkeypatch, **kw):
    pv = dict(GOOD, installed_commit=it.pinned_fr3d_commit())
    pv.update(kw)
    monkeypatch.setattr(it, "installed_fr3d_provenance", lambda: pv)


@pytest.mark.parametrize("kw", [dict(installed_commit="deadbeef"), dict(record_files_mismatched=1),
                                dict(record_files_checked=0), dict(import_inside_distribution=False)])
def test_unverified_installation_is_refused(monkeypatch, kw):
    _prov(monkeypatch, **kw)
    with pytest.raises(SystemExit, match="not verified"):
        it.verified_fr3d_commit()


def test_installed_package_is_actually_verified():
    it._FR3D_PROV = None
    pv = it.installed_fr3d_provenance()
    assert pv["installed_commit"] == it.pinned_fr3d_commit() and pv["record_files_mismatched"] == 0


def _cache(tmp_path, monkeypatch, raw_text, sidecar_extra):
    root = tmp_path
    (root / "inputs/structures/mmcif").mkdir(parents=True)
    (root / "inputs/structures/mmcif/XXXX.cif.gz").write_bytes(gzip.compress(b"data_XXXX\n", mtime=0))
    raw = root / "raw"
    raw.mkdir()
    (raw / "XXXX_basepair.txt").write_text(raw_text)
    (raw / "XXXX_stacking.txt").write_text("")
    monkeypatch.setattr(it, "P", lambda *a: os.path.join(str(root), *a))
    _prov(monkeypatch)
    want = dict(source_mmcif_sha256=it._sha(str(root / "inputs/structures/mmcif/XXXX.cif.gz")),
                decompressed_cif_sha256=it._cif_bytes_sha("XXXX"), fr3d_commit=it.pinned_fr3d_commit(),
                categories="basepair,stacking")
    (raw / "XXXX.provenance.json").write_text(json.dumps(dict(want, **sidecar_extra)))
    return raw


LINE = "XXXX|1|A|G|1\tcWW\tXXXX|1|A|C|2\t0\n"


def test_cache_without_raw_hashes_is_refused(tmp_path, monkeypatch):
    raw = _cache(tmp_path, monkeypatch, LINE, {})
    with pytest.raises(SystemExit, match="no raw-output hashes"):
        it.annotate("XXXX", raw_dir=str(raw))


def test_cache_with_changed_raw_bytes_is_refused(tmp_path, monkeypatch):
    raw = _cache(tmp_path, monkeypatch, LINE, {"raw_sha256": {"XXXX_basepair.txt": "0" * 64, "XXXX_stacking.txt": "0" * 64}})
    with pytest.raises(SystemExit, match="differ"):
        it.annotate("XXXX", raw_dir=str(raw))


def test_truncated_raw_output_is_refused(tmp_path, monkeypatch):
    raw = _cache(tmp_path, monkeypatch, "XXXX|1|A|G|1\tcWW\n", {"raw_sha256": {}})
    with pytest.raises(SystemExit, match="malformed"):
        it.annotate("XXXX", raw_dir=str(raw))


def test_verified_cache_is_reused(tmp_path, monkeypatch):
    raw = _cache(tmp_path, monkeypatch, LINE, {})
    good = it.raw_output_check([str(raw / "XXXX_basepair.txt"), str(raw / "XXXX_stacking.txt")])
    side = json.loads((raw / "XXXX.provenance.json").read_text())
    (raw / "XXXX.provenance.json").write_text(json.dumps(dict(side, raw_sha256=good)))
    assert it.annotate("XXXX", raw_dir=str(raw))[0].endswith("XXXX_basepair.txt")
