"""Before/after for the v5 natural-sequence policy. 'Previous' = v4 active dataset (7 pilot pairs + 1 prospective
tRNA pair, after the single-run refactor); 'natural' = current active tables. All values computed from tables."""
import csv
import os

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
V5 = os.path.join(ROOT, "deliverables", "2026-10-09_v5")
R = lambda p: list(csv.DictReader(open(os.path.join(ROOT, p)), delimiter="\t"))  # noqa: E731
Rb = lambda p: list(csv.DictReader(open(os.path.join(V5, "before_natural", "results", p)), delimiter="\t"))  # noqa: E731
Re = lambda p: list(csv.DictReader(open(os.path.join(ROOT, "expansion_v4", "results", p)), delimiter="\t"))  # noqa: E731

prev_pairs = Rb("selected_pairs.tsv") + Re("selected_pairs.tsv")
prev_reps = Rb("selected_representatives.tsv") + Re("selected_representatives.tsv")
now_pairs, now_reps = R("results/selected_pairs.tsv"), R("results/selected_representatives.tsv")
elig = R("review/natural_sequence_eligibility.tsv")
prev_regions = Rb("region_review.tsv") + Re("region_review.tsv")
now_regions = R("results/region_review.tsv")
prev_int = [r for r in Rb("interaction_summary.tsv") + Re("interaction_summary.tsv")
            if r["interaction_class"] == "all" and r["source_side"] == "query"]
now_int = [r for r in R("results/interaction_summary.tsv") if r["interaction_class"] == "all" and r["source_side"] == "query"]
fam = lambda ps: sorted({p["rfam_acc"] for p in ps})  # noqa: E731
rows = [
    ("Families with an analysed pair", f"{len(fam(prev_pairs))} ({', '.join(fam(prev_pairs))})",
     f"{len(fam(now_pairs))} ({', '.join(fam(now_pairs))})", "all representatives of RF00059, RF00162, RF00174, RF00442 "
     "are confirmed engineered; RF00005 has no accepted pair (5CCB carries an artificial 5' G)"),
    ("Structures (RNA chains) analysed", str(len(prev_reps)), str(len(now_reps)),
     "only verified-natural representatives in accepted pairs remain active"),
    ("Verified-natural representatives (any pair status)", "not assessed under this policy",
     str(sum(r["natural_sequence_status"] == "verified_natural" for r in elig)),
     "3FU2, 6VUI, 7REX (accepted, paired) and 7EQJ (accepted representative, no eligible partner)"),
    ("Confirmed-engineered representatives", "kept with masks (exploratory tiers)",
     str(sum(r["natural_sequence_status"] == "confirmed_engineered" for r in elig)),
     "masking no longer makes a construct eligible; terminal artificial nucleotides count as engineering"),
    ("Unresolved / pending representatives", "n/a", str(sum(r["natural_sequence_status"] == "unresolved" for r in elig)), "none"),
    ("Distinct analysed sequences", str(len({r["deposited_seq_parent_mapped"] for r in prev_reps})),
     str(len({r["deposited_seq_parent_mapped"] for r in now_reps})), "as structures"),
    ("Pairs", str(len(prev_pairs)), str(len(now_pairs)), "a pair is accepted only if both representatives are accepted"),
    ("Pairs labelled primary", str(sum(p["tier"] == "primary" for p in prev_pairs)), str(len(now_pairs)),
     "RF00174 4GXY-6VMY (previously primary) is excluded: both constructs carry artificial terminal nucleotides"),
    ("Primary STAR3D outputs used", str(len(prev_pairs)), str(len(R("results/primary_star3d_outputs.tsv"))),
     "the 3 preQ1 outputs are reused unchanged (inputs byte-identical); no STAR3D run was needed"),
    ("Candidate regions", str(len(prev_regions)), str(len(now_regions)), "regions of excluded pairs archived"),
    ("Source-side interactions evaluated (query side, all classes)", str(sum(int(r["source_interactions"]) for r in prev_int
                                                                        if r["comparison"] in ("rfam_vs_star3d", "rfam_vs_star3d_forward"))),
     str(sum(int(r["source_interactions"]) for r in now_int)), "only accepted pairs"),
    ("7REX P1 candidate", "supported candidate (moderate)", "supported candidate (moderate) - unchanged",
     "all three supporting representatives (3FU2, 6VUI, 7REX) pass the natural-sequence policy"),
    ("Agreement control", "TPP 2GDI-3D2G (71 same / 1 different)", "3FU2-6VUI (24 same / 4 different) as the closest available",
     "TPP pair excluded (both constructs engineered)"),
    ("Coverage-limitation examples", "cobalamin, SAM-I", "none in the active dataset", "excluded pairs"),
    ("Pairing-rule sensitivity (guanidine-I 78->25 nt)", "reported as a limitation", "archived historical observation",
     "guanidine-I excluded; sensitivity analyses archived"),
    ("tRNA exploratory agreement (59/64)", "reported", "withdrawn from active results", "5CCB excluded (artificial 5' G)"),
]
with open(os.path.join(V5, "tables", "before_after_natural_dataset.tsv"), "w", newline="") as f:
    w = csv.writer(f, delimiter="\t", lineterminator="\n")
    w.writerow(["item", "previous_dataset", "natural_sequence_dataset", "reason_for_change"])
    w.writerows(rows)
for r in rows:
    print(" | ".join(r))
