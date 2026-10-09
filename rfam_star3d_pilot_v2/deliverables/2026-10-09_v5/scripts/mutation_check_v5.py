"""Re-introduce each historical defect into a scratch copy of scripts/ and confirm the regression tests FAIL.
(Demonstrates that tests detect the defective behaviour, not merely a missing function.)"""
import os
import shutil
import subprocess
import sys
import tempfile

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
PY = os.path.join(ROOT, ".venv", "bin", "python")
M = [  # (defect, file, old, new, test file)
    ("masked target ignored in eligibility", "interactions.py",
     'if per_method[m]["target_masked"] == "yes":', 'if False:', "test_interaction_masking.py"),
    ("masked source ignored", "interactions.py", 'if source_masked == "yes":', 'if False:', "test_interaction_masking.py"),
    ("one shared denominator across comparisons (unmapped method ignored)", "interactions.py",
     'if st == "unmapped_endpoint":', 'if False:', "test_interaction_masking.py"),
    ("symmetry mates counted as intrachain", "interactions.py",
     'if u1["symop"] == "1_555" and u2["symop"] == "1_555":', 'if True:', "test_interaction_masking.py"),
    ("non-injective map silently collapsed", "interactions.py",
     'raise SystemExit(f"STAGE FAILED: {what} is not one-to-one', 'print(f"{what}', "test_interaction_masking.py"),
    ("region targets not checked", "regions.py",
     'rt = [tgt_cw.get(rfam_map[k]) for k in span if k in rfam_map]', 'rt = []', "test_regions.py"),
    ("region intervening positions skipped", "regions.py",
     'src = [src_cw.get(k) for k in span]', 'src = [src_cw.get(k) for k in (span[0], span[-1])]', "test_regions.py"),
    ("old interpretations auto-accepted after eligibility change", "regions.py",
     'if exact and not changed:', 'if src:', "test_regions.py"),
    ("stored STAR3D output not re-validated", "compare.py",
     'probs = list(pa["bad_lines"])', 'return []', "test_compare_validation.py"),
    ("non-injective STAR3D output accepted", "compare.py",
     'injective = len(set(qs)) == len(qs) and len(set(ts)) == len(ts)', 'injective = True', "test_compare_validation.py"),
    ("subset rerun allowed", "compare.py",
     'raise SystemExit("subset runs would overwrite', 'print("subset runs would overwrite', "test_subset_refusal.py"),
    ("preprocessing contents not validated", "star3d.py",
     'fatal, warn = preprocessing_problems(work, sid, ch)', 'fatal, warn = [], []', "test_star3d_gate.py"),
    ("checksum mismatch does not block", "fresh_repro.py",
     'ok = rec["compressed_identical"] and rec.get("decompressed_identical", True)', 'ok = True', "test_fresh_repro_gate.py"),
    ("configured FR3D commit trusted instead of installed", "interactions.py",
     'if (pv["installed_commit"] != pinned_fr3d_commit() or', 'if (False or', "test_fr3d_provenance.py"),
    ("cached FR3D output reused without raw-hash check", "interactions.py",
     'if raw_output_check(outs) != got["raw_sha256"]:', 'if False:', "test_fr3d_provenance.py"),
    ("v5: alignment repeated (replicate loop re-introduced)", "star3d.py",
     '    rc, dur, st, so = docker(work, cmd, os.path.join(base, "logs", run_id))\n    outp',
     '    docker(work, cmd, os.path.join(base, "logs", run_id))\n    rc, dur, st, so = docker(work, cmd, os.path.join(base, "logs", run_id))\n    outp',
     "test_single_run_policy.py"),
    ("v5: reverse-run substitution in primary selection", "select_primary_outputs.py",
     'fwd = sorted([r for r in runs if r["direction"] == "forward"], key=order_key)',
     'fwd = sorted(runs, key=order_key)', "test_single_run_policy.py"),
    ("multi-family Stockholm record", "reference.py",
     'f.write("//\\n")', 'pass', "test_stockholm_export.py"),
]
rows = []
for name, fn, old, new, test in M:
    d = tempfile.mkdtemp()
    shutil.copytree(os.path.join(ROOT, "scripts"), os.path.join(d, "scripts"))
    shutil.copytree(os.path.join(ROOT, "tests"), os.path.join(d, "tests"))
    for f in ("config.yaml",):
        shutil.copy(os.path.join(ROOT, f), d)
    os.symlink(os.path.join(ROOT, "inputs"), os.path.join(d, "inputs"))
    os.symlink(os.path.join(ROOT, "results"), os.path.join(d, "results"))
    p = os.path.join(d, "scripts", fn)
    s = open(p).read()
    if old not in s:
        rows.append((name, fn, test, "MUTATION_NOT_APPLIED"))
        continue
    open(p, "w").write(s.replace(old, new, 1))
    r = subprocess.run([PY, "-m", "pytest", "-q", "-p", "no:cacheprovider", os.path.join("tests", test)],
                       cwd=d, capture_output=True, text=True)
    last = [l for l in r.stdout.splitlines() if "passed" in l or "failed" in l or "error" in l][-1:]
    rows.append((name, fn, test, "DETECTED" if r.returncode != 0 else "NOT DETECTED", last[0] if last else ""))
    shutil.rmtree(d)
print("defect_reintroduced\tfile\ttest_file\tresult\tpytest_summary")
for r in rows:
    print("\t".join(r))
