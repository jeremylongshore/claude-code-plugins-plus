---
name: local-tts
description: Generate speech from text locally using VoxCPM2 (Apache-2.0, 30 languages, voice design, voice cloning). Use when the user asks to "say" or "speak" something, wants a voiceover or narration, wants to clone a voice, or wants to generate audio from text. Free, runs locally, no API calls. Output is a 48 kHz wav file.
version: 1.0.0
author: Bubble Invest
license: Apache-2.0
user-invocable: true
allowed-tools:
  - Bash
  - Read
  - Write
---

# Local TTS (VoxCPM2)

Local, offline text-to-speech via OpenBMB VoxCPM2 (2B params, 30 languages, Voice Design, Voice Cloning). Runs on Apple Silicon via Metal (MPS). Apache-2.0, zero cost, zero cloud.

## When to use

- User asks to "say", "speak", "read out loud", "generate a voiceover", or "turn this into audio"
- User wants to clone a voice from a reference clip
- User wants to create a character voice from a description
- You need to attach a voice message to a Telegram reply
- Any narration, voiceover, or TTS task

Do **not** use for real-time voice agents — the RTF on Apple Silicon is ~2.3x (slower than realtime). Good for batch generation, not live streaming.

## Supported languages (30)

Arabic, Burmese, Chinese (+ dialects), Danish, Dutch, English, Finnish, French, German, Greek, Hebrew, Hindi, Indonesian, Italian, Japanese, Khmer, Korean, Lao, Malay, Norwegian, Polish, Portuguese, Russian, Spanish, Swahili, Swedish, Tagalog, Thai, Turkish, Vietnamese. No language tag needed — just pass the text.

## Setup

On first use, run the setup script to create the Python environment:

```bash
bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh
```

This creates a venv at `~/.local-tts/venv` and installs dependencies. Takes ~2 minutes. First generation will additionally download ~10 GB model weights (one-time).

You can customize the venv location with `LOCAL_TTS_VENV` and the Python binary with `LOCAL_TTS_PYTHON` environment variables.

## Invocation

```bash
VENV=~/.local-tts/venv
SCRIPT=${CLAUDE_PLUGIN_ROOT}/scripts/generate.py
OUT=/tmp/tts_$(date +%s).wav

"$VENV/bin/python" "$SCRIPT" \
  --text "Your text here." \
  --out "$OUT"
```

Script prints `OK <duration>s <rtf>x <path>` on success. The wav is 48 kHz.

## Three modes

### 1. Default voice

```bash
"$VENV/bin/python" "$SCRIPT" --text "Hello world." --out /tmp/hi.wav
```

### 2. Voice Design (no reference audio)

Describe the voice in parentheses at the start of the text. The parenthetical is stripped from the spoken audio and used as style conditioning.

```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "(A warm, calm female voice, mid-30s, American accent)Welcome back." \
  --out /tmp/design.wav
```

Examples of descriptions that work:
- `(young woman, gentle and sweet voice)`
- `(older man, deep resonant voice, slow pace)`
- `(cheerful, energetic, fast-talking)`
- `(voix feminine chaleureuse, ton pose)` — descriptions in any supported language are fine

### 3. Voice Cloning

Provide a short (3-10s) reference clip. Clones timbre, accent, emotional tone. You can still layer style guidance with a `(description)` prefix.

```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "This is the cloned voice speaking." \
  --ref /path/to/reference.wav \
  --out /tmp/clone.wav
```

Ultimate cloning (reference + prompt = max fidelity, reproduces micro-level vocal nuances):

```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "Highest fidelity clone." \
  --ref /path/to/ref.wav \
  --prompt-wav /path/to/ref.wav \
  --prompt-text "The exact transcript of what is said in ref.wav" \
  --out /tmp/ultimate.wav
```

## Script options

| Flag | Purpose |
|---|---|
| `--text STR` | Text to synthesize. |
| `--stdin` | Read text from stdin (use instead of `--text` for long / piped input). |
| `--out PATH` | Output wav path. **Required.** |
| `--ref PATH` | Reference audio for cloning. |
| `--prompt-wav PATH` | Prompt wav for ultimate cloning. |
| `--prompt-text STR` | Transcript of the prompt wav (required with `--prompt-wav`). |
| `--cfg FLOAT` | Classifier-free guidance (default 2.0). |
| `--steps INT` | Diffusion inference steps (default 10). Higher = slower, marginally better. |
| `--model ID` | Model id or local path (default `openbmb/VoxCPM2`). |
| `--quiet` | Suppress loading messages. |

## Performance (Apple Silicon, MPS, bfloat16)

- **First load**: ~340s (downloads ~10 GB weights to `~/.cache/huggingface/`)
- **Subsequent loads**: ~25s (cache warm)
- **Generation**: RTF ~2.3x (10s audio = ~23s compute)

## Common patterns

### Generate and attach to a Telegram reply

```bash
VENV=~/.local-tts/venv
SCRIPT=${CLAUDE_PLUGIN_ROOT}/scripts/generate.py
OUT=/tmp/msg_$(date +%s).wav
"$VENV/bin/python" "$SCRIPT" --text "Your message" --out "$OUT"
# then use the telegram reply tool with files=["$OUT"]
```

### Long text via stdin

```bash
cat article.txt | "$VENV/bin/python" "$SCRIPT" --stdin --out /tmp/article.wav
```

### Clone + style overlay

```bash
"$VENV/bin/python" "$SCRIPT" \
  --text "(enthusiastic, happy, smiling)Great news everyone!" \
  --ref /path/to/voice-sample.mp3 \
  --out /tmp/happy_clone.wav
```

## Troubleshooting

- **"ModuleNotFoundError: voxcpm"** — Run `bash ${CLAUDE_PLUGIN_ROOT}/scripts/setup.sh` to create the environment.
- **"No such file: VoxCPM2 weights"** — First run downloads the model (~10 GB). Requires internet.
- **Slow first call** — Model load is ~25s after cache warmup. Each invocation loads the model fresh.
- **prompt_wav_path error** — When using `--prompt-wav`, you must also provide `--prompt-text` with the transcript.

## References

- VoxCPM2 repo: https://github.com/OpenBMB/VoxCPM
- Model card: https://huggingface.co/openbmb/VoxCPM2
- License: Apache-2.0 (commercial use allowed)
