"""MANIFEST.tsv (v5): each active output and session deliverable -> generator, inputs/config, sha256, bytes."""
import hashlib
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sha = lambda p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()  # noqa: E731
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
SW = ("Python 3.13 (.venv; requirements.lock.txt); FR3D-python 288f98cc (installed, RECORD-verified); original STAR3D v1.2 "
      "tarball c9da4405, image star3d-runtime:1 (amd64 emulated); ONE forward alignment per pair")
REF = "Rfam 15.1 Rfam.seed.gz 41f014f4; config.yaml " + sha("config.yaml")[:12]
G = [
    ("review/natural_sequence_eligibility.tsv", "manual decisions (AI agent) + natural_policy.py validation", "papers, genomes, mmCIF (evidence paths per row)"),
    ("metadata/cohort_v2.0_natural_freeze.json", "scripts/natural_policy.py rebuild-cohort", "eligibility table; archive/cohort_v1.1_pre_natural_policy"),
    ("results/selected_representatives.tsv", "scripts/natural_policy.py rebuild-cohort", "eligibility table"),
    ("results/selected_pairs.tsv", "scripts/natural_policy.py rebuild-cohort", "eligibility table"),
    ("results/family_inventory.tsv", "scripts/reconcile_inventory.py", "eligibility table; v3 screening"),
    ("results/dataset_chains.tsv", "derived from eligibility table", "review/natural_sequence_eligibility.tsv"),
    ("results/dataset_chains.md", "derived from eligibility table", "review/natural_sequence_eligibility.tsv"),
    ("results/residue_crosswalk.tsv", "scripts/prepare_inputs.py", REF + "; mmCIF"),
    ("mappings/aligner_inputs.tsv", "scripts/prepare_inputs.py", "mmCIF"),
    ("results/reference_pairs.tsv", "scripts/reference.py", REF),
    ("results/standard_seed_membership.tsv", "scripts/reference.py", REF),
    ("results/standard_seed_rows.sto", "scripts/reference.py", REF),
    ("results/primary_star3d_outputs.tsv", "scripts/select_primary_outputs.py", "results/run_manifest.tsv; runs/*/attempt*/STAR3D_source"),
    ("results/correspondence_comparison.tsv", "scripts/compare.py", "primary outputs; reference_pairs; crosswalk"),
    ("results/pair_summary.tsv", "scripts/compare.py", "as above"),
    ("results/interaction_comparison.tsv", "scripts/interactions.py", "annotations/raw (FR3D); comparison"),
    ("results/interaction_summary.tsv", "scripts/interactions.py", "as above"),
    ("results/region_review.tsv", "scripts/regions.py (+ carried reviews)", "comparison; interactions"),
    ("results/region_evidence", "scripts/region_evidence.py", "results; mmCIF; annotations"),
    ("results/derived_alignment_views.md", "scripts/derived_alignment_view.py", "comparison; crosswalk; primary outputs"),
    ("results/derived_alignment_views.tsv", "scripts/derived_alignment_view.py", "as above"),
    ("review/candidate_RF00522", "scripts/candidate_evidence.py", "comparison; annotations; anchor fits"),
    ("reports", "hand-written + scripts/evidence_cards.py", "tables above"),
    ("deliverables/2026-10-09_v5/tables", "deliverables/2026-10-09_v5/scripts/*.py", "before/, before_natural/, results"),
    ("deliverables/2026-10-09_v5/architecture", "pandoc 2.12 + headless Chrome; diagrams/render.py (mermaid 10.9.1)", "guide .md; diagrams/*.mmd"),
    ("deliverables/2026-10-09_v5/site", "scripts/export_site_data.py + static html/js/css", "site/data/export_manifest.json"),
    ("deliverables/2026-10-09_v5", "hand-written reports (AI agent)", "tables above"),
    ("archive", "git mv / copies of superseded active tables (unchanged)", "v4 active state"),
]
rows, seen = [], set()
for path, gen, inp in G:
    full = os.path.join(ROOT, path)
    files = [path] if os.path.isfile(full) else sorted(
        os.path.relpath(os.path.join(d, f), ROOT) for d, _, fs in os.walk(full) for f in fs
        if not f.startswith(".") and not f.endswith(".tar.gz") and "MANIFEST" not in f and "__pycache__" not in d)
    if path == "deliverables/2026-10-09_v5":
        files = [f for f in files if f.count("/") == 2]
    for f in files:
        if f not in seen:
            seen.add(f)
            rows.append((f, gen, inp, sha(f), str(os.path.getsize(os.path.join(ROOT, f)))))
with open(os.path.join(ROOT, "deliverables/2026-10-09_v5/MANIFEST.tsv"), "w") as fo:
    fo.write(f"# generated at commit {commit} (plus the working-tree changes committed with it); software: {SW}\n")
    fo.write("path\tgenerated_by\tinputs_and_config\tsha256\tbytes\n")
    for r in rows:
        fo.write("\t".join(r) + "\n")
print(len(rows), "entries")
