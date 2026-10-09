"""v3 screening downloader. Writes ONLY to inputs/structures/mmcif, inputs/ncbi/genomes, inputs/literature (gitignored)
and records url/sha256/UTC in review/v3_screening/download_manifest.tsv (never touches metadata/sources_manifest.tsv).
Usage: v3_fetch.py mmcif PDB...  |  v3_fetch.py genome ACC...  |  v3_fetch.py url URL RELPATH"""
import csv, datetime as dt, hashlib, os, ssl, sys, time, urllib.request
import certifi
CTX = ssl.create_default_context(cafile=certifi.where())
ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
MAN = os.path.join(ROOT, "review/v3_screening/download_manifest.tsv")
F = ["url", "local_path", "retrieved_utc", "http_status", "bytes", "sha256", "note"]
UA = "rfam-star3d-pilot/1.0 (academic research; modest rate)"

def sha(p):
    return hashlib.sha256(open(p, "rb").read()).hexdigest()

def get(url, rel, note=""):
    local = os.path.join(ROOT, "inputs", rel)
    if os.path.exists(local):
        print("exists", rel, sha(local)); return local
    os.makedirs(os.path.dirname(local), exist_ok=True)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, context=CTX, timeout=180) as r:
        data, st = r.read(), r.status
    open(local, "wb").write(data)
    new = not os.path.exists(MAN)
    with open(MAN, "a", newline="") as fh:
        w = csv.DictWriter(fh, F, delimiter="\t")
        if new: w.writeheader()
        w.writerow(dict(url=url, local_path=os.path.relpath(local, ROOT),
                        retrieved_utc=dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds"),
                        http_status=st, bytes=len(data), sha256=sha(local), note=note))
    print("got", rel, len(data)); time.sleep(0.4)
    return local

if __name__ == "__main__":
    kind, args = sys.argv[1], sys.argv[2:]
    if kind == "mmcif":
        for p in args:
            get(f"https://files.rcsb.org/download/{p}.cif.gz", f"structures/mmcif/{p}.cif.gz", "v3 screening")
    elif kind == "genome":
        for a in args:
            get(f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={a}&rettype=fasta&retmode=text",
                f"ncbi/genomes/{a}.fasta", "v3 exact-source genome")
    elif kind == "url":
        get(args[0], args[1], "v3 literature/metadata")
