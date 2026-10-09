"""Correspondence diagram for RF00522 6VUI_A -> 7REX_A, drawn ONLY from retained tables:
residue_evidence (seed / STAR3D forward / exploratory adjusted partners) and FR3D normalized annotations (cWW arcs).
Not a 3D rendering; positions are residue indices, not coordinates."""
import csv
import os

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import Arc  # noqa: E402

ROOT = os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
P = lambda *a: os.path.join(ROOT, *a)  # noqa: E731
R = lambda p: list(csv.DictReader(open(p), delimiter="\t"))  # noqa: E731
ev = R(P("review/candidate_RF00522/residue_evidence_RF00522__6VUI_A__7REX_A.tsv"))
ann = {k: [r for r in R(P("annotations/normalized", f"RF00522__{k}_A.tsv")) if r["label"] == "cWW"] for k in ("6VUI", "7REX")}
idx = lambda v: int("".join(c for c in v if c.isdigit())) if any(c.isdigit() for c in v) else None  # noqa: E731
nt_t = {}
for e in ev:
    for col in ("rfam_partner", "star3d_fwd_partner"):
        if idx(e[col]):
            nt_t[idx(e[col])] = e[col][0]
LO, HI = 1, 24
fig, axes = plt.subplots(3, 1, figsize=(12, 8.4), sharex=True)
COL = {"seed": "#B5179E", "star3d": "#0B6E4F", "adjusted": "#3A0CA3"}
for ax, (key, col, title) in zip(axes, [("seed", "rfam_partner", "Ordinary Rfam seed (15.1) correspondence"),
                                        ("star3d", "star3d_fwd_partner", "Original STAR3D v1.2 (forward, replicate 1)"),
                                        ("adjusted", "adjusted_partner", "EXPLORATORY adjusted 7REX row (designed on these data)")]):
    yq, yt = 1.0, 0.0
    for e in ev:
        i = int(e["source_row_index"])
        j = idx(e[col])
        if i > HI:
            continue
        ax.text(i, yq + 0.12, e["source_nt"], ha="center", va="bottom", fontsize=9)
        if j and LO <= j <= HI + 1:
            same = idx(e["rfam_partner"]) == idx(e["star3d_fwd_partner"])
            ax.plot([i, j], [yq, yt], color=COL[key] if not same else "#9A9A9A", lw=2.0 if not same else 0.8,
                    ls="-" if not same else ":")
    for j in range(LO, HI + 2):
        ax.text(j, yt - 0.12, nt_t.get(j, ""), ha="center", va="top", fontsize=9)
    for nm, y, up in (("6VUI", yq, True), ("7REX", yt, False)):
        for a in ann[nm]:
            i, j = int(a["i"]), int(a["j"])
            if j <= HI + 1:
                c, w = (i + j) / 2, j - i
                h = min(0.07 * w, 1.1)
                ax.add_patch(Arc((c, y + (0.3 if up else -0.3)), w, h, theta1=0 if up else 180,
                                 theta2=180 if up else 360, color="#555555", lw=0.8))
    ax.text(0.2, yq, "6VUI", ha="right", va="center", fontsize=9, weight="bold")
    ax.text(0.2, yt, "7REX", ha="right", va="center", fontsize=9, weight="bold")
    ax.set_title(title, fontsize=10, loc="left")
    ax.set_ylim(-0.95, 1.95)
    ax.set_yticks([])
    for s in ("left", "right", "top"):
        ax.spines[s].set_visible(False)
axes[-1].set_xticks(range(1, HI + 2))
axes[-1].set_xlabel("Residue index (author numbering = row index for both chains)")
fig.text(0.01, 0.005, "Coloured solid lines: positions where seed and STAR3D partners differ; grey dotted: both methods agree. "
         "Grey arcs: FR3D cWW annotations\nin each structure (6VUI above, 7REX below). Data: "
         "review/candidate_RF00522/residue_evidence_RF00522__6VUI_A__7REX_A.tsv; annotations/normalized/.", fontsize=7.5)
fig.tight_layout(rect=(0, 0.05, 1, 1))
out = P("deliverables/2026-10-09/figures/fig_7REX_correspondence_6VUI.png")
os.makedirs(os.path.dirname(out), exist_ok=True)
fig.savefig(out, dpi=150)
print(out)
