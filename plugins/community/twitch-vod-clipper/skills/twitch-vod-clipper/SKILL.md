---
name: twitch-vod-clipper
description: |
  When the user asks you to clip a Twitch VOD, download a streamer's
  video, or turn a Twitch broadcast into Shorts/Reels clips.

  Trigger phrases:
  - "clip this VOD"
  - "make clips from"
  - "download twitch VOD"
  - "turn this stream into shorts"
allowed-tools: Bash, Read, Write, Edit, Glob
version: 1.0.0
author: Carl Johnson <gupsspam@users.noreply.github.com>
license: MIT
compatibility: agentskills.io/specification
tags: [twitch, video, clipping, shorts, content-creation, ffmpeg]
---

## Overview

This skill turns a full-length Twitch VOD into a set of short, vertical (9:16) clips ready for YouTube Shorts, Instagram Reels, and TikTok. It downloads the VOD with `yt-dlp` (including subscriber-only VODs via browser cookies), transcribes it with Whisper, scores the transcript and audio track to find high-energy "viral" moments, then renders each moment as a 1080x1920 clip with face-tracked cropping, word-by-word animated captions, a channel watermark, and optional intro/outro cards. It finishes by generating a bold-text thumbnail for each clip and a manifest describing everything it produced.

## Prerequisites

**Command-line tools** (must be on `PATH`):

- `yt-dlp` — VOD downloading (`pip install -U yt-dlp` or the standalone binary)
- `ffmpeg` and `ffprobe` — built with `libass` support for animated subtitle rendering (check with `ffmpeg -filters | grep subtitles`)
- `python3` (3.9+)

**Python packages:**

```bash
pip install openai-whisper mediapipe pillow numpy
```

**Assets and accounts:**

- `cookies.txt` (Netscape format) exported from a logged-in Twitch browser session — required only for subscriber-only VODs. Export with a browser extension such as "Get cookies.txt LOCALLY", or use `yt-dlp --cookies-from-browser chrome`.
- A watermark PNG with transparency (e.g. `assets/watermark.png`), ideally ~200px wide.
- A bold TTF/OTF font for captions and thumbnails (e.g. Montserrat ExtraBold) in `assets/fonts/`.

**Hardware note:** Whisper's `medium` model wants ~5 GB of VRAM/RAM; fall back to `small` or `base` on constrained machines.

## Instructions

1. **Verify prerequisites.** Run `yt-dlp --version`, `ffmpeg -version`, `ffprobe -version`, and `python3 -c "import whisper, mediapipe, PIL"`. If anything is missing, tell the user exactly what to install (see Prerequisites) and stop. Confirm `ffmpeg -filters | grep -q subtitles` succeeds so libass rendering is available.

2. **Collect inputs.** You need: the VOD URL (e.g. `https://www.twitch.tv/videos/123456789`), the number of clips wanted (default 5), target clip length (default 30–60 s), the watermark path, and — if the VOD is sub-only — the path to `cookies.txt`.

3. **Set up a workspace.** Create a working directory per VOD, e.g. `work/<vod_id>/` with subfolders `clips/`, `thumbnails/`, and `tmp/`.

4. **Inspect the VOD before downloading.** Run `yt-dlp --dump-json --no-download "<URL>"` (add `--cookies cookies.txt` if provided) and capture the title, duration, and uploader. Warn the user if the VOD is longer than ~6 hours — transcription time scales linearly.

5. **Download the VOD.** Prefer 1080p source quality but cap it to keep files manageable:

   ```bash
   yt-dlp --cookies cookies.txt \
     -f "bv*[height<=1080]+ba/b[height<=1080]/b" \
     --concurrent-fragments 8 \
     -o "work/<vod_id>/vod.%(ext)s" \
     "<URL>"
   ```

   If the container is not MP4, remux it: `ffmpeg -i vod.mkv -c copy vod.mp4`.

6. **Extract a transcription-friendly audio track:**

   ```bash
   ffmpeg -i work/<vod_id>/vod.mp4 -vn -ac 1 -ar 16000 work/<vod_id>/tmp/audio.wav
   ```

7. **Transcribe with Whisper, keeping word timestamps** — these drive the animated captions later:

   ```bash
   whisper work/<vod_id>/tmp/audio.wav --model medium --language en \
     --word_timestamps True --output_format json \
     --output_dir work/<vod_id>/tmp/
   ```

   Use `--model small` if the machine is memory-constrained; use `--device cuda` when a GPU is present.

8. **Compute an audio-energy curve.** In Python, load `audio.wav`, compute RMS energy over 1-second windows, and z-score-normalize it. Peaks here correspond to shouting, laughter, hype moments, and game audio spikes.

9. **Score transcript segments for virality.** For each Whisper segment, combine (with roughly equal weight): (a) mean audio-energy z-score over the segment, (b) exclamation/caps density (`!`, `?!`, all-caps words like "NO WAY", "LET'S GO"), (c) hype-keyword hits (`insane`, `clip that`, `oh my god`, `what`, laughter tokens like "haha"/"lmao"), and (d) speech-rate spikes (words/sec vs. the VOD average — punchlines and panic are fast).

