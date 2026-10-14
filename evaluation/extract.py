"""Extract L2-normalised embeddings for every file and model; record per-file latency.

Usage: .venv/bin/python evaluation/extract.py [--models titanet ecapa ...] [--condition clean]
Output: evaluation/embeddings/<model>__<condition>.npz  (+ items.csv inventory)
"""
import os
import sys
import time
import argparse

import numpy as np
import pandas as pd
import torch
import tqdm

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from common import OUT, MODELS, CONDITIONS, inventory, load_audio, degrade, load_model  # noqa: E402

SEED = 1234


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--models", nargs="+", default=MODELS)
    ap.add_argument("--condition", default="clean", choices=CONDITIONS)
    args = ap.parse_args()

    torch.manual_seed(SEED)
    np.random.seed(SEED)
    torch.set_num_threads(os.cpu_count())

    speakers, items = inventory()
    emb_dir = os.path.join(OUT, "embeddings")
    os.makedirs(emb_dir, exist_ok=True)
    pd.DataFrame([i.__dict__ for i in items]).to_csv(os.path.join(emb_dir, "items.csv"), index=False)
    print(f"{len(speakers)} speakers, {len(items)} files")

    # Decode audio once; it is shared by all models.
    audio = {i.path: degrade(load_audio(i.path), args.condition, i.path)
             for i in tqdm.tqdm(items, desc=f"loading audio ({args.condition})")}

    for name in args.models:
        out_path = os.path.join(emb_dir, f"{name}__{args.condition}.npz")
        # Incremental: reuse embeddings of files already processed, compute only new paths.
        done = {}
        if os.path.exists(out_path):
            z = np.load(out_path)
            done = {p: (e, s) for p, e, s in zip(z["paths"], z["emb"], z["seconds"])}
        todo = [it for it in items if it.path not in done]
        if not todo and len(done) == len(items):
            print(f"skip {name}: up to date")
            continue
        model = load_model(name)
        model(audio[items[0].path])  # warm-up, excluded from timing
        for it in tqdm.tqdm(todo, desc=name):
            wav = audio[it.path]
            t0 = time.perf_counter()
            e = model(wav)
            secs = time.perf_counter() - t0
            e = np.asarray(e, dtype=np.float32).reshape(-1)
            done[it.path] = (e / np.linalg.norm(e), secs)
        np.savez_compressed(
            out_path,
            paths=np.array([i.path for i in items]),
            emb=np.stack([done[i.path][0] for i in items]),
            seconds=np.array([done[i.path][1] for i in items]),
            audio_seconds=np.array([len(audio[i.path]) / 16000 for i in items]),
        )
        print(f"saved {out_path} ({len(todo)} new files)")
        del model


if __name__ == "__main__":
    main()
