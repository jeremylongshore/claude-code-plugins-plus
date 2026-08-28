---
name: viraloop
description: OpenClaw AI agent skill for automated TikTok and Instagram carousel growth. Analyzes any website URL to extract brand, competitors, value proposition, then generates viral slides with auto-publishing and trending music via upload-post API. Built-in analytics feedback loop.
metadata: {"clawdbot":{"emoji":"🔄","requires":{"env":["GEMINI_API_KEY","UPLOADPOST_TOKEN"],"bins":["node","jq","uv"]}}}
allowed-tools: Read, Write, Edit, Glob, Bash(node:*), Bash(python3:*), Bash(curl:*)
version: "1.0.0"
author: Upload-Post <support@upload-post.com>
license: MIT
compatibility: "Designed for Claude Code; requires Node.js and Python 3 on PATH plus GEMINI_API_KEY and UPLOADPOST_TOKEN. Publishes carousels to TikTok and Instagram."
tags:
- carousels
- tiktok
- instagram
- growth
- automation
---

# Viraloop

Analyze any website and generate a 6-slide carousel for TikTok/Instagram with visual coherence. Posts directly to your feed (no drafts) with auto trending music. Both APIs (Gemini + upload-post.com) have free plans — no credit card needed to start.

## Overview

Turn any URL into a 6-slide carousel for TikTok and Instagram, publish it straight to the
feed with trending audio, then read the analytics and feed what worked back into the next
run. The loop is the point: each day's hooks are chosen against what actually performed
yesterday, not against a fixed template.

Six stages: research the site, generate hook variants, render slides, review them with
vision, publish, then learn from the numbers.

## Prerequisites

- Node.js and Python 3 on PATH
- `GEMINI_API_KEY` for research, hooks and image generation
- `UPLOADPOST_TOKEN` plus a profile with TikTok and Instagram connected
- Both APIs have free tiers — no card needed to start

## Philosophy: Daily Iteration Loop

The key to growth is **consistency + learning**:

1. **Post 1 carousel per day** - Consistency beats virality
2. **Track everything** - Every post generates data
3. **Learn from data** - What hooks work? What times? What visuals?
4. **Iterate and improve** - Each carousel is better than the last

```
Day 1: Post → Analyze → Learn
Day 2: Post (improved) → Analyze → Learn  
Day 3: Post (better) → Analyze → Learn
...
Day 30: You have 30 data points and a refined strategy
```

The skill maintains a `learnings.json` that accumulates insights across all posts:
- Best performing hooks
- Optimal posting times
- Visual styles that work
- CTAs that convert

**This is not a one-shot tool. It's a growth engine.**

## Quick Start

```bash
# 1. Full business research
node {baseDir}/scripts/analyze-web.js https://your-website.com

# 2. Generate 3 hook variants (SHOCK, CURIOSITY, CONTRADICTION)
GEMINI_API_KEY="your-key" bash {baseDir}/scripts/generate-hooks.sh

# 3. Review hooks with vision, pick the best one

# 4. Generate slides using selected hook type
GEMINI_API_KEY="your-key" bash {baseDir}/scripts/generate-slides.sh [shock|curiosity|contradiction]

# 5. Review slides (agent verifies text and quality)
# Agent uses vision to check each slide

# 6. Publish to TikTok + Instagram
UPLOADPOST_TOKEN="your-token" bash {baseDir}/scripts/publish-carousel.sh

# 7. Check analytics (after 24-48h)
UPLOADPOST_TOKEN="your-token" bash {baseDir}/scripts/check-analytics.sh 7

# 8. Learn from data for next carousels
node {baseDir}/scripts/learn-from-analytics.js
```

## Instructions

1. **Research the site** with `analyze-web.js` to extract the business, audience and angles.
2. **Generate three hook variants** — SHOCK, CURIOSITY, CONTRADICTION — and review them.
3. **Pick one hook type** and generate the six slides against it.
4. **Review the slides with vision.** Check the text is legible and not clipped before
   anything is published; a broken slide is worse than no post.
5. **Publish to TikTok and Instagram** with `publish-carousel.sh`.
6. **Read analytics** after a day and run the learning step so the next batch is informed.

## Hook Categories (Visual Novelty System)

The key to breaking the 1000 views ceiling is **visual novelty in the first slide**. We generate 3 hook types:

| Type | Goal | Visual Style |
|------|------|--------------|
| **SHOCK** | Stop the scroll with impossible/absurd | Surreal, chaotic, "wait what?" |
| **CURIOSITY** | Create information gap | Mysterious, secrets being revealed |
| **CONTRADICTION** | Show impossible combination | Relaxed + intense, "how is that possible?" |

### Anti-Stock Filter
All hooks include anti-stock prompting to avoid:
- Generic stock photo aesthetics
- Shocked pretty girl trope
- Typical influencer poses
- Overused laptop-coffee setups
- Corporate handshake scenes

### Hook Testing Workflow
1. Generate 3 variants with `generate-hooks.sh`
2. Review with vision, score each 1-5 on novelty
3. Kill anything that looks familiar
4. Use best hook for carousel
5. Track which hook TYPE performs best over time

