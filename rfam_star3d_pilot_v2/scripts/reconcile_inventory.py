"""v5: reconcile results/family_inventory.tsv with current review decisions without hiding history.
Old review columns are renamed with a 'historical_' prefix (values unchanged); a current column states each family's
status under the v5 natural-sequence policy. Idempotent."""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import natural_policy as npol  # noqa: E402

P = npol.P
REN = {"review_status": "historical_review_status_v1", "review_decision": "historical_review_decision_v1_1",
       "shortlisted": "historical_shortlisted_v1"}


def main():
    path = P("results/family_inventory.tsv")
    rows = list(csv.DictReader(open(path), delimiter="\t"))
    dec = npol.load_decisions()
    pairs = list(csv.DictReader(open(P("results/selected_pairs.tsv")), delimiter="\t"))
    acc_fam = {}
    for p in pairs:
        acc_fam[p["rfam_acc"]] = acc_fam.get(p["rfam_acc"], 0) + 1
    by_fam = {}
    for k, r in dec.items():
        by_fam.setdefault(r["rfam_acc"], []).append(r)
    v3 = {r["family"] for r in csv.DictReader(open(P("review/v3_screening/candidate_screening.tsv")), delimiter="\t")}
    out = []
    for r in rows:
        r = {REN.get(k, k): v for k, v in r.items()}
        fam = r["rfam_acc"]
        if fam in acc_fam:
            cur = f"accepted_natural_pairs:{acc_fam[fam]}"
        elif fam in by_fam:
            n_ok = sum(npol.rep_accepted(x) for x in by_fam[fam])
            cur = (f"reviewed_v5: {n_ok} verified-natural accepted representative(s), no accepted pair" if n_ok
                   else "reviewed_v5: all analysed representatives excluded (confirmed engineered)")
        elif fam in v3:
            cur = "reviewed_v3: no accepted natural pair (screened under earlier criteria; none passed; not re-reviewed in v5)"
        elif r.get("historical_review_status_v1") == "verified":
            cur = "reviewed_v1: not accepted (excluded or pending earlier; not re-reviewed under the v5 natural policy)"
        elif r.get("screen_status") == "pass":
            cur = "screen_pass_not_reviewed"
        else:
            cur = "not_eligible_by_screen"
        r["current_status_v5_natural_policy"] = cur
        out.append(r)
    fields = list(out[0].keys())
    tmp = path + ".tmp"
    with open(tmp, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(out)
    os.replace(tmp, path)
    from collections import Counter
    print(Counter(r["current_status_v5_natural_policy"].split(":")[0] for r in out))


if __name__ == "__main__":
    main()
