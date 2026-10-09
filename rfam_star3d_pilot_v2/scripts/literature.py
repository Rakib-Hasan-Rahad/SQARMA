"""Phase 2b: retrieve primary-citation evidence (Europe PMC metadata + open-access full text)
for candidate representatives and extract construct/source passages for manual review.

Usage: literature.py PDB_CHAIN [PDB_CHAIN ...]
Writes review/literature/<PDB>_excerpts.txt (keyword passages with section context). Papers
themselves stay in inputs/literature/ (not redistributed).
"""
import csv
import os
import re
import sys
import urllib.parse
import xml.etree.ElementTree as ET

sys.path.insert(0, os.path.dirname(__file__))
import fetch  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
KEYWORDS = re.compile(
    r"(construct|mutat|mutant|engineer|replac|substitut|truncat|delet|insert|tetraloop|GAAA|UUCG|U1A|"
    r"crystalliz|transcri|organism|species|sequence of|derived from|from the|genom|natural|wild[- ]type|"
    r"modif|cloning|plasmid|ribozyme|hammerhead|HDV|scaffold|Fab|chaperone|numbering|nucleotides? \d)",
    re.I)


def epmc_search(query, rel):
    url = ("https://www.ebi.ac.uk/europepmc/webservices/rest/search?format=json&resultType=core&query="
           + urllib.parse.quote(query))
    return fetch.fetch_json(url, rel, f"Europe PMC metadata for {query}")


def pmc_html_passages(pmcid, pdb):
    import html as _html
    try:
        p = fetch.fetch(f"https://pmc.ncbi.nlm.nih.gov/articles/{pmcid}/", f"literature/{pdb}_{pmcid}.html",
                        f"PMC article HTML {pmcid} ({pdb}); read for construct review only")
    except RuntimeError as e:
        return [f"PMC HTML unavailable: {e}"]
    t = open(p, encoding="utf-8", errors="replace").read()
    if "reCAPTCHA" in t or "Checking your browser" in t:
        return ["PMC HTML BLOCKED (captcha page returned); construct methods UNREVIEWED from this source"]
    paras = re.findall(r"<(p|figcaption|caption)[^>]*>(.*?)</\1>", t, re.S)
    out = []
    for _, ptxt in paras:
        ptxt = re.sub(r"\s+", " ", _html.unescape(re.sub(r"<[^>]+>", "", ptxt))).strip()
        if len(ptxt) > 40 and KEYWORDS.search(ptxt):
            out.append(f"[PMC-HTML] {ptxt[:2500]}")
    return out or ["PMC HTML retrieved but no keyword passages found"]


def text_of(el):
    return re.sub(r"\s+", " ", "".join(el.itertext())).strip()


def main(keys):
    rows = {f"{r['pdb_id']}_{r['chain_token']}": r for r in
            csv.DictReader(open(os.path.join(ROOT, "mappings/structure_sequence_map.tsv")), delimiter="\t")}
    os.makedirs(os.path.join(ROOT, "review/literature"), exist_ok=True)
    for key in keys:
        r = rows[key]
        pdb = r["pdb_id"]
        m = re.search(r"PMID (\d+)", r["primary_citation"])
        d = re.search(r"DOI (\S+)", r["primary_citation"])
        q = f"EXT_ID:{m.group(1)} AND SRC:MED" if m else (f'DOI:"{d.group(1)}"' if d and d.group(1) != "None" else None)
        out = [f"# {key} {r['rfam_acc']} | {r['title']}", f"# citation: {r['primary_citation']}"]
        if not q:
            out.append("NO PRIMARY CITATION IDENTIFIER (status: unresolved literature evidence)")
        else:
            try:
                meta = epmc_search(q, f"literature/{pdb}_epmc.json")
                res = (meta.get("resultList") or {}).get("result") or []
                if not res:
                    out.append(f"Europe PMC returned no record for {q}")
                else:
                    a = res[0]
                    out.append(f"# EPMC id={a.get('id')} pmcid={a.get('pmcid')} OA={a.get('isOpenAccess')} "
                               f"inPMC={a.get('inPMC')} title={a.get('title')}")
                    out.append("## ABSTRACT\n" + re.sub(r"<[^>]+>", "", a.get("abstractText", "") or "(none)"))
                    pmcid = a.get("pmcid")
                    if pmcid:
                        try:
                            p = fetch.fetch(f"https://www.ebi.ac.uk/europepmc/webservices/rest/{pmcid}/fullTextXML",
                                            f"literature/{pdb}_{pmcid}.xml", f"Europe PMC full text {pmcid} ({pdb})")
                            root = ET.parse(p).getroot()
                            for sec in root.iter("sec"):
                                title = sec.find("title")
                                st = text_of(title) if title is not None else ""
                                for para in sec.findall("p"):
                                    t = text_of(para)
                                    for sent in re.split(r"(?<=[.;])\s+", t):
                                        if KEYWORDS.search(sent) and len(sent) < 1200:
                                            out.append(f"[{st[:40]}] {sent}")
                            for cap in root.iter("caption"):
                                t = text_of(cap)
                                if KEYWORDS.search(t):
                                    out.append(f"[FIGURE/TABLE CAPTION] {t[:1500]}")
                            for sm in root.iter("supplementary-material"):
                                out.append(f"[SUPPLEMENT] {text_of(sm)[:300]}")
                        except RuntimeError as e:
                            out.append(f"EPMC full text unavailable ({str(e)[-40:]}); trying PMC article HTML")
                            out += pmc_html_passages(pmcid, pdb)
                    else:
                        out.append("no PMC full text (not open access in Europe PMC): construct review relies on "
                                   "abstract + mmCIF; methods UNREVIEWED")
            except RuntimeError as e:
                out.append(f"metadata fetch failed: {e}")
        # de-duplicate while keeping order
        seen, uniq = set(), []
        for line in out:
            if line not in seen:
                uniq.append(line)
                seen.add(line)
        open(os.path.join(ROOT, f"review/literature/{key}_excerpts.txt"), "w").write("\n".join(uniq) + "\n")
        print(key, len(uniq), "lines", uniq[2][:120] if len(uniq) > 2 else "")


if __name__ == "__main__":
    main(sys.argv[1:])
