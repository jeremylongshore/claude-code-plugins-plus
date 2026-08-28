# 📱 TikTok App Marketing Skill

> Automate your entire TikTok + Instagram slideshow marketing pipeline with AI: **generate → overlay → post → track → iterate.**

An [OpenClaw](https://openclaw.ai) / AI agent skill that turns your app marketing into a data-driven machine. Based on Larry's methodology that achieved **7M+ views, 1M+ TikTok views, and $670/month MRR** — all from an AI agent.

## What It Does

1. **Researches competitors** — browser-based analysis of what's working in your niche
2. **Generates AI images** — photorealistic slideshow slides (OpenAI, Stability AI, Replicate, or bring your own)
3. **Adds text overlays** — node-canvas powered, battle-tested sizing and positioning from 100+ viral posts
4. **Posts to 10+ platforms simultaneously** — via [Upload-Post](https://upload-post.com) API (TikTok, Instagram, YouTube, LinkedIn, X, Threads, Pinterest, Reddit, Bluesky)
5. **Tracks analytics** — platform-level stats + per-post performance via Upload-Post
6. **Iterates based on data** — daily feedback loop that tells you what's working and what to change
7. **Optional: Tracks conversions** — RevenueCat integration for full funnel intelligence (views → downloads → paying users)

## Quick Start

### Prerequisites

- **Node.js** v18+
- **node-canvas** (`npm install canvas`) — for text overlays
- **[Upload-Post](https://upload-post.com) account** — handles multi-platform posting + analytics
- **Image generation API** (pick one): OpenAI, Stability AI, Replicate, or local images

### Installation

If you're using OpenClaw:
```bash
# Install as a skill
npx skills add Upload-Post/upload-post-larry-marketing-skill
```

Or clone directly:
```bash
git clone https://github.com/Upload-Post/upload-post-larry-marketing-skill.git
cd tiktok-marketing-skill
npm install canvas
```

### Setup

1. **Initialize the workspace:**
```bash
node scripts/onboarding.js --init --dir tiktok-marketing/
```

2. **Fill in `tiktok-marketing/config.json`:**
```json
{
  "app": {
    "name": "YourApp",
    "description": "What your app does",
    "audience": "Who it's for",
    "problem": "What pain it solves",
    "category": "home|beauty|fitness|productivity|food|other"
  },
  "imageGen": {
    "provider": "openai",
    "apiKey": "YOUR_OPENAI_KEY",
    "model": "gpt-image-1.5"
  },
  "uploadPost": {
    "apiKey": "YOUR_UPLOAD_POST_KEY",
    "profile": "your_profile",
    "platforms": ["tiktok", "instagram"]
  }
}
```

3. **Validate your config:**
```bash
node scripts/onboarding.js --validate --config tiktok-marketing/config.json
```

### Create Your First Post

```bash
# 1. Generate 6 slideshow images
node scripts/generate-slides.js \
  --config tiktok-marketing/config.json \
  --output tiktok-marketing/posts/my-first-post/ \
  --prompts prompts.json

# 2. Add text overlays
node scripts/add-text-overlay.js \
  --input tiktok-marketing/posts/my-first-post/ \
  --texts texts.json

# 3. Post to TikTok + Instagram
node scripts/post-to-platforms.js \
  --config tiktok-marketing/config.json \
  --dir tiktok-marketing/posts/my-first-post/ \
  --caption "Your caption here #hashtag1 #hashtag2"

# 4. Check analytics
node scripts/check-analytics.js --config tiktok-marketing/config.json --days 3
```

## The Feedback Loop

This is what makes the skill actually work. It's not just "post and pray" — it's a data-driven optimization engine.

Every morning, the daily report:
1. Pulls platform analytics from Upload-Post (followers, impressions, reach)
2. Checks upload history (per-post success/failure, post URLs)
3. If RevenueCat connected: pulls conversion data (trials, subscribers, revenue)
4. Applies the diagnostic framework:

| Views | Conversions | Action |
|-------|-------------|--------|
| 🟢 High | 🟢 High | **SCALE IT** — make 3 variations of the winning hook |
| 🟢 High | 🔴 Low | **FIX THE CTA** — hook works, downstream is broken |
| 🔴 Low | 🟢 High | **FIX THE HOOKS** — content converts, needs more eyeballs |
| 🔴 Low | 🔴 Low | **FULL RESET** — try radically different approach |

```bash
node scripts/daily-report.js --config tiktok-marketing/config.json --days 3
```

## File Structure

```
tiktok-marketing-skill/
├── SKILL.md                    # Full skill documentation (for AI agents)
├── _meta.json                  # Skill metadata
├── scripts/
│   ├── onboarding.js           # Config validator + directory initializer
│   ├── generate-slides.js      # Image generation (OpenAI/Stability/Replicate/local)
│   ├── add-text-overlay.js     # Text overlay with node-canvas
│   ├── post-to-platforms.js    # Multi-platform posting via Upload-Post
│   ├── check-analytics.js      # Analytics + upload history checker
│   ├── daily-report.js         # Daily marketing report with diagnostics
│   └── competitor-research.js  # Research helper (placeholder)
└── references/
    ├── slide-structure.md      # 6-slide formula + hook writing guide
    ├── app-categories.md       # Category-specific templates
    ├── analytics-loop.md       # Analytics API reference
    ├── competitor-research.md  # Research methodology
    └── revenuecat-integration.md # RevenueCat setup guide
```

## Why Upload-Post?

Upload-Post is the engine that powers multi-platform posting and analytics:

- **One API call → 10+ platforms** — TikTok, Instagram, YouTube, LinkedIn, X, Threads, Pinterest, Reddit, Bluesky
- **Automatic tracking** — every post gets a `request_id`, no manual video-ID linking needed
- **Platform analytics** — followers, impressions, reach, profile views with timeseries data
- **Upload history** — per-post success/failure, post URLs, platform-specific IDs
- **Async processing** — submit and check status later

Sign up at [upload-post.com](https://upload-post.com)

## Proven Hook Formulas

### Tier 1: Person + Conflict → AI → Changed Mind (BEST)
- "I showed my mum what AI thinks our kitchen should look like" (161K views)
- "My landlord said I can't change anything so I showed her this" (124K views)

### Tier 2: Relatable Budget Pain
- "POV: You have good taste but no budget"
- "I can't afford an interior designer so I tried AI"

See `references/slide-structure.md` for the complete hook writing guide.

## Tips

- **Always use portrait (9:16)** — fills the TikTok screen
- **Add trending music** — TikTok posts go to inbox as drafts, add a trending sound before publishing
- **3 posts/day minimum** — consistency beats sporadic viral hits
- **Use `gpt-image-1.5`** if using OpenAI — never `gpt-image-1` (massive quality difference)
- **Cross-post everything** — same content, different algorithms, more surface area

## License

MIT

## Credits

Based on [Larry's TikTok marketing methodology](https://clawhub.com). Adapted for [Upload-Post](https://upload-post.com) multi-platform API.
