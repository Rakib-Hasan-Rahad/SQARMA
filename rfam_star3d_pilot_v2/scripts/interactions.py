"""Phase 5: FR3D evaluation annotations and interaction-preservation comparison.

Evaluation annotations: fr3d-python (commit pinned in config), categories basepair+stacking, run on the
unchanged RCSB mmCIF (model 1 kept; other models/chains ignored after annotation). These are distinct
from STAR3D's own preprocessing annotations (MC-Annotate WWc pairs), but both describe canonical pairs,
so canonical-pair preservation is NOT independent validation of STAR3D.

Normalization: one record per unordered intrachain pair, ordered by row index (i<j); when an FR3D line
is reversed the two edge letters are swapped (e.g. tSH <-> tHS) and s35 <-> s53.
Canonical = cWW with identities AU/UA/GC/CG; cWW GU/UG = 'wobble'; everything else 'noncanonical'.

Outputs: annotations/normalized/<rep>.tsv, results/interaction_comparison.tsv, results/interaction_summary.tsv
Usage: interactions.py [pair_id ...]
"""
import csv
import gzip
import hashlib
import os
import subprocess
import sys
from collections import defaultdict

import yaml

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
CFG = yaml.safe_load(open(P("config.yaml")))
CANON = {("A", "U"), ("U", "A"), ("G", "C"), ("C", "G")}
WOBBLE = {("G", "U"), ("U", "G")}


def read_tsv(path):
    return list(csv.DictReader(open(path, encoding="utf-8"), delimiter="\t"))


def write_tsv(path, rows, fields):
    os.makedirs(os.path.dirname(path), exist_ok=True)
    with open(path, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=fields, delimiter="\t", lineterminator="\n", extrasaction="ignore")
        w.writeheader()
        for r in rows:
            w.writerow({k: ("NA" if r.get(k) is None or r.get(k) == "" else r[k]) for k in fields})


def reverse_label(label):
    """Reverse an FR3D interaction label for swapped endpoints."""
    neg = label.startswith("n")
    core = label[1:] if neg else label
    if core in ("s35", "s53"):
        core = "s53" if core == "s35" else "s35"
    elif len(core) == 3 and core[0] in "ct" and core[1] in "WHS" and core[2] in "WHS":
        core = core[0] + core[2] + core[1]
    elif len(core) == 4 and core[0] in "ct" and core[1] in "WHS" and core[2] in "WHSa" :
        core = core[0] + core[2] + core[1] + core[3:]
    return ("n" if neg else "") + core


def parse_unit(u):
    f = u.split("|")
    icode = f[7] if len(f) > 7 and f[7] else ""
    symop = f[8] if len(f) > 8 and f[8] else "1_555"     # absent symmetry operator = identity
    return dict(pdb=f[0], model=int(f[1]), chain=f[2], comp=f[3], num=int(f[4]), icode=icode, symop=symop)


def symmetry_class(u1, u2):
    """identity: both endpoints in the deposited copy; copy_duplicate: both in the same non-identity copy
    (re-annotation of an equivalent molecule); inter_copy: a contact BETWEEN different symmetry copies."""
    if u1["symop"] == "1_555" and u2["symop"] == "1_555":
        return "identity"
    if u1["symop"] == u2["symop"]:
        return "copy_duplicate"
    return "inter_copy"


def _sha(path):
    import hashlib
    h = hashlib.sha256()
    with open(path, "rb") as f:
        for b in iter(lambda: f.read(1 << 20), b""):
            h.update(b)
    return h.hexdigest()


def _cif_bytes_sha(pdb):
    import hashlib
    with gzip.open(P("inputs/structures/mmcif", f"{pdb}.cif.gz"), "rb") as fi:
        return hashlib.sha256(fi.read()).hexdigest()


_FR3D_PROV = None


