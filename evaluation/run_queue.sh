#!/bin/zsh
# Runs after the clean extraction: AASIST + degraded conditions, sequentially.
cd "$(dirname "$0")/.."
PY=.venv/bin/python
MODELS=(titanet ecapa resnet wavlm-base-sv wavlm-base-plus-sv)
while pgrep -f "evaluation/extract.py --models" >/dev/null; do sleep 30; done
$PY evaluation/aasist_score.py --condition clean
for c in noise20 noise10 g711; do
  $PY evaluation/extract.py --models $MODELS --condition $c
  $PY evaluation/aasist_score.py --condition $c
done
echo QUEUE_DONE
