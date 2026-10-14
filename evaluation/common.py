"""Shared inventory, model loaders and audio helpers for the revision re-run.

Audio is always loaded read-only (never written back), resampled to 16 kHz mono.
"""
import os
import glob
import re
import zlib
from dataclasses import dataclass

import numpy as np
import librosa
import torch

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = os.path.dirname(os.path.abspath(__file__))
SR = 16000

SYNTHS = ["11labs", "rvc", "tortoise", "xtts"]
SYNTH_LABEL = {"11labs": "ElevenLabs", "rvc": "RVC", "tortoise": "Tortoise", "xtts": "XTTS"}

# Clone index i in 0..19 reproduces the text of dataset_exp_2/<spk>/<spk>-(i+1).wav
# (verified by duration correlation r=0.72-0.83); 20..39 are different texts.
N_IDENTICAL = 20

# Speaker metadata (speaker folder name -> "M"/"F") is kept in a local, unpublished file
# evaluation/speaker_metadata.csv with columns: speaker,gender
def _load_gender():
    path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "speaker_metadata.csv")
    if not os.path.exists(path):
        return {}
    import csv
    with open(path) as f:
        return {r["speaker"]: r["gender"] for r in csv.DictReader(f)}


GENDER = _load_gender()

MODELS = [
    "pyannote", "wavlm-base-sv", "wavlm-base-plus-sv", "titanet", "ecapa", "resnet",
]


@dataclass
class Item:
    path: str      # relative to ROOT
    speaker: str
    subset: str    # enroll | test | attack
    synth: str     # "" for bona fide
    content: str   # "" | identical | varied
    index: int


def inventory():
    items = []
    speakers = sorted(os.listdir(os.path.join(ROOT, "dataset_exp_2")))
    for spk in speakers:
        for p in sorted(glob.glob(os.path.join(ROOT, "dataset_exp_1", spk, "*.wav"))):
            idx = int(re.search(r"(\d+)\.wav$", p).group(1))
            items.append(Item(os.path.relpath(p, ROOT), spk, "enroll", "", "", idx))
        for p in sorted(glob.glob(os.path.join(ROOT, "dataset_exp_2", spk, "*.wav"))):
            idx = int(re.search(r"(\d+)\.wav$", p).group(1))
            items.append(Item(os.path.relpath(p, ROOT), spk, "test", "", "", idx))
        for synth in SYNTHS:
            for p in sorted(glob.glob(os.path.join(ROOT, "data", synth, spk, "*"))):
                idx = int(re.search(rf"-(\d+)-{synth}\.\w+$", p).group(1))
                content = "identical" if idx < N_IDENTICAL else "varied"
                items.append(Item(os.path.relpath(p, ROOT), spk, "attack", synth, content, idx))
    return speakers, items


def load_audio(rel_path):
    wav, _ = librosa.load(os.path.join(ROOT, rel_path), sr=SR, mono=True)
    return wav.astype(np.float32)


CONDITIONS = ["clean", "noise20", "noise10", "g711"]


def degrade(wav, condition, rel_path):
    """Apply an acoustic condition. Noise is seeded by the file path, so it is reproducible."""
    if condition == "clean":
        return wav
    if condition.startswith("noise"):
        snr_db = float(condition[len("noise"):])
        seed = zlib.crc32(rel_path.encode())
        noise = np.random.default_rng(seed).standard_normal(len(wav)).astype(np.float32)
        p_sig, p_noise = np.mean(wav ** 2), np.mean(noise ** 2)
        noise *= np.sqrt(p_sig / (p_noise * 10 ** (snr_db / 10)))
        return wav + noise
    if condition == "g711":
        # ITU-T G.711 mu-law telephone channel: 8 kHz, 8-bit companding, back to 16 kHz
        import torchaudio.functional as AF
        x = torch.from_numpy(wav)
        x = AF.resample(x, SR, 8000)
        x = x / max(1.0, float(x.abs().max()))
        x = AF.mu_law_decoding(AF.mu_law_encoding(x, 256), 256)
        return AF.resample(x, 8000, SR).numpy().astype(np.float32)
    raise ValueError(condition)


# ---------------------------------------------------------------- models

class Embedder:
    name = ""

    def __call__(self, wav: np.ndarray) -> np.ndarray:
        raise NotImplementedError


class PyannoteEmb(Embedder):
    name = "pyannote"

    def __init__(self):
        from pyannote.audio import Model, Inference
        token = os.environ.get("HF_TOKEN") or True  # falls back to `huggingface-cli login`
        model = Model.from_pretrained("pyannote/embedding", use_auth_token=token)
        self.inf = Inference(model, window="whole", device=torch.device("cpu"))

    def __call__(self, wav):
        return np.asarray(self.inf({"waveform": torch.from_numpy(wav)[None], "sample_rate": SR}))


class WavLMEmb(Embedder):
    def __init__(self, name):
        from transformers import Wav2Vec2FeatureExtractor, WavLMForXVector
        self.name = name
        self.fe = Wav2Vec2FeatureExtractor.from_pretrained(f"microsoft/{name}")
        self.model = WavLMForXVector.from_pretrained(f"microsoft/{name}").eval()

    @torch.no_grad()
    def __call__(self, wav):
        inputs = self.fe([wav], sampling_rate=SR, return_tensors="pt")
        return self.model(**inputs).embeddings[0].numpy()


class TitaNetEmb(Embedder):
    name = "titanet"

    def __init__(self):
        import nemo.collections.asr as nemo_asr
        self.model = nemo_asr.models.EncDecSpeakerLabelModel.from_pretrained(
            "nvidia/speakerverification_en_titanet_large").eval()

    @torch.no_grad()
    def __call__(self, wav):
        emb, _ = self.model.infer_segment(wav)
        return emb[0].cpu().numpy()


class SpeechBrainEmb(Embedder):
    def __init__(self, name, source):
        from speechbrain.inference.speaker import EncoderClassifier
        self.name = name
        self.model = EncoderClassifier.from_hparams(
            source=source, savedir=os.path.join(ROOT, "pretrained_models", source.split("/")[1]),
            run_opts={"device": "cpu"})

    @torch.no_grad()
    def __call__(self, wav):
        return self.model.encode_batch(torch.from_numpy(wav)[None]).reshape(-1).numpy()


def load_model(name) -> Embedder:
    if name == "pyannote":
        return PyannoteEmb()
    if name.startswith("wavlm"):
        return WavLMEmb(name)
    if name == "titanet":
        return TitaNetEmb()
    if name == "ecapa":
        return SpeechBrainEmb("ecapa", "speechbrain/spkrec-ecapa-voxceleb")
    if name == "resnet":
        return SpeechBrainEmb("resnet", "speechbrain/spkrec-resnet-voxceleb")
    raise ValueError(name)
