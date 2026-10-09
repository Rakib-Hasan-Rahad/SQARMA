"""Phase 3: extract and validate the standard-seed baseline for every frozen pair.

No aligner is run. For each pair the two ORIGINAL gapped rows are taken from the pinned Rfam.seed.gz,
their bytes are traced back to the raw decompressed archive lines, and every original column with
residues in both rows becomes a reference pair. Residue-gap columns are written separately.

Outputs (keys prefixed by pair_id / rep_id):
  results/standard_seed_membership.tsv   proof of membership per selected row
  results/standard_seed_rows.sto         derived excerpt: selected rows + all #=GC lines, ORIGINAL columns
  results/reference_pairs.tsv            (pair, original column, row_A index, row_B index, structure join)
  results/reference_gap_assignments.tsv  residue-gap columns
  results/reference_example_<pair>.txt   readable excerpt for manual tracing
Usage: reference.py [pair_id ...]   (default: all pairs in results/selected_pairs.tsv)
"""
import csv
import gzip
import hashlib
import os
import sys

import yaml

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))
REF = CFG["reference"]


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def write_tsv(path, rows, fields):
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) is None or r.get(k) == "" else r[k]) for k in fields})


def check_reference():
    h = hashlib.sha256(open(P(REF["seed_path"]), "rb").read()).hexdigest()
    if os.path.basename(REF["seed_path"]) != "Rfam.seed.gz" or h != REF["seed_sha256"]:
        raise SystemExit("STAGE FAILED: reference source is not the pinned Rfam.seed.gz")


def raw_lines(wanted):
    """Read the decompressed archive and return {lineno: raw text} for wanted line numbers."""
    out, wanted = {}, set(wanted)
    with gzip.open(P(REF["seed_path"]), "rb") as f:
        for i, b in enumerate(f, 1):
            if i in wanted:
                out[i] = b.decode("utf-8", "replace").rstrip("\n")
    return out


def load_crosswalk():
    cw = {}
    path = P("results/residue_crosswalk.tsv")
    if os.path.exists(path):
        for r in read_tsv(path):
            cw[(r["rep_id"], int(r["row_index1"]))] = r
    return cw


def struct_status(cw, rep, k, masked):
    c = cw.get((rep["rep_id"], k))
    if c is None:
        return None, "no_crosswalk"
    if c["observed"] != "yes":
        return c, "missing_coordinates"
    if int(c["label_seq_id"]) in masked:
        return c, "engineered_position_masked"
    return c, "assessable"


