"""Metrics, statistics and figures for the revision.

Protocol (per model, per acoustic condition):
  * Enrollment voiceprint: mean of the 10 dataset_exp_1 embeddings of a speaker (eq. 2).
  * Calibration: all pairs inside dataset_exp_1 (900 target / 19,000 non-target);
    the decision threshold tau is the EER point of this set and is then frozen.
  * Bona fide test: every dataset_exp_2 file against every voiceprint
    (400 target / 7,600 zero-effort impostor trials).
  * Attacks: every clone against its target speaker's voiceprint
    (400 identical-content + 400 varied-content trials per cloning tool).
Accept rule: cosine similarity >= tau (equivalently cosine distance <= 1 - tau).

Usage: .venv/bin/python evaluation/evaluate.py [--condition clean]
"""
import os
import sys
import argparse
import itertools

import numpy as np
import pandas as pd
from scipy import stats
from statsmodels.stats.proportion import proportion_confint
from statsmodels.stats.contingency_tables import mcnemar
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt  # noqa: E402

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT, MODELS, SYNTHS, SYNTH_LABEL, GENDER  # noqa: E402

RNG = np.random.default_rng(1234)
N_BOOT = 2000
MODEL_LABEL = {
    "pyannote": "PyAnnote", "wavlm-base-sv": "WavLM-base-sv",
    "wavlm-base-plus-sv": "WavLM-base-plus-sv", "titanet": "TitaNet",
    "ecapa": "ECAPA-TDNN", "resnet": "ResNet-34",
}


# ---------------------------------------------------------------- metrics

def roc(tar, non):
    """FAR/FRR for every distinct threshold (accept if score >= thr)."""
    thr = np.unique(np.concatenate([tar, non]))
    tar_s, non_s = np.sort(tar), np.sort(non)
    frr = np.searchsorted(tar_s, thr, side="left") / len(tar)
    far = 1 - np.searchsorted(non_s, thr, side="left") / len(non)
    return thr, far, frr


def eer(tar, non):
    thr, far, frr = roc(tar, non)
    i = np.argmin(np.abs(far - frr))
    return (far[i] + frr[i]) / 2, thr[i]


def min_dcf(tar, non, p_target=0.01, c_miss=1.0, c_fa=1.0):
    _, far, frr = roc(tar, non)
    dcf = c_miss * p_target * frr + c_fa * (1 - p_target) * far
    return dcf.min() / min(c_miss * p_target, c_fa * (1 - p_target))


def thr_at_far(non, target_far):
    """Smallest threshold whose FAR does not exceed target_far."""
    non_s = np.sort(non)
    k = int(np.floor(target_far * len(non)))
    return non_s[len(non) - k] if k < len(non) else non_s[0]


def wilson(k, n):
    lo, hi = proportion_confint(k, n, alpha=0.05, method="wilson")
    return lo, hi


def speaker_bootstrap(df, col="accept"):
    """95% CI of a rate, resampling speakers (cluster bootstrap)."""
    per = df.groupby("speaker")[col].agg(["sum", "count"])
    s, c = per["sum"].to_numpy(), per["count"].to_numpy()
    idx = RNG.integers(0, len(per), size=(N_BOOT, len(per)))
    rates = s[idx].sum(1) / c[idx].sum(1)
    return np.percentile(rates, [2.5, 97.5])


# ---------------------------------------------------------------- scoring

def load(model, condition):
    z = np.load(os.path.join(OUT, "embeddings", f"{model}__{condition}.npz"))
    items = pd.read_csv(os.path.join(OUT, "embeddings", "items.csv"), keep_default_na=False)
    assert (items["path"].to_numpy() == z["paths"]).all()
    items["row"] = np.arange(len(items))
    return items, z["emb"], z["seconds"], z["audio_seconds"]


