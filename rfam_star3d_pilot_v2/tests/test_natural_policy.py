"""v5 natural-sequence dataset policy. Evidence classifications are explicit inputs; invented data except where the
real active tables are checked for leakage of excluded cases."""
import csv
import json
import os
import sys

import pytest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "scripts"))
import natural_policy as npol  # noqa: E402

ROOT = os.path.join(os.path.dirname(__file__), "..")


def dec(status, elig):
    return dict(natural_sequence_status=status, analysis_eligibility=elig)


def test_confirmed_engineered_cannot_be_accepted():
    assert npol.classify(dict(introduced_substitution=True, origin_documented=True)) == "confirmed_engineered"
    assert npol.eligibility("confirmed_engineered") == "excluded"


def test_masked_engineered_representative_remains_excluded():
    ev = dict(loop_or_stem_replacement=True, origin_documented=True, masked_positions=[63, 64])
    assert npol.eligibility(npol.classify(ev)) == "excluded"
    ev2 = dict(engineering_elsewhere_in_construct=True, origin_documented=True)    # outside the extracted interval
    assert npol.classify(ev2) == "confirmed_engineered"


def test_unresolved_cannot_enter_cohort():
    assert npol.classify(dict(origin_documented=False)) == "unresolved"
    assert npol.eligibility("unresolved") == "pending"
    with pytest.raises(SystemExit):
        p = os.path.join(os.path.dirname(__file__), "_tmp_bad_elig.tsv")
        open(p, "w").write("pdb_id\tauth_chain\tnatural_sequence_status\tanalysis_eligibility\nXXXX\tA\tunresolved\taccepted\n")
        try:
            npol.load_decisions(p)
        finally:
            os.remove(p)


def test_one_ineligible_representative_blocks_the_pair():
    d = {"A_1": dec("verified_natural", "accepted"), "B_1": dec("confirmed_engineered", "excluded"),
         "C_1": dec("unresolved", "pending")}
    assert not npol.pair_accepted(dict(query="A_1", target="B_1"), d)
    assert not npol.pair_accepted(dict(query="A_1", target="C_1"), d)
    d["D_1"] = dec("verified_natural", "accepted")
    assert npol.pair_accepted(dict(query="A_1", target="D_1"), d)
    assert not npol.pair_accepted(dict(query="A_1", target="D_1"), d, sequences={"A_1": "GGA", "D_1": "GGA"})


def test_synthesis_alone_is_not_engineering():
    ev = dict(origin_documented=True, chemically_synthesized=True, in_vitro_transcribed=True)
    assert npol.classify(ev) == "verified_natural" and npol.eligibility("verified_natural") == "accepted"


def test_missing_coordinates_are_not_a_sequence_deletion():
    ev = dict(origin_documented=True, missing_coordinates=[13, 14], partial_residue=12)
    assert npol.classify(ev) == "verified_natural"
    assert npol.eligibility("verified_natural", coordinates_ok=False) == "excluded"   # suitability, not engineering


def test_native_modifications_and_bound_partners_are_not_engineering():
    assert npol.classify(dict(origin_documented=True, native_modifications=True, bound_protein=True)) == "verified_natural"
    assert npol.eligibility("verified_natural", software_ok=False) == "excluded"


def test_excluded_cases_do_not_leak_into_active_tables():
    d = npol.load_decisions(os.path.join(ROOT, "review", "natural_sequence_eligibility.tsv"))
    bad = {k for k, r in d.items() if not npol.rep_accepted(r)}
    R = lambda p: list(csv.DictReader(open(os.path.join(ROOT, p)), delimiter="\t"))  # noqa: E731
    for r in R("results/selected_representatives.tsv"):
        assert r["key"] not in bad
    for t, col in (("results/selected_pairs.tsv", "pair_id"), ("results/pair_summary.tsv", "pair_id"),
                   ("results/primary_star3d_outputs.tsv", "pair_id"), ("results/correspondence_comparison.tsv", "pair_id"),
                   ("results/interaction_summary.tsv", "pair_id"), ("results/region_review.tsv", "pair_id")):
        for r in R(t):
            assert not ({f"{x}" for x in r[col].split("__")[1:]} & bad), (t, r[col])
    frz = json.load(open(os.path.join(ROOT, "metadata", "cohort_v2.0_natural_freeze.json")))
    assert not {r.split("__")[1] for r in frz["accepted_representatives"]} & bad
