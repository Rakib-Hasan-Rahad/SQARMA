"""Figure: per-residue distance from a source residue to its standard-seed partner vs its STAR3D partner
after a method-neutral fit (only residues both methods agree on). Reads results/neutral_fit_<pair>_<range>.tsv.
Usage: plot_neutral_fit.py <tsv> <out.png> "<title>"
Colors: reference categorical slots 1 (blue) and 2 (orange); shapes + direct labels give non-color identity.
"""
import csv
import sys

import matplotlib

matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

SURFACE, INK, INK2, GRID = "#fcfcfb", "#0b0b0b", "#52514e", "#e4e3df"
SEED, S3D = "#2a78d6", "#eb6834"


def main(tsv, out, title):
    lines = [l for l in open(tsv) if not l.startswith("#")]
    fit = next((l for l in open(tsv) if l.startswith("#")), "").strip("# \n")
    rows = list(csv.DictReader(lines, delimiter="\t"))
    x = [int(r["source_row_index"]) for r in rows]
    lab = [f"{r['source_nt']}{r['source_row_index']}" for r in rows]
    val = lambda r, k: float(r[k]) if r[k] not in ("NA", "") else None  # noqa: E731
    seed = [val(r, "rfam_C1p_dist") for r in rows]
    s3d = [val(r, "star3d_C1p_dist") for r in rows]
    fig, ax = plt.subplots(figsize=(8.5, 4.2), dpi=200)
    fig.patch.set_facecolor(SURFACE)
    ax.set_facecolor(SURFACE)
    for xs, ys, c, m, name in ((x, seed, SEED, "o", "standard-seed partner"), (x, s3d, S3D, "s", "STAR3D partner")):
        pts = [(a, b) for a, b in zip(xs, ys) if b is not None]
        ys_nan = [b if b is not None else float("nan") for b in ys]   # break the line where no partner exists
        ax.plot(xs, ys_nan, color=c, lw=2, marker=m, ms=8,
                markeredgecolor=SURFACE, markeredgewidth=2, label=name, zorder=3)
        ax.annotate(name, xy=pts[-1], xytext=(8, 0), textcoords="offset points", color=INK2, fontsize=9, va="center")
    ax.set_xticks(x)
    ax.set_xticklabels(lab, fontsize=8, color=INK2)
    ax.set_ylabel("C1' distance after neutral fit (Å)", color=INK2, fontsize=9)
    ax.set_xlabel("source residue (row index = author number)", color=INK2, fontsize=9)
    ax.set_ylim(bottom=0)
    ax.grid(axis="y", color=GRID, lw=0.8)
    for s in ("top", "right"):
        ax.spines[s].set_visible(False)
    for s in ("left", "bottom"):
        ax.spines[s].set_color(GRID)
    ax.tick_params(colors=INK2, labelsize=8)
    ax.legend(frameon=False, fontsize=8, loc="lower left", bbox_to_anchor=(0, 1.0), ncol=2, labelcolor=INK2)
    fig.suptitle(title, fontsize=10, color=INK, x=0.01, ha="left")
    import re as _re
    m = _re.search(r"C1' of (\d+) agreed.*fit RMSD ([\d.]+)", fit)
    foot = (f"Method-neutral fit: C1' atoms of {m.group(1)} residue pairs on which both methods agree "
            f"(RMSD {m.group(2)} Å); anchor list in {tsv.split('/')[-1]}") if m else fit[:150]
    fig.text(0.01, 0.01, foot, fontsize=6.5, color=INK2)
    fig.tight_layout(rect=(0, 0.04, 0.93, 0.95))
    fig.savefig(out, facecolor=SURFACE)


if __name__ == "__main__":
    main(*sys.argv[1:4])
