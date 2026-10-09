"""MANIFEST.tsv: each session output -> generator, inputs/config, software, sha256."""
import hashlib
import os
import subprocess

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
sha = lambda p: hashlib.sha256(open(os.path.join(ROOT, p), "rb").read()).hexdigest()  # noqa: E731
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
SW = ("Python 3.13 (.venv; requirements.lock.txt); FR3D-python 288f98cc (installed, RECORD-verified); "
      "STAR3D v1.2 tarball c9da4405, jar e03ff7bc; image star3d-runtime:1 e1602e60 (amd64 under QEMU); OpenJDK 1.8.0_504")
REF = "Rfam 15.1 Rfam.seed.gz 41f014f4; config.yaml " + sha("config.yaml")[:12]
G = [  # (path or dir, generator, inputs)
    ("results/region_evidence", "scripts/region_evidence.py (+ anchor_fit.py)", "results/*; mmCIF; annotations"),
    ("review/region_review_v4.tsv", "manual review (AI agent)", "results/region_evidence; PMC8752633"),
    ("results/sensitivity", "scripts/star3d_sensitivity.py, scripts/star3d_sensitivity_s2.py", "original .mca; S1/S2 .ct; STAR3D tarball c9da4405"),
    ("results/rfam_history", "scripts/rfam_history.py", "inputs/rfam_history/manifest.tsv (Rfam 14.0-15.0); pinned 15.1 files"),
    ("review/v4_expansion", "review/v4_expansion/screen_trna.py (+ PREREGISTRATION.md)", "RCSB GraphQL; NCBI esummary; mmCIF"),
    ("expansion_v4/results", "scripts/expansion_v4.py run", "expansion_v4/cohort_v4_prospective_freeze.json"),
    ("expansion_v4/review", "manual review (AI agent)", "expansion_v4/results/region_evidence"),
    ("deliverables/2026-10-09_v4/tables", "deliverables/2026-10-09_v4/scripts/*.py; manual tables", "results; review"),
    ("deliverables/2026-10-09_v4/star3d_sensitivity", "scripts/star3d_preproc_audit.py", "retained runs/*/STAR3D_struct_info"),
    ("deliverables/2026-10-09_v4/architecture", "pandoc 2.12 + headless Chrome; diagrams/render.py (mermaid 10.9.1)", "guide .md; diagrams/*.mmd"),
    ("deliverables/2026-10-09_v4/site", "scripts/export_site_data.py + static html/js/css", "tables listed in site/data/export_manifest.json"),
    ("deliverables/2026-10-09_v4", "hand-written reports (AI agent)", "tables above"),
    ("results/standard_seed_rows.sto", "scripts/reference.py", REF),
    ("results/standard_seed_membership.tsv", "scripts/reference.py", REF),
    ("results/reference_pairs.tsv", "scripts/reference.py", REF + "; results/residue_crosswalk.tsv"),
    ("results/correspondence_comparison.tsv", "scripts/compare.py", "results/run_manifest.tsv; runs/**/out/*.aln; results/reference_pairs.tsv"),
    ("results/pair_summary.tsv", "scripts/compare.py", "as above"),
    ("results/replicate_consistency.tsv", "scripts/compare.py", "as above"),
    ("results/interaction_comparison.tsv", "scripts/interactions.py", "annotations/raw (FR3D); results/correspondence_comparison.tsv"),
    ("results/interaction_summary.tsv", "scripts/interactions.py", "as above"),
    ("results/region_review.tsv", "scripts/regions.py", "results/correspondence_comparison.tsv; results/interaction_comparison.tsv"),
    ("reports/evidence_cards.md", "scripts/evidence_cards.py", "results/selected_representatives.tsv; review/decisions.yaml"),
    ("results/seed_collection_comparison", "scripts/survey_b.py", REF + "; Rfam 15.1 Rfam.3d.seed.gz 4055ce87"),
    ("review/v3_screening", "review/v3_screening/scripts/*.py (agent B)", "mmCIF + NCBI genomes listed in review/v3_screening/download_manifest.tsv"),
    ("audit/fresh_repro_v3_other4", "scripts/fresh_repro.py --pairs (4 pairs)", "fresh downloads (metadata/sources_manifest.tsv URLs)"),
    ("deliverables/2026-10-09/tables", "deliverables/2026-10-09/scripts/*.py; scripts/interactions.py --verify-regenerate", "review/candidate_RF00522; annotations; results"),
    ("deliverables/2026-10-09/figures", "deliverables/2026-10-09/scripts/fig_7REX_correspondence.py", "review/candidate_RF00522/residue_evidence_*; annotations/normalized"),
    ("deliverables/2026-10-09/star3d_audit", "STAR3D audit agent (scripts inside)", "runs/**/STAR3D_source; inputs/software"),
    ("deliverables/2026-10-09/site", "scripts/export_site_data.py + static html/js/css", "tables listed in site/data/export_manifest.json"),
    ("deliverables/2026-10-09", "hand-written reports (AI agent)", "tables above"),
]
rows, seen = [], set()
for path, gen, inp in G:
    full = os.path.join(ROOT, path)
    files = [path] if os.path.isfile(full) else sorted(
        os.path.relpath(os.path.join(d, f), ROOT) for d, _, fs in os.walk(full) for f in fs
        if not f.startswith(".") and not f.endswith(".tar.gz") and "MANIFEST" not in f)
    if path in ("deliverables/2026-10-09", "deliverables/2026-10-09_v4"):
        files = [f for f in files if f.count("/") == 2]
    for f in files:
        if f in seen:
            continue
        seen.add(f)
        rows.append((f, gen, inp, sha(f), str(os.path.getsize(os.path.join(ROOT, f)))))
with open(os.path.join(ROOT, "deliverables/2026-10-09_v4/MANIFEST.tsv"), "w") as fo:
    fo.write(f"# generated at data commit {commit}; software: {SW}\n")
    fo.write("path\tgenerated_by\tinputs_and_config\tsha256\tbytes\n")
    for r in rows:
        fo.write("\t".join(r) + "\n")
print(len(rows), "entries")