def score_model(model, condition, enroll_condition="clean", exclude=()):
    items, emb, secs, dur = load(model, condition)
    if condition != enroll_condition:   # enrollment always uses clean audio
        _, emb_clean, _, _ = load(model, enroll_condition)
        enr = items["subset"] == "enroll"
        emb = emb.copy()
        emb[enr.to_numpy()] = emb_clean[enr.to_numpy()]

    items = items[~items.speaker.isin(exclude)]
    speakers = sorted(items["speaker"].unique())
    enroll = items[items.subset == "enroll"]

    # Calibration: all pairs within the enrollment set.
    e_emb, e_spk = emb[enroll.row], enroll.speaker.to_numpy()
    sim = e_emb @ e_emb.T
    iu = np.triu_indices(len(enroll), 1)
    same = e_spk[iu[0]] == e_spk[iu[1]]
    cal_tar, cal_non = sim[iu][same], sim[iu][~same]
    cal_eer, tau = eer(cal_tar, cal_non)

    # Voiceprints.
    vp = np.stack([emb[enroll.row[enroll.speaker == s]].mean(0) for s in speakers])
    vp /= np.linalg.norm(vp, axis=1, keepdims=True)
    spk_idx = {s: i for i, s in enumerate(speakers)}

    rows = []
    test = items[items.subset == "test"]
    S = emb[test.row] @ vp.T
    for j, (_, it) in enumerate(test.iterrows()):
        for s in speakers:
            rows.append(dict(trial="target" if s == it.speaker else "nontarget",
                             claimed=s, speaker=it.speaker, path=it.path, synth="", content="",
                             index=it["index"], score=S[j, spk_idx[s]]))
    att = items[items.subset == "attack"]
    A = (emb[att.row] * vp[[spk_idx[s] for s in att.speaker]]).sum(1)
    for j, (_, it) in enumerate(att.iterrows()):
        rows.append(dict(trial="spoof", claimed=it.speaker, speaker=it.speaker, path=it.path,
                         synth=it.synth, content=it.content, index=it["index"], score=A[j]))
    trials = pd.DataFrame(rows)
    trials["model"] = model
    trials["condition"] = condition
    trials["accept"] = (trials.score >= tau).astype(int)
    trials["gender"] = trials.speaker.map(GENDER)

    timing = dict(model=model, condition=condition,
                  ms_per_file=1000 * secs.mean(), ms_std=1000 * secs.std(),
                  rtf=float((secs / dur).mean()))
    calib = dict(model=model, condition=condition, cal_eer=cal_eer, tau=tau,
                 cal_min_dcf_01=min_dcf(cal_tar, cal_non, 0.01),
                 cal_min_dcf_05=min_dcf(cal_tar, cal_non, 0.05),
                 n_cal_target=len(cal_tar), n_cal_nontarget=len(cal_non))
    return trials, calib, timing


# ---------------------------------------------------------------- tables

def bona_fide_table(trials, calib):
    out = []
    for (model, cond), t in trials.groupby(["model", "condition"]):
        tar = t[t.trial == "target"].score.to_numpy()
        non = t[t.trial == "nontarget"].score.to_numpy()
        tau = calib[(model, cond)]["tau"]
        far, frr = (non >= tau).mean(), (tar < tau).mean()
        e, _ = eer(tar, non)
        out.append(dict(model=model, condition=cond, FAR=far, FRR=frr, HTER=(far + frr) / 2,
                        EER=e, minDCF_001=min_dcf(tar, non, 0.01), minDCF_005=min_dcf(tar, non, 0.05),
                        tau=tau, ACC_balanced=1 - (far + frr) / 2,
                        n_target=len(tar), n_nontarget=len(non)))
    return pd.DataFrame(out)


