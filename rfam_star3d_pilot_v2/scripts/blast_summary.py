"""Summarize NCBI blastn XML: best natural hit (excluding synthetic constructs / PDB / vectors) and
every difference between the deposited construct (query, numbered = label_seq_id) and that hit."""
import csv
import glob
import os
import xml.etree.ElementTree as ET

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
EXCL = ("synthetic construct", "vector", "chain ", "crystal structure", "Chain", "PDB")


def diffs(q, h, qfrom):
    out, qi = [], qfrom
    for a, b in zip(q, h):
        if a == "-":
            out.append(f"ins_after_{qi - 1}:{b}")
            continue
        if b == "-":
            out.append(f"{qi}{a}>del")
        elif a != b:
            out.append(f"{qi}{a}>{b}")
        qi += 1
    return out


def main():
    rows = []
    for f in sorted(glob.glob(os.path.join(ROOT, "inputs/blast/*_blastn_nt*.xml"))):
        key = os.path.basename(f).split("_blastn")[0] + ("@" + os.path.basename(f).split("_txid")[1][:-4] if "_txid" in f else "")
        root = ET.parse(f).getroot()
        qlen = int(root.findtext(".//BlastOutput_query-len"))
        hits = root.findall(".//Hit")
        best = None
        for h in hits:
            d = h.findtext("Hit_def")
            if any(x.lower() in d.lower() for x in EXCL):
                continue
            hsp = h.find(".//Hsp")
            best = (h, hsp)
            break
        if not best:
            rows.append(dict(key=key, query_len=qlen, n_hits=len(hits), status="no_natural_hit"))
            continue
        h, hsp = best
        qf, qt = int(hsp.findtext("Hsp_query-from")), int(hsp.findtext("Hsp_query-to"))
        q, s = hsp.findtext("Hsp_qseq"), hsp.findtext("Hsp_hseq")
        dd = diffs(q.replace("T", "U"), s.replace("T", "U"), qf)
        rows.append(dict(key=key, query_len=qlen, n_hits=len(hits), status="natural_hit",
                         hit_accession=h.findtext("Hit_accession"), hit_def=h.findtext("Hit_def")[:150],
                         hit_from=hsp.findtext("Hsp_hit-from"), hit_to=hsp.findtext("Hsp_hit-to"),
                         query_from=qf, query_to=qt, identities=hsp.findtext("Hsp_identity"),
                         align_len=hsp.findtext("Hsp_align-len"), evalue=hsp.findtext("Hsp_evalue"),
                         unaligned_query_5p=f"1-{qf - 1}" if qf > 1 else "", unaligned_query_3p=f"{qt + 1}-{qlen}" if qt < qlen else "",
                         differences=";".join(dd), n_differences=len(dd)))
    fields = ["key", "query_len", "n_hits", "status", "hit_accession", "hit_def", "hit_from", "hit_to", "query_from",
              "query_to", "identities", "align_len", "evalue", "unaligned_query_5p", "unaligned_query_3p",
              "n_differences", "differences"]
    with open(os.path.join(ROOT, "review/natural_sequence_comparison.tsv"), "w", newline="") as fo:
        w = csv.DictWriter(fo, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        for r in rows:
            w.writerow({k: r.get(k, "NA") if r.get(k, "") != "" else "NA" for k in fields})
    for r in rows:
        print(r["key"], r["status"], r.get("hit_def", "")[:70], r.get("identities"), "/", r.get("align_len"),
              "unal5", r.get("unaligned_query_5p"), "unal3", r.get("unaligned_query_3p"), "diffs:", r.get("differences", "")[:200])


if __name__ == "__main__":
    main()
