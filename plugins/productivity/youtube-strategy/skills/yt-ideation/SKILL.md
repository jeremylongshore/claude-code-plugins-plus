---
name: yt-ideation
description: |
  Generate and validate YouTube video ideas aligned with content pillars, audience strategy,
  and priority tiers. Use this skill whenever the user says "generate ideas", "brainstorm videos",
  "what should I make next", "video ideas", "content ideas", "ideation", "what topics should I cover",
  or wants to come up with new video concepts.
allowed-tools: WebSearch, Read, Write, Task
version: 1.0.0
author: Claude Code Plugins <plugins@claudecodeplugins.io>
license: MIT
---

# YouTube Ideation

You are generating and validating video ideas for a YouTube channel. Every idea must align with the content strategy and serve the target audience.

## Before You Start

You need from the user:

1. **Focus area** - What tool, niche, or topic to ideate around (e.g., "AI tools for professionals", "recent software updates", "productivity workflows")
2. **Research data** (optional) - If `/yt-research` was run first, load `niche-analysis.json` and `niche-report.md` for data-informed ideation
3. **Constraints** (optional) - Any specific requirements (e.g., "only short videos", "needs to be filmable this week", "must tie to a product launch")

If the user provided focus already, confirm and proceed.

## The Ideation Process

### Step 1: Load Context

Understand the creator's:
- **Content pillars** - What core topics does the channel focus on?
- **Audience** - Who are the viewers? What's their skill level?
- **Content types** - What formats work best? (tutorials, reviews, updates, comparisons)
- **Trending vs evergreen** - What's the balance between timely and long-lasting content?

### Step 2: Generate 15-20 Raw Ideas

Use these ideation methods:

**Method 1: Gap Analysis** (if research data available)
- Content gaps from competitor analysis
- Topics with high demand but low competition
- Complex concepts that need accessible translation

**Method 2: Trend Riding**
- Recent tool updates or feature launches
- Industry developments relevant to the audience
- Viral topics that can be made practical

**Method 3: Format Innovation**
- Existing topics in new formats (comparison, mega-guide, use-case compilation)
- Content types competitors aren't using
- Series potential (multi-part tutorials)

**Method 4: Audience Needs**
- Questions the audience is asking (Reddit, YouTube comments, community)
- Problems viewers face with the tools they use
- "How do I..." queries for the niche

For each idea, define:
- **Working title**
- **Content tier** (Tier 1: growth content, Tier 2: supporting content)
- **Content type** (Full Tutorial, Feature Tutorial, Update Video, Use Case Video, Comparison, etc.)
- **One-line angle** (what makes this video unique)
- **Timeliness** (trending/urgent or evergreen)

**Priority distribution:**
- 60-70% Tier 1 ideas (the growth engine)
- 30-40% Tier 2 ideas (supporting content)

### Step 3: Quick Self-Filter

Before validation, run each idea through a strategy test:
- Does it serve the target audience? (Must be yes)
- Can it be practically demonstrated? (Prefer yes)
- Does it support the content funnel? (Can we give away an asset?)
- Is it filmable in the current format?

Remove ideas that fail the test. Note why for transparency.

### Step 4: Validate Ideas

Spawn `idea-validator` sub-agents (5 ideas per agent) to assess:
- Search demand (YouTube autocomplete, Google Trends, forums)
- Competition level (existing videos, quality bar)
- Trend direction (rising, stable, declining)
- Audience fit (accessibility, practical value)

Each sub-agent returns an opportunity score (1-10) per idea.

### Step 5: Present Ranked Results

Present ideas to the user sorted by opportunity score:

```markdown
Here are your validated video ideas, ranked by opportunity:

| # | Title | Tier | Type | Demand | Competition | Score |
|---|-------|------|------|--------|-------------|-------|
| 1 | [title] | Tier 1 | Feature Tutorial | High | Low | 9.2 |
| 2 | [title] | Tier 1 | Update Video | High | Medium | 8.5 |
...

Top recommendation: [title] - [1 sentence why]

Which ideas do you want to develop into briefs?
```

Options:
- Pick 1-3 ideas to brief
- Generate more ideas in a different direction
- Refine a specific idea before briefing
- Go back to research

## Key Principles

- **Tier 1 first** - Always prioritize growth content (tutorials, use cases, updates). These drive channel growth.
- **Audience-appropriate** - Every idea must pass the "would the target viewer find this useful?" test.
- **Practical over theoretical** - Favor ideas where the viewer walks away with something they can DO.
- **CTA-ready** - Strong ideas include a natural asset giveaway (template, workflow, plugin) that ties to the creator's business.
- **Data-informed** - When research data is available, use it. Gut-feel ideation is a fallback, not the default.
