# Voice Cloning Attack: Resilience of Speaker-Verification Systems

Evaluation code and results for the paper *“Assessment of the Resilience of Voice Authentication Systems Against AI-Generated Voice Cloning”* (Ruda, Sabodashko, Opirskyy, Dzhaliuk, Khoma, Podpora; Multimedia Tools and Applications, under review).

Five speaker-embedding models (TitaNet, PyAnnote, ECAPA-TDNN, WavLM-base-sv, WavLM-base-plus-sv) are attacked with clones from four voice-cloning tools (ElevenLabs, RVC, XTTS, Tortoise TTS). A pretrained AASIST countermeasure is evaluated on the same attacks. Everything is evaluated under clean, noisy (20/10 dB SNR) and G.711 telephone-channel conditions.

> **Audio is not included.** For copyright and privacy reasons, this repository contains no source recordings and no synthetic speech. Speakers are identified only by anonymous IDs (S01–S20).

## Contents

| Path | What it is |
|---|---|
| `evaluation/common.py` | Data inventory, audio loading, acoustic conditions, model wrappers |
| `evaluation/extract.py` | Embedding extraction (incremental; also records per-file latency) |
| `evaluation/aasist_score.py` | AASIST countermeasure scores |
| `evaluation/evaluate.py` | Metrics (EER, minDCF, FAR/FRR, IAPMR, SPF-EER), bootstrap CIs, McNemar / Wilcoxon / Mann–Whitney tests, DET curves |
| `evaluation/make_paper_assets.py` | Tables and figures of the paper |
| `evaluation/results/<condition>/` | Results for `clean`, `noise20`, `noise10`, `g711`, including per-trial scores (`trials.csv.gz`) |
| `evaluation/paper_assets/` | Tables (`tables.md`, `tables.html`) and figures (PDF/PNG) as used in the paper |

## Protocol

- **Enrollment:** 10 × 10-s recordings per speaker. The voiceprint is the mean of the L2-normalised embeddings.
- **Calibration:** all 19,900 enrollment pairs. The threshold τ is set at the EER point and then frozen.
- **Bona fide test:** 20 recordings per speaker, each scored against every voiceprint (400 target / 7,600 zero-effort impostor trials).
- **Attacks:** 40 clones per speaker and tool. Clones 0–19 reproduce the text of the speaker's test recordings (*identical content*); clones 20–39 use unseen text (*varied content*). Each clone is scored against its target's voiceprint.
- **Decision rule:** cosine similarity ≥ τ.

## Reproducing the results

### 1. Environment

The paper's results were obtained with Python 3.11 on CPU (Apple M4 Pro).

```bash
uv venv --python 3.11 .venv
uv pip install --python .venv/bin/python -r requirements.txt
# NeMo pulls in triton (Linux only); on macOS install it without dependencies:
uv pip install --python .venv/bin/python --no-deps nemo_toolkit==1.23.0
```

- **PyAnnote:** `pyannote/embedding` is gated. Accept its conditions on Hugging Face and run `huggingface-cli login`.
- **AASIST:** clone the official repository, which includes the ASVspoof 2019 LA weights:

```bash
git clone https://github.com/clovaai/aasist evaluation/third_party/aasist
```

### 2. Data layout (not distributed)

```
dataset_exp_1/<speaker>/*.wav                    enrollment (10 per speaker)
dataset_exp_2/<speaker>/<speaker>-NN.wav         bona fide test (20 per speaker)
data/<tool>/<speaker>/<speaker>-<i>-<tool>.wav   clones, tool ∈ {11labs, rvc, tortoise, xtts}, i = 0..39
evaluation/speaker_metadata.csv                  optional: speaker,gender (for the gender analysis)
```

### 3. Run

```bash
for c in clean noise20 noise10 g711; do
  .venv/bin/python evaluation/extract.py --condition $c
  .venv/bin/python evaluation/aasist_score.py --condition $c
  .venv/bin/python evaluation/evaluate.py --condition $c
done
.venv/bin/python evaluation/make_paper_assets.py
```

To only re-create the tables and figures from the included results, run `make_paper_assets.py`.

## Results format

`trials.csv.gz` contains one row per trial, with these columns:

| Column | Meaning |
|---|---|
| `model` | embedding model |
| `condition` | acoustic condition |
| `trial` | `target`, `nontarget` or `spoof` |
| `speaker` | true speaker (anonymous ID) |
| `claimed` | claimed identity (anonymous ID) |
| `synth` | cloning tool |
| `content` | `identical` or `varied` |
| `index` | utterance index |
| `score` | cosine similarity |
| `accept` | decision at τ |
| `gender` | speaker gender |
