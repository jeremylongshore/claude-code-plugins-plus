# Competitor Research Guide

## Why This Matters

Before creating content, you MUST understand the landscape. What hooks are competitors using? What's getting views? What gaps exist? This research directly drives your hook strategy and content differentiation.

## Research Process

### 1. Ask for Browser Permission

Always ask the user before browsing. Something like:

> "I want to research what your competitors are doing on TikTok — what's getting views, what hooks they use, what's working. Can I use the browser to look around?"

### 2. TikTok Research

Search TikTok for the app's niche. Look for:

- **Competitor accounts** posting similar content (aim for 3-5)
- **Top-performing videos** in the niche — what hooks do they use?
- **Slide formats** — before/after, listicle, POV, tutorial, reaction
- **View counts** — what's average vs exceptional in this niche?
- **Posting frequency** — how often do successful accounts post?
- **CTAs** — "link in bio", "search on App Store", app name in text, etc.
- **Trending sounds** — what music/sounds are popular in this niche?
- **Comment sentiment** — what do people ask about? What complaints?

### 3. App Store Research

Check the app's category on App Store / Google Play:

- Competitor apps in the same category
- Their screenshots, descriptions, ratings
- What features they highlight
- Their pricing model (free, freemium, subscription)
- Review sentiment — what do users love/hate about competitors?

### 4. Gap Analysis

The most valuable output is identifying what competitors AREN'T doing:

- **Content gaps:** Formats no one is using (listicles? tutorials? comparisons?)
- **Hook gaps:** Emotional angles no one has tried
- **Platform gaps:** Are competitors only on TikTok? Instagram opportunity?
- **Audience gaps:** Is there an underserved segment?
- **Quality gaps:** Are competitor images/videos low effort? Can we do better?

### 5. Save Findings

Store in `tiktok-marketing/competitor-research.json`:

```json
{
  "researchDate": "2026-02-16",
  "competitors": [
    {
      "name": "CompetitorApp",
      "tiktokHandle": "@competitor",
      "followers": 50000,
      "topHooks": ["hook text 1", "hook text 2"],
      "avgViews": 15000,
      "bestVideo": {
        "views": 500000,
        "hook": "The hook that went viral",
        "format": "before-after slideshow",
        "url": "https://tiktok.com/..."
      },
      "format": "before-after slideshows",
      "postingFrequency": "daily",
      "cta": "link in bio",
      "strengths": "Great visuals, consistent posting",
      "weaknesses": "Same hooks every time, no storytelling"
    }
  ],
  "nicheInsights": {
    "trendingSounds": ["sound name 1"],
    "commonFormats": ["before-after", "POV"],
    "averageViews": 15000,
    "topPerformingViews": 500000,
    "gapOpportunities": "Nobody is doing person+conflict hooks in this niche",
    "avoidPatterns": "Price comparison posts get <1K views consistently"
  }
}
```

### 6. Share Findings Conversationally

Don't dump the JSON. Talk about it:

> "So I looked at what's out there in [niche]. The main players are [A], [B], and [C]. [A] is doing well with [format] — their best post got [X] views. But I noticed nobody's really doing [gap]. That's where I think we can win. Here's my plan..."

## Ongoing Research

Don't just research once. During weekly reviews:

- Check if competitors have posted new viral content
- Look for new entrants in the niche
- Monitor trending sounds and formats
- Update `competitor-research.json` with new findings

Reference competitor data when suggesting hooks — "Competitor X got 200K views with a landlord hook, let's try our version."
