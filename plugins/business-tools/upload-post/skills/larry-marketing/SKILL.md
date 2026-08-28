---
name: tiktok-app-marketing
description: Automate TikTok + Instagram slideshow marketing for any app or product. Researches competitors, generates AI images, adds text overlays, posts via Upload-Post (multi-platform in one API call), tracks analytics, and iterates on what works. Use when setting up TikTok marketing automation, creating slideshow posts, analyzing post performance, optimizing app marketing funnels, or when a user mentions TikTok growth, slideshow ads, or social media marketing for their app. Covers competitor research (browser-based), image generation, text overlays, multi-platform posting (Upload-Post API — TikTok + Instagram + more simultaneously), analytics tracking, hook testing, CTA optimization, conversion tracking with RevenueCat, and a full feedback loop that adjusts hooks and CTAs based on views vs conversions.
allowed-tools: Read, Write, Edit, Glob, Bash(node:*), Bash(curl:*)
version: "1.0.0"
author: Upload-Post <support@upload-post.com>
license: MIT
compatibility: "Designed for Claude Code; requires Node.js on PATH plus GEMINI_API_KEY and UPLOAD_POST_API_KEY. Scripts under scripts/ do the image generation, overlays, posting and analytics."
tags:
- marketing
- tiktok
- instagram
- slideshows
- growth
---

# TikTok App Marketing

Automate your entire TikTok slideshow marketing pipeline: generate → overlay → post → track → iterate.

**Proven results:** 7 million views on the viral X article, 1M+ TikTok views, $670/month MRR — all from an AI agent running on an old gaming PC.

## Overview

A closed-loop marketing pipeline for an app or product on TikTok and Instagram, built on the
Larry methodology: study what competitors in the category are already winning with, generate
slideshow images, overlay hook text, post to both platforms, then read the numbers and let
them pick the next batch's hooks.

The loop is the product. Generating slideshows is the easy half; measuring which hook drove
installs and feeding that back is what makes it compound.

## Prerequisites

This skill does NOT bundle any dependencies. Your AI agent will need to research and install the following based on your setup. Tell your agent what you're working with and it will figure out the rest.