def installed_fr3d_provenance():
    """v3 repair C: provenance of the FR3D package the running interpreter ACTUALLY imports (not a config label):
    the installed distribution's PEP 610 direct_url.json VCS commit, plus a check that every installed fr3d file
    still matches the sha256 in the distribution RECORD and that `import fr3d` resolves inside that distribution."""
    global _FR3D_PROV
    if _FR3D_PROV is not None:
        return _FR3D_PROV
    import base64
    import importlib.metadata as md
    import json
    import fr3d
    dist = md.distribution("fr3d")
    du = json.loads(dist.read_text("direct_url.json") or "{}")
    base = os.path.realpath(str(dist.locate_file("")))
    checked = bad = 0
    for f in dist.files or []:
        if not f.hash or not str(f).startswith("fr3d"):
            continue
        data = open(dist.locate_file(f), "rb").read()
        dig = base64.urlsafe_b64encode(hashlib.sha256(data).digest()).rstrip(b"=").decode()
        checked += 1
        bad += dig != f.hash.value
    imported = os.path.realpath(os.path.dirname(fr3d.__file__))
    _FR3D_PROV = dict(interpreter=sys.executable, distribution=f"{dist.metadata['Name']} {dist.version}",
                      vcs_url=du.get("url"), installed_commit=(du.get("vcs_info") or {}).get("commit_id"),
                      imported_from=imported, import_inside_distribution=imported.startswith(base),
                      record_files_checked=checked, record_files_mismatched=bad)
    return _FR3D_PROV


def pinned_fr3d_commit():
    return CFG["annotation"]["tool"].split("commit")[-1].strip()


def verified_fr3d_commit():
    """Installed commit, or stop: an unverifiable or different FR3D must not produce/reuse annotations."""
    pv = installed_fr3d_provenance()
    if (pv["installed_commit"] != pinned_fr3d_commit() or pv["record_files_mismatched"] or not pv["record_files_checked"]
            or not pv["import_inside_distribution"]):
        raise SystemExit(f"FR3D provenance not verified: {pv} (pinned {pinned_fr3d_commit()})")
    return pv["installed_commit"]


def raw_output_check(paths):
    """Hashes and completeness of FR3D raw outputs: files exist and every non-blank line is
    '<unit>\t<label>\t<unit>...' with parseable unit IDs."""
    out = {}
    for path in paths:
        if not os.path.exists(path):
            raise SystemExit(f"FR3D raw output missing: {path}")
        for k, line in enumerate(open(path), 1):
            if not line.strip():
                continue
            f = line.rstrip("\n").split("\t")
            try:
                assert len(f) >= 3
                parse_unit(f[0]), parse_unit(f[2])
            except Exception:
                raise SystemExit(f"FR3D raw output incomplete/malformed: {path} line {k}") from None
        out[os.path.basename(path)] = _sha(path)
    return out


def annotate(pdb, raw_dir=None):
    """Run (or reuse) FR3D for one entry. Reuse requires a provenance sidecar whose source mmCIF sha256,
    decompressed-CIF sha256, VERIFIED installed FR3D commit and raw-output sha256s match the current files, and
    complete raw outputs; otherwise the stage fails (v3 repair C)."""
    import json
    raw_dir = raw_dir or P("annotations/raw")
    side = os.path.join(raw_dir, f"{pdb}.provenance.json")
    want = dict(source_mmcif=f"inputs/structures/mmcif/{pdb}.cif.gz",
                source_mmcif_sha256=_sha(P("inputs/structures/mmcif", f"{pdb}.cif.gz")),
                decompressed_cif_sha256=_cif_bytes_sha(pdb),
                fr3d_commit=verified_fr3d_commit(),
                categories="basepair,stacking", model_policy="all models annotated; model 1 kept in normalization")
    raw = os.path.join(raw_dir, f"{pdb}_basepair.txt")
    outs = [raw, os.path.join(raw_dir, f"{pdb}_stacking.txt")]
    if os.path.exists(raw):
        if not os.path.exists(side):
            raise SystemExit(f"cached FR3D output for {pdb} has no provenance sidecar; regenerate or backfill")
        got = json.load(open(side))
        for k in ("source_mmcif_sha256", "decompressed_cif_sha256", "fr3d_commit", "categories"):
            if got.get(k) != want[k]:
                raise SystemExit(f"cached FR3D output for {pdb}: provenance mismatch on {k}")
        if "raw_sha256" not in got:
            raise SystemExit(f"cached FR3D output for {pdb}: sidecar has no raw-output hashes "
                             "(run interactions.py --verify-regenerate)")
        if raw_output_check(outs) != got["raw_sha256"]:
            raise SystemExit(f"cached FR3D output for {pdb}: raw output bytes differ from the sidecar record")
    else:
        os.makedirs(raw_dir, exist_ok=True)
        cif_dir = os.path.join(raw_dir, "_cif")
        os.makedirs(cif_dir, exist_ok=True)
        cif = os.path.join(cif_dir, f"{pdb}.cif")
        with gzip.open(P("inputs/structures/mmcif", f"{pdb}.cif.gz"), "rb") as fi, open(cif, "wb") as fo:
            fo.write(fi.read())
        cmd = [sys.executable, "-m", "fr3d.classifiers.NA_pairwise_interactions", "-i", cif_dir,
               "-o", raw_dir, "-c", "basepair,stacking", f"{pdb}.cif"]
        p = subprocess.run(cmd, capture_output=True, text=True)
        open(os.path.join(raw_dir, f"{pdb}.log"), "w").write(" ".join(cmd) + "\n" + p.stdout + p.stderr)
        if p.returncode != 0:
            raise RuntimeError(f"FR3D failed for {pdb}")
        json.dump(dict(want, command=" ".join(cmd), provenance="generated", raw_sha256=raw_output_check(outs),
                       fr3d_installed=installed_fr3d_provenance()), open(side, "w"), indent=1)
    return [os.path.join(raw_dir, f"{pdb}_basepair.txt"), os.path.join(raw_dir, f"{pdb}_stacking.txt")]


