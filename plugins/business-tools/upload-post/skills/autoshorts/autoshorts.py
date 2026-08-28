#!/usr/bin/env python3
"""autoshorts CLI — viral clip pipeline.

Subcommands:
    pick                  pick the next video to process from INPUT_FOLDER
    transcribe <video>    Whisper transcription with word timestamps
    analyze <video>       Gemini 3 Flash multimodal clip selection
    extract <video>       FFmpeg cut a single clip
    hook <video>          FFmpeg hook-text overlay
    preview <video>       extract a single frame for visual QA by the agent running the skill
    publish <video>       upload to TikTok/Instagram/YouTube via Upload-Post
    mark-processed <video>
    list-processed
    learn                 weekly: pull analytics, find winners/losers, refresh HOT.md
    reflect               post-publish: extract qualitative patterns from approved vs rejected hooks
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent
load_dotenv(ROOT / ".env")

INPUT_FOLDER = Path(os.getenv("INPUT_FOLDER", ROOT / "input")).expanduser()
OUTPUT_FOLDER = Path(os.getenv("OUTPUT_FOLDER", ROOT / "output")).expanduser()
STATE_FOLDER = ROOT / "state"
STATE_FILE = STATE_FOLDER / "processed.json"

LEARNINGS_FOLDER = ROOT / "learnings"
HOT_FILE = LEARNINGS_FOLDER / "HOT.md"
POST_HISTORY = LEARNINGS_FOLDER / "post-history.jsonl"
CANDIDATE_HISTORY = LEARNINGS_FOLDER / "candidate-history.jsonl"
METRICS_FILE = LEARNINGS_FOLDER / "metrics.jsonl"
RUNS_FOLDER = LEARNINGS_FOLDER / "runs"

VIDEO_EXTS = {".mp4", ".mov", ".mkv", ".m4v", ".webm"}
GEMINI_MODEL = "gemini-3-flash-preview"
UPLOAD_POST_BASE = "https://api.upload-post.com/api"


def append_jsonl(path: Path, record: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("a", encoding="utf-8") as f:
        f.write(json.dumps(record, ensure_ascii=False) + "\n")


def read_jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    out = []
    with path.open(encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                out.append(json.loads(line))
    return out


# ---------- helpers ----------

def sha256_of(path: Path) -> str:
    h = hashlib.sha256()
    with path.open("rb") as f:
        for chunk in iter(lambda: f.read(1024 * 1024), b""):
            h.update(chunk)
    return h.hexdigest()


def load_state() -> dict:
    if not STATE_FILE.exists():
        return {"cycle_started_at": None, "processed": []}
    state = json.loads(STATE_FILE.read_text())
    state.setdefault("cycle_started_at", None)
    state.setdefault("processed", [])
    # Backfill schema: old records may only have processed_at, not last_processed_at.
    for rec in state["processed"]:
        if "last_processed_at" not in rec:
            rec["last_processed_at"] = rec.get("processed_at")
        if "first_processed_at" not in rec:
            rec["first_processed_at"] = rec.get("processed_at")
        if "cycles_count" not in rec:
            rec["cycles_count"] = 1
    return state


def save_state(state: dict) -> None:
    STATE_FOLDER.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2, ensure_ascii=False))


def video_slug(video: Path) -> str:
    return video.stem.replace(" ", "_")


def video_output_dir(video: Path) -> Path:
    d = OUTPUT_FOLDER / video_slug(video)
    d.mkdir(parents=True, exist_ok=True)
    return d


def run_ffmpeg(args: list[str]) -> None:
    cmd = ["ffmpeg", "-y", "-hide_banner", "-loglevel", "error", *args]
    res = subprocess.run(cmd, capture_output=True, text=True)
    if res.returncode != 0:
        sys.stderr.write(res.stderr)
        raise SystemExit(f"ffmpeg failed: {' '.join(cmd)}")


def ffprobe_duration(video: Path) -> float:
    res = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-show_entries", "format=duration",
            "-of", "default=noprint_wrappers=1:nokey=1",
            str(video),
        ],
        capture_output=True, text=True, check=True,
    )
    return float(res.stdout.strip())


def ffprobe_dimensions(video: Path) -> tuple[int, int]:
    res = subprocess.run(
        [
            "ffprobe", "-v", "error",
            "-select_streams", "v:0",
            "-show_entries", "stream=width,height",
            "-of", "csv=p=0:s=x",
            str(video),
        ],
        capture_output=True, text=True, check=True,
    )
    w, h = res.stdout.strip().split("x")
    return int(w), int(h)


# ---------- pick ----------

def cmd_pick(_: argparse.Namespace) -> None:
    """Print the path of the next video to process.

    Cycle strategy: each video is picked at most once per cycle. When every
    video in INPUT_FOLDER has been processed in the current cycle, a new cycle
    starts and they all become available again. Newest unprocessed-this-cycle
    wins, so freshly added videos still jump the queue.
    """
    if not INPUT_FOLDER.exists():
        raise SystemExit(f"INPUT_FOLDER not found: {INPUT_FOLDER}")

    candidates = [
        p for p in INPUT_FOLDER.iterdir()
        if p.is_file() and p.suffix.lower() in VIDEO_EXTS
    ]
    if not candidates:
        raise SystemExit(f"no videos in {INPUT_FOLDER}")

    state = load_state()
    cycle_start = state.get("cycle_started_at")
    by_hash = {rec["hash"]: rec for rec in state["processed"]}

    def is_available(p: Path) -> bool:
        rec = by_hash.get(sha256_of(p))
        if rec is None:
            return True  # never processed
        last = rec.get("last_processed_at")
        if cycle_start is None or last is None:
            return False  # processed before cycle tracking existed → treat as taken
        return last < cycle_start

    available = [p for p in candidates if is_available(p)]
    new_cycle = False

    if not available:
        # All videos processed in current cycle → start a new one.
        state["cycle_started_at"] = datetime.now().isoformat(timespec="seconds")
        save_state(state)
        cycle_start = state["cycle_started_at"]
        available = list(candidates)
        new_cycle = True

    available.sort(key=lambda p: p.stat().st_mtime, reverse=True)
    chosen = available[0]
    rec = by_hash.get(sha256_of(chosen)) or {}

    print(json.dumps({
        "path": str(chosen),
        "name": chosen.name,
        "size_mb": round(chosen.stat().st_size / 1_000_000, 1),
        "mtime": datetime.fromtimestamp(chosen.stat().st_mtime).isoformat(),
        "duration_s": round(ffprobe_duration(chosen), 1),
        "previous_cycles_completed": rec.get("cycles_count", 0),
        "remaining_in_cycle": len(available) - 1,
        "cycle_started_at": cycle_start,
        "new_cycle_started": new_cycle,
    }, indent=2))


# ---------- transcribe ----------

def cmd_transcribe(args: argparse.Namespace) -> None:
    from faster_whisper import WhisperModel

    video = Path(args.video).resolve()
    out_dir = video_output_dir(video)
    out_path = Path(args.output) if args.output else out_dir / "transcript.json"

    model_name = args.model or os.getenv("WHISPER_MODEL", "medium")
    print(f"[transcribe] loading whisper {model_name}…", file=sys.stderr)
    model = WhisperModel(model_name, device="cpu", compute_type="int8")

    print(f"[transcribe] running on {video.name}…", file=sys.stderr)
    segments_iter, info = model.transcribe(
        str(video),
        word_timestamps=True,
        vad_filter=True,
    )

    segments = []
    for seg in segments_iter:
        words = []
        for w in (seg.words or []):
            words.append({"s": round(w.start, 3), "e": round(w.end, 3), "t": w.word.strip()})
        segments.append({
            "start": round(seg.start, 3),
            "end": round(seg.end, 3),
            "text": seg.text.strip(),
            "words": words,
        })

    payload = {
        "video": video.name,
        "language": info.language,
        "language_probability": round(info.language_probability, 3),
        "duration": round(info.duration, 3),
        "segments": segments,
    }
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"[transcribe] {len(segments)} segments → {out_path}", file=sys.stderr)
    print(str(out_path))


# ---------- analyze ----------

ANALYZE_PROMPT = """You are an expert short-form viral video editor. You are given:
1. A long video file.
2. A transcript with sentence-level segments and per-word timestamps.

