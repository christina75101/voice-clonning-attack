"""Build manuscript-ready tables (Markdown + HTML for pasting into Word) and figures (PDF + 600-dpi PNG).

Run after evaluate.py has been run for every condition.
Usage: .venv/bin/python evaluation/make_paper_assets.py
"""
import os
import sys
import json

import numpy as np
import pandas as pd
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402
from scipy.stats import norm  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT, SYNTHS, SYNTH_LABEL  # noqa: E402
from evaluate import roc  # noqa: E402

RES = os.path.join(OUT, "results")
DST = os.path.join(OUT, "paper_assets")
os.makedirs(DST, exist_ok=True)

# Paper column order and names
MODELS = ["pyannote", "wavlm-base-sv", "wavlm-base-plus-sv", "titanet", "ecapa"]
ML = {"pyannote": "PyAnnote", "wavlm-base-sv": "WavLM-base-sv", "wavlm-base-plus-sv": "WavLM-base-plus-sv",
      "titanet": "TitaNet", "ecapa": "ECAPA-TDNN"}
CONDS = ["clean", "noise20", "noise10", "g711"]
CL = {"clean": "Clean", "noise20": "White noise 20 dB", "noise10": "White noise 10 dB", "g711": "G.711 (8 kHz μ-law)"}
SL = SYNTH_LABEL

# Categorical palette (validated default, light mode), fixed order
PAL = ["#2a78d6", "#eb6834", "#1baf7a", "#eda100", "#e87ba4", "#008300"]
MCOL = dict(zip(MODELS, PAL))
SCOL = dict(zip(SYNTHS, PAL[:4]))
INK, MUTED, GRID = "#1f1f1e", "#5f5e5a", "#d9d8d2"

plt.rcParams.update({
    "font.family": "DejaVu Sans", "font.size": 10, "axes.titlesize": 11, "axes.labelsize": 10,
    "xtick.labelsize": 9, "ytick.labelsize": 9, "legend.fontsize": 9,
    "axes.edgecolor": MUTED, "axes.labelcolor": INK, "xtick.color": MUTED, "ytick.color": MUTED,
    "text.color": INK, "axes.spines.top": False, "axes.spines.right": False,
    "axes.grid": True, "grid.color": GRID, "grid.linewidth": 0.6, "axes.axisbelow": True,
    "pdf.fonttype": 42, "savefig.bbox": "tight",
})


def rd(cond, name):
    return pd.read_csv(os.path.join(RES, cond, name))


def pct(x, d=1):
    return f"{100 * x:.{d}f}"


def ci(x, lo, hi):
    return f"{100 * x:.1f} [{100 * lo:.1f}–{100 * hi:.1f}]"


tables = []   # (title, note, DataFrame)


def add(title, df, note=""):
    tables.append((title, note, df))


# ---------------------------------------------------------------- tables
cal = rd("clean", "calibration.csv").set_index("model")
add("Table 2. Calibration stage (all pairs of the 200 enrollment recordings: 900 target / 19,000 non-target)",
    pd.DataFrame({"Model": [ML[m] for m in MODELS],
                  "EER, %": [pct(cal.loc[m, "cal_eer"], 2) for m in MODELS],
                  "minDCF (P_tar=0.01)": [f"{cal.loc[m, 'cal_min_dcf_01']:.3f}" for m in MODELS],
                  "minDCF (P_tar=0.05)": [f"{cal.loc[m, 'cal_min_dcf_05']:.3f}" for m in MODELS],
                  "τ (cosine similarity)": [f"{cal.loc[m, 'tau']:.3f}" for m in MODELS]}),
    "τ is the EER threshold of the calibration set; it is frozen for all later experiments.")

bf = rd("clean", "bona_fide.csv").set_index("model")
add("Table 4. Testing stage, bona fide trials (400 target / 7,600 zero-effort impostor)",
    pd.DataFrame({"Model": [ML[m] for m in MODELS],
                  "EER, %": [pct(bf.loc[m, "EER"], 2) for m in MODELS],
                  "minDCF (0.01)": [f"{bf.loc[m, 'minDCF_001']:.3f}" for m in MODELS],
                  "minDCF (0.05)": [f"{bf.loc[m, 'minDCF_005']:.3f}" for m in MODELS],
                  "FAR at τ, %": [pct(bf.loc[m, "FAR"], 2) for m in MODELS],
                  "FRR at τ, %": [pct(bf.loc[m, "FRR"], 2) for m in MODELS],
                  "HTER at τ, %": [pct(bf.loc[m, "HTER"], 2) for m in MODELS]}),
    "EER and minDCF are threshold-free; FAR/FRR/HTER use the frozen calibration threshold τ.")