def verify_regenerate(report_path):
    """v3: rerun FR3D (verified installed commit) for every retained raw output into a scratch directory, compare
    bytes, and upgrade the sidecar to verified provenance only when raw outputs are byte-identical. The previous
    sidecar is kept as <pdb>.provenance.v2.1.json. Differences are reported and the retained files are untouched."""
    import json
    import shutil
    commit = verified_fr3d_commit()
    rows = []
    for f in sorted(os.listdir(P("annotations/raw"))):
        if not f.endswith("_basepair.txt"):
            continue
        pdb = f.split("_")[0]
        scratch = P("annotations", "_v3_regen", pdb)
        shutil.rmtree(scratch, ignore_errors=True)
        os.makedirs(scratch)
        side = P("annotations/raw", f"{pdb}.provenance.json")
        old = json.load(open(side)) if os.path.exists(side) else {}
        new = json.load(open(annotate(pdb, raw_dir=scratch) and os.path.join(scratch, f"{pdb}.provenance.json")))
        kept = [P("annotations/raw", f"{pdb}_{k}.txt") for k in ("basepair", "stacking")]
        same = raw_output_check(kept) == new["raw_sha256"]
        rows.append(dict(pdb=pdb, previous_provenance=old.get("provenance", "missing"), installed_commit=commit,
                         regenerated_basepair_sha256=new["raw_sha256"][f"{pdb}_basepair.txt"],
                         regenerated_stacking_sha256=new["raw_sha256"][f"{pdb}_stacking.txt"],
                         retained_byte_identical="yes" if same else "NO"))
        if same:
            if old and not os.path.exists(side.replace(".json", ".v2.1.json")):
                shutil.copyfile(side, side.replace(".json", ".v2.1.json"))
            json.dump(dict(new, provenance="verified_v3: regenerated with the verified installed FR3D commit; raw "
                                           "outputs byte-identical to the retained files"), open(side, "w"), indent=1)
        print(pdb, "identical" if same else "DIFFERS")
    with open(report_path, "w") as fo:
        fo.write("\t".join(rows[0]) + "\n")
        for r in rows:
            fo.write("\t".join(str(v) for v in r.values()) + "\n")
    return rows


