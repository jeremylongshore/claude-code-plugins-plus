---
name: local-tts
description: 'Generate speech locally from text using VoxCPM2 (2B params, Apache-2.0).
  30 languages,

  voice design (describe a voice), voice cloning (from 3-10s reference). Runs 100%

  offline on Apple Silicon via Metal (MPS). Zero API calls, zero cost.

  Use when user asks to "say" or "speak" something, wants a voiceover, wants to clone

  a voice, or wants to generate audio from text. Trigger phrases: "say this",

  "read out loud", "clone my voice", "generate voiceover", "text to speech", "TTS".

  '
allowed-tools: Read, Bash(python3:*), Bash(file:*), Bash(ls:*)
version: 1.0.0
author: Bubble Invest <contact@bubbleinvest.com>
license: Apache-2.0
tags:
- tts
- voice
- audio
- voice-cloning
- voice-design
- offline
- apple-silicon
- narration
user-invocable: true
compatibility: Designed for Claude Code
---
# Local TTS — Offline Text-to-Speech

Generate speech from text using VoxCPM2 locally. 30 languages, voice design, voice cloning. Runs on Apple Silicon via Metal. Apache-2.0, zero cost.

## Overview

This skill wraps VoxCPM2 (OpenBMB, Apache-2.0) for local text-to-speech. It supports three modes:

1. **Default voice** — just feed text, get natural speech in 30 languages (auto-detected)
2. **Voice Design** — describe the voice in a parenthetical prefix, get matching speech
3. **Voice Cloning** — provide a 3-10s reference clip, the output mimics the voice

All processing happens on-device. No API keys. No network calls after the initial model download. Output is 48 kHz WAV ready for any use (Telegram voice messages, podcasts, video narration).

## Prerequisites

- Python 3.10+ (3.12 recommended)
- macOS with Apple Silicon preferred (M1/M2/M3/M4). Linux with CUDA also works.
- ~10 GB disk space for model weights (downloaded once on first use)
- ~16 GB RAM recommended

The skill expects a Python venv at `~/.local-tts/venv` with the `voxcpm` package installed. If missing, create it:

```bash
mkdir -p ~/.local-tts
python3.12 -m venv ~/.local-tts/venv
~/.local-tts/venv/bin/pip install --upgrade pip voxcpm
```

First generation downloads ~10 GB of model weights to `~/.cache/huggingface/`. Subsequent runs load the cache in ~30s.

## Instructions

### Step 1 — Verify the environment

```bash
ls ~/.local-tts/venv/bin/python && echo "venv OK" || echo "Run setup first"
```

If the venv is missing, guide the user through the setup commands above.

### Step 2 — Generate the speech

Use the `generate.py` script bundled in this plugin. The entry point:

```bash
VENV=~/.local-tts/venv
SCRIPT=${CLAUDE_PLUGIN_ROOT}/scripts/generate.py
OUT=/tmp/tts_$(date +%s).wav
```

**Default voice (auto-detected language)**:
```bash
"$VENV/bin/python" "$SCRIPT" --text "Your text here." --out "$OUT"
```

**Voice Design** — describe the voice in parentheses at the start. The parenthetical is stripped from the spoken audio.
```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "(warm female voice, mid-30s, American accent)Welcome back." \
  --out "$OUT"
```

Description examples that work:
- `(young woman, gentle and sweet voice)`
- `(older man, deep resonant voice, slow pace)`
- `(cheerful, energetic, fast-talking)`
- `(voix féminine chaleureuse, ton posé)` — descriptions in any supported language

**Voice Cloning** — provide a reference clip (3-10s). Clones timbre, accent, emotional tone.
```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "This is the cloned voice speaking." \
  --ref /path/to/reference.wav \
  --out "$OUT"
```

**Ultimate Cloning** — reference + prompt for maximum fidelity (reproduces micro-level vocal nuances):
```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "Highest fidelity clone." \
  --ref /path/to/ref.wav \
  --prompt-wav /path/to/ref.wav \
  --out "$OUT"
```

**Long text via stdin** (for articles, scripts):
```bash
cat /path/to/article.txt | "$VENV/bin/python" "$SCRIPT" --stdin --out "$OUT"
```

### Step 3 — Verify and hand off

```bash
file "$OUT"   # Should show: "RIFF ... WAVE audio, Microsoft PCM, 16 bit, mono 48000 Hz"
ls -lh "$OUT" # Check size is reasonable
```

The script prints `OK <duration>s <rtf>x <path>` on success.

## Output

- **Format**: 48 kHz mono WAV, 16-bit PCM
- **Location**: whatever `--out` path specified (typically `/tmp/tts_*.wav`)
- **Size**: roughly 100 KB per second of audio
- **Usage**: ready to attach to Telegram, embed in video, use as voiceover

## Script options

| Flag | Purpose |
|------|---------|
| `--text STR` | Text to synthesize |
| `--stdin` | Read text from stdin (for long input) |
| `--out PATH` | Output WAV path (required) |
| `--ref PATH` | Reference audio for cloning |
| `--prompt-wav PATH` | Prompt wav for ultimate cloning |
| `--cfg FLOAT` | Classifier-free guidance (default 2.0) |
| `--steps INT` | Diffusion steps (default 10) |
| `--model ID` | Model id (default `openbmb/VoxCPM2`) |
| `--quiet` | Suppress loading messages |

## Supported languages (30)

Arabic, Burmese, Chinese (+ dialects), Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Indonesian, Italian, Japanese, Khmer, Korean, Lao, Malay, Norwegian, Polish, Portuguese, Russian, Spanish, Swahili, Swedish, Tagalog, Thai, Turkish, Vietnamese.

No language tag needed — VoxCPM auto-detects from the text.

## Error Handling

- **`ModuleNotFoundError: voxcpm`** — venv missing. Run the setup commands from Prerequisites.
- **`No such file: VoxCPM2 weights`** — HuggingFace cache missing. First run will download (needs network, ~10 GB).
- **Slow first call (~5 min)** — normal. Model download + initial load. Subsequent runs ~30s.
- **French pronunciation edge cases** — add an IPA-ish hint or rephrase. Most names and proper nouns work out of the box.

## Performance

On Apple M4 with MPS + bfloat16:
- First load: ~340s (downloads weights)
- Subsequent loads: ~30s
- Generation: ~2.3× realtime (10s audio ≈ 23s compute)

Not suitable for real-time streaming. Good for batch generation, voiceovers, podcasts, voice messages.

## Examples

**Example 1: Voice message for Telegram**
```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "Hey, quick voice note about our meeting tomorrow." \
  --out /tmp/voice_msg.wav
```

**Example 2: Clone a voice from an MP3**
```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "Bonjour, c'est une voix clonée localement." \
  --ref ~/my_voice_sample.mp3 \
  --out /tmp/cloned.wav
```

**Example 3: Designed voice for narration**
```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "(deep narrator voice, dramatic, slow pace)In a world where AI runs locally..." \
  --out /tmp/narration.wav
```

## Resources

- VoxCPM2 source: https://github.com/OpenBMB/VoxCPM
- Model card: https://huggingface.co/openbmb/VoxCPM2
- Script source (same as bundled): https://github.com/vdk888/local-tts/blob/main/scripts/generate.py
- License: Apache-2.0
