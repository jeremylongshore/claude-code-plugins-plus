# autoshorts

> Turn long videos into a daily stream of viral short-form clips for TikTok, Instagram Reels and YouTube Shorts — with a human-in-the-loop approval step you can answer from your phone.

The idea is to keep a small backlog of long videos and forward a new one to your agent every time you record. The agent (Hermes / Openclaw / whatever you're running) saves it into the input folder for you — you don't manage paths yourself, you just send the video in chat. Once a day the skill picks one video from that folder (newest unprocessed first, so the one you just sent jumps the queue), decides which moments are worth clipping, cuts them, overlays a punchy hook on top, and asks you (in the same chat channel) which ones you want to publish. You reply with the clip IDs. It schedules them on TikTok / Instagram / YouTube via [Upload-Post](https://upload-post.com).

**Input videos should already be 9:16 vertical** (1080×1920 ideally) and ready to post on social — with your subtitles already burned in if you want subs. The skill does NOT reformat, crop, or burn subtitles. It only cuts and adds a hook text overlay on top. Treat the input folder as "near-final long-form footage", not raw camera dumps.

It's the same workflow Opus Clip / Vizard sell, but you own every piece of it and you stay in the loop on what actually ships.

---

## Setup prompt

Paste into Claude Code, Codex, Hermes, Openclaw, or any agent with shell access:

> Set up https://github.com/mutonby/skill-autoshorts for me. Read README.md.

---

## Install

When an agent reads this section, here's the full install protocol it should follow:

1. Clone or `git pull` this repo into `~/Documents/skill-autoshorts/` (or whatever path the user prefers).
2. Make sure `ffmpeg` is installed (`brew install ffmpeg` on macOS, `apt install ffmpeg` on Linux). Verify with `ffmpeg -version`.
3. Create the venv and install Python deps: `python3 -m venv venv && ./venv/bin/pip install -r requirements.txt`.
4. Register `SKILL.md` with whichever agent harness is running. For Claude Code, copy or symlink it into `~/.claude/skills/autoshorts/SKILL.md`. For Hermes / Openclaw follow their skill registration docs.
5. Create `.env` from `.env.example` and ask the user to paste the values you need:
   - `GEMINI_API_KEY` — https://aistudio.google.com/apikey (free tier is enough).
   - `UPLOAD_POST_API_KEY` and `UPLOAD_POST_PROFILE` — https://app.upload-post.com → Settings → API Keys + Manage Users (free tier available, no credit card required).
   - Default `INPUT_FOLDER` and `OUTPUT_FOLDER` to `~/Documents/skill-autoshorts/input` and `.../output` unless the user says otherwise. Default `WHISPER_MODEL=medium` and `TIMEZONE=Europe/Madrid` (override if the user is in another timezone).
6. Verify the Upload-Post key works: `curl -s -H "Authorization: Apikey $UPLOAD_POST_API_KEY" https://api.upload-post.com/api/uploadposts/users` should return the user's profile and connected platforms. Surface any platform with `reauth_required: true` so the user can fix it before the first publish.
7. Read `SKILL.md` end-to-end. That's the canonical daily workflow — visual QA, weekly `learn`, all the operational rules.

**After install, do nothing else.** Don't transcribe, don't call Gemini, don't publish. Tell the user everything is ready, summarize what's connected on Upload-Post, and wait. The user will forward videos to you in chat going forward — your job is to save each one into `INPUT_FOLDER` and invoke the skill (`/autoshorts` or equivalent) when they ask.

### Notes for the user during install

- The first transcribe call downloads Whisper `medium` (~1.5 GB). Subsequent runs are instant.
- Upload-Post platform requirements: **TikTok** any account works · **Instagram** must be a Business or Creator account linked to a Facebook Page · **YouTube** any Google account · LinkedIn / Reddit / Threads / X also supported.
- The `UPLOAD_POST_PROFILE` value is the **profile name** you create in Upload-Post → Manage Users, NOT your social handle.

---

## The interesting part: how the clips are picked

Most "auto-clip" tools either (a) work from text only and miss the visual cues that make a moment funny / tense / shareable, or (b) work from video only and produce ragged cuts that chop people mid-word. We sidestep both.

```
┌─────────────────┐
│  long video.mp4 │
└────────┬────────┘
         │
         ├──────────────► Whisper (medium, local)
         │                ─ word-level timestamps
         │                ─ language auto-detect
         │                ─ outputs transcript.json
         │
         └──────────────► Gemini 3 Flash (multimodal, cloud)
                          ─ receives the FULL VIDEO + the transcript
                          ─ sees laughter, gestures, scene changes
                          ─ MUST snap clip start/end to word boundaries from the transcript
                          ─ outputs clips.json with {start, end, hook_text, reason, score}

                                          │
                                          ▼
                          ffmpeg cut + Pillow hook overlay
                                          │
                                          ▼
                                 Upload-Post API
                                  ↳ TikTok (draft)
                                  ↳ Instagram Reels
                                  ↳ YouTube Shorts
```

**Why this combo works:**

1. **Whisper is the clock.** Word-level timestamps mean every cut starts and ends on a clean word boundary. No mid-syllable chops, no half-breaths.
2. **Gemini Flash is the editor.** It's multimodal — we send the actual video file via the Files API along with the transcript. It can see a punchline land, hear laughter, notice a scene change, react to a chart on screen. Crucially, the prompt forces it to use timestamps from the Whisper transcript, so it can't hallucinate "20.5s" and miss by a syllable.
3. **The pipeline is human-gated.** The model proposes; you dispose. Every candidate is cut and rendered before you see it, so you review the actual final video, not a description. You answer from your phone.

---

## Usage

### Inside an agent harness (recommended — Hermes / Openclaw / similar)

This is what the skill is built for. An agent harness on a VPS runs the daily cron, pings you on your messenger ("here are today's candidates, which do I publish?"), captures your reply, and closes the loop. You drop new videos in chat whenever you record; you get a daily push of clip candidates; you reply with IDs from your phone. Hands-off after install.

The skill itself doesn't talk to Telegram / WhatsApp / etc. — the harness does. The skill just runs the pipeline and surfaces a candidates table; the harness forwards it to your messenger and pipes your reply back.

For invocation, the harness either fires `/autoshorts` on its daily cron, or invokes the equivalent in its own skill system. SKILL.md is the contract.

### As a standalone CLI

```bash
source venv/bin/activate

# 1. Pick the next unprocessed video
python autoshorts.py pick

# 2. Transcribe (writes output/<slug>/transcript.json)
python autoshorts.py transcribe input/your-video.mp4

# 3. Analyze with Gemini (writes output/<slug>/clips.json)
python autoshorts.py analyze input/your-video.mp4

# 4. For each clip in clips.json:
python autoshorts.py extract input/your-video.mp4 \
    --start 12.34 --end 45.67 \
    --output output/your-video/clip_1.mp4

python autoshorts.py hook output/your-video/clip_1.mp4 \
    --text "Tu hook aquí" --duration 3 \
    --output output/your-video/clip_1_final.mp4

# 5. Publish (TikTok defaults to draft / MEDIA_UPLOAD)
python autoshorts.py publish output/your-video/clip_1_final.mp4 \
    --platforms tiktok,instagram,youtube \
    --title "general title" \
    --description "general description" \
    --tiktok-title "TikTok-specific (max 90 chars, can have emojis + hashtags)" \
    --instagram-title "Instagram caption (long-form, 500-800 chars + 20-30 hashtags)" \
    --youtube-title "YouTube title (~40-60 chars, SEO-friendly)" \
    --schedule "2026-05-01T10:00:00" \
    --timezone "Europe/Madrid" \
    --tiktok-mode draft

# 6. Mark the source video as consumed (so tomorrow's pick skips it)
python autoshorts.py mark-processed input/your-video.mp4 \
    --clips-generated 5 --clips-published 3
```

### As a daily loop

The whole thing is designed to run forever, one video per day:

- You drop new long videos into `INPUT_FOLDER` whenever you have one.
- A cron / systemd / openclaw schedule fires `/autoshorts` daily.
- `pick` always chooses the **newest unprocessed** video. Fresh material jumps the queue. Old unprocessed videos still drain over time.
- `state/processed.json` (sha256-keyed) is the only memory between runs — it's what prevents the same video being clipped twice.
- If you reject ALL candidates ("none"), the video is still marked consumed. To retry, manually remove its entry from `state/processed.json`.

---

## How it learns

The pipeline gets smarter with every clip you publish. Engagement data flows back from Upload-Post analytics into the Gemini prompt that selects tomorrow's clips.

```
                          publish ─────► Upload-Post
                            │                │
                            ▼                ▼
                  post-history.jsonl   real platform metrics
                  (clip → request_id,   (views, likes, comments,
                   hook, score, …)      shares, saves)
                            │                │
                            └───────┬────────┘
                                    │
                                    ▼ (weekly)
                              learn subcommand
                            ─ z-score per platform
                            ─ composite = 0.6·views + 0.4·engagement_rate
                            ─ top 20% = winners
                            ─ bottom 20% = losers
                                    │
                                    ▼
                              Gemini Flash
                            "Here are winners and losers,
                             plus the current HOT.md.
                             Output an updated HOT.md
                             (≤80 lines of patterns)."
                                    │
                                    ▼
                            learnings/HOT.md
                                    │
                                    ▼ (every analyze call, automatically)
                            prepended to Gemini's analyze prompt
                                    │
                                    ▼
                            tomorrow's clips reflect what worked
```

### Three CLI commands drive the loop

| Command | Cadence | What it does |
|---|---|---|
| `publish` (with `--clip-id --hook-text --viral-score --reason --video-source`) | every approved clip | logs the clip's full context to `learnings/post-history.jsonl` so we can correlate it with metrics later |
| `learn` | weekly | pulls fresh analytics, finds winners/losers, asks Gemini to refresh `HOT.md` |
| `reflect` (optional) | when you want | quick qualitative pass — compares which candidates you APPROVED vs REJECTED, no metrics needed |

### Composite metric

`learn` ranks clips by a weighted z-score:

```
composite = 0.6 × z(total_views) + 0.4 × z(engagement_rate)

where engagement_rate = (likes + comments + shares + saves) / total_views
```

Both weights are flags (`--weight-views`, `--weight-engagement`) — bump engagement higher if you care more about quality than reach, lower if you're optimizing pure volume.

### Soak window

`learn --soak-days 7` (default): clips younger than 7 days are excluded — engagement metrics need time to mature, daily learning would chase noise. Older than 90 days = stale and ignored too.

If you have fewer than ~5 winners + 5 losers, `learn` skips the synthesis and writes a "not enough data" note to `learnings/runs/learn-YYYY-MM-DD.md`. Just keep publishing.

### Auditability

Every `learn` run writes a full audit to `learnings/runs/learn-YYYY-MM-DD.md`: which clips were called winners, with their scores, the previous HOT.md, and the new HOT.md side-by-side. The previous HOT.md is also backed up as `HOT.YYYYMMDD-HHMMSS.md.bak`. You can roll back if Gemini synthesizes garbage.

### Reflect (no-metrics qualitative pass)

`reflect --window-days 30` is a faster pass that doesn't wait for engagement data. It compares the clips Gemini OFFERED against the ones you APPROVED and asks Gemini to extract qualitative patterns ("approves hooks with concrete numbers, rejects question-form hooks"). Output goes to `learnings/runs/reflect-...md` and is **not** auto-promoted to HOT.md — it's notes for you to read and curate.

### Why we don't auto-promote everything

`learn` overwrites `HOT.md` based on metrics only — that's safe because the data is real. `reflect` is observational and could lock in your past biases ("I always reject question hooks") rather than what actually performs. So reflect output stays in `runs/` for human review.

---

## File layout

```
skill-autoshorts/
├── README.md                  ← you are here
├── autoshorts.py              ← CLI: pick / transcribe / analyze / extract / hook / publish / mark-processed
├── requirements.txt
├── .env                       ← secrets (gitignored)
├── .env.example
├── input/                     ← drop long videos here
├── output/
│   └── <video_slug>/
│       ├── transcript.json    ← Whisper output (segments + word timestamps)
│       ├── clips.json         ← Gemini's clip selections
│       ├── clip_1.mp4         ← raw cut
│       ├── clip_1_final.mp4   ← cut + hook overlay
│       └── …
├── state/
│   └── processed.json         ← sha256s of videos already processed
└── learnings/
    ├── HOT.md                 ← auto-managed by `learn`, prepended to every analyze prompt
    ├── post-history.jsonl     ← every clip we published (request_id, hook, score, …)
    ├── candidate-history.jsonl ← every candidate Gemini offered (so reflect can compare)
    ├── metrics.jsonl          ← analytics snapshots from Upload-Post
    ├── insights/              ← MANUAL notes (not used by the pipeline)
    └── runs/
        ├── learn-YYYY-MM-DD.md
        └── reflect-YYYY-MM-DD-HHMM.md
```

---

## Per-platform copy guidance

The publish helper takes one general `--title` / `--description` plus per-platform overrides. Lengths are asymmetric:

| Platform | Field | Practical sweet spot | Hard limit | Style |
|---|---|---|---|---|
| YouTube Shorts | `--youtube-title` | **40–60 chars** | 100 | Short, SEO-friendly with keywords. Truncates on mobile if longer. |
| TikTok | `--tiktok-title` | 70–85 chars | 90 | Punchy, 1–2 emojis, hashtags at the end |
| Instagram Reels | `--instagram-title` | 500–800 chars | 2200 | Long-form storytelling: hook line, 2–4 short paragraphs, CTA, then 20–30 hashtags |

Don't reuse the same string across platforms. YouTube wants compression; Instagram wants depth.

---

## Why these tech choices

- **Whisper `medium`** — the sweet spot for accuracy vs. speed on consumer hardware (CPU `int8`). `small` is twice as fast but loses on technical vocabulary; `large-v3` is markedly better but ~3× slower.
- **Gemini 3 Flash Preview (multimodal)** — has a free tier, accepts video via the Files API, returns strict JSON via `response_mime_type=application/json`, and is cheap enough to run daily. Crucially, it can *watch* the video, not just read its transcript.
- **Pillow + ffmpeg overlay** for the hook — the alternative (ffmpeg's `drawtext` filter) requires `libfreetype` which is missing from many Homebrew ffmpeg builds. Rendering the hook to a transparent PNG with PIL and compositing with the always-available `overlay` filter is more portable and gives nicer text rendering (anti-aliasing, auto word-wrap, multi-line layout). The hook itself uses a TikTok-style **black pill behind each line of text** (78% opacity, rounded corners) so it stays legible regardless of what's underneath — pure white frames, pure black frames, or busy screenshares all work without per-frame analysis.
- **Upload-Post** — one API for ~10 platforms, OAuth handled in their dashboard, supports scheduling and platform-specific titles. The free tier (10 uploads/month) is enough to validate the pipeline; paid plans for production volume.

## Limitations / things to know

- **Quota**: Upload-Post free tier = 10 uploads/month, where one publish to 3 platforms counts as 3. Paid plans available.
- **TikTok draft mode (default)**: with `--tiktok-mode draft`, clips land in your TikTok inbox (`post_mode=MEDIA_UPLOAD`) — you finish editing in the TikTok app before publishing. Use `--tiktok-mode direct` if you want immediate publication.
- **Whisper first-run download**: ~1.5 GB on first transcribe; cached afterwards.
- **Gemini Files API processing**: a 9-minute video takes ~30–60s of processing on Google's side before it's queryable. The script polls and waits.
- **Rate-limiting**: the daily-loop design is partly to stay friendly with TikTok / Instagram limits — bulk-publishing a backlog at once is more likely to be flagged than 1/day.
- **Newest-first prioritization**: if you keep dropping new videos every day, older ones may sit in the queue indefinitely. That's intentional (fresh content > old backlog) but if you want strict FIFO, swap the sort in `cmd_pick`.