att = rd("clean", "attacks.csv")
for content, tno in [("identical", 7), ("varied", 8)]:
    a = att[att.content == content].set_index(["synth", "model"])
    df = pd.DataFrame({"Cloning tool": [SL[s] for s in SYNTHS]})
    for m in MODELS:
        df[ML[m]] = [ci(a.loc[(s, m), "IAPMR_EER"], a.loc[(s, m), "boot_lo"], a.loc[(s, m), "boot_hi"]) for s in SYNTHS]
    add(f"Table {tno}. Attack success rate (IAPMR, %) with {content} linguistic content, threshold τ; "
        f"95% CI from speaker-level bootstrap (2,000 resamples). n = 400 attacks per cell", df,
        "For reference, genuine acceptance at τ: " + ", ".join(f"{ML[m]} {pct(att[att.model == m].GAR.iloc[0])}%" for m in MODELS) + ".")

a = att[att.content == "all"].set_index(["synth", "model"])
rows = []
for op, opl in [("EER", "τ (EER)"), ("FAR1", "FAR = 1%"), ("FAR01", "FAR = 0.1%")]:
    for m in MODELS:
        r = {"Operating point": opl, "Model": ML[m], "FRR (genuine), %": pct(a.loc[(SYNTHS[0], m), f"FRR_{op}"])}
        for s in SYNTHS:
            r[f"IAPMR {SL[s]}, %"] = pct(a.loc[(s, m), f"IAPMR_{op}"])
        rows.append(r)
add("Table 9. Attack success (IAPMR) and genuine rejection (FRR) at three operating points (identical + varied content, 800 attacks per tool)",
    pd.DataFrame(rows), "FAR = 1% and 0.1% thresholds are set on the 7,600 zero-effort impostor trials.")

df = pd.DataFrame({"Model": [ML[m] for m in MODELS]})
for s in SYNTHS:
    df[SL[s]] = [pct(a.loc[(s, m), "SPF_EER"]) for m in MODELS]
add("Table 10. Spoof-EER (%), genuine target trials vs. cloned attacks, threshold-free", df,
    "50% = clones indistinguishable from genuine speech; 0% = perfect separation.")

ce = rd("clean", "content_effect.csv")
p = ce["p_rate"].to_numpy()
order = np.argsort(p)
adj = np.minimum(1, np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order]))
ce.loc[ce.index[order], "p_holm"] = adj
ce = ce.set_index(["synth", "model"])
rows = []
for s in SYNTHS:
    for m in MODELS:
        r = ce.loc[(s, m)]
        rows.append({"Cloning tool": SL[s], "Model": ML[m], "Identical, %": pct(r.iapmr_identical),
                     "Varied, %": pct(r.iapmr_varied), "Δ (identical − varied), pp": f"{r.delta_pp:+.2f}",
                     "p (Wilcoxon)": f"{r.p_rate:.3f}", "p (Holm)": f"{r.p_holm:.3f}"})
add("Table 11. Effect of linguistic content (speaker-level paired Wilcoxon signed-rank test, 20 speakers; Holm correction over 20 tests)",
    pd.DataFrame(rows))

cm = pd.concat([rd(c, "aasist.csv") for c in CONDS])
cm = cm[cm.content == "all"].set_index(["condition", "synth"])
rows = []
for c in CONDS:
    r = {"Condition": CL[c]}
    for s in SYNTHS:
        r[f"{SL[s]} CM-EER / APCER, %"] = f"{pct(cm.loc[(c, s), 'CM_EER'])} / {pct(cm.loc[(c, s), 'APCER'])}"
    rows.append(r)
add("Table 12. AASIST countermeasure (ASVspoof 2019 LA weights): CM-EER and APCER at BPCER = 5%", pd.DataFrame(rows),
    "The CM threshold is set on bona fide test audio only (5% of genuine recordings rejected).")

