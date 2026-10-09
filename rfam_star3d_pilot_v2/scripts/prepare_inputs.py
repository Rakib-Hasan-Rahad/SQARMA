"""Phase 4a: build STAR3D/FR3D inputs and the residue crosswalk for each selected RNA.

Policy (declared in config.yaml / README):
  * source = RCSB mmCIF (unchanged, in inputs/structures/mmcif); first model only;
  * altlocs: gemmi remove_alternative_conformations() keeps the first conformer of each atom;
  * extracted region = residues of the selected label_asym chain whose label_seq_id lies in the
    family interval (residues matched to the Rfam row); nothing else (no ligands, waters, other chains);
  * chain ID written = author chain ID (must be one character for STAR3D); residue numbers and
    insertion codes = author values, unchanged; no atoms added or renamed;
  * every residue is recorded in mappings/conversion/<rep>.tsv and in residue_crosswalk.tsv.

Usage: prepare_inputs.py  (reads results/selected_representatives.tsv)
"""
import csv
import hashlib
import json
import os
import sys

import gemmi

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
STAR3D_ATOMS = {"C3'", "C4'", "C5'", "O3'", "O5'", "P"}


def sha(path):
    return hashlib.sha256(open(path, "rb").read()).hexdigest()


def read_tsv(path):
    with open(path, encoding="utf-8") as f:
        return list(csv.DictReader(f, delimiter="\t"))


def write_tsv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) is None or r.get(k) == "" else r[k]) for k in fields})


def star3d_id(rep):
    # file stem used inside STAR3D (lower-case, unique per representative)
    return f"{rep['pdb_id'].lower()}{rep['auth_asym_id'].lower()}"


def prepare(rep, seed):
    pdb, asym, auth = rep["pdb_id"], rep["label_asym_id"], rep["auth_asym_id"]
    if len(auth) != 1:
        raise ValueError(f"{pdb} chain {auth}: STAR3D needs a one-character chain ID")
    cif = P("inputs/structures/mmcif", f"{pdb}.cif.gz")
    st = gemmi.read_structure(cif)
    st.setup_entities()
    n_models = len(st)
    while len(st) > 1:
        del st[1]
    n_alt_before = sum(1 for ch in st[0] for r in ch for a in r if a.altloc != "\0")
    st.remove_alternative_conformations()
    lo, hi = int(rep["family_label_seq_start"]), int(rep["family_label_seq_end"])
    out = gemmi.Structure()
    out.name = pdb
    out.cell = st.cell
    out.spacegroup_hm = st.spacegroup_hm
    model = gemmi.Model("1")
    newch = gemmi.Chain(auth)
    conv = []
    for ch in st[0]:
        for res in ch:
            if res.subchain != asym or res.label_seq is None or not (lo <= res.label_seq <= hi):
                continue
            r2 = res.clone()
            newch.add_residue(r2)
            names = {a.name for a in res}
            conv.append(dict(label_seq_id=res.label_seq, auth_seq_id=res.seqid.num,
                             ins_code=res.seqid.icode.strip(), comp_id=res.name, het=res.het_flag,
                             n_atoms=len(res), has_all_star3d_atoms="yes" if STAR3D_ATOMS <= names else "no",
                             missing_star3d_atoms=",".join(sorted(STAR3D_ATOMS - names))))
    model.add_chain(newch)
    out.add_model(model)
    out.setup_entities()
    sid = star3d_id(rep)
    sub = "runs/_controls/_inputs" if rep["rep_id"].startswith("CONTROL__") else "runs/_inputs"
    os.makedirs(P(sub), exist_ok=True)
    path = P(sub, f"{sid}.pdb")
    opts = gemmi.PdbWriteOptions(minimal=True)
    opts.ter_records = True
    out.write_pdb(path, opts)
    # STAR3D residue order = order of residues in file (its PDB parser); index them
    for i, c in enumerate(conv):
        c["star3d_index0"] = i
    # verify by re-reading the written file exactly as STAR3D would (cols 17-20, 22-26, 26)
    seen, order = None, []
    for line in open(path):
        if line.startswith(("ATOM", "HETATM")):
            key = (line[21], line[22:26].strip(), line[26])
            if key != seen:
                order.append(key)
                seen = key
        if line.startswith("TER"):
            break
    if len(order) != len(conv) or any(int(o[1]) != c["auth_seq_id"] or o[2].strip() != c["ins_code"]
                                      for o, c in zip(order, conv)):
        raise RuntimeError(f"{sid}: re-read residue order does not match conversion map")
    keys = [(c["auth_seq_id"], c["ins_code"]) for c in conv]
    if len(set(keys)) != len(keys):
        raise RuntimeError(f"{sid}: author residue ID collision in extracted chain")
    meta = dict(rep_id=rep["rep_id"], star3d_id=sid, pdb_id=pdb, label_asym_id=asym, auth_asym_id=auth,
                model_used=1, n_models_in_entry=n_models, altloc_atoms_before=n_alt_before,
                label_seq_range=f"{lo}-{hi}", residues_written=len(conv), file=os.path.relpath(path, ROOT),
                sha256=sha(path), source_mmcif_sha256=sha(cif))
    write_tsv(P("mappings/conversion", ("controls/" if rep["rep_id"].startswith("CONTROL__") else "") + f"{rep['rep_id']}.tsv"), conv,
              ["star3d_index0", "label_seq_id", "auth_seq_id", "ins_code", "comp_id", "het", "n_atoms",
               "has_all_star3d_atoms", "missing_star3d_atoms"])
    return meta, conv


