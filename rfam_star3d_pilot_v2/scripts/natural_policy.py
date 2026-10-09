"""v5 natural-sequence dataset policy (the researcher's explicit requirement, 2026-10-09; not attributed to the
professor). The active scientific dataset contains only experimental structures of VERIFIED NATURAL RNA sequences.

Evidence classifications are explicit INPUTS (review/natural_sequence_eligibility.tsv, written from documented
evidence). No sequence-matching function here decides biology on its own; these functions only apply the policy
consistently and keep excluded or unresolved cases out of the accepted cohort.

Usage: natural_policy.py rebuild-cohort     (writes the active selected_representatives/selected_pairs tables and
                                            metadata/cohort_v2.0_natural_freeze.json; archives the previous cohort)"""
import csv
import datetime as dt
import hashlib
import json
import os
import shutil
import sys

ROOT = os.environ.get("SQARMA_STUDY_ROOT") or os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
NATURAL = ("verified_natural", "confirmed_engineered", "unresolved")
ELIGIBILITY = ("accepted", "excluded", "pending")
ENGINEERING_FLAGS = ("introduced_substitution", "artificial_insertion_or_extension", "internal_deletion",
                     "loop_or_stem_replacement", "chimeric_segment", "engineering_elsewhere_in_construct")


def classify(evidence):
    """Natural-sequence status from explicit evidence flags (dict of booleans + 'origin_documented').
    Masking, missing coordinates, synthesis/transcription, native modifications and bound partners are NOT
    engineering flags and cannot change this status."""
    if any(evidence.get(f) for f in ENGINEERING_FLAGS):
        return "confirmed_engineered"
    if not evidence.get("origin_documented"):
        return "unresolved"
    return "verified_natural"


def eligibility(natural_status, mapping_ok=True, coordinates_ok=True, software_ok=True):
    """Analysis eligibility. A verified natural sequence can still be excluded for mapping/coordinate/software
    reasons; unresolved cases are pending (never accepted); engineered cases are excluded (masking is irrelevant)."""
    if natural_status not in NATURAL:
        raise ValueError(f"unknown natural-sequence status {natural_status}")
    if natural_status == "unresolved":
        return "pending"
    if natural_status == "confirmed_engineered":
        return "excluded"
    return "accepted" if (mapping_ok and coordinates_ok and software_ok) else "excluded"


def rep_accepted(row):
    return row["natural_sequence_status"] == "verified_natural" and row["analysis_eligibility"] == "accepted"


def pair_accepted(pair, decisions, sequences=None):
    """A pair is accepted only if BOTH representatives are accepted and their analysed sequences are distinct."""
    a, b = decisions.get(pair["query"]), decisions.get(pair["target"])
    if a is None or b is None or not (rep_accepted(a) and rep_accepted(b)):
        return False
    if sequences is not None and sequences.get(pair["query"]) == sequences.get(pair["target"]):
        return False
    return True


def load_decisions(path=None):
    rows = list(csv.DictReader(open(path or P("review/natural_sequence_eligibility.tsv")), delimiter="\t"))
    for r in rows:
        if r["natural_sequence_status"] not in NATURAL or r["analysis_eligibility"] not in ELIGIBILITY:
            raise SystemExit(f"invalid status in eligibility table: {r['pdb_id']}_{r['auth_chain']}")
        if r["analysis_eligibility"] == "accepted" and r["natural_sequence_status"] != "verified_natural":
            raise SystemExit(f"{r['pdb_id']}_{r['auth_chain']}: only verified_natural can be accepted")
    return {f"{r['pdb_id']}_{r['auth_chain']}": r for r in rows}


def _R(p):
    return list(csv.DictReader(open(p, encoding="utf-8"), delimiter="\t"))


def _W(p, rows, fields):
    tmp = p + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    os.replace(tmp, p)


def rebuild_cohort():
    dec = load_decisions()
    arch = P("archive", "cohort_v1.1_pre_natural_policy")
    os.makedirs(arch, exist_ok=True)
    src_reps, src_pairs = P("results/selected_representatives.tsv"), P("results/selected_pairs.tsv")
    if not os.path.exists(os.path.join(arch, "selected_pairs.tsv")):
        shutil.copy(src_reps, arch)
        shutil.copy(src_pairs, arch)
    reps = _R(os.path.join(arch, "selected_representatives.tsv"))
    pairs = _R(os.path.join(arch, "selected_pairs.tsv"))
    seq = {r["key"]: r["deposited_seq_parent_mapped"] for r in reps}
    missing = [r["key"] for r in reps if r["key"] not in dec]
    if missing:
        raise SystemExit(f"no eligibility decision for {missing}")
    keep_pairs = [dict(p, tier="accepted_natural", cohort_version="2.0_natural",
                       rationale=p["rationale"] + " | v5: both representatives verified_natural + accepted")
                  for p in pairs if pair_accepted(p, dec, seq)]
    used = {p["query_rep"] for p in keep_pairs} | {p["target_rep"] for p in keep_pairs}
    keep_reps = [dict(r, family_decision="accepted_natural", decision="accept_verified_natural") for r in reps
                 if r["rep_id"] in used]
    _W(src_reps, keep_reps, list(reps[0].keys()))
    _W(src_pairs, keep_pairs, list(pairs[0].keys()))
    sha = lambda p: hashlib.sha256(open(p, "rb").read()).hexdigest()  # noqa: E731
    frz = dict(frozen_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"), cohort_version="2.0_natural",
               policy="only verified natural RNA sequences (researcher requirement 2026-10-09)",
               statement="frozen from eligibility decisions only; alignment scores, RMSD and interaction preservation were not consulted",
               accepted_pairs=[p["pair_id"] for p in keep_pairs], accepted_representatives=sorted(used),
               excluded_or_pending=sorted(k for k, r in dec.items() if not rep_accepted(r)),
               files={os.path.relpath(p, ROOT): sha(p) for p in (src_reps, src_pairs, P("review/natural_sequence_eligibility.tsv"))})
    json.dump(frz, open(P("metadata", "cohort_v2.0_natural_freeze.json"), "w"), indent=1)
    print(json.dumps(frz, indent=1))


if __name__ == "__main__":
    {"rebuild-cohort": rebuild_cohort}[sys.argv[1]]()
