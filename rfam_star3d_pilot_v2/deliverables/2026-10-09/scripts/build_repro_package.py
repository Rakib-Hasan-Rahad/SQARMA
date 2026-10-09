"""Build the v3 reproducibility package from committed study files (git ls-files at HEAD). Excludes third-party
binaries/large coordinate files (retrieval instructions + sha256 in metadata/sources_manifest.tsv). Verifies itself."""
import hashlib
import os
import subprocess
import sys
import tarfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
D = os.path.join(ROOT, "deliverables", "2026-10-09")
NAME = "repro_package_v3_2026-10-09"
EXCLUDE_PREFIX = ("audit/repro_package_RF00522_v2.1", "deliverables/2026-10-09/site/assets",
                  "deliverables/2026-10-09/before_repairs/correspondence_comparison.tsv")
commit = subprocess.check_output(["git", "rev-parse", "HEAD"], cwd=ROOT, text=True).strip()
dirty = subprocess.check_output(["git", "status", "--porcelain", "--", "."], cwd=ROOT, text=True).strip()
if dirty:
    sys.exit("refusing to package a dirty study directory; commit first:\n" + dirty)
files = subprocess.check_output(["git", "ls-files", "--", "."], cwd=ROOT, text=True).split("\n")
files = sorted(f for f in files if f and not f.startswith(EXCLUDE_PREFIX) and not f.endswith(".tar.gz"))
readme = f"""# Reproducibility package, SQARMA Rfam-seed vs original STAR3D pilot (v3, 2026-10-09)

Source commit: {commit} (branch v3-session-2026-10-09). Files: {len(files)} committed study files (git ls-files).
Environment: requirements.lock.txt (Python 3.13; FR3D-python @ 288f98ccfd72dc6d88036c124605c05ce623b1b7);
STAR3D runtime image built from scripts/Dockerfile.star3d (ubuntu:22.04, openjdk-8, linux/amd64).

NOT included (third-party or large; retrieve and verify sha256 from metadata/sources_manifest.tsv):
- STAR3D v1.2: http://genome.ucf.edu/STAR3D/STAR3D_v1.2.tar.gz
  sha256 c9da44059d9cfc40828e798ebd4f6194c55415e17aaae7d90ac0f849ec2ed946 -> inputs/software/
- mmCIF coordinates: URLs + sha256 in metadata/sources_manifest.tsv (inputs/structures/mmcif/)
- Rfam 15.1 Rfam.3d.seed.gz (Survey B): https://ftp.ebi.ac.uk/pub/databases/Rfam/15.1/Rfam.3d.seed.gz
  sha256 4055ce87a369794a1e4455badcaf7c3bc3a7a524368b5b249e34b2a8d2e8146f -> inputs/rfam_survey_b/
- Literature texts (copyright), NCBI genomes (re-fetch by accession listed in review/*exact_source*.tsv).

Rerun: see README.md "Rerun by stage"; tests: python -m pytest -q tests (51 expected to pass).
Checksums of every file in this package: SHA256SUMS.
"""
out = os.path.join(D, NAME + ".tar.gz")
sums = []
for f in files:
    sums.append(f"{hashlib.sha256(open(os.path.join(ROOT, f), 'rb').read()).hexdigest()}  {f}")
with tarfile.open(out, "w:gz") as t:
    for f in files:
        t.add(os.path.join(ROOT, f), arcname=f"{NAME}/{f}")
    for name, text in (("PACKAGE_README.md", readme), ("SHA256SUMS", "\n".join(sums) + "\n")):
        p = os.path.join(D, "_tmp_" + name)
        open(p, "w").write(text)
        t.add(p, arcname=f"{NAME}/{name}")
        os.remove(p)
# verify: every member hash matches, the derived Stockholm parses inside the package
import io  # noqa: E402
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import stockholm  # noqa: E402
n = 0
with tarfile.open(out) as t:
    want = dict(l.split("  ", 1)[::-1] for l in sums)
    for m in t.getmembers():
        rel = m.name.split("/", 1)[1]
        if rel in want:
            assert hashlib.sha256(t.extractfile(m).read()).hexdigest() == want[rel], rel
            n += 1
    sto = t.extractfile(f"{NAME}/results/standard_seed_rows.sto").read()
    tmp = os.path.join(D, "_tmp.sto")
    open(tmp, "wb").write(sto)
    fams = [a.acc for a in stockholm.parse(tmp)]
    os.remove(tmp)
h = hashlib.sha256(open(out, "rb").read()).hexdigest()
open(out + ".sha256", "w").write(f"{h}  {NAME}.tar.gz\n")
print(f"package {out}: {n}/{len(files)} member hashes verified; Stockholm families parsed: {fams}; sha256 {h}; commit {commit}")
