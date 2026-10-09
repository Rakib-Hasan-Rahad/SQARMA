"""Exact-source genomic check (v2.1): is the deposited family-interval sequence present EXACTLY in the reference
genome of the CLAIMED source organism? (A BLAST match to a related species is not exact-source verification.)
Genomes are fetched via NCBI efetch into inputs/ncbi/ (checksummed manifest). Both strands are searched.
Usage: exact_source_check.py KEY:ACCESSION[:organism] ...  -> review/exact_source_check.tsv (appends/updates)
"""
import csv
import os
import sys

sys.path.insert(0, os.path.dirname(__file__))
import fetch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
COMP = str.maketrans("ACGTN", "TGCAN")


def genome(acc):
    url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/efetch.fcgi?db=nuccore&id={acc}&rettype=fasta&retmode=text"
    p = fetch.fetch(url, f"ncbi/genomes/{acc}.fasta", f"reference genome {acc} for exact-source sequence check")
    lines = open(p).read().splitlines()
    if not lines or not lines[0].startswith(">"):
        raise RuntimeError(f"{acc}: not a FASTA record")
    return lines[0], "".join(lines[1:]).upper()


def find_all(g, s):
    out, i = [], g.find(s)
    while i != -1:
        out.append(i + 1)
        i = g.find(s, i + 1)
    return out


def main(specs):
    links = {f"{r['pdb_id']}_{r['chain_token']}": r for r in
             csv.DictReader(open(os.path.join(ROOT, "mappings/structure_sequence_map.tsv")), delimiter="\t")
             if r["link_basis"] == "explicit_GR_feature"}
    path = os.path.join(ROOT, "review/exact_source_check.tsv")
    rows = {r["key"] + "|" + r["accession"]: r for r in csv.DictReader(open(path), delimiter="\t")} if os.path.exists(path) else {}
    for spec in specs:
        key, acc, *org = spec.split(":")
        L = links[key]
        dep = L["deposited_seq_parent_mapped"]
        off, n = int(L["row_offset_in_deposited"]), int(L["row_len"])
        fam = dep[off:off + n].replace("U", "T")
        full = dep.replace("U", "T")
        import yaml
        dec = yaml.safe_load(open(os.path.join(ROOT, "review/decisions.yaml")))["families"]
        masked = next((set(x.get("masked") or []) for d in dec.values() for x in d.get("representatives", [])
                       if x["key"] == key), set())
        lab0 = int(L["family_label_seq_start"])
        lo, hi = lab0, lab0 + n - 1
        while lo in masked:
            lo += 1
        while hi in masked:
            hi -= 1
        internal_masked = sorted(m for m in masked if lo <= m <= hi)
        core = dep[lo - 1:hi].replace("U", "T")
        head, g = genome(acc)
        rc = g.translate(COMP)[::-1]
        hits_fam = [f"+{p}" for p in find_all(g, fam)] + [f"-{len(g) - p - len(fam) + 2}" for p in find_all(rc, fam)]
        hits_full = [f"+{p}" for p in find_all(g, full)] + [f"-{len(g) - p - len(full) + 2}" for p in find_all(rc, full)]
        hits_core = [f"+{p}" for p in find_all(g, core)] + [f"-{len(g) - p - len(core) + 2}" for p in find_all(rc, core)]
        rows[key + "|" + acc] = dict(core_label_range=f"{lo}-{hi}", core_exact_hits=";".join(hits_core) or "none",
                                     internal_masked_positions=",".join(map(str, internal_masked)) or "none",
                                     key=key, claimed_organism=(org[0] if org else ""), accession=acc,
                                     genome_title=head[1:120], genome_len=len(g), family_interval_len=len(fam),
                                     family_interval_exact_hits=";".join(hits_fam) or "none",
                                     deposited_full_len=len(full), deposited_full_exact_hits=";".join(hits_full) or "none",
                                     verdict=("exact_source_verified" if hits_fam else
                                              "core_exact_source_verified_termini_differ" if hits_core and not internal_masked else
                                              "NOT_found_exactly_in_claimed_genome"))
        print(rows[key + "|" + acc])
    fields = ["key", "claimed_organism", "accession", "genome_title", "genome_len", "family_interval_len",
              "family_interval_exact_hits", "core_label_range", "core_exact_hits", "internal_masked_positions", "deposited_full_len", "deposited_full_exact_hits", "verdict"]
    with open(path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows.values())


if __name__ == "__main__":
    main(sys.argv[1:])