def attack_table(trials, calib):
    out = []
    for (model, cond), t in trials.groupby(["model", "condition"]):
        tar = t[t.trial == "target"]
        non = t[t.trial == "nontarget"].score.to_numpy()
        ops = {"EER": calib[(model, cond)]["tau"],
               "FAR1": thr_at_far(non, 0.01), "FAR01": thr_at_far(non, 0.001)}
        for synth, content in itertools.product(SYNTHS, ["identical", "varied", "all"]):
            sp = t[(t.trial == "spoof") & (t.synth == synth)]
            if content != "all":
                sp = sp[sp.content == content]
            row = dict(model=model, condition=cond, synth=synth, content=content, n=len(sp))
            for op, thr in ops.items():
                k = int((sp.score >= thr).sum())
                row[f"IAPMR_{op}"] = k / len(sp)
                row[f"FRR_{op}"] = (tar.score < thr).mean()   # genuine rejection at the same threshold
                if op == "EER":
                    row["wilson_lo"], row["wilson_hi"] = wilson(k, len(sp))
                    row["boot_lo"], row["boot_hi"] = speaker_bootstrap(sp.assign(accept=(sp.score >= thr)))
                    per = sp.assign(a=(sp.score >= thr)).groupby("speaker").a.mean()
                    row["speaker_sd"] = per.std()
                    row["speaker_min"], row["speaker_max"] = per.min(), per.max()
                    row["GAR"] = (tar.score >= thr).mean()   # genuine acceptance, same threshold
            row["SPF_EER"] = eer(tar.score.to_numpy(), sp.score.to_numpy())[0]
            row["mean_score"] = sp.score.mean()
            out.append(row)
    return pd.DataFrame(out)


def model_pairwise_mcnemar(trials):
    """Exact McNemar between every pair of models, paired on the same clone file."""
    sp = trials[trials.trial == "spoof"]
    out = []
    for (cond, synth, content), g in sp.groupby(["condition", "synth", "content"]):
        wide = g.pivot_table(index="path", columns="model", values="accept")
        for a, b in itertools.combinations(wide.columns, 2):
            x, y = wide[a], wide[b]
            tab = [[((x == 1) & (y == 1)).sum(), ((x == 1) & (y == 0)).sum()],
                   [((x == 0) & (y == 1)).sum(), ((x == 0) & (y == 0)).sum()]]
            p = mcnemar(tab, exact=True).pvalue
            out.append(dict(condition=cond, synth=synth, content=content, model_a=a, model_b=b,
                            iapmr_a=x.mean(), iapmr_b=y.mean(), b=tab[0][1], c=tab[1][0], p=p))
    df = pd.DataFrame(out)
    # Holm correction within each condition
    for cond, idx in df.groupby("condition").groups.items():
        p = df.loc[idx, "p"].to_numpy()
        order = np.argsort(p)
        adj = np.minimum(1, np.maximum.accumulate((len(p) - np.arange(len(p))) * p[order]))
        df.loc[np.array(idx)[order], "p_holm"] = adj
    return df


def content_effect(trials):
    """Identical vs varied: speaker-level paired Wilcoxon on accept rate and mean score."""
    sp = trials[trials.trial == "spoof"]
    out = []
    for (model, cond, synth), g in sp.groupby(["model", "condition", "synth"]):
        per = g.groupby(["speaker", "content"]).agg(rate=("accept", "mean"), score=("score", "mean")).unstack()
        d_rate = per["rate"]["identical"] - per["rate"]["varied"]
        d_score = per["score"]["identical"] - per["score"]["varied"]
        p_rate = stats.wilcoxon(d_rate).pvalue if (d_rate != 0).any() else 1.0
        p_score = stats.wilcoxon(d_score).pvalue
        out.append(dict(model=model, condition=cond, synth=synth,
                        iapmr_identical=per["rate"]["identical"].mean(),
                        iapmr_varied=per["rate"]["varied"].mean(),
                        delta_pp=100 * d_rate.mean(), p_rate=p_rate,
                        delta_score=d_score.mean(), p_score=p_score))
    return pd.DataFrame(out)


def gender_table(trials):
    sp = trials[trials.trial == "spoof"]
    out = []
    for (model, cond), g in sp.groupby(["model", "condition"]):
        per = g.groupby(["speaker", "gender"]).accept.mean().reset_index()
        m, f = per[per.gender == "M"].accept, per[per.gender == "F"].accept
        out.append(dict(model=model, condition=cond, iapmr_male=g[g.gender == "M"].accept.mean(),
                        iapmr_female=g[g.gender == "F"].accept.mean(),
                        p_mannwhitney=stats.mannwhitneyu(m, f).pvalue))
    return pd.DataFrame(out)