## Image Model

Uses **gemini-3.1-flash-image-preview** to generate slides.
- Local script: `{baseDir}/scripts/generate_image.py`
- Supports image-to-image for visual coherence between slides

## Step 1: Full Research (`analyze-web.js`)

Performs COMPLETE business investigation:

### 1. Brand Analysis
- Brand name (from domain or title)
- Logo (URL or SVG)
- CSS colors (background, primary, links, headings)
- Typography (body font, heading font)
- Favicon

### 2. Content Analysis
- Headline and tagline
- All headings (page structure)
- Features/benefits (title + description)
- Pricing/plans
- Testimonials
- Stats/metrics
- CTAs
- Meta tags (title, description, og:image)

### 3. Internal Pages
- Navigates pricing, features, about, testimonials
- Extracts additional content from each page

### 4. Competitor Detection
- Searches for known competitor mentions in content
- List of 20+ known SaaS competitors (Buffer, Hootsuite, Later, etc.)
- Detects "vs", "alternative", "compare" sections
- No external searches required - all from the website itself

### 5. Storytelling
- Detects business type (SaaS, ecommerce, app)
- Detects niche (social-media-tools, developer-tools, etc.)
- Generates hooks based on customer pain points
- Defines pain points from features
- Creates transformation narrative (before → after)

### 6. Visual Context
- Brand colors in CSS format
- Color description for prompts
- Typography for slides
- Image themes based on niche
- Style guide for coherence

**Output:** `/tmp/carousel/analysis.json`

## Step 2: Generate Slides (`generate-slides.sh`)

Generates 6 slides with visual coherence using image-to-image:

| Slide | Type | Content |
|-------|------|---------|
| 1 | **HOOK** | Question/problem that hooks. Establishes ALL visual style. |
| 2 | **Problem** | Agitate the pain. "You upload to TikTok... then Instagram..." |
| 3 | **Agitation** | Competition advancing. Urgency. |
| 4 | **Solution** | Present the product with its value proposition. |
| 5 | **Feature** | Main benefit. |
| 6 | **CTA** | "Link in bio 👆" + call to action. |

### Visual Coherence
- Slide 1 generates the base style (colors, typography, mood)
- Slides 2-6 use image-to-image with slide 1 as reference
- Maintains same color palette, fonts, and aesthetic

### Prompts per Slide
Each slide has:
- **Text:** The main message
- **Scene:** Detailed visual description for background
- **Style:** Based on brand analysis

**Output:** 
- `/tmp/carousel/slide-{1-6}.jpg`
- `/tmp/carousel/caption.txt`

## Step 3: Review with Vision

After generating, the agent MUST review each slide:
- ✓ Text is legible and correct
- ✓ Words are not cut off
- ✓ Correct spelling
- ✓ Visual coherence between slides
- ✓ Acceptable image quality

If there are errors, regenerate the specific slide.

## Image Format

- **Resolution:** 768x1376 (9:16 vertical ratio)
- **Format:** JPG (TikTok does NOT accept PNG)
- **Text:** Large, bold, with shadow for readability
- **Background:** Scene relevant to the business, not just solid colors

## Step 4: Publish to TikTok + Instagram (`publish-carousel.sh`)

Publishes the carousel to TikTok and Instagram using Upload-Post API.

```bash
UPLOADPOST_TOKEN="your-token" bash {baseDir}/scripts/publish-carousel.sh
```

**Endpoint:** `POST /api/upload_photos`
- Docs: https://docs.upload-post.com/api/upload-photo

**Parameters sent:**
- `platform[]=tiktok` + `platform[]=instagram`
- `auto_add_music=true` - Adds music on TikTok automatically
- `tiktok_title` - Short title (max 90 chars) + hashtags
- `title` - Full caption for Instagram
- `privacy_level=PUBLIC_TO_EVERYONE`
- `media_type=IMAGE` - Photo carousel on Instagram
- `async_upload=true` - Process in background
- `photos[]` - The 6 slides JPG

**⚠️ IMPORTANT Instagram:** 
After publishing, user must go to Instagram and add viral music manually:
1. Open Instagram → Profile → The post
2. Edit → Add music
3. Search for trending/viral song

**Output:** Saves `request_id` in `post-info.json` for tracking.

## Step 5: Analyze Performance (`check-analytics.sh`)

Gets TikTok and Instagram analytics to see what works.

```bash
UPLOADPOST_TOKEN="your-token" bash {baseDir}/scripts/check-analytics.sh 7
```

**Endpoints used:**

1. **Profile analytics:**
   ```
   GET /api/analytics/{user}?platforms=tiktok
   ```
   → Followers, likes, comments, shares, impressions

2. **Total impressions:**
   ```
   GET /api/uploadposts/total-impressions/{user}?platform=tiktok&breakdown=true
   ```
   → Total views per day

3. **Per-post analytics:**
   ```
   GET /api/uploadposts/post-analytics/{request_id}
   ```
   → Views, likes, comments for the specific carousel (TikTok + Instagram)

Docs: https://docs.upload-post.com/api/get-analytics

