"""Submit NCBI BLAST (blastn, nt or core_nt, organism-restricted) and save XML to inputs/blast/v3_<key>.xml. Records in v3 manifest.
Usage: v3_blast.py KEY SEQ ORGANISM_QUERY"""
import sys, time, urllib.parse, urllib.request, re, os
sys.path.insert(0, os.path.dirname(__file__)); import v3_fetch
key, seq, org = sys.argv[1:4]
data = urllib.parse.urlencode({"CMD": "Put", "PROGRAM": "blastn", "DATABASE": "core_nt", "QUERY": seq, "ENTREZ_QUERY": org,
                               "WORD_SIZE": "11", "HITLIST_SIZE": "10"}).encode()
r = urllib.request.urlopen(urllib.request.Request("https://blast.ncbi.nlm.nih.gov/Blast.cgi", data, headers={"User-Agent": v3_fetch.UA}), context=v3_fetch.CTX, timeout=60).read().decode()
rid = re.search(r"RID = (\S+)", r).group(1); print("RID", rid, flush=True)
for _ in range(40):
    time.sleep(15)
    s = urllib.request.urlopen(f"https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Get&FORMAT_OBJECT=SearchInfo&RID={rid}", context=v3_fetch.CTX, timeout=60).read().decode()
    if "Status=READY" in s: break
    if "Status=FAILED" in s or "Status=UNKNOWN" in s: sys.exit("blast failed")
v3_fetch.get(f"https://blast.ncbi.nlm.nih.gov/Blast.cgi?CMD=Get&FORMAT_TYPE=XML&RID={rid}", f"blast/v3_{key}.xml", f"v3 blast {org}")
