"""v4 provenance survey (auxiliary; never changes the primary 15.1 baseline). For Rfam releases 14.0-15.1:
  - per pilot family: record sha256 (raw bytes), row count, presence of the pilot rows, GR structure features;
  - RF00522: aligned strings of the 3FU2/6VUI/7REX rows and the 6VUI->7REX residue correspondence at P1;
  - releases with Rfam.3d.seed.gz: curated record vs ordinary record byte identity.
Only documented facts are reported; no inference about how a row was created.
Outputs: results/rfam_history/{release_family_records.tsv, rf00522_rows.tsv, curated_vs_ordinary.tsv}"""
import csv
import gzip
import hashlib
import os
import re
import sys

sys.path.insert(0, os.path.dirname(__file__))
import stockholm  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
OUT = P("results", "rfam_history")
FAMS = {"RF00059", "RF00162", "RF00174", "RF00442", "RF00522"}
ROWS = {"3FU2": "URS000080E020_32630/1-34", "6VUI": "URS000080E32E_119072/1-33", "7REX": "URS00023119CB_2126436/1-34"}


def records(path):
    out, cur = {}, []
    for b in gzip.open(path, "rb"):
        cur.append(b)
        if b.startswith(b"//"):
            t = b"".join(cur)
            m = re.search(rb"#=GF AC\s+(\S+)", t)
            out[m.group(1).decode()] = t
            cur = []
    return out


def corr(a, b):
    out, ia, ib = {}, 0, 0
    for x, y in zip(a, b):
        ra, rb = x not in "-.", y not in "-."
        ia += ra
        ib += rb
        if ra and rb:
            out[ia] = ib
    return out


def main():
    os.makedirs(OUT, exist_ok=True)
    rel = sorted({d for d in os.listdir(P("inputs/rfam_history")) if re.match(r"^\d+\.\d+$", d)},
                 key=lambda v: tuple(map(int, v.split("."))))
    paths = {v: P("inputs/rfam_history", v, "Rfam.seed.gz") for v in rel}
    paths["15.1"] = P("inputs/rfam/15.1/Rfam.seed.gz")
    cur3d = {v: P("inputs/rfam_history", v, "Rfam.3d.seed.gz") for v in rel
             if os.path.exists(P("inputs/rfam_history", v, "Rfam.3d.seed.gz"))}
    cur3d["15.1"] = P("inputs/rfam_survey_b/Rfam.3d.seed.gz")
    fam_rows, rf522, cvo = [], [], []
    for v in list(rel) + ["15.1"]:
        recs = records(paths[v])
        for f in sorted(FAMS):
            t = recs.get(f)
            if t is None:
                fam_rows.append(dict(release=v, family=f, present=False))
                continue
            tmp = os.path.join(OUT, "_tmp.sto")
            open(tmp, "wb").write(t)
            a = next(stockholm.parse(tmp))
            os.remove(tmp)
            gr = sorted({k for d in a.gr.values() for k in d if k.endswith("_SS")})
            fam_rows.append(dict(release=v, family=f, present=True, record_sha256=hashlib.sha256(t).hexdigest()[:16],
                                 rows=len(a.seqs), width=a.width, n_gr_structure_features=len(gr),
                                 sscons_sha256=hashlib.sha256(a.gc.get("SS_cons", "").encode()).hexdigest()[:12]))
            if f == "RF00522":
                s = {k: a.seqs.get(n) for k, n in ROWS.items()}
                c = corr(s["6VUI"], s["7REX"]) if s["6VUI"] and s["7REX"] else {}
                rf522.append(dict(release=v, rows=len(a.seqs),
                                  **{f"{k}_row_present": s[k] is not None for k in ROWS},
                                  rex_aligned=s["7REX"] or "NA",
                                  rex_gr_features=";".join(a.gr.get(ROWS["7REX"], {})) or "none",
                                  p1_6vui_16_to_7rex=c.get(16, "NA"), p1_6vui_20_to_7rex=c.get(20, "NA"),
                                  l1_6vui_11_to_7rex=c.get(11, "NA")))
        if v in cur3d:
            c3 = records(cur3d[v])
            same = sum(1 for k, t in c3.items() if recs.get(k) == t)
            cvo.append(dict(release=v, curated_families=len(c3), in_ordinary=sum(k in recs for k in c3),
                            byte_identical_records=same, ordinary_families=len(recs),
                            pilot_families_in_curated=";".join(sorted(FAMS & set(c3)))))
    for name, rows in (("release_family_records.tsv", fam_rows), ("rf00522_rows.tsv", rf522),
                       ("curated_vs_ordinary.tsv", cvo)):
        fields = list(dict.fromkeys(k for r in rows for k in r))
        with open(os.path.join(OUT, name), "w", newline="") as fo:
            w = csv.DictWriter(fo, fieldnames=fields, delimiter="\t", lineterminator="\n", restval="NA")
            w.writeheader()
            w.writerows(rows)
    for r in rf522:
        print(r)
    for r in cvo:
        print(r)


if __name__ == "__main__":
    main()