def backfill_sidecars():
    """One-off (v2.1): write sidecars for pre-existing raw files ONLY if the CIF FR3D actually read
    (annotations/_cif/<pdb>.cif) is byte-identical to the pinned download. Marked 'reconstructed'."""
    import json
    for f in sorted(os.listdir(P("annotations/raw"))):
        if not f.endswith("_basepair.txt"):
            continue
        pdb = f.split("_")[0]
        side = P("annotations/raw", f"{pdb}.provenance.json")
        if os.path.exists(side):
            continue
        used = P("annotations/_cif", f"{pdb}.cif")
        ok = os.path.exists(used) and _sha(used) == _cif_bytes_sha(pdb)
        if not ok:
            print(pdb, "NOT backfilled: CIF used by FR3D missing or differs from pinned download")
            continue
        json.dump(dict(source_mmcif=f"inputs/structures/mmcif/{pdb}.cif.gz",
                       source_mmcif_sha256=_sha(P("inputs/structures/mmcif", f"{pdb}.cif.gz")),
                       decompressed_cif_sha256=_sha(used),
                       fr3d_commit=CFG["annotation"]["tool"].split("commit")[-1].strip(),
                       categories="basepair,stacking",
                       model_policy="all models annotated; model 1 kept in normalization",
                       provenance="reconstructed_v2.1: annotations/_cif CIF verified byte-identical to pinned "
                                  "mmCIF; FR3D commit taken from the single environment record (venv pinned)"),
                  open(side, "w"), indent=1)
        print(pdb, "backfilled")


def normalized(rep_id, rep, cw):
    """Intrachain interactions with both endpoints in the row interval, model 1, normalized."""
    by_auth = {(r["auth_asym_id"], int(r["auth_seq_id"]), "" if r["ins_code"] in ("NA", "") else r["ins_code"]): int(r["row_index1"])
               for r in cw.values() if r["observed"] == "yes"}
    nt = {int(r["row_index1"]): r["parent_nt"] for r in cw.values()}
    out, interchain, seen = [], 0, set()
    symcount = {"copy_duplicate": 0, "inter_copy": 0}
    for path in annotate(rep["pdb_id"]):
        for line in open(path):
            f = line.rstrip("\n").split("\t")
            if len(f) < 3:
                continue
            u1, lab, u2 = parse_unit(f[0]), f[1], parse_unit(f[2])
            if u1["model"] != 1 or u2["model"] != 1:
                continue
            sc = symmetry_class(u1, u2)
            if sc != "identity":            # never counted as an intramolecular interaction
                symcount[sc] += 1
                continue
            ch = rep["auth_asym_id"]
            if (u1["chain"] == ch) != (u2["chain"] == ch):
                interchain += 1
                continue
            if u1["chain"] != ch:
                continue
            i = by_auth.get((ch, u1["num"], u1["icode"]))
            j = by_auth.get((ch, u2["num"], u2["icode"]))
            if i is None or j is None:
                continue
            if i > j:
                i, j, lab = j, i, reverse_label(lab)
            key = (i, j, lab)
            if key in seen:
                continue
            seen.add(key)
            kind = "stack" if lab.lstrip("n").startswith("s") else "basepair"
            if kind == "basepair" and lab == "cWW" and (nt[i], nt[j]) in CANON:
                cls = "canonical"
            elif kind == "basepair" and lab == "cWW" and (nt[i], nt[j]) in WOBBLE:
                cls = "wobble"
            elif kind == "basepair":
                cls = "noncanonical"
            else:
                cls = "stack"
            out.append(dict(rep_id=rep_id, i=i, j=j, label=lab, kind=kind, pair_class=cls,
                            nt_i=nt[i], nt_j=nt[j], crossing=f[3] if len(f) > 3 else None))
    SYMMETRY_LOG[rep_id] = symcount
    write_tsv(P("annotations/normalized", f"{rep_id}.tsv"), out,
              ["rep_id", "i", "j", "label", "kind", "pair_class", "nt_i", "nt_j", "crossing"])
    return out, interchain


def primary_replicates(comp):
    """(pair_id, direction) -> lowest-numbered replicate whose run completed (failed replicates stay in tables)."""
    ok = {}
    for r in comp:
        if r["category"] != "technical_failure_or_no_alignment":
            key = (r["pair_id"], r["direction"])
            ok[key] = min(ok.get(key, 99), int(r["replicate"]))
    return ok


