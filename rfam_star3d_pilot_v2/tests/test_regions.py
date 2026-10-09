"""INVENTED TEST DATA ONLY: region eligibility for structural adjudication (audit fix v2.1)."""
import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import regions  # noqa: E402


def cw(n, masked=(), unobserved=()):
    return {k: dict(engineered_masked="yes" if k in masked else "no", observed="no" if k in unobserved else "yes")
            for k in range(1, n + 1)}


def test_clean_source_with_masked_rfam_target_not_eligible():
    src, tgt = cw(30), cw(30, masked={18})
    el = regions.region_eligibility([5, 6, 7], src, tgt, {5: 16, 6: 17, 7: 18}, {5: 15, 6: 16, 7: 17})
    assert el["source_engineering_overlap"] == "no"
    assert el["rfam_target_engineering_overlap"] == "yes" and el["star3d_target_engineering_overlap"] == "no"
    assert el["eligible_for_structural_adjudication"] == "no"


def test_clean_source_with_masked_star3d_target_not_eligible():
    src, tgt = cw(30), cw(30, masked={15})
    el = regions.region_eligibility([5, 6, 7], src, tgt, {5: 16, 6: 17, 7: 18}, {5: 15, 6: 16, 7: 17})
    assert el["star3d_target_engineering_overlap"] == "yes"
    assert el["eligible_for_structural_adjudication"] == "no"


def test_intervening_source_position_checked():
    # disagreement residues 5 and 7, intervening 6 is engineered -> whole span counts
    src, tgt = cw(30, masked={6}), cw(30)
    el = regions.region_eligibility([5, 6, 7], src, tgt, {}, {})
    assert el["source_engineering_overlap"] == "yes" and el["eligible_for_structural_adjudication"] == "no"


def test_unobserved_target_not_eligible_and_clean_is_eligible():
    src, tgt = cw(30), cw(30, unobserved={17})
    assert regions.region_eligibility([5, 6], src, tgt, {5: 16, 6: 17}, {})["rfam_target_unobserved"] == "yes"
    clean = regions.region_eligibility([5, 6], cw(30), cw(30), {5: 16, 6: 17}, {5: 17, 6: 18})
    assert clean["eligible_for_structural_adjudication"] == "yes"


def test_manual_interpretations_carried_not_reset():
    prev = [dict(region_id="P__r7-23", pair_id="P", row_index_start="7", row_index_end="23", inspected="inspected",
                 classification="supported_candidate", interpretation="text")]
    out = regions.carry_interpretations([dict(region_id="P__r7-23", pair_id="P", row_index_start=7, row_index_end=23),
                                         dict(region_id="P__r8-12", pair_id="P", row_index_start=8, row_index_end=12),
                                         dict(region_id="Q__r1-2", pair_id="Q", row_index_start=1, row_index_end=2)], prev)
    assert out[0]["classification"] == "supported_candidate" and out[0]["interpretation_source"].startswith("carried exact")
    assert out[1]["inspected"] == "needs_reassessment"                 # boundary changed: not auto-accepted
    assert out[1]["interpretation"].startswith("HISTORICAL") and "supported_candidate" in out[1]["interpretation"]
    assert out[2]["inspected"] == "pending"


def test_changed_eligibility_triggers_reassessment():
    prev = [dict(region_id="P__r17-23", pair_id="P", row_index_start="17", row_index_end="23", inspected="inspected",
                 classification="possible_STAR3D_issue", interpretation="text",
                 eligible_for_structural_adjudication="yes")]
    out = regions.carry_interpretations([dict(region_id="P__r17-23", pair_id="P", row_index_start=17, row_index_end=23,
                                              eligible_for_structural_adjudication="no")], prev)
    assert out[0]["classification"] == "needs_reassessment" and "eligibility changed" in out[0]["interpretation_source"]