### Required
- **Node.js** (v18+) — all scripts run on Node. Your agent should verify this is installed and install it if not.
- **node-canvas** (`npm install canvas`) — used for adding text overlays to slide images. This is a native module that may need build tools (Python, make, C++ compiler) on some systems. Your agent should research the install requirements for your OS.
- **Upload-Post** — this is the backbone of the whole system. Upload-Post handles posting to TikTok, Instagram, and 10+ other platforms simultaneously with a single API call. It also provides **analytics** (followers, impressions, reach) and **upload history** (per-post tracking) that power the daily feedback loop. Without Upload-Post, the agent can't post or track what's working — and the feedback loop is what makes this skill actually grow your account instead of just posting blindly. Sign up at [upload-post.com](https://upload-post.com).

### Image Generation (pick one)
You choose what generates your images. Your agent should research the API docs for whichever you pick:
- **OpenAI** — `gpt-image-1.5` **(ALWAYS 1.5, never 1)**. Needs an OpenAI API key. Best for realistic photo-style images. This is what Larry uses and what we strongly recommend.
- **Stability AI** — Stable Diffusion XL and newer. Needs a Stability AI API key. Good for stylized/artistic images.
- **Replicate** — run any open-source model (Flux, SDXL, etc.). Needs a Replicate API token. Most flexible.
- **Local** — bring your own images. No API needed. Place images in the output directory and the script skips generation.

### Conversion Tracking (optional but recommended for mobile apps)
- **RevenueCat** — this is what completes the intelligence loop. Upload-Post tells you which posts get impressions. RevenueCat tells you which posts drive **paying users**. Combined, the agent can distinguish between a viral post that makes no money and a modest post that actually converts — and optimize accordingly. Install the RevenueCat skill from ClaWHub (`clawhub install revenuecat`) for full API access to subscribers, MRR, trials, churn, and revenue. There's also a **RevenueCat MCP** for programmatic control over products and offerings from your agent/IDE.

### Cross-Posting (built-in with Upload-Post)
Upload-Post supports posting to TikTok, Instagram, YouTube, LinkedIn, Facebook, X (Twitter), Threads, Pinterest, Reddit, and Bluesky — all in a single API call. Your agent should research which platforms fit your audience and connect them in your Upload-Post profile. Same content, different algorithms, more reach.

## First Run — Onboarding

The first run collects what the pipeline needs about the app: name, category, audience,
value proposition, competitors to study, and the RevenueCat or analytics hookup used to
attribute installs.

Run the onboarding script and answer its prompts:

```bash
node scripts/onboarding.js
```

It writes the answers to the skill's config and validates that `GEMINI_API_KEY` and
`UPLOAD_POST_API_KEY` resolve. If a required value is missing, ask the user rather than
inventing a default.

Full walkthrough, including every prompt and the category-specific guidance:
[references/onboarding.md](references/onboarding.md).

## Instructions

1. **Onboard once** — capture the app, category, audience and competitors.
2. **Research competitors** in the category to find the hooks already working.
3. **Generate slideshow images** with `scripts/generate-slides.js`.
4. **Add hook text overlays** with `scripts/add-text-overlay.js`.
5. **Post to TikTok and Instagram** with `scripts/post-to-platforms.js`. TikTok slideshows go
   up as drafts by design — see the note in the workflow below.
6. **Track analytics** with `scripts/check-analytics.js` and produce the daily report.
7. **Feed the numbers back** into the next batch's hook selection. Never skip this step.

## Core Workflow

### 1. Generate Slideshow Images

Use `scripts/generate-slides.js`:

```bash
node scripts/generate-slides.js --config tiktok-marketing/config.json --output tiktok-marketing/posts/YYYY-MM-DD-HHmm/ --prompts prompts.json
```

The script auto-routes to the correct provider based on `config.imageGen.provider`. Supports OpenAI, Stability AI, Replicate, or local images.

**⚠️ Timeout warning:** Generating 6 images takes 3-9 minutes total (30-90 seconds each for gpt-image-1.5). Set your exec timeout to at least **600 seconds (10 minutes)**. If you get `spawnSync ETIMEDOUT`, the exec timeout is too short. The script supports resume — if it fails partway, re-run it and completed slides will be skipped.

**Critical image rules (all providers):**
- ALWAYS portrait aspect ratio (1024x1536 or 9:16 equivalent) — fills TikTok screen
- Include "iPhone photo" and "realistic lighting" in prompts (for AI providers)
- ALL 6 slides share the EXACT same base description (only style/feature changes)
- Lock key elements across all slides (architecture, face shape, camera angle)
- See [references/slide-structure.md](references/slide-structure.md) for the 6-slide formula

### 2. Add Text Overlays

This step uses `node-canvas` to render text directly onto your slide images. This is how Larry produces slides that have hit **1M+ views on TikTok** — the text sizing, positioning, and styling are dialled in from hundreds of posts.

#### Setting Up node-canvas

Before you can add text overlays, your human needs to install `node-canvas`. Prompt them:

> "To add text overlays to the slides, I need a library called node-canvas. It renders text directly onto images with full control over sizing, positioning, and styling — this is what Larry uses for his viral TikTok slides.
>
> Can you run this in your terminal?"
>
> ```bash
> npm install canvas
> ```
>
> "If that fails, it's because node-canvas needs some system libraries. Here's what to install first:"
>
> **macOS:**
> ```bash
> brew install pkg-config cairo pango libpng jpeg giflib librsvg
> npm install canvas
> ```
>
> **Ubuntu/Debian:**
> ```bash
> sudo apt-get install build-essential libcairo2-dev libpango1.0-dev libjpeg-dev libgif-dev librsvg2-dev
> npm install canvas
> ```
>
> **Windows:**
> ```bash
> # node-canvas auto-downloads prebuilt binaries on Windows
> npm install canvas
> ```
>
> "Once installed, I can handle everything else — generating the overlays, sizing the text, positioning it perfectly. You won't need to touch this again."

**Don't skip this step.** Without node-canvas, the text overlays won't work. If installation fails, help them troubleshoot — it's usually a missing system library. Once it's installed once, it stays.

#### How Larry's Text Overlay Process Works

1. **Load the raw slide image** into a node-canvas
2. **Configure text settings** based on the text length for that specific slide
3. **Draw the text** with white fill and thick black outline
4. **Review the output** — check sizing, positioning, readability
5. **Adjust and re-render** if anything looks off
6. **Save the final image** once it looks right

**Exact code Larry uses:**

```javascript
const { createCanvas, loadImage } = require('canvas');
const fs = require('fs');

async function addOverlay(imagePath, text, outputPath) {
  const img = await loadImage(imagePath);
  const canvas = createCanvas(img.width, img.height);
  const ctx = canvas.getContext('2d');
  ctx.drawImage(img, 0, 0);

  // ─── Adjust font size based on text length ───
  const wordCount = text.split(/\s+/).length;
  let fontSizePercent;
  if (wordCount <= 5)       fontSizePercent = 0.075;  // Short: 75px on 1024w
  else if (wordCount <= 12) fontSizePercent = 0.065;  // Medium: 66px
  else                      fontSizePercent = 0.050;  // Long: 51px

  const fontSize = Math.round(img.width * fontSizePercent);
  const outlineWidth = Math.round(fontSize * 0.15);
  const maxWidth = img.width * 0.75;
  const lineHeight = fontSize * 1.3;

  ctx.font = `bold ${fontSize}px Arial`;
  ctx.textAlign = 'center';
  ctx.textBaseline = 'top';

  // ─── Word wrap ───
  const lines = [];
  const manualLines = text.split('\n');
  for (const ml of manualLines) {
    const words = ml.trim().split(/\s+/);
    let current = '';
    for (const word of words) {
      const test = current ? `${current} ${word}` : word;
      if (ctx.measureText(test).width <= maxWidth) {
        current = test;
      } else {
        if (current) lines.push(current);
        current = word;
      }
    }
    if (current) lines.push(current);
  }

  // ─── Position: centered at ~28% from top ───
  const totalHeight = lines.length * lineHeight;
  const startY = (img.height * 0.28) - (totalHeight / 2);
  const x = img.width / 2;

  // ─── Draw each line ───
  for (let i = 0; i < lines.length; i++) {
    const y = startY + (i * lineHeight);

    // Black outline
    ctx.strokeStyle = '#000000';
    ctx.lineWidth = outlineWidth;
    ctx.lineJoin = 'round';
    ctx.miterLimit = 2;
    ctx.strokeText(lines[i], x, y);

    // White fill
    ctx.fillStyle = '#FFFFFF';
    ctx.fillText(lines[i], x, y);
  }

  fs.writeFileSync(outputPath, canvas.toBuffer('image/png'));
}
```

**Key details that make Larry's slides look professional:**

- **Dynamic font sizing** — short text gets bigger (75px), long text gets smaller (51px). Every slide is optimized.
- **Word wrap** — respects manual `\n` breaks but also auto-wraps lines that exceed 75% width. No squashing.
- **Centered at 28% from top** — text block is vertically centered around this point, not pinned to it. Stays in the safe zone regardless of line count.
- **Thick outline** — 15% of font size. Makes text readable on ANY background.
- **Manual line breaks preferred** — use `\n` in your text for control. Keep lines to 4-6 words.

**Text content rules:**
- **REACTIONS not labels** — "Wait... this is actually nice??" not "Modern minimalist"
- **4-6 words per line** — short lines are scannable at a glance
- **3-4 lines per slide is ideal**
- **No emoji** — canvas can't render them reliably
- **Safe zones:** No text in bottom 20% (TikTok controls) or top 10% (status bar)

**The difference between OK slides and viral slides is in these details.** Larry's slides consistently hit 50K-150K+ views because the text is sized right, positioned right, and readable at a glance while scrolling.

**⚠️ LINE BREAKS ARE CRITICAL — Read This:**

The `texts.json` file must contain text with `\n` line breaks to control where lines wrap. If you pass a single long string without line breaks, the script will auto-wrap, but **manual breaks look much better** because you control the rhythm.

**Good (manual breaks, 4-6 words per line):**
```json
[
  "I showed my landlord\nwhat AI thinks our\nkitchen should look like",
  "She said you can't\nchange anything\nchallenge accepted",
  "So I downloaded\nthis app and\ntook one photo",
  "Wait... is this\nactually the same\nkitchen??",
  "Okay I'm literally\nobsessed with\nthis one",
  "Snugly showed me\nwhat's possible\nlink in bio"
]
```

**Bad (no breaks — will auto-wrap but looks worse):**
```json
[
  "I showed my landlord what AI thinks our kitchen should look like",
  ...
]
```

**Rules for writing overlay text:**
1. **4-6 words per line MAX** — short lines are scannable at a glance
2. **Use `\n` to break lines** — gives you control over the rhythm
3. **3-4 lines per slide is ideal** — more lines are fine, they won't overflow
4. **Read it out loud** — each line should feel like a natural pause
5. **No emoji** — canvas can't render them, they'll show as blank
6. **REACTIONS not labels** — "Wait... this is nice??" not "Modern minimalist"

The script auto-wraps any line that exceeds 75% width as a safety net, but always prefer manual `\n` breaks for the best visual result.

### 3. Post to TikTok + Instagram

Use `scripts/post-to-platforms.js`:

```bash
node scripts/post-to-platforms.js --config tiktok-marketing/config.json --dir tiktok-marketing/posts/YYYY-MM-DD-HHmm/ --caption "caption" --title "title"
```

This uploads all slide images and posts them to TikTok + Instagram (and any other configured platforms) simultaneously in a single API call via Upload-Post.

**How it works:**
1. Reads slide images from the directory (slide1.png through slideN.png)
2. Sends them to Upload-Post's `POST /upload_photos` endpoint
3. Includes all configured platforms in one request
4. Uses `async_upload=true` for background processing
5. Returns a `request_id` for tracking (saved in `meta.json`)

**No manual video-ID linking needed.** Upload-Post tracks posts automatically by `request_id`. The upload history endpoint returns per-platform post URLs and success/failure status.

**Caption rules:** Long storytelling captions (3x more views). Structure: Hook → Problem → Discovery → What it does → Result → max 5 hashtags. Conversational tone.

### Why We Post TikTok Slideshows as Drafts — Best Practice

For TikTok specifically, posts go as photo carousels. TikTok photo posts benefit enormously from trending sounds:

1. **Music is everything on TikTok.** Trending sounds massively boost reach. The algorithm favours posts using popular audio.
2. **After posting, add music from TikTok's sound library** — browse what's trending in your niche.
3. **Posts without music get buried.** Silent slideshows look like ads and get skipped. A trending sound makes your content feel native.

This is the workflow that helped us hit 1M+ TikTok views and $670/month MRR. Don't skip the music step.

**Instagram carousels don't need music** — they work great as-is. Upload-Post handles both platforms with appropriate settings.

### 4. Track Analytics

Use `scripts/check-analytics.js` to pull platform analytics and upload history:

```bash
node scripts/check-analytics.js --config tiktok-marketing/config.json --days 3
```

The script:
1. Fetches platform-level analytics (followers, impressions, reach, profile views)
2. Fetches upload history for the last N days
3. Groups uploads by `request_id` (one post = multiple platform entries)
4. Shows per-post success/failure status and post URLs
5. Saves a snapshot to `analytics-snapshot.json`

**No connection step needed.** Unlike systems that require manually linking post IDs, Upload-Post tracks everything automatically by `request_id`. When you upload, the history immediately shows which platforms received the post and their post URLs.

**The daily cron handles all of this automatically.** It runs in the morning, checks the last 3 days, and generates a comprehensive report.

---

## The Feedback Loop (CRITICAL — This is What Makes It Work)

This is the part that separates the pipeline from a slideshow generator. Every post is
measured, and the next batch is chosen against what actually performed — not against a
fixed template.

The rules that matter:

- **Never post a batch without reading the previous batch's numbers first.** Posting blind
  turns the loop into noise.
- **Change one variable at a time** — hook or CTA, not both — or you cannot attribute the
  result.
- **Kill losers fast, scale winners slowly.** A hook that underperforms twice is dead; one
  that wins once is not yet proven.
- **Attribute to installs, not likes.** Views without installs mean the hook worked and the
  offer did not.

Full mechanics, thresholds and the analytics queries:
[references/feedback-loop.md](references/feedback-loop.md) and
[references/analytics-loop.md](references/analytics-loop.md).

## Posting Schedule

Optimal times (adjust for audience timezone):
- **7:30 AM** — catch early scrollers
- **4:30 PM** — afternoon break
- **9:00 PM** — evening wind-down

3x/day minimum. Consistency beats sporadic viral hits. 100 posts beats 1 viral.

## Cross-Posting

Upload-Post supports posting the same content to 10+ platforms simultaneously in a single API call. Recommend:
- **Instagram** — especially strong for beauty/lifestyle/home (included by default)
- **YouTube Shorts** — long-tail discovery
- **Threads** — lightweight engagement driver
- **LinkedIn** — for B2B/professional apps
- **Pinterest** — strong for visual/home/design niches

Same slides, different algorithms, more surface area. Each platform's algo evaluates content independently. Upload-Post handles format requirements per platform automatically.

## App Category Templates

See [references/app-categories.md](references/app-categories.md) for category-specific slide prompts and hook formulas.

## Output

Each batch produces the rendered slides, the posted URLs per platform, and a daily report
tying hooks to results:

```
Batch 2026-08-29 — hook type: CONTRADICTION

  tiktok     ✅  draft created (publish from the app)
  instagram  ✅  https://instagram.com/p/C8xY2...

Yesterday's batch (CURIOSITY):
  views 12,401 · saves 388 · installs 47 · CPI-equivalent €0.00
  → CONTRADICTION selected for today
```

Always report installs alongside views. Views without installs mean the hook worked and the
offer did not, and that distinction drives the next decision.

## Error Handling

- **Gemini rate limit or quota** — the free tier limits per minute as well as per day. Back
  off and retry; do not silently switch to a worse model mid-batch.
- **Text overlay clipped or unreadable** — regenerate the slide. A broken slide published is
  worse than a batch delayed.
- **Upload-Post `401`** — the key was sent as `Bearer`. Use `Authorization: Apikey <key>`.
- **Instagram rejects the post** — the account must be Business or Creator and linked to a
  Facebook Page; personal accounts cannot publish through the API.
- **TikTok slideshow appears as a draft** — that is intended, not a failure. See the
  best-practice note in the workflow: publishing from inside the app gets better reach.
- **Analytics empty right after posting** — platform metrics lag by hours. Do not treat an
  empty first read as a zero-performing post; wait for the next cycle.

## Examples

**Full daily batch**

```bash
node scripts/competitor-research.js
node scripts/generate-slides.js
node scripts/add-text-overlay.js
node scripts/post-to-platforms.js
```

**Read yesterday's numbers before choosing today's hook**

```bash
node scripts/check-analytics.js
node scripts/daily-report.js
```

## Common Mistakes

| Mistake | Fix |
|---------|-----|
| 1536x1024 (landscape) | Use 1024x1536 (portrait) |
| Font at 5% | Use 6.5% of width |
| Text at bottom | Position at 30% from top |
| Different rooms per slide | Lock architecture in EVERY prompt |
| Labels not reactions | "Wait this is nice??" not "Modern style" |
| Only tracking views | Track conversions — views without revenue = vanity |
| Same hooks forever | Iterate based on data, test new formats weekly |
| No cross-posting | Use Upload-Post to post everywhere simultaneously |
| `spawnSync ETIMEDOUT` | Exec timeout too short — image gen takes 3-9 min for 6 slides. Use a 10-minute timeout or generate slides one at a time |

## Resources

- Onboarding walkthrough: [references/onboarding.md](references/onboarding.md)
- Feedback loop mechanics: [references/feedback-loop.md](references/feedback-loop.md)
- Analytics loop: [references/analytics-loop.md](references/analytics-loop.md)
- Competitor research method: [references/competitor-research.md](references/competitor-research.md)
- Slide structure: [references/slide-structure.md](references/slide-structure.md)
- App category templates: [references/app-categories.md](references/app-categories.md)
- RevenueCat integration: [references/revenuecat-integration.md](references/revenuecat-integration.md)
- Upload-Post API documentation: https://docs.upload-post.com
