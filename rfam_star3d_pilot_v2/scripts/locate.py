"""Locate deposited positions (label_seq_id) in the pinned standard seed: row residue, original
column, SS_cons character, named structural element and motif/ligand flags from #=GC tracks.

Library use: locate(fam, row_name, offset0, label_seq_ids) ; CLI: locate.py FAM ROW OFFSET0 POS [POS...]
Element names are read from bracketed spans such as '[==P2==]' in the family's own #=GC track
(any track whose name contains 'element'); positions outside any span get 'unlabelled'.
"""
import os
import re
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))
_CACHE = {}


def family(fam):
    if fam not in _CACHE:
        _CACHE[fam] = next(stockholm.parse(os.path.join(ROOT, CFG["reference"]["seed_path"]), only={fam}))
    return _CACHE[fam]


def element_spans(track):
    spans = []
    for m in re.finditer(r"\[[^\[\]]*\]", track):
        label = re.sub(r"^=+|=+$", "", m.group(0)[1:-1]).replace("=", " ").strip() or "?"
        spans.append((m.start(), m.end() - 1, label))
    return spans


def locate(fam, row_name, offset0, label_seq_ids):
    a = family(fam)
    cols = stockholm.residue_columns(a.seqs[row_name])
    el_tracks = {k: element_spans(v) for k, v in a.gc.items() if "element" in k.lower()}
    flag_tracks = {k: v for k, v in a.gc.items() if k.startswith("RNA_") and "element" not in k.lower()}
    out = []
    for L in label_seq_ids:
        k = int(L) - 1 - int(offset0)        # 0-based row residue index
        if not 0 <= k < len(cols):
            out.append(dict(label_seq_id=L, row_index1=None, column1=None, element="outside_row_interval"))
            continue
        c = cols[k]
        els = [lab for spans in el_tracks.values() for s, e, lab in spans if s <= c <= e]
        flags = [k2 for k2, v in flag_tracks.items() if v[c] not in "=.-"]
        out.append(dict(label_seq_id=L, row_index1=k + 1, column1=c + 1, row_nt=a.seqs[row_name][c],
                        ss_cons=a.gc.get("SS_cons", "?")[c], element=";".join(els) or "unlabelled",
                        motif_flags=";".join(flags)))
    return out


if __name__ == "__main__":
    fam, row, off, *pos = sys.argv[1:]
    for r in locate(fam, row, off, pos):
        print(r)