SYMMETRY_LOG = {}
METHODS = ("rfam", "star3d_forward", "star3d_reverse")
COMPARISONS = {"rfam_vs_star3d_forward": ("rfam", "star3d_forward"),
               "rfam_vs_star3d_reverse": ("rfam", "star3d_reverse"),
               "all_three_methods": METHODS}


def invert_injective(mp, what):
    """Invert a residue map; a non one-to-one map is a validation failure, never silently collapsed."""
    inv = {}
    for a, b in mp.items():
        if b in inv:
            raise SystemExit(f"STAGE FAILED: {what} is not one-to-one (target {b} <- {inv[b]}, {a})")
        inv[b] = a
    return inv


def method_status(s, mp, tix, tobs, tmask):
    """Map one source interaction through one method. Returns dict with status, targets, target mask flag."""
    a, b = mp.get(s["i"]), mp.get(s["j"])
    if a is None or b is None:
        return dict(status="unmapped_endpoint", a=a, b=b, target_masked="NA")
    masked = "yes" if (a in tmask or b in tmask) else "no"
    if a not in tobs or b not in tobs:
        return dict(status="target_endpoint_unobserved", a=a, b=b, target_masked=masked)
    x, y = (a, b) if a < b else (b, a)
    lab = s["label"] if a < b else reverse_label(s["label"])   # endpoint order reversed -> edge labels swap
    labs = tix.get((x, y), set())
    st = "exact_class_preserved" if lab in labs else ("different_class" if labs else "no_annotated_target_pair")
    return dict(status=st, a=a, b=b, target_masked=masked)


def comparison_eligibility(source_masked, per_method, methods):
    """Eligibility of one source interaction for an UNMASKED comparison between `methods`.
    Requires: source endpoints unmasked; every compared method maps both endpoints; all mapped targets
    observed; no mapped target engineered-masked under ANY compared method. Returns (eligible, reason)."""
    if source_masked == "yes":
        return False, "source_endpoint_masked"
    for m in methods:
        st = per_method[m]["status"]
        if st == "unmapped_endpoint":
            return False, f"{m}_unmapped_endpoint"
        if st == "target_endpoint_unobserved":
            return False, f"{m}_target_unobserved"
    for m in methods:
        if per_method[m]["target_masked"] == "yes":
            return False, f"{m}_target_masked"
    return True, "eligible"


