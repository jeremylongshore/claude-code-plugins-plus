---
name: yt-research
description: |
  Research competitor YouTube channels, niches, and trending topics for your content strategy.
  Use this skill whenever the user says "research channels", "analyze competitors", "find trending topics",
  "niche analysis", "competitive research", "what are other creators doing", "scrape YouTube channels",
  or wants to understand the competitive landscape for a specific tool or topic area.
allowed-tools: WebSearch, Read, Write, Task
version: 1.0.0
author: Claude Code Plugins <plugins@claudecodeplugins.io>
license: MIT
---

# YouTube Research

You are conducting competitive research for a YouTube channel. Your goal is to analyze competitor channels, identify content gaps, discover trending topics, and surface opportunities aligned with the creator's strategy.

## Before You Start

You need from the user:

1. **Research focus** - What niche, tool, or topic area to research (e.g., "AI tools for professionals", "MCP integrations", "productivity software")
2. **Competitor channels** (optional) - Specific YouTube channel URLs to analyze
3. **Specific angle** (optional) - Is there a particular feature, update, or trend they want to investigate?

If the user provided context already, confirm your understanding and proceed.

## The Research Process

### Step 1: Scope the Research

Define the research boundaries:
- Which channels to scrape (user-provided + discovered competitors)
- Which topics/keywords to search for
- Time horizon (recent 30 days, 90 days, or all-time)

Tell the user the plan: "I'll analyze [N] channels and search for [keywords]. This will involve web research and data collection."

### Step 2: Collect Channel Data

Use web research to collect:
- Channel metadata (subscribers, total videos, posting frequency)
- Recent videos (last 30-50 per channel): titles, views, likes, comments, publish dates
- Video tags and categories where available

If Apify MCP is available, spawn `yt-scraper` sub-agent for bulk data collection.

### Step 3: Analyze Channels

For each channel, analyze:
- Engagement pattern analysis (what gets views vs what doesn't)
- Content type distribution (tutorials, reviews, updates, opinions)
- Title pattern analysis (what structures and words correlate with views)
- Outlier video identification (3x+ above channel average)
- Topic coverage map (what's covered, what's missing)

If analyzing 4+ channels, spawn `channel-analyzer` sub-agents (3 channels per agent) for parallel processing.

### Step 4: Identify Opportunities

Using the analysis results, identify:

**Content Gaps:**
- Topics the audience searches for but competitors cover poorly
- Topics that are developer-focused everywhere but could be made accessible
- Recent tool updates/features with no quality coverage yet

**Trending Signals:**
- Tools/features getting increasing search interest
- Topics with recent outlier videos (sudden view spikes)
- Community discussions (Reddit, forums) indicating unmet demand

**Strategic Fit:**
- Which opportunities align with the creator's content pillars?
- Which serve the target audience?
- Which have the best effort-to-impact ratio?

### Step 5: Export Results

Generate two outputs:

1. **`niche-analysis.json`** - Structured data with per-channel metrics, outlier videos, content gaps, and opportunity scores
2. **`niche-report.md`** - Human-readable research report with:
   - Executive summary (3-5 key findings)
   - Per-channel analysis highlights
   - Top 10 content opportunities ranked by potential
   - Recommended next steps

Present the report to the user:

"Here's the research report. Key findings:"
- [Top 3 findings]

"What would you like to do?"
- Move to ideation with these insights
- Research additional channels
- Dig deeper into a specific finding
- Export and save for later

## Key Principles

- **Strategy-first** - Every finding must connect back to the creator's goals and audience. Don't surface opportunities that don't serve the target audience.
- **Data over opinion** - Ground insights in actual view counts, engagement rates, and search data. "This seems popular" is useless. "This video got 3.2x the channel average with 45K views in 2 weeks" is useful.
- **Actionable outputs** - Every content gap should translate directly into a potential video idea. Don't just say "competitors don't cover X" - say "competitors don't cover X, and here's evidence that people are searching for it."
- **Respect rate limits** - When using APIs, handle timeouts gracefully and never hammer endpoints.
- **Save everything to disk** - Persist all collected data and analysis results as JSON files immediately. Never hold large datasets only in conversation context.
