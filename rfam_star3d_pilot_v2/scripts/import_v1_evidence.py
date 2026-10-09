"""V2 §14: import V1 literature / BLAST / RNAcentral downloads, checksum-verified, into this study.

Only raw downloads are imported (never V1 derived tables). Each file is copied through
fetch.reuse_previous_study(), which re-verifies SHA-256 against the V1 manifest and records the reuse.
Usage: import_v1_evidence.py [prefix ...]   (default prefixes: literature/ blast/)
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import fetch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def main(prefixes):
    man = os.path.join(fetch.PREVIOUS_STUDY, "metadata", "sources_manifest.tsv")
    rows = [r for r in csv.DictReader(open(man), delimiter="\t") if r["status"] == "ok"]
    n = 0
    for r in rows:
        rel = r["local_path"].removeprefix("inputs/")
        if not any(rel.startswith(p) for p in prefixes):
            continue
        local = os.path.join(ROOT, "inputs", rel)
        if os.path.exists(local):
            continue
        src = os.path.join(fetch.PREVIOUS_STUDY, r["local_path"])
        if not os.path.exists(src):   # e.g. quarantined captcha pages
            print("skip (absent in V1, see V1 correction rows):", rel)
            continue
        got = fetch.reuse_previous_study(r["url"], local, r["purpose"], rel, r["release"])
        if not got:
            print("NOT IMPORTED (checksum mismatch):", rel)
        else:
            n += 1
    print("imported", n)


if __name__ == "__main__":
    main(sys.argv[1:] or ["literature/", "blast/"])