def countermeasure_tables(trials, condition, bpcer=0.05):
    """AASIST alone and cascaded with each SV model (accept only if both accept).

    The CM threshold is set on bona fide test audio so that `bpcer` of genuine
    attempts are rejected; it uses no spoofed data.
    """
    path = os.path.join(OUT, "embeddings", f"aasist__{condition}.npz")
    if not os.path.exists(path):
        return None, None
    z = np.load(path)
    cm = pd.Series(z["score"], index=z["paths"])
    bona = cm[[p.startswith("dataset_exp_2/") for p in cm.index]].to_numpy()
    tau_cm = np.quantile(bona, bpcer)

    cm_rows = []
    for synth in SYNTHS:
        for content in ["identical", "varied", "all"]:
            sel = [p.startswith(f"data/{synth}/") for p in cm.index]
            sp = trials[(trials.trial == "spoof") & (trials.synth == synth)].drop_duplicates("path")
            if content != "all":
                sp = sp[sp.content == content]
            s = cm[sp.path].to_numpy()
            k = int((s >= tau_cm).sum())
            lo, hi = wilson(k, len(s))
            cm_rows.append(dict(condition=condition, synth=synth, content=content, n=len(s),
                                CM_EER=eer(bona, cm[np.array(sel)].to_numpy())[0] if content == "all" else np.nan,
                                APCER=k / len(s), wilson_lo=lo, wilson_hi=hi,
                                BPCER=(bona < tau_cm).mean(), tau_cm=tau_cm))

    t = trials.copy()
    t["cm_accept"] = (cm[t.path].to_numpy() >= tau_cm).astype(int)
    t["joint"] = t.accept & t.cm_accept
    sasv = []
    for (model, synth), g in t[t.trial == "spoof"].groupby(["model", "synth"]):
        gen = t[(t.model == model) & (t.trial == "target")]
        k = int(g.joint.sum())
        lo, hi = wilson(k, len(g))
        sasv.append(dict(model=model, condition=condition, synth=synth,
                         IAPMR_sv=g.accept.mean(), IAPMR_sv_cm=k / len(g),
                         wilson_lo=lo, wilson_hi=hi,
                         FRR_sv=1 - gen.accept.mean(), FRR_sv_cm=1 - gen.joint.mean()))
    return pd.DataFrame(cm_rows), pd.DataFrame(sasv)


# ---------------------------------------------------------------- figures

def det_plot(trials, path):
    from scipy.stats import norm
    models = [m for m in MODELS if m in trials.model.unique()]
    fig, axes = plt.subplots(2, 3, figsize=(12, 8), sharex=True, sharey=True)
    ticks = np.array([0.001, 0.01, 0.05, 0.2, 0.5, 0.8, 0.95])
    for ax, model in zip(axes.flat, models):
        t = trials[trials.model == model]
        tar = t[t.trial == "target"].score.to_numpy()
        curves = [("Zero-effort impostor", t[t.trial == "nontarget"].score.to_numpy(), "k", "-")]
        for synth, c in zip(SYNTHS, ["C0", "C1", "C2", "C3"]):
            curves.append((SYNTH_LABEL[synth], t[(t.trial == "spoof") & (t.synth == synth)].score.to_numpy(), c, "--"))
        for label, non, color, ls in curves:
            _, far, frr = roc(tar, non)
            far, frr = np.clip(far, 5e-4, 1 - 5e-4), np.clip(frr, 5e-4, 1 - 5e-4)
            ax.plot(norm.ppf(far), norm.ppf(frr), color=color, ls=ls, lw=1.5, label=label)
        ax.set_title(MODEL_LABEL[model])
        ax.set_xticks(norm.ppf(ticks)); ax.set_xticklabels([f"{100*x:g}" for x in ticks])
        ax.set_yticks(norm.ppf(ticks)); ax.set_yticklabels([f"{100*x:g}" for x in ticks])
        ax.grid(alpha=.3)
    for ax in axes[-1]:
        ax.set_xlabel("False acceptance / IAPMR (%)")
    for ax in axes[:, 0]:
        ax.set_ylabel("False rejection rate (%)")
    for ax in axes.flat[len(models):]:
        ax.axis("off")
    axes.flat[0].legend(fontsize=8, loc="lower left")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


