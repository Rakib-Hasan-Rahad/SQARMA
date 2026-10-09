"""Re-read STAR3D inputs exactly as PDB.java does; report gaps, HETATM, altloc column, partial residues, non-ACGU."""
import sys, csv, glob, os
ROOT = sys.argv[1]
REIJ = {"C3'", "C4'", "C5'", "O3'", "O5'", "P"}
inputs = list(csv.DictReader(open(os.path.join(ROOT, "mappings/aligner_inputs.tsv")), delimiter="\t"))
print("star3d_id\tn_res\tseq_as_star3d\tnonACGU(sym@id)\thetatm_res\taltloc_nonblank_atoms\tTER_count\tneg_or_icode\tpartial_reijmers(id:n_atoms_of_6)\tcoordinate_gaps(list-adjacent pairs with numbering jump)")
for m in inputs:
    path = os.path.join(ROOT, m["file"])
    res, cur, ter, alt, het = [], None, 0, 0, set()
    atoms = {}
    terminated = set()
    for line in open(path):
        if line.startswith("ENDMDL"): break
        if line.startswith("TER"): ter += 1; terminated.add(line[21:22] or ""); cur = None; continue
        if line.startswith(("ATOM", "HETATM")):
            ch = line[21]
            if ch in terminated: continue
            rid = (ch, int(line[22:26]), line[26])
            if rid != cur:
                res.append((rid, line[17:20].strip())); cur = rid
            if line[16] != " ": alt += 1
            if line.startswith("HETATM"): het.add(f"{line[17:20].strip()}{rid[1]}")
            atoms.setdefault(rid, set()).add(line[12:16].strip())
    seq = "".join(s if s in "ACGU" and len(s) == 1 else "N" for _, s in res)
    nonacgu = [f"{s}@{r[1]}" for r, s in res if s not in ("A", "C", "G", "U")]
    neg = [f"{r[1]}{r[2].strip()}" for r, _ in res if r[1] < 0 or r[2] != " "]
    partial = [f"{r[1]}:{len(atoms[r] & REIJ)}" for r, _ in res if len(atoms[r] & REIJ) < 6]
    gaps = [f"{res[i][0][1]}->{res[i+1][0][1]}" for i in range(len(res) - 1) if res[i+1][0][1] - res[i][0][1] != 1 and res[i+1][0][2] == " "]
    print("\t".join(map(str, [m["star3d_id"], len(res), seq, ",".join(nonacgu) or "-", ",".join(sorted(het)) or "-", alt, ter,
                              ",".join(neg) or "-", ",".join(partial) or "-", ",".join(gaps) or "-"])))