10. **Build candidate clips.** Take the top-scoring segments, expand each to the target length (default 30–60 s) by including surrounding segments for setup/payoff context, snap boundaries to sentence starts/ends from the transcript, and merge candidates that overlap. Discard candidates within 2 minutes of a higher-scoring one to avoid near-duplicates.

11. **Report the candidates.** Print a table of start/end timestamps, scores, and a one-line transcript preview for each, then proceed with the top N (or the user's picks if they respond).

12. **Cut each clip losslessly first**, then re-encode during the vertical render (a stream copy keeps this step fast; keyframe imprecision is fixed in step 15's re-encode):

    ```bash
    ffmpeg -ss <start> -to <end> -i vod.mp4 -c copy tmp/clip_<n>_raw.mp4
    ```

13. **Find the face-crop center with MediaPipe.** Sample ~2 frames/sec from the raw clip (`ffmpeg -i clip_raw.mp4 -vf fps=2 tmp/frames_%04d.jpg`), run MediaPipe Face Detection on each frame, and record the horizontal center of the largest face. Smooth the trajectory with a rolling median so the crop doesn't jitter. If no face is detected in >70% of frames (gameplay-only footage), fall back to a center crop.

14. **Generate the ASS caption file** for each clip from the word-level timestamps. Use `PlayResX: 1080`, `PlayResY: 1920`, a bold style with thick outline, and per-word karaoke highlighting so the active word pops:

    ```
    [Script Info]
    PlayResX: 1080
    PlayResY: 1920

    [V4+ Styles]
    Format: Name, Fontname, Fontsize, PrimaryColour, SecondaryColour, OutlineColour, BackColour, Bold, Outline, Shadow, Alignment, MarginV
    Style: Hype,Montserrat ExtraBold,72,&H00FFFFFF,&H0000E5FF,&H00000000,&H80000000,-1,5,2,2,340

    [Events]
    Format: Layer, Start, End, Style, Name, MarginL, MarginR, MarginV, Effect, Text
    Dialogue: 0,0:00:01.20,0:00:03.10,Hype,,0,0,0,,{\\k45}NO {\\k38}WAY {\\k52}HE {\\k61}HIT {\\k49}THAT
    ```

    Group words into lines of 3–5, offset all timestamps by the clip's start time, and give the highlight color (`SecondaryColour`) a punchy yellow/cyan.

15. **Render the vertical clip** — face-tracked crop to 9:16, scale to 1080x1920, burn in captions, overlay the watermark, and normalize loudness in one pass:

    ```bash
    ffmpeg -i tmp/clip_<n>_raw.mp4 -i assets/watermark.png -filter_complex "
      [0:v]crop=ih*9/16:ih:<face_x>-ih*9/32:0,scale=1080:1920,
      subtitles=tmp/clip_<n>.ass:fontsdir=assets/fonts[cap];
      [cap][1:v]overlay=W-w-40:120[v]" \
      -map "[v]" -map 0:a -af loudnorm=I=-14:TP=-1.5:LRA=11 \
      -c:v libx264 -preset medium -crf 20 -c:a aac -b:a 192k -r 30 \
      clips/clip_<n>.mp4
    ```

    For a moving face center, replace the constant `<face_x>` with a piecewise expression or render the smoothed trajectory via `sendcmd`. Clamp the crop x-offset to `[0, iw - ih*9/16]`.

16. **(Optional) Add intro/outro cards.** Generate a 1-second title card (`ffmpeg -f lavfi -i color=c=black:s=1080x1920:d=1 -vf "drawtext=fontfile=assets/fonts/font.ttf:text='<CLIP TITLE>':fontcolor=white:fontsize=80:x=(w-tw)/2:y=(h-th)/2" -c:v libx264 -r 30 tmp/intro.mp4`), give it a silent AAC track so streams match, then join with the concat demuxer:

    ```bash
    printf "file 'intro.mp4'\nfile '../clips/clip_<n>.mp4'\nfile 'outro.mp4'\n" > tmp/concat.txt
    ffmpeg -f concat -safe 0 -i tmp/concat.txt -c copy clips/clip_<n>_final.mp4
    ```

    All parts must share codec, resolution, frame rate, and audio parameters for `-c copy` to work; otherwise re-encode the concat.

17. **Generate a thumbnail per clip.** Grab the frame at the clip's energy peak (`ffmpeg -ss <peak> -i clips/clip_<n>.mp4 -frames:v 1 tmp/thumb_raw.png`), then use Pillow to boost saturation/contrast slightly and stamp 2–4 huge stroked caption words (white fill, thick black stroke via `ImageDraw.text(..., stroke_width=12, stroke_fill="black")`) near the top. Save as `thumbnails/clip_<n>.jpg` at quality 90.

18. **Verify every output with ffprobe.** Confirm each clip is 1080x1920, has both audio and video streams, and its duration matches the planned cut within ±1 s:

    ```bash
    ffprobe -v error -select_streams v:0 -show_entries stream=width,height -show_entries format=duration -of json clips/clip_<n>.mp4
    ```

19. **Write `manifest.json`** in the workspace root listing, for each clip: source VOD URL/ID, start/end timestamps, virality score, transcript excerpt, output file, and thumbnail file.

20. **Summarize for the user.** List the produced clips with timestamps and one-line descriptions, note any clips that were skipped or fell back to center-crop, and point to the manifest. Clean up `tmp/` unless the user wants to keep intermediates.

## Output

All output lands in `work/<vod_id>/`:

```
work/<vod_id>/
├── vod.mp4                  # full downloaded VOD (kept for re-clipping)
├── manifest.json            # machine-readable summary of the run
├── clips/
│   ├── clip_1.mp4           # 1080x1920, H.264 + AAC, captions & watermark burned in
│   ├── clip_1_final.mp4     # only when intro/outro cards were requested
│   └── ...
├── thumbnails/
│   ├── clip_1.jpg           # 1080x1920 thumbnail with stroked title text
│   └── ...
└── tmp/                     # audio.wav, transcript JSON, ASS files, raw cuts (deleted on success)
```

Clips are encoded at CRF 20, 30 fps, loudness-normalized to −14 LUFS — upload-ready for Shorts, Reels, and TikTok without further processing.

## Error Handling

- **`yt-dlp` fails with HTTP 403 / "subscriber-only" / "This video is only available to subscribers".** The VOD needs authentication. Ask the user for a fresh `cookies.txt` from a logged-in session (or use `--cookies-from-browser chrome`). Cookies expire — re-export if a previously working file starts failing.
- **`yt-dlp` reports "Unsupported URL" or no formats.** The VOD may have been deleted or is still live. Confirm the URL is a `/videos/<id>` link, and update yt-dlp (`yt-dlp -U`) since Twitch changes break older versions.
- **Whisper runs out of memory or is killed.** Retry with a smaller model (`--model small`, then `base`). On GPU OOM, add `--device cpu` (slower but reliable).
- **Word timestamps missing from the transcript JSON.** `--word_timestamps True` was omitted or the whisper version is too old; upgrade `openai-whisper` and re-run — captions cannot be animated without word timings.
- **No faces detected / crop looks wrong on gameplay footage.** Expected for facecam-less streams. Fall back to center crop, or ask the user for a fixed facecam region (e.g. "facecam is bottom-left") and crop around it instead.
- **Captions don't render or use the wrong font.** ffmpeg lacks libass, or the font isn't found. Verify `ffmpeg -filters | grep subtitles`; pass `fontsdir=assets/fonts` in the subtitles filter and make the ASS `Fontname` match the font's real family name.
- **Clip audio/video out of sync or starts on a frozen frame.** Stream-copy cuts snap to keyframes. Re-encode the cut instead: `ffmpeg -ss <start> -to <end> -i vod.mp4 -c:v libx264 -c:a aac tmp/clip_raw.mp4`.
- **Concat with intro/outro produces broken output.** The parts' streams don't match. Re-encode the concat (drop `-c copy`) or regenerate the cards with identical codec/resolution/fps/audio settings.
- **Disk fills up mid-run.** A 6-hour 1080p VOD is 10 GB+. Check free space up front (`df -h .`); offer to download at `height<=720` if space is tight.

## Examples

**Example 1 — basic clipping:**

> "Clip this VOD into 5 shorts: https://www.twitch.tv/videos/2141592653"

Downloads the VOD, transcribes it, picks the 5 highest-energy moments, and renders `clips/clip_1.mp4` … `clip_5.mp4` with captions and thumbnails.

**Example 2 — subscriber-only VOD with branding:**

> "Make clips from https://www.twitch.tv/videos/2140000001 — it's sub-only, cookies are in ~/cookies.txt, use my watermark at assets/wm.png, and keep clips under 45 seconds"

Uses `--cookies ~/cookies.txt` for the download, caps clip length at 45 s, and overlays `assets/wm.png` on every clip.

**Example 3 — targeted moment:**

> "Download twitch VOD 2139999999 and turn the boss fight around 1:23:00 into a short with captions"

Skips global moment detection: transcribes only the 1:18:00–1:28:00 region, finds the energy peak near 1:23:00, and renders a single captioned vertical clip plus thumbnail.

## Resources

- [yt-dlp](https://github.com/yt-dlp/yt-dlp) — downloader docs, format selection, and cookie options
- [FFmpeg filters documentation](https://ffmpeg.org/ffmpeg-filters.html) — `crop`, `scale`, `subtitles`, `overlay`, `drawtext`, `loudnorm`
- [openai-whisper](https://github.com/openai/whisper) — models, languages, and word-timestamp support
- [MediaPipe Face Detection](https://developers.google.com/mediapipe/solutions/vision/face_detector) — face detector API used for crop tracking
- [ASS subtitle format reference](http://www.tcax.org/docs/ass-specs.htm) — style fields and `\k` karaoke override tags
- [libass](https://github.com/libass/libass) — the renderer behind ffmpeg's `subtitles` filter
- [Pillow](https://pillow.readthedocs.io/) — `ImageDraw` text with `stroke_width` for thumbnails
- [Twitch VOD basics](https://help.twitch.tv/s/article/video-on-demand) — VOD availability and subscriber-only settings