sv = rd("clean", "sv_plus_aasist.csv").set_index(["model", "synth"])
rows = []
for m in MODELS:
    r = {"Model": ML[m], "FRR SV → SV+CM, %": f"{pct(sv.loc[(m, SYNTHS[0]), 'FRR_sv'])} → {pct(sv.loc[(m, SYNTHS[0]), 'FRR_sv_cm'])}"}
    for s in SYNTHS:
        r[f"IAPMR {SL[s]}: SV → SV+CM, %"] = f"{pct(sv.loc[(m, s), 'IAPMR_sv'])} → {pct(sv.loc[(m, s), 'IAPMR_sv_cm'])}"
    rows.append(r)
add("Table 13. Cascaded system: speaker verification (threshold τ) followed by AASIST (BPCER = 5%), clean condition",
    pd.DataFrame(rows))

bfc = pd.concat([rd(c, "bona_fide.csv") for c in CONDS]).set_index(["model", "condition"])
atc = pd.concat([rd(c, "attacks.csv") for c in CONDS])
atc = atc[atc.content == "all"].set_index(["model", "synth", "condition"])
rows = []
for m in MODELS:
    r = {"Model": ML[m], "Metric": "Bona fide EER / FRR at τ, %"}
    for c in CONDS:
        r[CL[c]] = f"{pct(bfc.loc[(m, c), 'EER'])} / {pct(bfc.loc[(m, c), 'FRR'])}"
    rows.append(r)
    for s in SYNTHS:
        r = {"Model": "", "Metric": f"IAPMR {SL[s]}, %"}
        for c in CONDS:
            r[CL[c]] = pct(atc.loc[(m, s, c), "IAPMR_EER"])
        rows.append(r)
add("Table 14. Degraded acoustic conditions (applied to test and attack audio; enrollment and τ from clean audio)",
    pd.DataFrame(rows))

params = json.load(open(os.path.join(RES, "params.json")))
tm = rd("clean", "timing.csv").set_index("model")
z = pd.read_csv(os.path.join(RES, "clean", "aasist_scores.csv.gz"))
rows = [{"Model": ML[m], "Parameters, M": f"{params[m] / 1e6:.1f}",
         "Time per recording, ms (mean ± sd)": f"{tm.loc[m, 'ms_per_file']:.0f} ± {tm.loc[m, 'ms_std']:.0f}",
         "Real-time factor": f"{tm.loc[m, 'rtf']:.4f}"} for m in MODELS]
rows.append({"Model": "AASIST (CM)", "Parameters, M": f"{params['aasist'] / 1e6:.2f}",
             "Time per recording, ms (mean ± sd)": f"{1000 * z['seconds'].mean():.0f} ± {1000 * z['seconds'].std(ddof=0):.0f}",
             "Real-time factor": f"{(z['seconds'] / z['audio_seconds']).mean():.4f}"})
add("Table 15. Computational cost (CPU inference, Apple M4 Pro, 14 cores; mean recording length 8.0 s)", pd.DataFrame(rows),
    "Embedding extraction only; cosine scoring against a stored voiceprint adds < 0.1 ms. Parameter counts include the models' classification heads where present.")

g = rd("clean", "gender.csv").set_index("model")
a = att[att.content == "all"]
rows = []
for m in MODELS:
    t = pd.read_csv(os.path.join(RES, "clean", "per_speaker_iapmr.csv"), index_col=[0, 1]).loc[m]
    per = t.mean(axis=0)   # per speaker, averaged over tools
    rows.append({"Model": ML[m], "IAPMR male, %": pct(g.loc[m, "iapmr_male"]), "IAPMR female, %": pct(g.loc[m, "iapmr_female"]),
                 "p (Mann–Whitney, speakers)": f"{g.loc[m, 'p_mannwhitney']:.3f}",
                 "Per-speaker IAPMR, mean ± sd, %": f"{100 * per.mean():.1f} ± {100 * per.std():.1f}",
                 "Min–max, %": f"{100 * per.min():.1f}–{100 * per.max():.1f}"})
add("Table 16. Gender-disaggregated and per-speaker attack success (all tools, both content conditions, clean)", pd.DataFrame(rows))


