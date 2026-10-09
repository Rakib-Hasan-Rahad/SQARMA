"""INVENTED TEST DATA ONLY: interaction normalization and denominator rules."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import interactions as it  # noqa: E402


def test_reverse_swaps_edges():
    assert it.reverse_label("tSH") == "tHS"
    assert it.reverse_label("cWS") == "cSW"
    assert it.reverse_label("cWW") == "cWW"
    assert it.reverse_label("ntSH") == "ntHS"
    assert it.reverse_label("s35") == "s53" and it.reverse_label("s33") == "s33"
    for lab in ("tSH", "cHW", "s35", "ncSW"):
        assert it.reverse_label(it.reverse_label(lab)) == lab


def test_unit_id_parse_with_icode():
    # field order PDB|Model|Chain|Res|Num|Atom|AltLoc|InsCode|SymOp
    u = it.parse_unit("1ABC|1|A|G|12||||1_555")          # symop only, no insertion code
    assert (u["chain"], u["num"], u["icode"], u["model"]) == ("A", 12, "", 1)
    u = it.parse_unit("1ABC|1|A|G|12|||A")
    assert u["icode"] == "A"


def test_common_denominator_identical_across_methods():
    # a source interaction counts toward the common set only if BOTH methods map both endpoints
    rows = [dict(rfam_status="exact_class_preserved", star3d_forward_status="unmapped_endpoint"),
            dict(rfam_status="no_annotated_target_pair", star3d_forward_status="exact_class_preserved"),
            dict(rfam_status="exact_class_preserved", star3d_forward_status="different_class")]
    bad = ("unmapped_endpoint", "target_endpoint_unobserved")
    common = [r for r in rows if r["rfam_status"] not in bad and r["star3d_forward_status"] not in bad]
    assert len(common) == 2  # same denominator for both methods
