"""INVENTED TEST DATA ONLY: engineering-mask eligibility for interaction comparisons (audit fix v2.1)."""
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import interactions as it  # noqa: E402

SRC = dict(i=2, j=9, label="tSH")              # one source interaction 2-9 tSH
TIX = {(12, 19): {"tSH"}, (13, 20): {"tSH"}}   # target annotations
TOBS = set(range(1, 40))


def per(rfam_map, s3d_map, tmask):
    return {"rfam": it.method_status(SRC, rfam_map, TIX, TOBS, tmask),
            "star3d_forward": it.method_status(SRC, s3d_map, TIX, TOBS, tmask),
            "star3d_reverse": it.method_status(SRC, s3d_map, TIX, TOBS, tmask)}


def test_masked_star3d_target_excludes():
    # Rfam maps to 12-19 (unmasked); STAR3D maps to 13-20 and target 20 is engineered
    d = per({2: 12, 9: 19}, {2: 13, 9: 20}, tmask={20})
    ok, why = it.comparison_eligibility("no", d, ("rfam", "star3d_forward"))
    assert not ok and why == "star3d_forward_target_masked"
    assert d["rfam"]["target_masked"] == "no" and d["star3d_forward"]["target_masked"] == "yes"


def test_masked_rfam_target_excludes():
    d = per({2: 12, 9: 19}, {2: 13, 9: 20}, tmask={12})
    ok, why = it.comparison_eligibility("no", d, ("rfam", "star3d_forward"))
    assert not ok and why == "rfam_target_masked"


def test_unmasked_observed_interaction_eligible():
    d = per({2: 12, 9: 19}, {2: 13, 9: 20}, tmask=set())
    ok, why = it.comparison_eligibility("no", d, ("rfam", "star3d_forward"))
    assert ok and why == "eligible"
    assert d["rfam"]["status"] == "exact_class_preserved" and d["star3d_forward"]["status"] == "exact_class_preserved"


def test_masked_source_excludes_even_if_targets_clean():
    d = per({2: 12, 9: 19}, {2: 13, 9: 20}, tmask=set())
    assert it.comparison_eligibility("yes", d, ("rfam", "star3d_forward")) == (False, "source_endpoint_masked")


def test_reversed_endpoint_order_swaps_edges():
    # mapping reverses order (2->19, 9->12): source tSH must be looked up as tHS at target (12,19)
    tix = {(12, 19): {"tHS"}}
    st = it.method_status(SRC, {2: 19, 9: 12}, tix, TOBS, set())
    assert st["status"] == "exact_class_preserved"
    st2 = it.method_status(SRC, {2: 19, 9: 12}, {(12, 19): {"tSH"}}, TOBS, set())
    assert st2["status"] == "different_class"


def test_unobserved_target_and_unmapped():
    st = it.method_status(SRC, {2: 12, 9: 19}, TIX, TOBS - {19}, set())
    assert st["status"] == "target_endpoint_unobserved"
    st = it.method_status(SRC, {2: 12}, TIX, TOBS, set())
    assert st["status"] == "unmapped_endpoint"
    d = {"rfam": st, "star3d_forward": st}
    assert it.comparison_eligibility("no", d, ("rfam", "star3d_forward"))[1] == "rfam_unmapped_endpoint"


def test_three_way_denominator_uses_all_methods():
    d = per({2: 12, 9: 19}, {2: 13, 9: 20}, tmask=set())
    d["star3d_reverse"] = it.method_status(SRC, {2: 13, 9: 20}, TIX, TOBS, {13})
    assert it.comparison_eligibility("no", d, ("rfam", "star3d_forward"))[0]
    assert it.comparison_eligibility("no", d, it.COMPARISONS["all_three_methods"]) == (False, "star3d_reverse_target_masked")


def test_symmetry_classes():
    u = lambda op: dict(symop=op)  # noqa: E731
    assert it.symmetry_class(u("1_555"), u("1_555")) == "identity"
    assert it.symmetry_class(u("4_555"), u("4_555")) == "copy_duplicate"
    assert it.symmetry_class(u("1_555"), u("4_555")) == "inter_copy"
    assert it.parse_unit("4KQY|1|A|G|5||||4_555")["symop"] == "4_555"
    assert it.parse_unit("4KQY|1|A|G|5")["symop"] == "1_555"


def test_non_injective_inversion_fails():
    with pytest.raises(SystemExit):
        it.invert_injective({1: 5, 2: 5}, "test map")
    assert it.invert_injective({1: 5, 2: 6}, "ok") == {5: 1, 6: 2}