def write_tables():
    md, html = [], ["<html><head><meta charset='utf-8'><style>"
                    "body{font-family:'Times New Roman',serif;font-size:10pt}"
                    "table{border-collapse:collapse;margin-bottom:6pt}"
                    "td,th{border-top:1px solid #000;border-bottom:1px solid #000;padding:2px 6px;text-align:center}"
                    "p.t{font-weight:bold;margin-top:18pt}p.n{font-size:9pt}</style></head><body>"]
    for title, note, df in tables:
        md.append(f"**{title}**\n\n" + df.to_markdown(index=False) + (f"\n\n*{note}*" if note else "") + "\n")
        html.append(f"<p class='t'>{title}</p>" + df.to_html(index=False, border=0, escape=True)
                    + (f"<p class='n'>{note}</p>" if note else ""))
    html.append("</body></html>")
    open(os.path.join(DST, "tables.md"), "w").write("\n".join(md))
    open(os.path.join(DST, "tables.html"), "w").write("\n".join(html))


# ---------------------------------------------------------------- figures

def save(fig, name):
    fig.savefig(os.path.join(DST, name + ".pdf"))
    fig.savefig(os.path.join(DST, name + ".png"), dpi=600)
    plt.close(fig)


def fig_iapmr():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4), sharey=True)
    w = 0.16
    for ax, content in zip(axes, ["identical", "varied"]):
        d = att[att.content == content].set_index(["synth", "model"])
        for k, m in enumerate(MODELS):
            x = np.arange(len(SYNTHS)) + (k - 2) * (w + 0.01)
            y = np.array([100 * d.loc[(s, m), "IAPMR_EER"] for s in SYNTHS])
            lo = np.array([100 * d.loc[(s, m), "boot_lo"] for s in SYNTHS])
            hi = np.array([100 * d.loc[(s, m), "boot_hi"] for s in SYNTHS])
            ax.bar(x, y, w, color=MCOL[m], label=ML[m], edgecolor="white", linewidth=0.8)
            ax.errorbar(x, y, yerr=[y - lo, hi - y], fmt="none", ecolor=INK, elinewidth=0.8, capsize=2)
        ax.set_xticks(np.arange(len(SYNTHS)))
        ax.set_xticklabels([SL[s] for s in SYNTHS])
        ax.set_title(f"{content.capitalize()} linguistic content")
        ax.set_ylim(0, 105)
        ax.grid(axis="x", visible=False)
    axes[0].set_ylabel("Attack success rate, IAPMR (%)")
    axes[0].legend(ncol=5, loc="upper left", bbox_to_anchor=(0, 1.22), frameon=False)
    save(fig, "fig3_iapmr_by_tool")


def fig_det():
    t = pd.read_csv(os.path.join(RES, "clean", "trials.csv.gz"))
    ticks = np.array([0.001, 0.01, 0.05, 0.2, 0.5, 0.8])
    fig, axes = plt.subplots(2, 3, figsize=(11, 7.2), sharex=True, sharey=True)
    styles = ["--", "-.", ":", (0, (5, 1, 1, 1))]
    for ax, m in zip(axes.flat, MODELS):
        g = t[t.model == m]
        tar = g[g.trial == "target"].score.to_numpy()
        curves = [("Zero-effort impostor", g[g.trial == "nontarget"].score.to_numpy(), INK, "-")]
        curves += [(SL[s], g[(g.trial == "spoof") & (g.synth == s)].score.to_numpy(), SCOL[s], st) for s, st in zip(SYNTHS, styles)]
        for label, non, col, ls in curves:
            _, far, frr = roc(tar, non)
            ax.plot(norm.ppf(np.clip(far, 5e-4, 1 - 5e-4)), norm.ppf(np.clip(frr, 5e-4, 1 - 5e-4)),
                    color=col, ls=ls, lw=2, label=label)
        ax.set_title(ML[m])
        ax.set_xticks(norm.ppf(ticks)); ax.set_xticklabels([f"{100 * x:g}" for x in ticks])
        ax.set_yticks(norm.ppf(ticks)); ax.set_yticklabels([f"{100 * x:g}" for x in ticks])
        ax.set_xlim(norm.ppf(5e-4), norm.ppf(0.95)); ax.set_ylim(norm.ppf(5e-4), norm.ppf(0.95))
    for ax in axes[-1]:
        ax.set_xlabel("FAR / IAPMR (%)")
    for ax in axes[:, 0]:
        ax.set_ylabel("FRR (%)")
    leg = axes.flat[-1]
    leg.axis("off")
    h, l = axes.flat[0].get_legend_handles_labels()
    leg.legend(h, l, loc="center", frameon=False, title="Non-target / attack trials", fontsize=10)
    save(fig, "fig_det_curves")


