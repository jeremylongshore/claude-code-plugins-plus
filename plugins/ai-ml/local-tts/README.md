# Local TTS — Offline Text-to-Speech

**Generate speech locally with VoxCPM2. 30 languages, voice design, voice cloning. Zero cloud, zero cost.**

Runs 100% on your machine using VoxCPM2 (2B-parameter model, Apache-2.0). Optimized for Apple Silicon via Metal (MPS). No API keys, no rate limits, no telemetry.

---

## Features

| Feature | Description |
|---------|-------------|
| **Text-to-Speech** | 30 languages, auto-detected from input text |
| **Voice Design** | Describe a voice in natural language (e.g. "warm female voice, mid-30s") |
| **Voice Cloning** | Clone any voice from a 3-10 second reference clip |
| **Ultimate Cloning** | Reference + prompt for maximum fidelity (vocal micro-nuances) |
| **48 kHz output** | Production-quality WAV ready for Telegram, video, podcast |

---

## Installation

```bash
/plugin install local-tts@claude-code-plugins-plus
```

### Requirements

- **Python 3.10+** (3.12 recommended)
- **macOS with Apple Silicon** (M1/M2/M3/M4) — uses Metal for acceleration. Linux with CUDA also supported but not the default target.
- **~10 GB disk** for model weights (downloaded on first use to `~/.cache/huggingface/`)
- **~16 GB RAM** recommended

### First-run setup

The plugin uses a dedicated Python venv. Create it once:

```bash
mkdir -p ~/.local-tts
python3.12 -m venv ~/.local-tts/venv
~/.local-tts/venv/bin/pip install --upgrade pip
~/.local-tts/venv/bin/pip install voxcpm
```

On first call, VoxCPM2 downloads ~10 GB of model weights. Subsequent calls reuse the cache (30s startup vs 5+ min first time).

---

## Usage

### Via natural language (auto-triggered)

Just ask Claude to:

- "Say hello in French"
- "Generate a voiceover for this text: ..."
- "Clone this voice: /path/to/sample.wav and say ..."
- "Make a warm female voice reading: ..."

### Direct invocation

```bash
VENV=~/.local-tts/venv
SCRIPT=${CLAUDE_PLUGIN_ROOT}/scripts/generate.py

# 1. Basic TTS (default voice)
"$VENV/bin/python" "$SCRIPT" --text "Hello world" --out /tmp/hello.wav

# 2. Voice Design (no reference needed)
"$VENV/bin/python" "$SCRIPT" \
  --text "(warm female voice, mid-30s, calm)Welcome back." \
  --out /tmp/design.wav

# 3. Voice Cloning (3-10s reference)
"$VENV/bin/python" "$SCRIPT" \
  --text "This is my cloned voice." \
  --ref /path/to/sample.wav \
  --out /tmp/clone.wav

# 4. Long text via stdin
cat article.txt | "$VENV/bin/python" "$SCRIPT" --stdin --out /tmp/article.wav
```

### Supported languages (30)

Arabic, Burmese, Chinese (+ dialects), Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Indonesian, Italian, Japanese, Khmer, Korean, Lao, Malay, Norwegian, Polish, Portuguese, Russian, Spanish, Swahili, Swedish, Tagalog, Thai, Turkish, Vietnamese.

No language tag needed — VoxCPM auto-detects from the text.

---

## Performance (Apple M4, MPS, bfloat16)

| Metric | Value |
|--------|-------|
| First model load | ~340s (downloads 10 GB weights) |
| Subsequent loads | ~30s |
| Generation RTF | ~2.3× realtime (10s audio ≈ 23s compute) |

Not suitable for real-time streaming. Great for batch generation, voiceovers, podcasts, Telegram voice messages.

---

## Script options

| Flag | Description |
|------|-------------|
| `--text STR` | Text to synthesize |
| `--stdin` | Read text from stdin (for long input) |
| `--out PATH` | Output WAV path (required) |
| `--ref PATH` | Reference audio for cloning |
| `--prompt-wav PATH` | Prompt wav for ultimate cloning (max fidelity) |
| `--cfg FLOAT` | Classifier-free guidance (default 2.0) |
| `--steps INT` | Diffusion steps (default 10, higher = slower but marginally better) |
| `--model ID` | Model id (default `openbmb/VoxCPM2`) |
| `--quiet` | Suppress loading messages |

---

## Troubleshooting

**`ModuleNotFoundError: voxcpm`** — venv missing or wrong path. Run the setup commands above.

**`No such file: VoxCPM2 weights`** — HuggingFace cache missing. First run will download (needs network).

**Slow first call** — normal, model load takes 30s after cache warms. Subsequent calls in the same Python process are instant; this script spawns a fresh process per call. For batch work, write a wrapper that loads the model once.

**French pronunciation of names** — add an IPA-ish hint or rephrase. Most names work out of the box.

---

## Links

- **VoxCPM2 repo**: https://github.com/OpenBMB/VoxCPM
- **Model card**: https://huggingface.co/openbmb/VoxCPM2
- **Source plugin**: https://github.com/vdk888/local-tts (same codebase)

---

## License

Apache-2.0 — Bubble Invest 2026