def iapmr_plot(att, path):
    models = [m for m in MODELS if m in att.model.unique()]
    fig, axes = plt.subplots(1, 2, figsize=(13, 4.5), sharey=True)
    w = 0.8 / len(models)
    for ax, content in zip(axes, ["identical", "varied"]):
        d = att[(att.content == content)]
        for k, model in enumerate(models):
            r = d[d.model == model].set_index("synth").loc[SYNTHS]
            x = np.arange(len(SYNTHS)) + k * w
            y = 100 * r.IAPMR_EER
            ax.bar(x, y, w, label=MODEL_LABEL[model],
                   yerr=[100 * (r.IAPMR_EER - r.boot_lo), 100 * (r.boot_hi - r.IAPMR_EER)], capsize=2)
        ax.set_xticks(np.arange(len(SYNTHS)) + w * (len(models) - 1) / 2)
        ax.set_xticklabels([SYNTH_LABEL[s] for s in SYNTHS])
        ax.set_title(f"{content.capitalize()} linguistic content")
        ax.set_ylim(0, 100)
        ax.grid(axis="y", alpha=.3)
    axes[0].set_ylabel("Attack success rate, IAPMR (%)")
    axes[1].legend(fontsize=8, loc="lower right")
    fig.tight_layout()
    fig.savefig(path)
    plt.close(fig)


# ---------------------------------------------------------------- main

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", default="clean")
    ap.add_argument("--models", nargs="+", default=MODELS)
    ap.add_argument("--exclude", nargs="*", default=[], help="speakers to drop")
    ap.add_argument("--tag", default="", help="suffix for the results folder")
    args = ap.parse_args()

    res = os.path.join(OUT, "results", args.condition + args.tag)
    os.makedirs(res, exist_ok=True)
    all_trials, calib, timing = [], {}, []
    for m in args.models:
        if not os.path.exists(os.path.join(OUT, "embeddings", f"{m}__{args.condition}.npz")):
            print(f"no embeddings for {m}, skipping")
            continue
        t, c, tm = score_model(m, args.condition, exclude=args.exclude)
        all_trials.append(t)
        calib[(m, args.condition)] = c
        timing.append(tm)
    trials = pd.concat(all_trials, ignore_index=True)
    trials.to_csv(os.path.join(res, "trials.csv.gz"), index=False)

    pd.DataFrame(calib.values()).to_csv(os.path.join(res, "calibration.csv"), index=False)
    bona_fide_table(trials, calib).to_csv(os.path.join(res, "bona_fide.csv"), index=False)
    att = attack_table(trials, calib)
    att.to_csv(os.path.join(res, "attacks.csv"), index=False)
    model_pairwise_mcnemar(trials).to_csv(os.path.join(res, "mcnemar_models.csv"), index=False)
    content_effect(trials).to_csv(os.path.join(res, "content_effect.csv"), index=False)
    gender_table(trials).to_csv(os.path.join(res, "gender.csv"), index=False)
    pd.DataFrame(timing).to_csv(os.path.join(res, "timing.csv"), index=False)
    (trials[trials.trial == "spoof"].groupby(["model", "synth", "speaker"]).accept.mean()
     .unstack("speaker").to_csv(os.path.join(res, "per_speaker_iapmr.csv")))
    cm_tab, sasv_tab = countermeasure_tables(trials, args.condition)
    if cm_tab is not None:
        cm_tab.to_csv(os.path.join(res, "aasist.csv"), index=False)
        sasv_tab.to_csv(os.path.join(res, "sv_plus_aasist.csv"), index=False)
    det_plot(trials, os.path.join(res, "det_curves.pdf"))
    iapmr_plot(att, os.path.join(res, "iapmr.pdf"))
    print(f"results in {res}")


if __name__ == "__main__":
    main()