def main(only):
    if only:
        raise SystemExit("subset runs would overwrite the complete global tables; run without arguments")
    check_reference()
    reps = {r["rep_id"]: r for r in read_tsv(P("results/selected_representatives.tsv"))}
    pairs = [p for p in read_tsv(P("results/selected_pairs.tsv")) if not only or p["pair_id"] in only]
    fams = {p["rfam_acc"] for p in pairs}
    seed = {a.acc: a for a in stockholm.parse(P(REF["seed_path"]), only=fams)}
    cw = load_crosswalk()

    # membership proof
    used = sorted({p["query_rep"] for p in pairs} | {p["target_rep"] for p in pairs})
    need = {}
    for rid in used:
        r = reps[rid]
        need[rid] = [int(x) for x in r["seed_row_lines"].split(",")]
    raw = raw_lines([n for v in need.values() for n in v])
    mem = []
    for rid in used:
        r, a = reps[rid], seed[reps[rid]["rfam_acc"]]
        name = r["row_name"]
        traced = "".join(raw[n].split()[1] for n in need[rid] if raw[n].split()[0] == name)
        ok_name = all(raw[n].split()[0] == name for n in need[rid])
        aligned = a.seqs.get(name)
        h = hashlib.sha256(aligned.encode()).hexdigest() if aligned else None
        status = "verified" if (aligned and ok_name and traced == aligned and h == r["seed_row_aligned_sha256"]) else "failed"
        mem.append(dict(rep_id=rid, rfam_acc=r["rfam_acc"], row_name=name, reference_source="Rfam.seed.gz",
                        rfam_release=REF["rfam_release"], seed_sha256=REF["seed_sha256"],
                        decompressed_line_numbers=r["seed_row_lines"], aligned_length=len(aligned or ""),
                        aligned_sha256=h, phase2_recorded_sha256=r["seed_row_aligned_sha256"],
                        raw_line_trace_equals_parsed="yes" if traced == aligned else "no",
                        ungapped_len=len(stockholm.residue_columns(aligned or "")), membership_status=status))
        if status != "verified":
            raise SystemExit(f"STAGE FAILED: {rid} row not verified in pinned standard seed")
    write_tsv(P("results/standard_seed_membership.tsv"), mem, list(mem[0].keys()))

    # derived Stockholm excerpt with original columns
    with open(P("results/standard_seed_rows.sto"), "w") as f:
        f.write("# STOCKHOLM 1.0\n#=GF CC DERIVED EXCERPT of pinned Rfam.seed.gz (release %s, sha256 %s); "
                "original columns preserved; not an alignment product\n" % (REF["rfam_release"], REF["seed_sha256"]))
        for fam in sorted(fams):
            a = seed[fam]
            f.write(f"#=GF AC   {fam}\n")
            for rid in used:
                if reps[rid]["rfam_acc"] == fam:
                    n = reps[rid]["row_name"]
                    f.write(f"{n:<45} {a.seqs[n]}\n")
                    for feat, s in a.gr.get(n, {}).items():
                        f.write(f"#=GR {n:<40} {feat:<10} {s}\n")
            for k, s in a.gc.items():
                f.write(f"#=GC {k:<40} {s}\n")
        f.write("//\n")

    rp, gaps = [], []
    for p in pairs:
        A, B = reps[p["query_rep"]], reps[p["target_rep"]]
        a = seed[p["rfam_acc"]]
        sa, sb = a.seqs[A["row_name"]], a.seqs[B["row_name"]]
        mA = {int(x) for x in A["masked_label_seq_ids"].split(";") if x not in ("", "NA")}
        mB = {int(x) for x in B["masked_label_seq_ids"].split(";") if x not in ("", "NA")}
        ia = ib = 0
        ss = a.gc.get("SS_cons", "")
        for col, (ca, cb) in enumerate(zip(sa, sb), 1):
            ga, gb = ca in "-.", cb in "-.",
            if not ga:
                ia += 1
            if not gb:
                ib += 1
            if ga and gb:
                continue
            if not ga and not gb:
                xa, sta = struct_status(cw, A, ia, mA)
                xb, stb = struct_status(cw, B, ib, mB)
                both = "assessable" if sta == stb == "assessable" else \
                    ("engineered_position_masked" if "engineered_position_masked" in (sta, stb) else
                     ("missing_coordinates" if "missing_coordinates" in (sta, stb) else "no_crosswalk"))
                rp.append(dict(pair_id=p["pair_id"], rfam_acc=p["rfam_acc"], original_column=col, ss_cons=ss[col - 1],
                               row_A=A["row_name"], row_A_index=ia, row_A_nt=ca, row_B=B["row_name"], row_B_index=ib,
                               row_B_nt=cb, A_label_seq_id=xa["label_seq_id"] if xa else None,
                               A_auth=f"{xa['auth_asym_id']}:{xa['auth_seq_id']}{xa['ins_code'] if xa['ins_code'] != 'NA' else ''}" if xa else None,
                               B_label_seq_id=xb["label_seq_id"] if xb else None,
                               B_auth=f"{xb['auth_asym_id']}:{xb['auth_seq_id']}{xb['ins_code'] if xb['ins_code'] != 'NA' else ''}" if xb else None,
                               A_status=sta, B_status=stb, structural_assessability=both,
                               reference_source="Rfam.seed.gz", rfam_release=REF["rfam_release"],
                               seed_sha256=REF["seed_sha256"]))
            else:
                row, idx, nt, rep, msk = (("A", ia, ca, A, mA) if not ga else ("B", ib, cb, B, mB))
                x, stt = struct_status(cw, rep, idx, msk)
                gaps.append(dict(pair_id=p["pair_id"], rfam_acc=p["rfam_acc"], original_column=col, ss_cons=ss[col - 1],
                                 residue_row=row, row_name=rep["row_name"], row_index=idx, row_nt=nt,
                                 label_seq_id=x["label_seq_id"] if x else None, structure_status=stt,
                                 partner="gap", reference_source="Rfam.seed.gz", rfam_release=REF["rfam_release"]))
        # readable example
        with open(P(f"results/reference_example_{p['pair_id']}.txt"), "w") as f:
            f.write(f"{p['pair_id']}  (pinned Rfam.seed.gz {REF['rfam_release']}; ORIGINAL column numbers)\n")
            for start in range(0, len(sa), 60):
                f.write(f"col {start + 1:>4}  {'A':<3} {sa[start:start + 60]}\n")
                f.write(f"{'':9} {'B':<3} {sb[start:start + 60]}\n")
                f.write(f"{'':9} SS  {ss[start:start + 60]}\n\n")
    f1 = ["pair_id", "rfam_acc", "original_column", "ss_cons", "row_A", "row_A_index", "row_A_nt", "row_B",
          "row_B_index", "row_B_nt", "A_label_seq_id", "A_auth", "B_label_seq_id", "B_auth", "A_status", "B_status",
          "structural_assessability", "reference_source", "rfam_release", "seed_sha256"]
    write_tsv(P("results/reference_pairs.tsv"), rp, f1)
    write_tsv(P("results/reference_gap_assignments.tsv"), gaps, list(gaps[0].keys()) if gaps else ["pair_id"])
    for p in pairs:
        n = [r for r in rp if r["pair_id"] == p["pair_id"]]
        print(p["pair_id"], "reference pairs", len(n), "assessable", sum(r["structural_assessability"] == "assessable" for r in n),
              "gap assignments", sum(g["pair_id"] == p["pair_id"] for g in gaps))


if __name__ == "__main__":
    main(sys.argv[1:])
