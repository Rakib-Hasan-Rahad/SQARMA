"""INVENTED TEST DATA ONLY — parser/mapping checks, never research results."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import stockholm  # noqa: E402

INTERLEAVED = """# STOCKHOLM 1.0
#=GF AC   RFTEST1
seqA/1-7        AC-GU
#=GR seqA/1-7   SS ((.))
seqB/3-9        ACCGU
#=GC SS_cons    <<.>>

seqA/1-7        UA
#=GR seqA/1-7   SS ..
seqB/3-9        -A
#=GC SS_cons    ..
//
"""


def _write(tmp_path, text, name="t.sto"):
    p = tmp_path / name
    p.write_text(text)
    return str(p)


def test_interleaved_assembly_with_annotations_and_gaps(tmp_path):
    a = next(stockholm.parse(_write(tmp_path, INTERLEAVED)))
    assert a.seqs["seqA/1-7"] == "AC-GUUA"
    assert a.seqs["seqB/3-9"] == "ACCGU-A"
    assert a.gr["seqA/1-7"]["SS"] == "((.))..", "GR annotation must be concatenated, not a sequence row"
    assert "SS" not in a.seqs and a.gc["SS_cons"] == "<<.>>.."
    assert a.ungapped("seqA/1-7") == "ACGUUA"


def test_hypothetical_mapping_from_prompt():
    # V2 prompt §8: rows A-CGU and AUCGU -> (1,1),(2,3),(3,4),(4,5); column 2 pairs gap with B residue 2
    pairs = [(i + 1, j + 1) for i, j in stockholm.pairwise_correspondence("A-CGU", "AUCGU")]
    assert pairs == [(1, 1), (2, 3), (3, 4), (4, 5)]


def test_all_gap_columns_do_not_change_correspondence():
    a, b = "A-CGU", "AUCGU"
    a2, b2 = "A--.CG-U", "AU-.CG-U"   # inserted columns are gaps in both rows
    assert stockholm.pairwise_correspondence(a, b) == stockholm.pairwise_correspondence(a2, b2)


def test_trimmed_interval_offset_reconciles_without_shift():
    # same RNA, row 1 covers residues 1-6, row 2 covers 3-6 of the same source (start offset 2)
    full, trimmed = "GGACGU", "ACGU"
    off = full.index(trimmed)
    assert off == 2
    assert all(full[off + k] == trimmed[k] for k in range(len(trimmed)))


def test_malformed_record_rejected(tmp_path):
    bad = "# STOCKHOLM 1.0\nx/1-3 ACG\ny/1-2 AC\n//\n"
    with pytest.raises(stockholm.StockholmError):
        list(stockholm.parse(_write(tmp_path, bad)))


def test_duplicate_row_names_are_not_silently_merged(tmp_path):
    # a repeated name in one block (as in some pipeline intermediates) concatenates -> width error
    dup = "# STOCKHOLM 1.0\nx/1-3 ACG\ny/1-3 ACG\nx/1-3 ACG\n//\n"
    with pytest.raises(stockholm.StockholmError):
        list(stockholm.parse(_write(tmp_path, dup)))


def test_gr_for_unknown_sequence_rejected(tmp_path):
    t = "# STOCKHOLM 1.0\nx/1-3 ACG\n#=GR z/1-3 SS ...\n//\n"
    with pytest.raises(stockholm.StockholmError):
        list(stockholm.parse(_write(tmp_path, t)))


def test_split_name_reverse_strand():
    assert stockholm.split_name("AB000001.1/50-10") == ("AB000001.1", 50, 10)


def test_reverse_strand_row_coordinates_count_down():
    import prepare_inputs
    assert [prepare_inputs.row_coordinate({"row_start": "2022", "row_end": "1950"}, k) for k in (0, 1, 72)] == [2022, 2021, 1950]
    assert [prepare_inputs.row_coordinate({"row_start": "1", "row_end": "34"}, k) for k in (0, 33)] == [1, 34]
