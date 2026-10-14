"""Redraw Fig. 1 (enrollment) and Fig. 2 (verification) as high-resolution figures."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from matplotlib.patches import FancyBboxPatch, Polygon  # noqa: E402

DST = os.path.join(os.path.dirname(os.path.abspath(__file__)), "paper_assets")
INK, FILL, ACC = "#1f1f1e", "#f4f3ef", "#2a78d6"
plt.rcParams.update({"font.family": "DejaVu Sans", "font.size": 10, "pdf.fonttype": 42})


def box(ax, x, y, w, h, text, fill=FILL, bold=False, ec=INK):
    ax.add_patch(FancyBboxPatch((x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.08",
                                fc=fill, ec=ec, lw=1.2))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center", fontsize=9.5,
            fontweight="bold" if bold else "normal", color=INK, linespacing=1.25)


def arrow(ax, x0, y0, x1, y1):
    ax.annotate("", xy=(x1, y1), xytext=(x0, y0),
                arrowprops=dict(arrowstyle="-|>", color=INK, lw=1.2, shrinkA=0, shrinkB=0, mutation_scale=12))


def save(fig, name):
    fig.savefig(os.path.join(DST, name + ".pdf"), bbox_inches="tight")
    fig.savefig(os.path.join(DST, name + ".png"), dpi=600, bbox_inches="tight")
    plt.close(fig)


def fig1():
    fig, ax = plt.subplots(figsize=(10, 3.6))
    ax.set_xlim(0, 10.2); ax.set_ylim(0, 3.6); ax.axis("off")
    ys = [2.85, 2.15, 1.45, 0.35]
    labels = ["Recording 1", "Recording 2", "Recording 3", "Recording 10"]
    for y, l in zip(ys, labels):
        box(ax, 0.05, y, 1.35, 0.5, l)
        arrow(ax, 1.4, y + 0.25, 1.95, y + 0.25)
    ax.text(0.72, 1.05, "⋮", ha="center", va="center", fontsize=16, color=INK)
    ax.add_patch(FancyBboxPatch((1.95, 0.2), 4.1, 3.25, boxstyle="round,pad=0.02,rounding_size=0.1",
                                fc="white", ec=INK, lw=1.2, ls="--"))
    ax.text(4.0, 3.2, "Embedding extractor $f_m(\\cdot)$", ha="center", fontsize=10, fontweight="bold")
    box(ax, 2.2, 1.35, 1.65, 0.9, "Acoustic front-end\n(filterbank or\nraw waveform)")
    box(ax, 4.2, 1.35, 1.65, 0.9, "Neural network\n(TitaNet, ECAPA,\nWavLM, PyAnnote)")
    arrow(ax, 3.85, 1.8, 4.2, 1.8)
    ax.text(4.0, 0.55, "one L2-normalised embedding\nper recording", ha="center", fontsize=8.5, color="#5f5e5a")
    arrow(ax, 6.05, 1.8, 6.5, 1.8)
    box(ax, 6.5, 1.35, 1.6, 0.9, "Averaging over\n10 embeddings\n(eq. 2)")
    arrow(ax, 8.1, 1.8, 8.5, 1.8)
    box(ax, 8.5, 1.35, 1.65, 0.9, "Reference\nvoiceprint $\\mathbf{v}_u$", fill="#e1edfb", ec=ACC, bold=True)
    save(fig, "fig1_enrollment")


def fig2():
    fig, ax = plt.subplots(figsize=(10.4, 3.9))
    ax.set_xlim(0, 10.5); ax.set_ylim(0, 3.95); ax.axis("off")
    box(ax, 0.05, 2.6, 1.5, 0.75, "Test recording\n$x_{test}$")
    arrow(ax, 1.55, 2.98, 1.9, 2.98)
    box(ax, 1.9, 2.6, 2.1, 0.75, "Embedding extractor\n$f_m(\\cdot)$")
    arrow(ax, 4.0, 2.98, 4.35, 2.98)
    box(ax, 4.35, 2.6, 2.05, 0.75, "Cosine similarity\n$s(\\mathbf{v}_{test}, \\mathbf{v}_u)$, eq. (4)")
    box(ax, 1.9, 1.2, 2.1, 0.75, "Stored reference\nvoiceprint $\\mathbf{v}_u$", fill="#e1edfb", ec=ACC)
    ax.plot([4.0, 5.375], [1.58, 1.58], color=INK, lw=1.2)
    arrow(ax, 5.375, 1.58, 5.375, 2.6)
    cx = 7.75
    box(ax, cx - 0.9, 3.22, 1.8, 0.62, "Threshold τ\n(calibrated, frozen)")
    ax.plot([cx, cx], [3.22, 2.98], color=INK, lw=1.2)
    arrow(ax, 6.4, 2.98, cx, 2.98)
    ax.add_patch(Polygon([[cx, 2.98], [cx + 1.1, 2.35], [cx, 1.72], [cx - 1.1, 2.35]], closed=True, fc=FILL, ec=INK, lw=1.2))
    ax.text(cx, 2.35, "$s \\geq \\tau$ ?", ha="center", va="center", fontsize=10)
    arrow(ax, cx, 1.72, cx, 1.05)
    ax.text(cx + 0.1, 1.38, "yes", fontsize=9)
    box(ax, cx - 1.0, 0.3, 2.0, 0.75, "Accept\n(identity verified)", fill="#d8f0e5", ec="#1baf7a")
    ax.plot([cx + 1.1, 9.75], [2.35, 2.35], color=INK, lw=1.2)
    arrow(ax, 9.75, 2.35, 9.75, 1.05)
    ax.text(9.2, 2.45, "no", fontsize=9)
    box(ax, 9.1, 0.3, 1.3, 0.75, "Reject", fill="#fbe2df", ec="#e34948")
    save(fig, "fig2_verification")


if __name__ == "__main__":
    fig1(); fig2()
