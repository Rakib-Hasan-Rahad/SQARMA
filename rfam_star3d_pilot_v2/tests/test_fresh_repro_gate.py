"""v3 repair B: a changed download or rebuilt input must stop every dependent step (no silent adoption)."""
import gzip
import json
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import fresh_repro as fr  # noqa: E402

PAIRS = {"P1": {"query_rep": "F__AAAA_A", "target_rep": "F__BBBB_A"},
         "P2": {"query_rep": "F__BBBB_A", "target_rep": "F__CCCC_A"},
         "P3": {"query_rep": "F__AAAA_A", "target_rep": "F__CCCC_A"}}


def _pinned(tmp_path, content=b"data_X\nATOM 1\n"):
    p = tmp_path / "pinned.cif.gz"
    p.write_bytes(gzip.compress(content, mtime=0))
    return p


def test_altered_download_blocks_dependent_alignments_and_annotation(tmp_path):
    pinned = _pinned(tmp_path)
    gate = fr.InputGate(str(tmp_path / "fr"))
    fresh_file = tmp_path / "fresh.cif.gz"
    altered = gzip.compress(b"data_X\nATOM 2\n", mtime=0)
    fresh_file.write_bytes(altered)
    rec = gate.check_download("rep:F__AAAA_A", "inputs/structures/mmcif/AAAA.cif.gz", altered,
                              fr.sha_bytes(pinned.read_bytes()), pinned_path=str(pinned), fresh_path=str(fresh_file))
    assert rec["verdict"] == "rejected_content_change"
    diag = tmp_path / "fr" / "diagnostics" / "inputs__structures__mmcif__AAAA.cif.gz.mismatch.json"
    assert json.loads(diag.read_text())["verdict"] == "rejected_content_change"
    assert (tmp_path / "fr" / "quarantine" / "inputs__structures__mmcif__AAAA.cif.gz.rejected").read_bytes() == altered
    assert not fresh_file.exists()                       # not left where a cache could reuse it
    ran = []
    status = fr.run_allowed_pairs(gate, PAIRS, lambda p: ran.append(p))
    assert status == {"P1": "blocked_input_mismatch", "P2": "run", "P3": "blocked_input_mismatch"}
    assert ran == [PAIRS["P2"]]
    assert not gate.allowed_rep("F__AAAA_A")             # FR3D annotation is skipped too


def test_container_only_change_is_distinguished_but_rejected(tmp_path):
    pinned = _pinned(tmp_path)
    gate = fr.InputGate(str(tmp_path / "fr"))
    regz = gzip.compress(b"data_X\nATOM 1\n", mtime=12345)   # same content, different gzip header
    rec = gate.check_download("rep:F__AAAA_A", "a.cif.gz", regz, fr.sha_bytes(pinned.read_bytes()),
                              pinned_path=str(pinned))
    assert rec["decompressed_identical"] and not rec["compressed_identical"]
    assert rec["verdict"] == "rejected_container_only_change"
    assert not gate.allowed_rep("F__AAAA_A")


def test_software_mismatch_blocks_all_alignments(tmp_path):
    gate = fr.InputGate(str(tmp_path / "fr"))
    gate.check_download("software", "inputs/software/STAR3D_v1.2.tar.gz", b"other", fr.sha_bytes(b"pinned"))
    ran = []
    assert set(fr.run_allowed_pairs(gate, PAIRS, ran.append).values()) == {"blocked_input_mismatch"}
    assert ran == []


def test_altered_rebuilt_input_blocks_alignment(tmp_path):
    gate = fr.InputGate(str(tmp_path / "fr"))
    gate.check_rebuilt("rep:F__CCCC_A", "inputs/pdb/CCCC.pdb", b"ATOM new\n", b"ATOM old\n")
    ran = []
    status = fr.run_allowed_pairs(gate, PAIRS, ran.append)
    assert status == {"P1": "run", "P2": "blocked_input_mismatch", "P3": "blocked_input_mismatch"}
    assert (tmp_path / "fr" / "diagnostics" / "inputs__pdb__CCCC.pdb.mismatch.json").exists()


def test_identical_inputs_pass(tmp_path):
    pinned = _pinned(tmp_path)
    gate = fr.InputGate(str(tmp_path / "fr"))
    gate.check_download("rep:F__AAAA_A", "a.cif.gz", pinned.read_bytes(), fr.sha_bytes(pinned.read_bytes()),
                        pinned_path=str(pinned))
    assert gate.blocked == {}
    assert set(fr.run_allowed_pairs(gate, PAIRS, lambda p: None).values()) == {"run"}