def fig_tradeoff():
    a = att[att.content == "all"]
    fig, ax = plt.subplots(figsize=(6.2, 4.6))
    marks = {"EER": "o", "FAR1": "s", "FAR01": "^"}
    for m in MODELS:
        g = a[a.model == m]
        xs = [100 * g[f"FRR_{op}"].iloc[0] for op in marks]
        ys = [100 * g[f"IAPMR_{op}"].mean() for op in marks]
        ax.plot(xs, ys, color=MCOL[m], lw=2, label=ML[m])
        for (op, mk), x, y in zip(marks.items(), xs, ys):
            ax.plot(x, y, mk, color=MCOL[m], ms=8, mec="white", mew=1.5)
    for op, mk, lab in [("EER", "o", "τ (EER)"), ("FAR1", "s", "FAR = 1%"), ("FAR01", "^", "FAR = 0.1%")]:
        ax.plot([], [], mk, color=MUTED, ms=8, label=lab)
    ax.set_xlabel("Genuine users rejected, FRR (%)")
    ax.set_ylabel("Attacks accepted, IAPMR (%), mean of 4 tools")
    ax.set_xscale("log"); ax.set_xlim(0.5, 60); ax.set_ylim(0, 102)
    ax.set_xticks([0.5, 1, 2, 5, 10, 20, 50]); ax.set_xticklabels(["0.5", "1", "2", "5", "10", "20", "50"])
    ax.legend(frameon=False, fontsize=8.5, loc="lower left")
    save(fig, "fig_security_usability_tradeoff")


def fig_conditions():
    fig, axes = plt.subplots(1, 2, figsize=(11, 4))
    x = np.arange(len(CONDS))
    for m in MODELS:
        axes[0].plot(x, [100 * bfc.loc[(m, c), "EER"] for c in CONDS], "-o", color=MCOL[m], lw=2, ms=8,
                     mec="white", mew=1.5, label=ML[m])
        axes[1].plot(x, [100 * np.mean([atc.loc[(m, s, c), "IAPMR_EER"] for s in SYNTHS]) for c in CONDS], "-o",
                     color=MCOL[m], lw=2, ms=8, mec="white", mew=1.5, label=ML[m])
    for ax in axes:
        ax.set_xticks(x); ax.set_xticklabels(["Clean", "20 dB SNR", "10 dB SNR", "G.711"])
    axes[0].set_ylabel("Bona fide EER (%)"); axes[0].set_title("Verification of genuine speakers")
    axes[1].set_ylabel("IAPMR at τ (%), mean of 4 tools"); axes[1].set_title("Cloning attacks")
    axes[1].set_ylim(0, 102)
    axes[0].legend(frameon=False)
    save(fig, "fig_conditions")


def fig_aasist():
    z = pd.read_csv(os.path.join(RES, "clean", "aasist_scores.csv.gz"))
    groups = [("Bona fide", z[z.kind == "bonafide_test"].score, INK)]
    groups += [(SL[k], z[z.kind == k].score, SCOL[k]) for k in SYNTHS]
    tau = rd("clean", "aasist.csv").tau_cm.iloc[0]
    fig, ax = plt.subplots(figsize=(7, 4))
    bp = ax.boxplot([g[1].to_numpy() for g in groups], widths=0.5, patch_artist=True, showfliers=False,
                    medianprops=dict(color="white", lw=2))
    for patch, (_, _, col) in zip(bp["boxes"], groups):
        patch.set_facecolor(col); patch.set_edgecolor(col)
    for el in ["whiskers", "caps"]:
        for line in bp[el]:
            line.set_color(MUTED)
    ax.axhline(tau, color=MUTED, ls="--", lw=1.2)
    ax.text(len(groups) + 0.45, tau, "CM threshold\n(BPCER = 5%)", va="center", ha="left", fontsize=8.5, color=MUTED)
    ax.set_xticks(range(1, len(groups) + 1)); ax.set_xticklabels([g[0] for g in groups])
    ax.set_ylabel("AASIST score (bona fide log-odds)")
    ax.grid(axis="x", visible=False)
    save(fig, "fig_aasist_scores")


if __name__ == "__main__":
    write_tables()
    fig_iapmr(); fig_det(); fig_tradeoff(); fig_conditions(); fig_aasist()
    print("assets in", DST)