def crosswalk(rep, conv, seed, scheme):
    """Per row residue: every numbering system + ORIGINAL standard-seed column."""
    rows = []
    fam, name = rep["rfam_acc"], rep["row_name"]
    a = seed[fam]
    cols = stockholm.residue_columns(a.seqs[name])
    by_label = {c["label_seq_id"]: c for c in conv}
    off = int(rep["row_offset_in_deposited"])
    masked = {int(x) for x in rep["masked_label_seq_ids"].split(";") if x not in ("", "NA")}
    row_seq = a.ungapped(name)
    if len(cols) != len(row_seq):
        raise RuntimeError("column map length mismatch")
    for k, ch in enumerate(row_seq):
        sch = scheme[off + k]
        lab = int(sch["seq_id"])
        c = by_label.get(lab)
        par = rep["deposited_seq_parent_mapped"][off + k]
        rows.append(dict(
            rep_id=rep["rep_id"], rfam_acc=fam, row_name=name, row_index1=k + 1,
            row_coordinate=int(rep["row_start"]) + k, row_nt=ch, original_column=cols[k] + 1,
            reference_source="Rfam.seed.gz", rfam_release=CFG["reference"]["rfam_release"],
            seed_sha256=CFG["reference"]["seed_sha256"],
            pdb_id=rep["pdb_id"], model=1, label_asym_id=rep["label_asym_id"], auth_asym_id=rep["auth_asym_id"],
            entity_id=rep["entity_id"], deposited_index1=off + k + 1, label_seq_id=lab,
            # coordinate-record author number (atom_site.auth_seq_id == pdb_seq_num); this is what STAR3D/FR3D print
            auth_seq_id=c["auth_seq_id"] if c else sch["pdb_seq_num"],
            ins_code=c["ins_code"] if c else sch["pdb_ins_code"],
            scheme_auth_seq_num=sch["auth_seq_num"], scheme_pdb_seq_num=sch["pdb_seq_num"],
            comp_id=sch["mon_id"], parent_nt=par,
            modified="yes" if sch["mon_id"] not in ("A", "C", "G", "U") else "no",
            engineered_masked="yes" if lab in masked else "no",
            observed="yes" if c else "no", star3d_atoms_complete=c["has_all_star3d_atoms"] if c else "no",
            star3d_index0=c["star3d_index0"] if c else None,
            star3d_resid=f"{rep['auth_asym_id']}:{c['auth_seq_id']}{c['ins_code']}" if c else None,
            identity_check="ok" if par == ch.upper().replace("T", "U") else "MISMATCH"))
    return rows


def main():
    import yaml as _y
    global CFG
    CFG = _y.safe_load(open(P("config.yaml")))
    reps = read_tsv(P("results/selected_representatives.tsv"))
    fams = {r["rfam_acc"] for r in reps}
    seed = {a.acc: a for a in stockholm.parse(P(CFG["reference"]["seed_path"]), only=fams)}
    metas, cw = [], []
    for rep in reps:
        safe = "".join(ch if ch.isalnum() else "_" for ch in rep["row_name"])
        ev = json.load(open(P("review/evidence", f"{rep['pdb_id']}_{rep['chain_token']}_{rep['rfam_acc']}_{safe}.json")))
        meta, conv = prepare(rep, seed)
        metas.append(meta)
        cw += crosswalk(rep, conv, seed, ev["scheme_chain"])
        print(meta["rep_id"], meta["residues_written"], "residues ->", meta["file"])
    write_tsv(P("mappings/aligner_inputs.tsv"), metas, list(metas[0].keys()))
    write_tsv(P("results/residue_crosswalk.tsv"), cw, list(cw[0].keys()))
    bad = [r for r in cw if r["identity_check"] != "ok"]
    print("crosswalk rows", len(cw), "identity mismatches", len(bad))
    # hard check: every observed crosswalk residue ID equals the residue ID written in the aligner input file
    for meta in metas:
        written = []
        for line in open(P(meta["file"])):
            if line.startswith(("ATOM", "HETATM")):
                k = (line[21], int(line[22:26]), line[26].strip())
                if not written or written[-1] != k:
                    written.append(k)
        mine = [(r["auth_asym_id"], int(r["auth_seq_id"]), r["ins_code"] or "") for r in cw
                if r["rep_id"] == meta["rep_id"] and r["observed"] == "yes"]
        if written != mine:
            raise SystemExit(f"STAGE FAILED: {meta['rep_id']} crosswalk IDs differ from written input file")
        n_diff = sum(1 for r in cw if r["rep_id"] == meta["rep_id"] and r["scheme_auth_seq_num"] not in (None, "", str(r["auth_seq_id"])))
        print(meta["rep_id"], "IDs == input file: OK;", "residues where scheme auth_seq_num != coordinate auth_seq_id:", n_diff)
    if bad:
        raise SystemExit("STAGE FAILED: crosswalk identity mismatch")


if __name__ == "__main__":
    main()
