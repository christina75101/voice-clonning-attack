"""Score every file with the pretrained AASIST countermeasure (ASVspoof 2019 LA weights).

AASIST takes 64,600-sample (~4 s) inputs. Each file is split into non-overlapping 4 s
windows (the last one repeat-padded as in the official data_utils.pad) and the
bona fide log-odds (logit1 - logit0) is averaged over windows. Higher score = more likely bona fide.

Usage: .venv/bin/python evaluation/aasist_score.py [--condition clean]
Output: evaluation/embeddings/aasist__<condition>.npz  (scores instead of embeddings)
"""
import os
import sys
import json
import time
import argparse

import numpy as np
import torch
import tqdm

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.path.insert(0, os.path.join(HERE, "third_party", "aasist"))
from common import OUT, CONDITIONS, inventory, load_audio, degrade  # noqa: E402
from models.AASIST import Model  # noqa: E402

NB_SAMP = 64600


def windows(wav):
    if len(wav) < NB_SAMP:
        reps = NB_SAMP // len(wav) + 1
        return np.tile(wav, reps)[:NB_SAMP][None]
    n = len(wav) // NB_SAMP
    segs = [wav[i * NB_SAMP:(i + 1) * NB_SAMP] for i in range(n)]
    rest = wav[n * NB_SAMP:]
    if len(rest) >= NB_SAMP // 2:   # keep a long-enough tail, repeat-padded
        segs.append(np.tile(rest, NB_SAMP // len(rest) + 1)[:NB_SAMP])
    return np.stack(segs)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--condition", default="clean", choices=CONDITIONS)
    args = ap.parse_args()
    torch.manual_seed(1234)

    conf = json.load(open(os.path.join(HERE, "third_party", "aasist", "config", "AASIST.conf")))
    model = Model(conf["model_config"])
    state = torch.load(os.path.join(HERE, "third_party", "aasist", "models", "weights", "AASIST.pth"),
                       map_location="cpu")
    model.load_state_dict(state)
    model.eval()

    _, items = inventory()
    scores, secs, durs = [], [], []
    for it in tqdm.tqdm(items, desc=f"aasist ({args.condition})"):
        wav = degrade(load_audio(it.path), args.condition, it.path)
        x = torch.from_numpy(windows(wav)).float()
        t0 = time.perf_counter()
        with torch.no_grad():
            _, out = model(x)
        secs.append(time.perf_counter() - t0)
        scores.append(float((out[:, 1] - out[:, 0]).mean()))  # bona fide log-odds
        durs.append(len(wav) / 16000)

    out_path = os.path.join(OUT, "embeddings", f"aasist__{args.condition}.npz")
    np.savez_compressed(out_path, paths=np.array([i.path for i in items]), score=np.array(scores),
                        seconds=np.array(secs), audio_seconds=np.array(durs))
    print(f"saved {out_path}")


if __name__ == "__main__":
    main()
