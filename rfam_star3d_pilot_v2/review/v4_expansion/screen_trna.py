"""v4 expansion screen for RF00005 (tRNA) free X-ray candidates (pre-registered in PREREGISTRATION.md).
Verifies each sequence-only chain->row proposal with the pipeline's own structures.build_link and the row accession's
NCBI organism. Writes review/v4_expansion/candidate_structures.tsv. No STAR3D is run here."""
import csv
import hashlib
import json
import os
import sys
import urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(ROOT, "scripts"))
import fetch  # noqa: E402
import stockholm  # noqa: E402
import structures as S  # noqa: E402

OUT = os.path.join(ROOT, "review", "v4_expansion")
CANDS = [("1EHZ", "A", "K01553.1/1-73"), ("7EQJ", "B", "X17321.1/66-138"), ("9J4O", "A", "AB031211.1/7799-7884"),
         ("6PMO", "B", "AB013373.1/3754-3825"), ("9J4N", "A", "J01713.1/270-351"), ("1VTQ", "A", "Z35950.1/5070-5141"),
         ("5CCB", "N", "AP000442.6/2022-1950"), ("4YCP", "B", "AB035922.1/6128-6200"), ("2FK6", "R", "K01986.1/320-392")]


def ncbi_organism(acc):
    path = os.path.join(OUT, "raw", f"ncbi_esummary_{acc}.json")
    if not os.path.exists(path):
        url = f"https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi?db=nuccore&id={acc}&retmode=json"
        req = urllib.request.Request(url, headers={"User-Agent": fetch.UA})
        open(path, "wb").write(urllib.request.urlopen(req, timeout=60, context=fetch.SSL_CTX).read())
    d = json.load(open(path))
    uid = d["result"]["uids"][0]
    r = d["result"][uid]
    return r.get("organism"), r.get("taxid"), r.get("title")


def main():
    seed = next(stockholm.parse(os.path.join(ROOT, S.CFG["reference"]["seed_path"]), only={"RF00005"}))
    rows = []
    for pdb, chain, row in CANDS:
        path = S.get_mmcif(pdb)
        ev, b = S.extract_entry(pdb, path)
        obs, nmod, st = S.observed_atoms(path)
        acc, rs, re_ = stockholm.split_name(row)
        ung = seed.ungapped(row)
        srow = dict(row_name=row, ungapped_row=ung, gr_feature="NA (sequence-only proposal)", pdb_id=pdb, chain=chain,
                    urs="NA", row_taxid="NA", row_start=1, row_end=len(ung), row_len=len(ung),
                    row_seq_hash=hashlib.sha256(ung.encode()).hexdigest()[:16], in_mapping_file="yes")
        link, _ = S.build_link("RF00005", srow, ev, obs, nmod, b)
        org, tax, title = ncbi_organism(acc)
        mods_in = link.get("mods_in_family_interval", "")
        prot = [x for x in ev["entities"] if x["type"] == "polymer" and "polyribonucleotide" not in
                next((p.get("type", "") for p in ev["entity_poly"] if p["entity_id"] == x["id"]), "")]
        rows.append(dict(pdb_chain=f"{pdb}_{chain}", seed_row=row, row_accession_organism=org, row_accession_taxid=tax,
                         row_accession_title=title, entity_source_records=link.get("entity_source_records"),
                         expression_host=link.get("expression_host_records"), entity_src_method=link.get("entity_src_method"),
                         link_status=link.get("link_status"), sequence_match=link.get("sequence_match"),
                         row_offset_in_deposited=link.get("row_offset_in_deposited"), deposited_len=link.get("deposited_len"),
                         row_len=len(ung), observed_fraction=link.get("observed_fraction"),
                         incomplete_backbone=link.get("incomplete_backbone_seq_ids"),
                         modified_in_interval=mods_in or "none (checked)", method=link.get("exptl_method"),
                         resolution=link.get("resolution"), other_polymer_entities=link.get("other_polymer_entities") or "none",
                         ligands=link.get("ligands"), title=link.get("title"), citation=link.get("primary_citation"),
                         auth_chain_single_char=link.get("auth_chain_single_char")))
    with open(os.path.join(OUT, "candidate_structures.tsv"), "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(rows[0]), delimiter="\t", lineterminator="\n")
        w.writeheader()
        w.writerows(rows)
    for r in rows:
        print({k: (str(v)[:90]) for k, v in r.items()})


if __name__ == "__main__":
    main()
