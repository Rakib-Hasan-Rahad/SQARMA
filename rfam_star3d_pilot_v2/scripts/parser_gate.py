"""Phase 1 gate: Stockholm parser on a REAL interleaved record vs the pinned standard seed.

Usage: parser_gate.py <interleaved.sto> <FAMILY_ACC> <ROW_NAME> [GR_FEATURE]
An independent raw-line concatenation is compared with stockholm.parse(); the assembled rows are
then compared with the same family in the pinned Rfam.seed.gz. Writes logs/parser_gate_<FAMILY>.txt.
"""
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
CFG = yaml.safe_load(open(os.path.join(ROOT, "config.yaml")))


def raw_assemble(path, name, feat=None):
    seq, gr, lines = "", "", []
    for i, line in enumerate(open(path, encoding="utf-8"), 1):
        f = line.split()
        if len(f) == 2 and f[0] == name:
            seq += f[1]
            lines.append((i, line.rstrip()[:95]))
        elif feat and len(f) == 4 and f[:3] == ["#=GR", name, feat]:
            gr += f[3]
            lines.append((i, line.rstrip()[:95]))
    return seq, gr, lines


def main(path, fam, name, feat=None):
    rec = next(stockholm.parse(path))
    out = [f"interleaved file: {os.path.relpath(path, ROOT)}; record {rec.acc}; {len(rec.seqs)} rows; width {rec.width}"]
    seq, gr, lines = raw_assemble(path, name, feat)
    blocks = sum(1 for _, t in lines if not t.startswith("#"))
    out.append(f"raw lines for {name}{' / ' + feat if feat else ''} ({blocks} sequence blocks):")
    out += [f"  L{i}: {t}" for i, t in lines]
    ok_raw = seq == rec.seqs[name] and (not feat or gr == rec.gr[name][feat])
    out.append(f"independent raw assembly == parser assembly: {ok_raw}")
    seed = next(stockholm.parse(os.path.join(ROOT, CFG["reference"]["seed_path"]), only={fam}))
    same_names = set(seed.seqs) == set(rec.seqs)
    same_aln = same_names and all(seed.seqs[n] == rec.seqs[n] for n in seed.seqs)
    same_gc = {k: seed.gc.get(k) == rec.gc.get(k) for k in rec.gc}
    out.append(f"vs pinned Rfam.seed.gz ({CFG['reference']['rfam_release']}): rows {len(seed.seqs)}; same names {same_names}; "
               f"identical aligned strings {same_aln}; GC identical {same_gc}")
    out.append(f"GATE parser-on-interleaved-record: {'PASS' if ok_raw and blocks > 1 else 'FAIL'} "
               f"(reviewer: AI agent; raw lines above viewed directly)")
    txt = "\n".join(out)
    open(os.path.join(ROOT, f"logs/parser_gate_{fam}.txt"), "w").write(txt + "\n")
    print(txt)


if __name__ == "__main__":
    main(*sys.argv[1:])