## Step 6: Learn and Improve (`learn-from-analytics.js`)

Analyzes data and saves learnings for future carousels.

```bash
node {baseDir}/scripts/learn-from-analytics.js
```

**Generates:**
- `learnings.json` - Accumulated knowledge base
- Best hooks (those generating most views)
- Optimal posting times
- Recommendations for next carousel

## Full Flow

```bash
# 1. Research business
node {baseDir}/scripts/analyze-web.js https://my-product.com

# 2. Generate slides
GEMINI_API_KEY="..." bash {baseDir}/scripts/generate-slides.sh

# 3. Review with vision (agent verifies text)
# Agent checks each slide image

# 4. Publish
UPLOADPOST_TOKEN="..." UPLOADPOST_USER="myuser" bash {baseDir}/scripts/publish-carousel.sh

# 5. (After a few hours/days) Analyze
UPLOADPOST_TOKEN="..." UPLOADPOST_USER="myuser" bash {baseDir}/scripts/check-analytics.sh 7

# 6. Learn for next carousels
node {baseDir}/scripts/learn-from-analytics.js
```

## Output

Each run leaves six rendered slides plus a metadata file in the working directory, and the
publish step returns a per-platform result:

```
Carousel published
  tiktok     ✅  https://tiktok.com/@brand/photo/7412...
  instagram  ✅  https://instagram.com/p/C8xY2...
```

The analytics step returns views, likes and saves per slide set, which the learning step
consumes to rank hook types. Report which hook type won — that is the output that compounds.

## Error Handling

- **Gemini quota exhausted** — the free tier is per-minute as well as per-day. Back off and
  retry rather than dropping to a worse model mid-batch.
- **Slide text clipped or unreadable** — caught in the vision review step, which exists
  precisely for this. Regenerate the slide; do not publish it.
- **Upload-Post `401`** — the token was sent as `Bearer`. Use `Authorization: Apikey <token>`.
- **Instagram rejects the carousel** — the account must be Business or Creator and linked to
  a Facebook Page. Personal accounts cannot publish through the API.
- **One platform fails, the other succeeds** — expected. Report both and retry only the
  failure.

## Examples

**Full daily run against a site**

```bash
node scripts/analyze-web.js https://example.com
GEMINI_API_KEY="..." bash scripts/generate-hooks.sh
GEMINI_API_KEY="..." bash scripts/generate-slides.sh curiosity
bash scripts/publish-carousel.sh
```

**Check yesterday's numbers and learn from them**

```bash
bash scripts/check-analytics.sh
node scripts/learn-from-analytics.js
```

## Files

```
{baseDir}/
├── SKILL.md                      # This documentation
└── scripts/
    ├── analyze-web.js            # Full business research
    ├── generate-slides.sh        # Generate 6 slides with coherence
    ├── generate_image.py         # Gemini 3.1 flash image
    ├── review-slides.js          # Prepare slides for review
    ├── publish-carousel.sh       # Publish via Upload-Post API
    ├── check-analytics.sh        # Get analytics (TikTok + Instagram)
    ├── learn-from-analytics.js   # Learn from data
    └── search-competitors.js     # Optional external search
```

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google API key for image generation |
| `UPLOADPOST_TOKEN` | Upload-Post token for publishing and analytics |
| `UPLOADPOST_USER` | Upload-Post username (required) |

## Hook Examples by Niche

| Niche | Hook Example |
|-------|--------------|
| Social Media Tools | "Still posting to social media ONE BY ONE? 😩" |
| SaaS General | "Still doing this MANUALLY?" |
| Ecommerce | "The product TikTok won't stop recommending" |
| App | "The app I wish I'd discovered sooner" |
| Developer Tools | "The API that's going to change your code" |

## Why Viraloop?

| | Viraloop | Other skills |
|-|----------|-------|
| Publishing | Direct to feed | Drafts only |
| Music | Auto trending music | Manual |
| Platforms | TikTok + Instagram | Single platform |
| Research | Auto URL analysis | Manual description |
| Image coherence | Image-to-image reference | Independent slides |
| Image gen | Gemini (free tier) | Paid providers |
| Posting | upload-post.com (free, no CC) | Paid or self-hosted |
| Text overlay | AI-native (Gemini renders) | External scripts |
| Prompts | Structured templates | Free-form |
| Setup | 3 env vars | Complex multi-tool setup |

## Notes

- Analysis extracts competitors from the website content itself (20+ known SaaS)
- Image-to-image maintains coherence but takes ~20s per slide
- Generated caption includes niche-relevant hashtags
- Always review slide text - sometimes it gets cut off
- `auto_add_music` on TikTok improves engagement
- Check analytics after 24-48h for meaningful data
- Learnings accumulate and improve with each published carousel
- TikTok title max 90 characters (auto-truncated with hashtags)

## Resources

- Upload-Post API documentation: https://docs.upload-post.com
- Photo and carousel requirements: https://docs.upload-post.com/api/photo-requirements
- Gemini API keys: https://aistudio.google.com/apikey
- Dashboard: https://upload-post.com
