"""v3 repair A: the derived excerpt must be one valid Stockholm record per family."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import reference  # noqa: E402
import stockholm  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def _aln(acc, rows, gc):
    a = stockholm.Alignment()
    a.gf["ID"] = [acc + "_id"]
    a.gf["AC"] = [acc]
    for n, s in rows.items():
        a.seqs[n] = s
        a.gr[n] = {"X_SS": "." * len(s)}
    a.gc["SS_cons"] = gc
    return a


def test_unequal_width_families_round_trip(tmp_path):
    seed = {"RF90001": _aln("RF90001", {"r1/1-4": "AC-GU", "r2/1-5": "ACGGU"}, "....."),
            "RF90002": _aln("RF90002", {"s1/1-8": "AAAA--CCCC", "s2/1-9": "AAAAG-CCCC"}, "(((....)))")}
    out = str(tmp_path / "x.sto")
    reference.write_family_excerpts(out, seed, {k: list(v.seqs) for k, v in seed.items()})
    back = {a.acc: a for a in stockholm.parse(out)}
    assert sorted(back) == ["RF90001", "RF90002"]
    assert {k: a.width for k, a in back.items()} == {"RF90001": 5, "RF90002": 10}
    for k in seed:
        assert back[k].seqs == seed[k].seqs
        assert back[k].gc == seed[k].gc
        assert {n: dict(f) for n, f in back[k].gr.items()} == {n: dict(f) for n, f in seed[k].gr.items()}


def test_old_combined_writer_is_rejected(tmp_path):
    """The pre-repair layout (several families inside one record) must not parse."""
    p = tmp_path / "bad.sto"
    p.write_text("# STOCKHOLM 1.0\n#=GF AC   RF90001\nr1/1-4 AC-GU\n#=GF AC   RF90002\ns1/1-8 AAAA--CCCC\n//\n")
    try:
        list(stockholm.parse(str(p)))
    except stockholm.StockholmError:
        return
    raise AssertionError("combined unequal-width record parsed")


def test_actual_pilot_excerpt_round_trips_against_pinned_seed():
    """All families in results/standard_seed_rows.sto parse, and every row string equals the pinned seed."""
    sto = os.path.join(ROOT, "results", "standard_seed_rows.sto")
    seed_path = os.path.join(ROOT, reference.REF["seed_path"])
    if not os.path.exists(seed_path):
        import pytest
        pytest.skip("pinned Rfam.seed.gz not present")
    ex = {a.acc: a for a in stockholm.parse(sto)}
    assert len(ex) >= 1      # v5 natural cohort has one family; unequal widths are covered by the synthetic test
    seed = {a.acc: a for a in stockholm.parse(seed_path, only=set(ex))}
    for acc, a in ex.items():
        assert a.width == seed[acc].width
        for n, s in a.seqs.items():
            assert s == seed[acc].seqs[n]
            assert dict(a.gr.get(n, {})) == dict(seed[acc].gr.get(n, {}))
        assert dict(a.gc) == dict(seed[acc].gc)
