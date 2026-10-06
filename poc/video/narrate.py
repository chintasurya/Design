"""Generate the female voiceover for Prompt to Production.mp4.

Voice: Kokoro-82M (Apache-2.0), voice "af_heart", run locally with kokoro-onnx.
Nothing is sent to an online speech service.

Setup, once:
    python3 -m venv venv && venv/bin/pip install onnxruntime kokoro-onnx soundfile
    # model: npm packages kokoro-fp32a/b/c-shards; join kokoro-fp32.part0..18.bin in order -> kokoro.onnx
    # voices: npm package kokoro-local-runtime, voices/*.bin -> voices.npz (each reshaped to (-1, 1, 256))

Run:
    venv/bin/python narrate.py kokoro.onnx voices.npz narration_raw.wav
Then mix onto the video with the ffmpeg command in the commit that added this file.

narration-lines.json holds [scene start, scene end, words to say]. Spellings such
as "Jeera" and "Co-pah-do" are there on purpose, so the voice pronounces them right.
"""
import json
import sys

import numpy as np
import soundfile as sf
from kokoro_onnx import Kokoro

model, voices, out = sys.argv[1:4]
k = Kokoro(model, voices)
lines = json.load(open(__file__.rsplit('/', 1)[0] + '/narration-lines.json'))
SR, TOTAL = 24000, 205.0
track = np.zeros(int(TOTAL * SR), dtype=np.float32)
for i, (start, end, text) in enumerate(lines):
    lead = 0.6 if i == 0 else (0.35 if end - start < 6 else 0.5)
    room = end - start - lead - 0.25
    for speed in (0.94, 0.98, 1.02, 1.06, 1.1):  # slow and warm, faster only if a line would overrun its scene
        audio, _ = k.create(text, voice='af_heart', speed=speed, lang='en-us')
        if len(audio) / SR <= room:
            break
    s = int((start + lead) * SR)
    track[s:s + len(audio)] += audio[: len(track) - s]
sf.write(out, track, SR)
