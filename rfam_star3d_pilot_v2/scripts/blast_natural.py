"""Phase 2c: compare deposited constructs with natural sequences via NCBI BLAST URL API (blastn vs nt).

One query at a time, >=10 s between polls (NCBI usage guidelines). Raw XML results are kept in
inputs/blast/ and recorded in the source manifest. Usage: blast_natural.py PDB_CHAIN ...
"""
import csv
import datetime as dt
import os
import re
import sys
import time
import urllib.parse
import urllib.request

sys.path.insert(0, os.path.dirname(__file__))
import fetch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
URL = "https://blast.ncbi.nlm.nih.gov/Blast.cgi"


def put(seq, entrez=None):
    data = urllib.parse.urlencode({"CMD": "Put", "PROGRAM": "blastn", "DATABASE": "nt", "QUERY": seq,
                                   "WORD_SIZE": "11", "EXPECT": "1e-3", "HITLIST_SIZE": "20",
                                   "EMAIL": "", "TOOL": "rfam_star3d_pilot",
                                   **({"ENTREZ_QUERY": entrez} if entrez else {})}).encode()
    req = urllib.request.Request(URL, data=data, headers={"User-Agent": fetch.UA})
    txt = urllib.request.urlopen(req, timeout=120, context=fetch.SSL_CTX).read().decode()
    rid = re.search(r"RID = (\S+)", txt)
    if not rid:
        raise RuntimeError("no RID returned")
    return rid.group(1)


def poll(rid, max_wait=900):
    t0 = time.time()
    while time.time() - t0 < max_wait:
        time.sleep(15)
        q = urllib.parse.urlencode({"CMD": "Get", "FORMAT_OBJECT": "SearchInfo", "RID": rid})
        txt = urllib.request.urlopen(f"{URL}?{q}", timeout=120, context=fetch.SSL_CTX).read().decode()
        if "Status=READY" in txt:
            return True
        if "Status=FAILED" in txt or "Status=UNKNOWN" in txt:
            raise RuntimeError(f"BLAST status failed/unknown for {rid}")
    raise RuntimeError("BLAST timed out")


def main(keys):
    rows = {f"{r['pdb_id']}_{r['chain_token']}": r for r in
            csv.DictReader(open(os.path.join(ROOT, "mappings/structure_sequence_map.tsv")), delimiter="\t")}
    for spec in keys:
        key, _, taxid = spec.partition(":")
        entrez = f"txid{taxid}[Organism:exp]" if taxid else None
        r = rows[key]
        seq = r["deposited_seq_parent_mapped"].replace("U", "T")
        rel = f"blast/{key}_blastn_nt.xml" if not taxid else f"blast/{key}_blastn_nt_txid{taxid}.xml"
        if os.path.exists(os.path.join(ROOT, "inputs", rel)):
            print(key, "cached")
            continue
        try:
            rid = put(seq, entrez)
            poll(rid)
            q = urllib.parse.urlencode({"CMD": "Get", "FORMAT_TYPE": "XML", "RID": rid})
            fetch.fetch(f"{URL}?{q}", rel, f"NCBI blastn vs nt for {key} deposited sequence (natural-source check); "
                                           f"RID {rid}; organism filter {entrez}; submitted {dt.datetime.now(dt.timezone.utc).isoformat()}")
            print(key, "done", rid, flush=True)
        except Exception as e:
            print(key, "FAILED", e, flush=True)
        time.sleep(10)


if __name__ == "__main__":
    main(sys.argv[1:])