def main(only):
    if only:
        raise SystemExit("subset runs would overwrite the complete global tables; run without arguments")
    reps = {r["rep_id"]: r for r in read_tsv(P("results/selected_representatives.tsv"))}
    pairs = read_tsv(P("results/selected_pairs.tsv"))
    cw = defaultdict(dict)
    for r in read_tsv(P("results/residue_crosswalk.tsv")):
        cw[r["rep_id"]][int(r["row_index1"])] = r
    comp_all = read_tsv(P("results/correspondence_comparison.tsv"))
    prim = primary_replicates(comp_all)
    comp = [r for r in comp_all if prim.get((r["pair_id"], r["direction"])) == int(r["replicate"])]
    ann, interch = {}, {}
    rows, summ = [], []
    for p in pairs:
        for rid in (p["query_rep"], p["target_rep"]):
            if rid not in ann:
                ann[rid], interch[rid] = normalized(rid, reps[rid], cw[rid])
        fwd = {int(r["source_row_index"]): r for r in comp if r["pair_id"] == p["pair_id"] and r["direction"] == "forward"}
        rev = {int(r["source_row_index"]): r for r in comp if r["pair_id"] == p["pair_id"] and r["direction"] == "reverse"}
        maps = {
            "rfam": {i: int(r["rfam_partner"]) for i, r in fwd.items() if r["rfam_partner"] != "NA"},
            "star3d_forward": {i: int(r["star3d_partner"]) for i, r in fwd.items() if r["star3d_partner"] != "NA"},
            "star3d_reverse": {i: int(r["star3d_partner"]) for i, r in rev.items() if r["star3d_partner"] != "NA"},
        }
        for src_side in ("query", "target"):
            src = p["query_rep"] if src_side == "query" else p["target_rep"]
            tgt = p["target_rep"] if src_side == "query" else p["query_rep"]
            m = maps if src_side == "query" else {k: invert_injective(v, f"{p['pair_id']} {k}") for k, v in maps.items()}
            tix = defaultdict(set)
            for t in ann[tgt]:
                tix[(t["i"], t["j"])].add(t["label"])
            tobs = {k for k, r in cw[tgt].items() if r["observed"] == "yes"}
            tmask = {k for k, r in cw[tgt].items() if r["engineered_masked"] == "yes"}
            smask = {k for k, r in cw[src].items() if r["engineered_masked"] == "yes"}
            sel = []
            for s in ann[src]:
                per = {meth: method_status(s, m[meth], tix, tobs, tmask) for meth in METHODS}
                smasked = "yes" if (s["i"] in smask or s["j"] in smask) else "no"
                row = dict(pair_id=p["pair_id"], source_side=src_side, source_rep=src, target_rep=tgt,
                           i=s["i"], j=s["j"], label=s["label"], pair_class=s["pair_class"], kind=s["kind"],
                           source_masked=smasked)
                for meth in METHODS:
                    row[f"{meth}_status"] = per[meth]["status"]
                    row[f"{meth}_target"] = f"{per[meth]['a']}-{per[meth]['b']}"
                    row[f"{meth}_target_masked"] = per[meth]["target_masked"]
                for cname, meths in COMPARISONS.items():
                    ok, why = comparison_eligibility(smasked, per, meths)
                    row[f"eligible_{cname}"] = "yes" if ok else "no"
                    row[f"exclusion_{cname}"] = None if ok else why
                row.update(reference_source="Rfam.seed.gz", rfam_release=CFG["reference"]["rfam_release"])
                rows.append(row)
                sel.append(row)
            for cls in ("all", "canonical", "wobble", "noncanonical", "stack"):
                ss = [r for r in sel if cls == "all" or r["pair_class"] == cls]
                cov = {meth: sum(r[f"{meth}_status"] not in ("unmapped_endpoint", "target_endpoint_unobserved") for r in ss)
                       for meth in METHODS}
                pres = {meth: sum(r[f"{meth}_status"] == "exact_class_preserved" for r in ss) for meth in METHODS}
                for cname, meths in COMPARISONS.items():
                    el = [r for r in ss if r[f"eligible_{cname}"] == "yes"]
                    rec = dict(pair_id=p["pair_id"], source_side=src_side, interaction_class=cls, comparison=cname,
                               source_interactions=len(ss), eligible_unmasked=len(el),
                               interchain_lines_excluded=interch[src])
                    for meth in METHODS:
                        rec[f"{meth}_coverage_all"] = cov[meth]
                        rec[f"{meth}_preserved_all"] = pres[meth]
                        rec[f"{meth}_preserved_eligible"] = (sum(r[f"{meth}_status"] == "exact_class_preserved" for r in el)
                                                             if meth in meths else None)
                    summ.append(rec)
    write_tsv(P("annotations/normalized/_symmetry_lines_excluded.tsv"),
              [dict(rep_id=k, **v) for k, v in sorted(SYMMETRY_LOG.items())], ["rep_id", "copy_duplicate", "inter_copy"])
    fields = list(rows[0].keys())
    write_tsv(P("results/interaction_comparison.tsv"), rows, fields)
    write_tsv(P("results/interaction_summary.tsv"), summ, list(summ[0].keys()))
    for s in summ:
        if s["interaction_class"] == "all" and s["source_side"] == "query":
            print(s["pair_id"], s["comparison"], "n", s["source_interactions"], "eligible", s["eligible_unmasked"],
                  "rfam", s["rfam_preserved_eligible"], "fwd", s["star3d_forward_preserved_eligible"],
                  "rev", s["star3d_reverse_preserved_eligible"])


if __name__ == "__main__":
    if sys.argv[1:] == ["--backfill-sidecars"]:
        backfill_sidecars()
    elif sys.argv[1:2] == ["--verify-regenerate"]:
        verify_regenerate(sys.argv[2] if len(sys.argv) > 2 else P("annotations", "fr3d_verify_regenerate.tsv"))
    else:
        main(sys.argv[1:])
