# Viraloop 🔄

Generate viral TikTok/Instagram carousel slides from any website automatically.

## Philosophy: Daily Iteration

**Post 1 carousel per day. Learn. Iterate. Grow.**

```
Day 1:  Post → Analyze → Learn
Day 7:  7 data points, patterns emerging
Day 30: Refined strategy, proven hooks, optimal timing
```

The skill accumulates insights across ALL your posts in `learnings.json`.

## Features

- 🔍 **Full Business Research** - Analyzes brand, features, competitors from any URL
- 🎨 **AI Image Generation** - Creates 6 visually coherent slides with Gemini (free plan available, no credit card)
- 📱 **Direct Publishing** - Posts straight to your TikTok feed with auto trending music + Instagram simultaneously. No drafts, no manual steps
- 💰 **100% Free to Start** - Both APIs (Gemini and [upload-post.com](https://upload-post.com)) have free plans, no credit card required
- 📊 **Analytics Tracking** - Monitors performance across all posts
- 🔄 **Learning Loop** - Accumulates insights: best hooks, times, days, styles

## Quick Start

```bash
# 1. Analyze website
node scripts/analyze-web.js https://your-product.com

# 2. Generate slides
GEMINI_API_KEY="..." bash scripts/generate-slides.sh

# 3. Publish
UPLOADPOST_TOKEN="..." bash scripts/publish-carousel.sh

# 4. Check analytics
UPLOADPOST_TOKEN="..." bash scripts/check-analytics.sh 7
```

## Requirements

- Node.js 18+
- Playwright (`npm install playwright && npx playwright install chromium`)
- uv (Python package runner)
- jq

## Environment Variables

| Variable | Description |
|----------|-------------|
| `GEMINI_API_KEY` | Google API key for Gemini image generation |
| `UPLOADPOST_TOKEN` | Upload-Post API token |
| `UPLOADPOST_USER` | Upload-Post username |

## Slide Structure

1. **Hook** - Attention-grabbing question/problem
2. **Problem** - Agitate the pain point
3. **Agitation** - Show competition advancing
4. **Solution** - Reveal your product
5. **Feature** - Key benefit
6. **CTA** - Call to action (Link in bio)

## Credentials & Security

### Required Credentials

| Credential | Type | Where to Get |
|------------|------|--------------|
| `GEMINI_API_KEY` | Environment variable | [Google AI Studio](https://aistudio.google.com/app/apikey) |
| `UPLOADPOST_TOKEN` | Environment variable | [upload-post.com](https://upload-post.com) → Dashboard → API Keys |

### Optional

| Credential | Type | Description |
|------------|------|-------------|
| `UPLOADPOST_USER` | Environment variable | Upload-Post username (not sensitive) |

### Security Notes

- ✅ All credentials are read from environment variables, not stored in files
- ✅ No API keys are hardcoded in any scripts
- ✅ Website analysis only reads public web pages (no authentication scraping)
- ✅ All generated data stays local in `/tmp/carousel/`

### Data Flow

1. **Website URL** → Analyzed by Playwright (local browser) → `analysis.json`
2. **Analysis** → Sent to Gemini API → Returns generated images
3. **Images + Caption** → Sent to Upload-Post API → Published to TikTok/Instagram
4. **Analytics** → Fetched from Upload-Post API → Stored locally in `learnings.json`

### External Services Used

| Service | Purpose | Data Sent |
|---------|---------|-----------|
| Gemini API | Image generation | Text prompts describing slides |
| Upload-Post API | Publishing + analytics | Images, captions, profile username |

No sensitive user data is transmitted. Only the content you're publishing.

## Why Viraloop?

Most carousel automation skills post to drafts and require manual publishing. Viraloop is different:

| Feature | Viraloop | Other skills |
|---------|----------|-------|
| Publishing | **Direct to feed** — posts go live instantly | Drafts only — you publish manually |
| Music | **Auto trending music** via `auto_add_music` | Manual — you add it yourself |
| Platforms | **TikTok + Instagram in one call** | Single platform, manual cross-post |
| Research | **Auto-analyzes any URL** — brand, competitors, pricing, features | Manual — you describe your product |
| Image coherence | **Image-to-image** — slides 2-6 reference slide 1 | Each slide generated independently |
| Image gen | **Gemini** (free tier available) | Paid image providers required |
| Posting service | **upload-post.com** — free plan, no credit card | Paid or self-hosted alternatives |
| Text on images | **AI-native** — text rendered directly | External scripts for text overlay |
| Prompt quality | **Structured templates** — explicit fields for consistency | Free-form prompts |
| Setup | **3 env vars** and you're posting | Complex multi-tool setup |

## Documentation

See [SKILL.md](./SKILL.md) for full documentation.

## License

MIT
