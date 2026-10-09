"""Cached, checksummed downloads with a provenance manifest.

Every fetched file is written once under inputs/ (never overwritten), and a row is
appended to metadata/sources_manifest.tsv with URL, retrieval time, HTTP headers,
byte size, SHA-256 and purpose. An empty body or HTTP error is a failure, never an
empty dataset.
"""
import argparse
import csv
import datetime as dt
import hashlib
import json
import os
import sys
import time
import ssl
import urllib.request
import urllib.error

try:
    import certifi
    SSL_CTX = ssl.create_default_context(cafile=certifi.where())
except ImportError:  # python.org builds lack a system CA store; certifi is in requirements
    SSL_CTX = ssl.create_default_context()

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
MANIFEST = os.path.join(ROOT, "metadata", "sources_manifest.tsv")
FIELDS = ["source_id", "url", "local_path", "retrieved_utc", "http_status", "last_modified",
          "etag", "content_length_header", "bytes", "sha256", "release", "purpose", "status", "note"]
UA = "rfam-star3d-pilot/1.0 (academic research; modest rate)"


def sha256(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def manifest_rows():
    if not os.path.exists(MANIFEST):
        return []
    with open(MANIFEST, newline="") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def append_manifest(row):
    new = not os.path.exists(MANIFEST)
    with open(MANIFEST, "a", newline="") as f:
        w = csv.DictWriter(f, fieldnames=FIELDS, delimiter="\t", lineterminator="\n")
        if new:
            w.writeheader()
        w.writerow({k: row.get(k, "") for k in FIELDS})


def fetch(url, rel_path, purpose, source_id=None, release="", retries=3, timeout=120, pause=0.3):
    """Download url to inputs/<rel_path> unless already cached+recorded. Returns local path.

    Raises RuntimeError on failure (after bounded retries)."""
    local = os.path.join(ROOT, "inputs", rel_path)
    source_id = source_id or rel_path
    for r in manifest_rows():
        if r["local_path"] == os.path.relpath(local, ROOT) and r["status"] == "ok" and os.path.exists(local):
            if sha256(local) != r["sha256"]:
                raise RuntimeError(f"cached file {local} no longer matches recorded sha256")
            return local
    if os.path.exists(local):
        raise RuntimeError(f"{local} exists but is not in the manifest; refusing to overwrite")
    reused = reuse_previous_study(url, local, purpose, source_id, release)
    if reused:
        return reused
    os.makedirs(os.path.dirname(local), exist_ok=True)
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            req = urllib.request.Request(url, headers={"User-Agent": UA})
            with urllib.request.urlopen(req, timeout=timeout, context=SSL_CTX) as resp:
                status = resp.status
                hdr = resp.headers
                tmp = local + ".part"
                with open(tmp, "wb") as out:
                    while True:
                        chunk = resp.read(1 << 20)
                        if not chunk:
                            break
                        out.write(chunk)
            size = os.path.getsize(tmp)
            if status != 200 or size == 0:
                os.remove(tmp)
                raise RuntimeError(f"HTTP {status}, {size} bytes")
            cl = hdr.get("Content-Length")
            if cl and int(cl) != size:
                os.remove(tmp)
                raise RuntimeError(f"truncated: header {cl} vs {size}")
            os.rename(tmp, local)
            append_manifest(dict(source_id=source_id, url=url, local_path=os.path.relpath(local, ROOT),
                                 retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                                 http_status=status, last_modified=hdr.get("Last-Modified", ""),
                                 etag=hdr.get("ETag", ""), content_length_header=cl or "",
                                 bytes=size, sha256=sha256(local), release=release, purpose=purpose,
                                 status="ok"))
            time.sleep(pause)
            return local
        except (urllib.error.URLError, RuntimeError, TimeoutError, ConnectionError) as e:
            last_err = e
            if isinstance(e, urllib.error.HTTPError) and e.code == 404:
                break
            time.sleep(2 * attempt)
    append_manifest(dict(source_id=source_id, url=url, local_path=os.path.relpath(local, ROOT),
                         retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                         purpose=purpose, status="failed", note=str(last_err)[:300]))
    raise RuntimeError(f"failed to fetch {url}: {last_err}")


PREVIOUS_STUDY = os.environ.get("PREVIOUS_STUDY_ROOT",
                                os.path.join(os.path.dirname(ROOT), "rfam_star3d_pilot"))


def reuse_previous_study(url, local, purpose, source_id, release):
    """V2 section 14: reuse a V1 download only if its bytes still match the V1 manifest checksum."""
    man = os.path.join(PREVIOUS_STUDY, "metadata", "sources_manifest.tsv")
    if not os.path.exists(man):
        return None
    with open(man, newline="") as f:
        rows = [r for r in csv.DictReader(f, delimiter="\t") if r["url"] == url and r["status"] == "ok"]
    for r in rows:
        src = os.path.join(PREVIOUS_STUDY, r["local_path"])
        if os.path.exists(src) and sha256(src) == r["sha256"]:
            os.makedirs(os.path.dirname(local), exist_ok=True)
            import shutil
            shutil.copyfile(src, local)
            if sha256(local) != r["sha256"]:
                raise RuntimeError(f"copy of {src} failed checksum")
            append_manifest(dict(r, source_id=source_id, local_path=os.path.relpath(local, ROOT), release=release or r["release"],
                                 purpose=purpose, status="ok",
                                 note=f"reused V1 download (retrieved {r['retrieved_utc']}); sha256 re-verified "
                                      f"{dt.datetime.now(dt.timezone.utc).isoformat(timespec='seconds')}"))
            return local
    return None


def fetch_json(url, rel_path, purpose, **kw):
    p = fetch(url, rel_path, purpose, **kw)
    with open(p) as f:
        return json.load(f)


if __name__ == "__main__":
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("url")
    ap.add_argument("rel_path")
    ap.add_argument("purpose")
    ap.add_argument("--release", default="")
    a = ap.parse_args()
    print(fetch(a.url, a.rel_path, a.purpose, release=a.release))
