"""INVENTED TEST DATA ONLY: STAR3D output joins must fail loudly, never drop pairs silently (fix v2.1)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import compare  # noqa: E402

ALN = "#Aligned nucleotide: {n}\n#Alignment RMSD: 1.00A\n#Nucleotide mapping:\n{lines}"


def cwrep(n, chain="A", offset=0):
    return {k: dict(auth_asym_id=chain, auth_seq_id=str(k + offset), ins_code="NA", observed="yes",
                    engineered_masked="no", row_nt="G", label_seq_id=str(k), original_column=str(k)) for k in range(1, n + 1)}


def run_with(tmp_path, monkeypatch, lines):
    f = tmp_path / "x.aln"
    f.write_text(ALN.format(n=len(lines), lines="".join(l + "\n" for l in lines)))
    monkeypatch.setattr(compare, "P", lambda *a: str(f))
    compare.VALIDATION_FAILURES.clear()
    cw = {"Q": cwrep(5), "T": cwrep(5, "B", 100)}
    run = dict(run_id="r1", status="completed", direction="forward", output_aln="x.aln", replicate="1")
    pair = dict(query_rep="Q", target_rep="T", pair_id="p", tier="primary")
    return compare.compare_run(run, pair, cw, [])


def test_unmapped_output_line_is_validation_failure(tmp_path, monkeypatch):
    rows, smap, *_ = run_with(tmp_path, monkeypatch, ["A:1<->B:101", "A:2<->B:999"])   # B:999 not in crosswalk
    assert smap is None and compare.VALIDATION_FAILURES and compare.VALIDATION_FAILURES[0][1] == 1
    assert {r["category"] for r in rows} == {"validation_failed"}


def test_non_injective_output_is_validation_failure(tmp_path, monkeypatch):
    rows, smap, *_ = run_with(tmp_path, monkeypatch, ["A:1<->B:101", "A:2<->B:101"])
    assert smap is None and compare.VALIDATION_FAILURES[0][2] is False


def test_clean_output_maps(tmp_path, monkeypatch):
    rows, smap, *_ = run_with(tmp_path, monkeypatch, ["A:1<->B:101", "A:2<->B:102"])
    assert smap == {1: 1, 2: 2} and not compare.VALIDATION_FAILURES


def test_author_id_collision_is_fatal():
    cw = cwrep(3)
    cw[2]["auth_seq_id"] = "1"                     # two residues with the same author ID
    with pytest.raises(SystemExit):
        compare.resid_index(cw)