TASK
Find ALL moments suitable for TikTok / Instagram Reels / YouTube Shorts. Be generous — return every viable candidate, do not artificially limit. Quality over filler, but do not stop at 3 if there are 8 good ones.

REQUIREMENTS
- Duration 20-60 seconds.
- Self-contained: makes sense without prior context. Avoid moments that reference unseen context ("as I said earlier", "going back to that").
- Strong hook in the first 2 seconds: surprise, controversy, emotional peak, punchline, contrarian take, actionable tip, story climax.
- `start` MUST equal an existing word's start time in the transcript and `end` MUST equal an existing word's end time. Do NOT invent timestamps. Snap to word boundaries.
- Use multimodal cues from the video itself: laughter, gestures, scene changes, energy peaks, reactions.
- If two candidates overlap, return only the stronger one.

FOR EACH CLIP RETURN
- id (sequential int starting at 1)
- start (float seconds, snapped to a word's start_time)
- end (float seconds, snapped to a word's end_time)
- hook_text (max 8 words, attention-grabbing, SAME LANGUAGE as the video)
- reason (1 short sentence on why this is viral)
- viral_score (integer 1-10, 10 = certain hit)

OUTPUT
Return STRICT JSON only, no commentary, no markdown:
{"language": "<iso lang>", "clips": [{"id": 1, "start": 12.34, "end": 45.67, "hook_text": "...", "reason": "...", "viral_score": 8}, ...]}
"""

PRIORS_HEADER = """
PRIOR LEARNINGS FROM THIS CREATOR'S PAST CLIPS
The patterns below are derived from real engagement data on this creator's previously published clips. Apply them when selecting moments AND when writing hooks. They override the generic guidance above when they conflict.

"""

PRIORS_FOOTER = "\n\n--- end of prior learnings ---\n\nTRANSCRIPT\n"
TRANSCRIPT_HEADER = "\nTRANSCRIPT\n"


def cmd_analyze(args: argparse.Namespace) -> None:
    from google import genai
    from google.genai import types

    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise SystemExit("GEMINI_API_KEY missing in .env")

    video = Path(args.video).resolve()
    out_dir = video_output_dir(video)
    transcript_path = Path(args.transcript) if args.transcript else out_dir / "transcript.json"
    out_path = Path(args.output) if args.output else out_dir / "clips.json"

    if not transcript_path.exists():
        raise SystemExit(f"transcript not found: {transcript_path}")

    transcript = transcript_path.read_text()

    # Inject prior learnings if HOT.md exists with content.
    priors_block = ""
    if HOT_FILE.exists():
        hot = HOT_FILE.read_text().strip()
        if hot:
            priors_block = PRIORS_HEADER + hot + PRIORS_FOOTER
            print(f"[analyze] injecting {len(hot)} chars of priors from HOT.md", file=sys.stderr)

    if priors_block:
        prompt = ANALYZE_PROMPT + priors_block + transcript
    else:
        prompt = ANALYZE_PROMPT + TRANSCRIPT_HEADER + transcript

    client = genai.Client(api_key=api_key)
    print(f"[analyze] uploading {video.name} to Gemini Files API…", file=sys.stderr)
    uploaded = client.files.upload(file=str(video))

    while uploaded.state.name == "PROCESSING":
        time.sleep(3)
        uploaded = client.files.get(name=uploaded.name)
        print(f"[analyze] file state: {uploaded.state.name}", file=sys.stderr)

    if uploaded.state.name != "ACTIVE":
        raise SystemExit(f"video upload failed: {uploaded.state.name}")

    print(f"[analyze] calling {GEMINI_MODEL}…", file=sys.stderr)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[uploaded, prompt],
        config=types.GenerateContentConfig(
            response_mime_type="application/json",
        ),
    )

    raw = response.text.strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        out_path.with_suffix(".raw.txt").write_text(raw)
        raise SystemExit(f"Gemini returned non-JSON, dumped to {out_path.with_suffix('.raw.txt')}")

    out_path.write_text(json.dumps(data, indent=2, ensure_ascii=False))
    n = len(data.get("clips", []))
    print(f"[analyze] {n} clip candidates → {out_path}", file=sys.stderr)

    # Log every candidate to candidate-history so reflect can compare approved vs rejected.
    now_iso = datetime.now().isoformat(timespec="seconds")
    for c in data.get("clips", []):
        append_jsonl(CANDIDATE_HISTORY, {
            "video_source": video.name,
            "analyzed_at": now_iso,
            "clip_id": c.get("id"),
            "start": c.get("start"),
            "end": c.get("end"),
            "duration_s": (c.get("end", 0) - c.get("start", 0)) if c.get("end") and c.get("start") is not None else None,
            "hook_text": c.get("hook_text"),
            "viral_score_gemini": c.get("viral_score"),
            "reason_gemini": c.get("reason"),
            "language": data.get("language"),
            "had_priors": bool(priors_block),
        })

    print(str(out_path))


# ---------- extract ----------

def cmd_extract(args: argparse.Namespace) -> None:
    video = Path(args.video).resolve()
    start = float(args.start)
    end = float(args.end)
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    # Re-encode for frame-accurate cuts (copy mode would snap to keyframes).
    run_ffmpeg([
        "-ss", f"{start:.3f}",
        "-to", f"{end:.3f}",
        "-i", str(video),
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "aac", "-b:a", "160k",
        "-movflags", "+faststart",
        str(out),
    ])
    print(str(out))


# ---------- hook overlay ----------

DEFAULT_FONT = "/System/Library/Fonts/Supplemental/Impact.ttf"


def render_hook_png(text: str, png_path: Path, video_w: int, font_path: str,
                    font_size: int = 72, max_ratio: float = 0.85) -> None:
    """Render hook text to a transparent PNG sized to the video width.

    Auto-wraps long text. Each line gets a semi-opaque black "pill" behind it
    (TikTok/Instagram style) plus white fill + black stroke on the text itself,
    so the hook stays legible on any background — including pure black or
    pure white frames where stroke alone would fail.

    Avoids ffmpeg's drawtext filter (which requires libfreetype, often missing).
    """
    from PIL import Image, ImageDraw, ImageFont

    font = ImageFont.truetype(font_path, font_size)
    max_w = int(video_w * max_ratio)

    # Greedy word wrap on the available width minus the pill horizontal padding.
    plate_pad_x = 26
    plate_pad_y = 10
    line_gap = 10  # vertical gap between consecutive pills
    text_max_w = max_w - plate_pad_x * 2

    words = text.split()
    lines: list[str] = []
    current: list[str] = []
    for w in words:
        candidate = " ".join(current + [w])
        bbox = font.getbbox(candidate)
        if (bbox[2] - bbox[0]) > text_max_w and current:
            lines.append(" ".join(current))
            current = [w]
        else:
            current.append(w)
    if current:
        lines.append(" ".join(current))

    # Use font ascent/descent for stable line geometry.
    ascent, descent = font.getmetrics()
    line_h = ascent + descent
    pill_h = line_h + plate_pad_y * 2
    canvas_pad = 12  # outer padding so stroke isn't clipped
    total_h = pill_h * len(lines) + line_gap * (len(lines) - 1) + canvas_pad * 2

    img = Image.new("RGBA", (video_w, total_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    plate_color = (0, 0, 0, 200)  # ~78% opacity black

    for i, line in enumerate(lines):
        bbox = font.getbbox(line)
        line_w = bbox[2] - bbox[0]

        text_x = (video_w - line_w) // 2
        pill_top = canvas_pad + i * (pill_h + line_gap)
        text_y = pill_top + plate_pad_y

        plate_x0 = text_x - plate_pad_x
        plate_y0 = pill_top
        plate_x1 = text_x + line_w + plate_pad_x
        plate_y1 = pill_top + pill_h
        radius = min(24, pill_h // 3)
        draw.rounded_rectangle(
            (plate_x0, plate_y0, plate_x1, plate_y1),
            radius=radius, fill=plate_color,
        )

        draw.text(
            (text_x, text_y), line, font=font,
            fill=(255, 255, 255, 255),
            stroke_width=3, stroke_fill=(0, 0, 0, 255),
        )

    img.save(png_path, "PNG")


def cmd_hook(args: argparse.Namespace) -> None:
    video = Path(args.video).resolve()
    out = Path(args.output).resolve()
    out.parent.mkdir(parents=True, exist_ok=True)

    font = args.font or DEFAULT_FONT
    if not Path(font).exists():
        raise SystemExit(f"font not found: {font}")

    duration = float(args.duration)
    video_w, video_h = ffprobe_dimensions(video)

    png_path = out.with_suffix(".hook.png")
    render_hook_png(args.text, png_path, video_w, font)

    overlay = (
        f"[0:v][1:v]overlay=0:H*0.08:enable='lte(t,{duration})'"
    )

    run_ffmpeg([
        "-i", str(video),
        "-i", str(png_path),
        "-filter_complex", overlay,
        "-c:v", "libx264", "-preset", "fast", "-crf", "20",
        "-c:a", "copy",
        "-movflags", "+faststart",
        str(out),
    ])
    png_path.unlink(missing_ok=True)
    print(str(out))


# ---------- preview (frame extraction for agent-side QA) ----------

def cmd_preview(args: argparse.Namespace) -> None:
    """Extract one frame from a final clip so the agent running the skill
    (Claude / openclaw) can view it with their multimodal vision and decide
    whether the hook overlay looks correct. We do NOT call Gemini here —
    the agent reviews the PNG directly.
    """
    clip = Path(args.video).resolve()
    if not clip.exists():
        raise SystemExit(f"clip not found: {clip}")

    if args.output:
        out = Path(args.output).resolve()
    else:
        out = clip.with_name(f"preview_{clip.stem}.png")
    out.parent.mkdir(parents=True, exist_ok=True)

    run_ffmpeg([
        "-ss", f"{args.at_time:.3f}",
        "-i", str(clip),
        "-frames:v", "1",
        "-q:v", "2",
        str(out),
    ])
    print(str(out))


# ---------- publish ----------

def cmd_publish(args: argparse.Namespace) -> None:
    import requests

    api_key = os.getenv("UPLOAD_POST_API_KEY")
    profile = os.getenv("UPLOAD_POST_PROFILE")
    if not api_key or not profile:
        raise SystemExit("UPLOAD_POST_API_KEY or UPLOAD_POST_PROFILE missing in .env")

    video = Path(args.video).resolve()
    if not video.exists():
        raise SystemExit(f"video not found: {video}")

    platforms = [p.strip() for p in args.platforms.split(",") if p.strip()]
    timezone = args.timezone or os.getenv("TIMEZONE", "Europe/Madrid")

    data = [
        ("user", profile),
        ("title", args.title or ""),
        ("description", args.description or ""),
    ]
    for p in platforms:
        data.append(("platform[]", p))
    if args.tiktok_title:
        data.append(("tiktok_title", args.tiktok_title))
    if args.instagram_title:
        data.append(("instagram_title", args.instagram_title))
    if args.youtube_title:
        data.append(("youtube_title", args.youtube_title))
    if "tiktok" in platforms:
        post_mode = "MEDIA_UPLOAD" if args.tiktok_mode == "draft" else "DIRECT_POST"
        data.append(("post_mode", post_mode))
        if args.tiktok_privacy:
            data.append(("privacy_level", args.tiktok_privacy))
    if args.schedule:
        data.append(("scheduled_date", args.schedule))
        data.append(("timezone", timezone))
    elif args.add_to_queue:
        data.append(("add_to_queue", "true"))

    if args.dry_run:
        print(json.dumps({
            "DRY_RUN": True,
            "endpoint": f"{UPLOAD_POST_BASE}/upload",
            "video": str(video),
            "fields": [(k, v) for k, v in data],
        }, indent=2, ensure_ascii=False))
        return

    with video.open("rb") as fh:
        files = {"video": (video.name, fh, "video/mp4")}
        res = requests.post(
            f"{UPLOAD_POST_BASE}/upload",
            headers={"Authorization": f"Apikey {api_key}"},
            data=data,
            files=files,
            timeout=600,
        )

    if res.status_code >= 400:
        sys.stderr.write(res.text + "\n")
        raise SystemExit(f"upload-post HTTP {res.status_code}")

    body = res.json()

    # Append to post-history.jsonl so cmd_learn can correlate metrics → clip context.
    request_id = body.get("request_id")
    if request_id:
        append_jsonl(POST_HISTORY, {
            "request_id": request_id,
            "job_id": body.get("job_id"),
            "video_source": args.video_source,
            "clip_id": args.clip_id,
            "hook_text": args.hook_text,
            "viral_score_gemini": args.viral_score,
            "reason_gemini": args.reason,
            "duration_s": ffprobe_duration(video) if video.exists() else None,
            "platforms": platforms,
            "tiktok_title": args.tiktok_title,
            "instagram_title": args.instagram_title,
            "youtube_title": args.youtube_title,
            "general_title": args.title,
            "tiktok_mode": args.tiktok_mode if "tiktok" in platforms else None,
            "scheduled_date": args.schedule,
            "published_at": datetime.now().isoformat(timespec="seconds"),
            "clip_file": str(video),
        })

    print(json.dumps(body, indent=2, ensure_ascii=False))


# ---------- state ----------

def cmd_mark_processed(args: argparse.Namespace) -> None:
    video = Path(args.video).resolve()
    state = load_state()
    digest = sha256_of(video)
    now = datetime.now().isoformat(timespec="seconds")

    if state.get("cycle_started_at") is None:
        state["cycle_started_at"] = now

    existing = next((r for r in state["processed"] if r["hash"] == digest), None)
    if existing:
        existing["last_processed_at"] = now
        existing["cycles_count"] = existing.get("cycles_count", 1) + 1
        existing.setdefault("history", []).append({
            "processed_at": now,
            "clips_generated": args.clips_generated,
            "clips_published": args.clips_published,
        })
        existing["clips_generated"] = args.clips_generated
        existing["clips_published"] = args.clips_published
        cycle_n = existing["cycles_count"]
    else:
        rec = {
            "path": str(video),
            "name": video.name,
            "hash": digest,
            "first_processed_at": now,
            "last_processed_at": now,
            "cycles_count": 1,
            "clips_generated": args.clips_generated,
            "clips_published": args.clips_published,
            "history": [{
                "processed_at": now,
                "clips_generated": args.clips_generated,
                "clips_published": args.clips_published,
            }],
        }
        state["processed"].append(rec)
        cycle_n = 1
    save_state(state)
    print(f"marked: {video.name} (cycle #{cycle_n})")


def cmd_list_processed(_: argparse.Namespace) -> None:
    state = load_state()
    print(json.dumps(state, indent=2, ensure_ascii=False))


# ---------- learn ----------

LEARN_META_PROMPT = """You are a senior short-form content strategist. You have access to engagement data from this creator's previously published clips.

Below you will see:
1. The CURRENT HOT.md (or empty if none yet) — the patterns we currently believe in.
2. A list of WINNERS — clips that performed in the top 20% by composite score (0.6·views + 0.4·engagement_rate).
3. A list of LOSERS — clips that performed in the bottom 20%.

For each clip you see: the hook_text on screen, the duration, the original Gemini viral_score, the per-platform metrics, and the original reason Gemini gave for picking it.

YOUR JOB
Produce an updated HOT.md containing only patterns supported by the new evidence, merged with the existing HOT.md. Keep what is still corroborated; remove what the new data contradicts; add new patterns that show up in the winners and are absent from the losers.

CONSTRAINTS
- Maximum 80 lines of markdown.
- Each bullet is a single, actionable, falsifiable rule. Avoid platitudes ("be engaging").
- Cite sample sizes when meaningful: "(seen in 4/5 winners, 0/5 losers)".
- Do not include raw post titles or PII.
- If the evidence is weak (fewer than 5 winners or 5 losers), output the existing HOT.md with at most a single appended bullet noting "evidence still thin, X clips analyzed so far".
- Write in the language that dominates the creator's hooks. If the hooks are in Spanish, write the rules in Spanish. If mixed, prefer Spanish.

OUTPUT
Return ONLY the updated HOT.md content as plain markdown. No preamble, no JSON wrapper, no closing remarks. Just the file body."""


def _post_metrics(platforms: dict) -> dict:
    """Sum views/engagement across all platforms in a post-analytics response."""
    total_views = 0
    total_engagement = 0
    per_platform = {}
    for platform, data in (platforms or {}).items():
        m = (data or {}).get("post_metrics") or {}
        views = int(m.get("views") or m.get("impressions") or m.get("reach") or 0)
        likes = int(m.get("likes") or 0)
        comments = int(m.get("comments") or 0)
        shares = int(m.get("shares") or 0)
        saves = int(m.get("saves") or 0)
        eng = likes + comments + shares + saves
        total_views += views
        total_engagement += eng
        per_platform[platform] = {
            "views": views, "likes": likes, "comments": comments,
            "shares": shares, "saves": saves, "engagement": eng,
        }
    eng_rate = total_engagement / total_views if total_views else 0.0
    return {
        "total_views": total_views,
        "total_engagement": total_engagement,
        "engagement_rate": eng_rate,
        "per_platform": per_platform,
    }


def _zscore(values: list[float]) -> list[float]:
    if not values:
        return []
    n = len(values)
    mean = sum(values) / n
    var = sum((v - mean) ** 2 for v in values) / n
    sd = var ** 0.5
    if sd == 0:
        return [0.0] * n
    return [(v - mean) / sd for v in values]


def cmd_learn(args: argparse.Namespace) -> None:
    import requests
    from google import genai
    from google.genai import types

    api_key_up = os.getenv("UPLOAD_POST_API_KEY")
    api_key_g = os.getenv("GEMINI_API_KEY")
    if not api_key_up:
        raise SystemExit("UPLOAD_POST_API_KEY missing in .env")
    if not api_key_g:
        raise SystemExit("GEMINI_API_KEY missing in .env")

    history = read_jsonl(POST_HISTORY)
    if not history:
        raise SystemExit("post-history.jsonl is empty — publish some clips first")

    now = datetime.now()
    soak_seconds = args.soak_days * 86400
    max_age_seconds = args.max_age_days * 86400
    eligible = []
    for h in history:
        try:
            pub = datetime.fromisoformat(h["published_at"])
        except (KeyError, ValueError):
            continue
        age = (now - pub).total_seconds()
        if soak_seconds <= age <= max_age_seconds:
            eligible.append(h)

    print(f"[learn] {len(eligible)} clips in soak window ({args.soak_days}–{args.max_age_days} days old)",
          file=sys.stderr)
    if not eligible:
        raise SystemExit("no clips in soak window — wait or shorten --soak-days")

    # Fetch fresh metrics per clip.
    enriched = []
    for h in eligible:
        rid = h.get("request_id")
        if not rid:
            continue
        url = f"{UPLOAD_POST_BASE}/uploadposts/post-analytics/{rid}"
        try:
            r = requests.get(url, headers={"Authorization": f"Apikey {api_key_up}"}, timeout=30)
        except requests.RequestException as e:
            print(f"[learn] {rid}: HTTP error {e}", file=sys.stderr)
            continue
        if r.status_code >= 400:
            print(f"[learn] {rid}: HTTP {r.status_code}: {r.text[:200]}", file=sys.stderr)
            continue
        body = r.json()
        snap = {
            "fetched_at": now.isoformat(timespec="seconds"),
            "request_id": rid,
            "raw": body,
        }
        append_jsonl(METRICS_FILE, snap)

        m = _post_metrics(body.get("platforms") or {})
        enriched.append({**h, "metrics": m})

    if len(enriched) < 5:
        msg = f"only {len(enriched)} clips have analytics — need ≥5 winners + ≥5 losers, retry later"
        print(f"[learn] {msg}", file=sys.stderr)
        run_path = RUNS_FOLDER / f"learn-{now.strftime('%Y-%m-%d')}.md"
        run_path.parent.mkdir(parents=True, exist_ok=True)
        run_path.write_text(f"# Learn run — {now.date()}\n\n{msg}\n")
        return

    # Composite score per clip.
    views = [c["metrics"]["total_views"] for c in enriched]
    engs = [c["metrics"]["engagement_rate"] for c in enriched]
    z_views = _zscore(views)
    z_engs = _zscore(engs)
    for i, c in enumerate(enriched):
        c["composite"] = (
            args.weight_views * z_views[i]
            + args.weight_engagement * z_engs[i]
        )

    enriched.sort(key=lambda c: c["composite"], reverse=True)
    n = len(enriched)
    top_n = max(5, int(n * args.top_pct))
    bot_n = max(5, int(n * args.bottom_pct))
    winners = enriched[:top_n]
    losers = enriched[-bot_n:]

    def render_clip(c: dict) -> str:
        m = c["metrics"]
        return json.dumps({
            "hook_text": c.get("hook_text"),
            "duration_s": c.get("duration_s"),
            "viral_score_gemini": c.get("viral_score_gemini"),
            "reason_gemini": c.get("reason_gemini"),
            "platforms": c.get("platforms"),
            "video_source": c.get("video_source"),
            "metrics": {
                "total_views": m["total_views"],
                "total_engagement": m["total_engagement"],
                "engagement_rate": round(m["engagement_rate"], 4),
                "per_platform": m["per_platform"],
            },
            "composite_score": round(c["composite"], 3),
        }, ensure_ascii=False)

    winners_text = "\n".join(render_clip(c) for c in winners)
    losers_text = "\n".join(render_clip(c) for c in losers)

    current_hot = HOT_FILE.read_text() if HOT_FILE.exists() else ""

    full_prompt = (
        LEARN_META_PROMPT
        + "\n\n## CURRENT HOT.md\n"
        + (current_hot or "(empty — first learn run)")
        + f"\n\n## WINNERS (top {len(winners)} of {n})\n"
        + winners_text
        + f"\n\n## LOSERS (bottom {len(losers)} of {n})\n"
        + losers_text
    )

    client = genai.Client(api_key=api_key_g)
    print(f"[learn] calling {GEMINI_MODEL} with {len(winners)} winners + {len(losers)} losers…",
          file=sys.stderr)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[full_prompt],
        config=types.GenerateContentConfig(
            response_mime_type="text/plain",
        ),
    )

    new_hot = response.text.strip()
    if HOT_FILE.exists():
        backup = LEARNINGS_FOLDER / f"HOT.{now.strftime('%Y%m%d-%H%M%S')}.md.bak"
        backup.write_text(HOT_FILE.read_text())
    LEARNINGS_FOLDER.mkdir(parents=True, exist_ok=True)
    HOT_FILE.write_text(new_hot + "\n")

    # Audit run.
    run_path = RUNS_FOLDER / f"learn-{now.strftime('%Y-%m-%d')}.md"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    audit = [
        f"# Learn run — {now.isoformat(timespec='seconds')}",
        "",
        f"- soak: {args.soak_days}d / max age: {args.max_age_days}d",
        f"- weights: views={args.weight_views} engagement={args.weight_engagement}",
        f"- cohort: {n} clips with analytics",
        f"- winners ({len(winners)}):",
    ]
    for w in winners:
        audit.append(f"  - score={w['composite']:.2f}  views={w['metrics']['total_views']}  "
                     f"eng_rate={w['metrics']['engagement_rate']:.4f}  hook=\"{w.get('hook_text')}\"")
    audit.append(f"- losers ({len(losers)}):")
    for l in losers:
        audit.append(f"  - score={l['composite']:.2f}  views={l['metrics']['total_views']}  "
                     f"eng_rate={l['metrics']['engagement_rate']:.4f}  hook=\"{l.get('hook_text')}\"")
    audit.append("")
    audit.append("## New HOT.md")
    audit.append("")
    audit.append(new_hot)
    run_path.write_text("\n".join(audit))
    print(f"[learn] HOT.md updated ({len(new_hot)} chars), audit → {run_path}", file=sys.stderr)


# ---------- reflect ----------

REFLECT_META_PROMPT = """You are observing how a creator manually filters AI-suggested short-form clip candidates BEFORE any engagement data exists.

You will see:
1. The candidates the system OFFERED (hook + duration + Gemini's score + reason).
2. The candidates the creator APPROVED (subset that got published).
3. The candidates the creator REJECTED (offered but not published).

YOUR JOB
Identify qualitative patterns that explain the creator's filter. Examples: "approves hooks that contain a number", "rejects hooks that ask a question", "approves clips ≤30s", "rejects topics about X".

CONSTRAINTS
- Output 3-8 short observations.
- Each observation: rule + evidence count ("approved 4/5 hooks with numbers, rejected 0/3 question-form hooks").
- Do not extrapolate to engagement — you have no metrics. This is purely about creator preference.
- Write in the dominant language of the candidate hooks.

OUTPUT
Return STRICT JSON:
{"observations": [{"rule": "...", "evidence": "..."}, ...]}
"""


def cmd_reflect(args: argparse.Namespace) -> None:
    from google import genai
    from google.genai import types

    api_key_g = os.getenv("GEMINI_API_KEY")
    if not api_key_g:
        raise SystemExit("GEMINI_API_KEY missing in .env")

    candidates = read_jsonl(CANDIDATE_HISTORY)
    posts = read_jsonl(POST_HISTORY)
    if not candidates:
        raise SystemExit("candidate-history.jsonl is empty — run analyze on at least one video first")
    if not posts:
        raise SystemExit("post-history.jsonl is empty — publish some clips first")

    cutoff = datetime.now().timestamp() - args.window_days * 86400
    recent_candidates = []
    for c in candidates:
        try:
            ts = datetime.fromisoformat(c["analyzed_at"]).timestamp()
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            recent_candidates.append(c)

    approved_keys = set()
    for p in posts:
        try:
            ts = datetime.fromisoformat(p["published_at"]).timestamp()
        except (KeyError, ValueError):
            continue
        if ts >= cutoff:
            approved_keys.add((p.get("video_source"), p.get("hook_text")))

    approved = []
    rejected = []
    for c in recent_candidates:
        key = (c.get("video_source"), c.get("hook_text"))
        if key in approved_keys:
            approved.append(c)
        else:
            rejected.append(c)

    if not approved or not rejected:
        raise SystemExit(f"need both approved and rejected candidates in window; got {len(approved)} approved, {len(rejected)} rejected")

    def short(c: dict) -> dict:
        return {
            "hook": c.get("hook_text"),
            "duration_s": c.get("duration_s"),
            "viral_score_gemini": c.get("viral_score_gemini"),
            "reason_gemini": c.get("reason_gemini"),
            "language": c.get("language"),
        }

    full_prompt = (
        REFLECT_META_PROMPT
        + "\n\n## OFFERED\n" + json.dumps([short(c) for c in recent_candidates], ensure_ascii=False, indent=2)
        + "\n\n## APPROVED\n" + json.dumps([short(c) for c in approved], ensure_ascii=False, indent=2)
        + "\n\n## REJECTED\n" + json.dumps([short(c) for c in rejected], ensure_ascii=False, indent=2)
    )

    client = genai.Client(api_key=api_key_g)
    print(f"[reflect] {len(approved)} approved + {len(rejected)} rejected, calling {GEMINI_MODEL}…",
          file=sys.stderr)
    response = client.models.generate_content(
        model=GEMINI_MODEL,
        contents=[full_prompt],
        config=types.GenerateContentConfig(response_mime_type="application/json"),
    )

    try:
        data = json.loads(response.text)
    except json.JSONDecodeError:
        raise SystemExit(f"Gemini returned non-JSON: {response.text[:300]}")

    now = datetime.now()
    run_path = RUNS_FOLDER / f"reflect-{now.strftime('%Y-%m-%d-%H%M')}.md"
    run_path.parent.mkdir(parents=True, exist_ok=True)
    lines = [
        f"# Reflect run — {now.isoformat(timespec='seconds')}",
        "",
        f"- window: last {args.window_days} days",
        f"- approved: {len(approved)} / rejected: {len(rejected)}",
        "",
        "## Observations (NOT auto-promoted to HOT.md — read and curate manually)",
        "",
    ]
    for o in data.get("observations", []):
        lines.append(f"- **{o.get('rule')}** — {o.get('evidence')}")
    run_path.write_text("\n".join(lines) + "\n")
    print(f"[reflect] {len(data.get('observations', []))} observations → {run_path}", file=sys.stderr)
    print(json.dumps(data, indent=2, ensure_ascii=False))


# ---------- argparse ----------

def build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(prog="autoshorts")
    sub = p.add_subparsers(dest="cmd", required=True)

    sub.add_parser("pick").set_defaults(func=cmd_pick)

    t = sub.add_parser("transcribe")
    t.add_argument("video")
    t.add_argument("--model", default=None)
    t.add_argument("--output", default=None)
    t.set_defaults(func=cmd_transcribe)

    a = sub.add_parser("analyze")
    a.add_argument("video")
    a.add_argument("--transcript", default=None)
    a.add_argument("--output", default=None)
    a.set_defaults(func=cmd_analyze)

    e = sub.add_parser("extract")
    e.add_argument("video")
    e.add_argument("--start", required=True)
    e.add_argument("--end", required=True)
    e.add_argument("--output", required=True)
    e.set_defaults(func=cmd_extract)

    h = sub.add_parser("hook")
    h.add_argument("video")
    h.add_argument("--text", required=True)
    h.add_argument("--duration", default="3")
    h.add_argument("--font", default=None)
    h.add_argument("--output", required=True)
    h.set_defaults(func=cmd_hook)

    pv = sub.add_parser("preview", help="extract a single frame so the agent can visually QA the hook")
    pv.add_argument("video", help="path to clip_<ID>_final.mp4")
    pv.add_argument("--at-time", type=float, default=1.0,
                    help="timestamp (s) within the hook window; default 1.0 (mid-hook)")
    pv.add_argument("--output", default=None,
                    help="override output path; default: preview_<clip_stem>.png next to the clip")
    pv.set_defaults(func=cmd_preview)

    pub = sub.add_parser("publish")
    pub.add_argument("video")
    pub.add_argument("--platforms", required=True, help="comma-separated: tiktok,instagram,youtube")
    pub.add_argument("--title", default="")
    pub.add_argument("--description", default="")
    pub.add_argument("--tiktok-title", default=None)
    pub.add_argument("--instagram-title", default=None)
    pub.add_argument("--youtube-title", default=None)
    pub.add_argument("--schedule", default=None, help="ISO-8601 like 2026-05-01T10:00:00")
    pub.add_argument("--timezone", default=None)
    pub.add_argument("--add-to-queue", action="store_true")
    pub.add_argument("--tiktok-mode", choices=["draft", "direct"], default="draft",
                     help="draft → MEDIA_UPLOAD (lands in TikTok inbox), direct → DIRECT_POST")
    pub.add_argument("--tiktok-privacy", default="PUBLIC_TO_EVERYONE",
                     help="PUBLIC_TO_EVERYONE | MUTUAL_FOLLOW_FRIENDS | FOLLOWER_OF_CREATOR | SELF_ONLY")
    pub.add_argument("--dry-run", action="store_true")
    pub.add_argument("--clip-id", type=int, default=None,
                     help="for learning loop: the id from clips.json")
    pub.add_argument("--hook-text", default=None,
                     help="for learning loop: the on-screen hook overlay text")
    pub.add_argument("--viral-score", type=int, default=None,
                     help="for learning loop: Gemini's viral_score 1-10")
    pub.add_argument("--reason", default=None,
                     help="for learning loop: Gemini's reason explaining why this clip is viral")
    pub.add_argument("--video-source", default=None,
                     help="for learning loop: source video filename (e.g. larry-openclaw.mp4)")
    pub.set_defaults(func=cmd_publish)

    m = sub.add_parser("mark-processed")
    m.add_argument("video")
    m.add_argument("--clips-generated", type=int, default=0)
    m.add_argument("--clips-published", type=int, default=0)
    m.set_defaults(func=cmd_mark_processed)

    sub.add_parser("list-processed").set_defaults(func=cmd_list_processed)

    learn = sub.add_parser("learn", help="weekly: pull analytics, find winners/losers, refresh HOT.md")
    learn.add_argument("--soak-days", type=int, default=7,
                       help="ignore posts younger than this (analytics not mature)")
    learn.add_argument("--max-age-days", type=int, default=90,
                       help="ignore posts older than this (stale)")
    learn.add_argument("--top-pct", type=float, default=0.20)
    learn.add_argument("--bottom-pct", type=float, default=0.20)
    learn.add_argument("--weight-views", type=float, default=0.6)
    learn.add_argument("--weight-engagement", type=float, default=0.4)
    learn.set_defaults(func=cmd_learn)

    reflect = sub.add_parser("reflect", help="post-publish: extract qualitative patterns from approved vs rejected hooks")
    reflect.add_argument("--window-days", type=int, default=30,
                         help="how far back to look for candidates and approvals")
    reflect.set_defaults(func=cmd_reflect)

    return p


def main() -> None:
    args = build_parser().parse_args()
    args.func(args)


if __name__ == "__main__":
    main()
