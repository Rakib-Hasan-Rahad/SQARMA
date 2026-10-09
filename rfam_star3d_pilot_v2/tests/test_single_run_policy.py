"""v5 single-run policy: one forward original-STAR3D alignment per pair, fixed order, explicit primary output,
no retry and no silent substitution. Invented data except where the real primary-output table is checked."""
import csv
import hashlib
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
sys.path.insert(0, os.path.dirname(__file__))
import compare  # noqa: E402
import select_primary_outputs as sp  # noqa: E402
import star3d  # noqa: E402
from test_star3d_gate import GOOD_CT, _prep_docker, _setup  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _run(tmp_path, monkeypatch, align_rc=0):
    root, reps, inputs, pair, pdbs = _setup(tmp_path, monkeypatch)
    fake, issued = _prep_docker(pdbs, "Base-pairs ---\n", GOOD_CT)

    def wrapped(work, cmd, logbase):
        if "STAR3D.jar -o" in cmd and align_rc:
            issued.append(cmd)
            return align_rc, 0.1, "t", ""
        return fake(work, cmd, logbase)
    monkeypatch.setattr(star3d, "docker", wrapped)
    res = star3d.run_pair(pair, reps, inputs)
    rows = list(csv.DictReader(open(root / "results/run_manifest.tsv"), delimiter="\t"))
    return res, issued, rows


def test_exactly_one_alignment_and_one_preprocess_per_rna(tmp_path, monkeypatch):
    res, issued, rows = _run(tmp_path, monkeypatch)
    aligns = [c for c in issued if "STAR3D.jar -o" in c]
    pre = [c for c in issued if "Preprocess" in c]
    assert len(aligns) == 1 and len(pre) == 2
    assert [r["direction"] for r in rows if r["direction"] != "preprocess"] == ["forward"]


def test_fixed_query_target_order(tmp_path, monkeypatch):
    res, issued, rows = _run(tmp_path, monkeypatch)
    align = next(c for c in issued if "STAR3D.jar -o" in c)
    assert align.endswith("-p q1aa A t2bb B")                    # query (Q) first, target (T) second
    assert [c.split()[-2] for c in issued if "Preprocess" in c] == ["q1aa", "t2bb"]
    fwd = next(r for r in rows if r["direction"] == "forward")
    assert fwd["query_rep"] == "Q" and fwd["target_rep"] == "T"


def test_failed_alignment_is_not_retried_or_substituted(tmp_path, monkeypatch):
    (run_id, status), issued, rows = _run(tmp_path, monkeypatch, align_rc=139)
    assert status == "failed" and len([c for c in issued if "STAR3D.jar -o" in c]) == 1
    chosen, rejected = sp.choose(rows, lambda r: [] if r["status"] == "completed" else [r["status"]])
    assert chosen is None and rejected


def _rec(run_id, direction="forward", rep="1", status="completed", rmsd="3.0"):
    return dict(run_id=run_id, direction=direction, replicate=rep, status=status, rmsd=rmsd)


def test_earliest_valid_forward_chosen_not_the_best_scoring():
    runs = [_rec("P__a1__forward__rep1", rmsd="4.0"), _rec("P__a1__forward__rep2", rep="2", rmsd="1.0"),
            _rec("P__a1__reverse__rep1", direction="reverse", rmsd="0.5")]
    chosen, rejected = sp.choose(runs, lambda r: [])
    assert chosen["run_id"] == "P__a1__forward__rep1" and rejected == []


def test_failed_first_attempt_documented_and_next_valid_forward_used():
    runs = [_rec("attempt1__P__forward__rep1", status="failed_wrapper_defect"), _rec("P__a3__forward__rep1")]
    chosen, rejected = sp.choose(runs, lambda r: [] if r["status"] == "completed" else [r["status"]])
    assert chosen["run_id"] == "P__a3__forward__rep1" and "failed_wrapper_defect" in rejected[0]


def test_no_valid_forward_means_unavailable_even_if_reverse_exists():
    runs = [_rec("P__a1__forward__rep1", status="failed"), _rec("P__a1__reverse__rep1", direction="reverse")]
    chosen, _ = sp.choose(runs, lambda r: [] if r["status"] == "completed" else ["failed"])
    assert chosen is None


def test_unavailable_pair_stays_a_failure_in_comparison(monkeypatch, tmp_path):
    f = tmp_path / "primary.tsv"
    f.write_text("pair_id\tstatus\tselected_run_id\nPX\tunavailable\tNA\n")
    monkeypatch.setattr(compare, "P", lambda *a: str(f))
    run = compare.primary_runs({"PX": {}})["PX"]
    assert run["status"] == "unavailable"
    cw = {"Q": {1: dict(auth_asym_id="A", auth_seq_id="1", ins_code="NA", observed="yes", engineered_masked="no",
                        row_nt="G", label_seq_id="1", original_column="1")},
          "T": {1: dict(auth_asym_id="B", auth_seq_id="1", ins_code="NA", observed="yes", engineered_masked="no",
                        row_nt="G", label_seq_id="1", original_column="1")}}
    compare.VALIDATION_FAILURES.clear()
    rows, smap, *_ = compare.compare_run(run, dict(query_rep="Q", target_rep="T", pair_id="PX", tier="primary"), cw,
                                         [dict(row_A_index="1", row_B_index="1")])
    assert smap is None and rows[0]["category"] == "technical_failure_or_no_alignment"
    assert rows[0]["star3d_missing_reason"] == "no_valid_primary_output" and not compare.VALIDATION_FAILURES


def test_real_primary_table_reuses_pinned_original_output():
    path = os.path.join(ROOT, "results", "primary_star3d_outputs.tsv")
    rows = {r["pair_id"]: r for r in csv.DictReader(open(path), delimiter="\t")}
    r = rows["RF00522__6VUI_A__7REX_A"]
    assert r["output_aln"] == sp.PINNED["RF00522__6VUI_A__7REX_A"]
    aln = os.path.join(ROOT, r["output_aln"])
    assert hashlib.sha256(open(aln, "rb").read()).hexdigest() == r["output_sha256"]
    assert all(x["status"] == "selected" and "__forward" in x["selected_run_id"] for x in rows.values())
