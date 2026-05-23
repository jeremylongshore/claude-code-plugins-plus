#!/usr/bin/env python3
"""Local TTS via VoxCPM2 — shared skill helper.

Usage:
    python generate.py --text "Hello world" --out /tmp/hello.wav
    python generate.py --text "(warm female voice)Hi!" --out /tmp/vd.wav
    python generate.py --text "Clone me" --ref /path/to/ref.wav --out /tmp/clone.wav
    echo "piped text" | python generate.py --stdin --out /tmp/stdin.wav

Reads text via --text or --stdin. Writes a 48 kHz wav to --out.
Prints a one-line summary to stdout on success: "OK <duration>s <rtf>x <path>".
"""

import argparse
import sys
import time
from pathlib import Path


def main() -> int:
    p = argparse.ArgumentParser(description="Local TTS via VoxCPM2")
    p.add_argument("--text", help="Text to synthesize. Supports (voice description) prefix for Voice Design mode.")
    p.add_argument("--stdin", action="store_true", help="Read text from stdin instead of --text.")
    p.add_argument("--out", required=True, help="Output wav path (absolute recommended).")
    p.add_argument("--ref", help="Reference audio for voice cloning (wav, 16 kHz+).")
    p.add_argument("--prompt-wav", help="Prompt wav for ultimate cloning (pass same as --ref for max fidelity).")
    p.add_argument("--cfg", type=float, default=2.0, help="Classifier-free guidance (default 2.0).")
    p.add_argument(
        "--steps", type=int, default=10, help="Inference timesteps (default 10; higher = slower & slightly better)."
    )
    p.add_argument("--model", default="openbmb/VoxCPM2", help="Model id or local path (default openbmb/VoxCPM2).")
    p.add_argument("--quiet", action="store_true", help="Suppress progress output.")
    args = p.parse_args()

    if args.stdin:
        text = sys.stdin.read().strip()
    else:
        text = (args.text or "").strip()
    if not text:
        print("ERROR: no text provided (use --text or --stdin)", file=sys.stderr)
        return 2

    out = Path(args.out).expanduser().resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    if not args.quiet:
        print(f"[local-tts] loading {args.model}...", file=sys.stderr, flush=True)

    import soundfile as sf  # noqa: E402
    from voxcpm import VoxCPM  # noqa: E402

    t0 = time.time()
    model = VoxCPM.from_pretrained(args.model, load_denoiser=False)
    if not args.quiet:
        print(f"[local-tts] model ready in {time.time() - t0:.1f}s", file=sys.stderr, flush=True)

    kwargs = dict(text=text, cfg_value=args.cfg, inference_timesteps=args.steps)
    if args.ref:
        kwargs["reference_wav_path"] = args.ref
    if args.prompt_wav:
        kwargs["prompt_wav_path"] = args.prompt_wav

    t0 = time.time()
    wav = model.generate(**kwargs)
    dt = time.time() - t0
    sr = model.tts_model.sample_rate
    duration = len(wav) / sr
    rtf = dt / duration if duration > 0 else 0.0

    sf.write(str(out), wav, sr)
    print(f"OK {duration:.2f}s {rtf:.2f}x {out}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
