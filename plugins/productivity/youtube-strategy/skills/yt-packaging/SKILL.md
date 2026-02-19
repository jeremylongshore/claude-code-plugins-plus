---
name: yt-packaging
description: |
  Create optimized YouTube titles and thumbnail concepts for maximum CTR. Use this skill whenever the user
  says "title ideas", "thumbnail concepts", "package this video", "CTR optimization", "title options", "packaging",
  or has an approved brief and needs to finalize the title and thumbnail direction before outlining. Packaging
  determines whether viewers click.
allowed-tools: WebSearch, Read, Write
version: 1.0.0
author: Claude Code Plugins <plugins@claudecodeplugins.io>
license: MIT
---

# YouTube Packaging

You are creating the title and thumbnail concept for a YouTube video. Packaging is where CTR is determined - the title and thumbnail are the single biggest factor in whether a video succeeds.

## Before You Start

You need from the user:

1. **The approved brief** - Either load `video-brief-{slug}.md` from the working directory or get the brief details from the user
2. **Timing context** - Is this a trending/update video (speed matters) or evergreen (optimize for long-term search)?
3. **Competitive context** - What titles are competitors using for similar content? (Use WebSearch if not already known)

## The Packaging Process

### Step 1: Competitive Title Analysis

Before writing titles, research what's already out there:
- Search YouTube for the topic
- Note the top 5-10 existing titles
- Identify patterns: what words/structures appear in high-view videos?
- Identify gaps: what angle is NO ONE using?

### Step 2: Generate Title Options

Create 5-10 title options across different strategies:

**Strategy A: Direct Benefit**
Focus on what the viewer will be able to DO.
- "How to [Verb] [Tool] to [Outcome]"
- "Build [Thing] with [Tool] in [Time]"

**Strategy B: Curiosity Gap**
Create intrigue without being misleading.
- "The [Tool] Feature Nobody Is Talking About"
- "I Automated My Entire [Process] - Here's How"

**Strategy C: Authority/Definitive**
Position as THE resource.
- "The Complete [Tool] Guide for [Year]"
- "Everything You Need to Know About [Feature]"

**Strategy D: Trending/Urgency**
For update videos and time-sensitive content.
- "[Tool] Just Changed Everything - Here's What You Need to Know"
- "New [Feature] Walkthrough: [Specific Capability]"

**For each title:**
- Note which strategy it uses
- Estimate search-friendliness (contains searchable keywords?)
- Estimate curiosity factor (would you click?)
- Note the character count (aim for under 60 characters for full display)

### Step 3: Generate Thumbnail Concepts

Create 3-5 thumbnail concepts. Each concept should include:

**Visual description:**
- Main visual element (screen-share preview, tool logo, face expression, graphic)
- Text overlay (1-4 words MAX - the thumbnail is not the title)
- Color scheme and contrast
- Layout (rule of thirds, focal point)

**For each concept:**
- How does it complement the title? (Title + thumbnail = one message, not two separate messages)
- Does it stand out in a feed of similar videos?
- Is it readable at mobile size (small thumbnail)?
- Does it communicate the value proposition visually?

### Step 4: A/B Test Variants

For the top 2-3 title + thumbnail combos, suggest A/B testing variants:
- Same title, different thumbnail approach
- Same thumbnail, different title strategy
- Small tweaks (word swaps, number inclusion)

### Step 5: Present to User

Present all options in a structured format:

```markdown
## Title Options

| # | Title | Strategy | Keywords | Length |
|---|-------|----------|----------|--------|
| 1 | [title] | Direct Benefit | [keywords] | 48 chars |
| 2 | [title] | Curiosity Gap | [keywords] | 52 chars |
...

## Thumbnail Concepts

### Concept A: [Name]
- Visual: [description]
- Text overlay: "[text]"
- Complements titles: #1, #3

### Concept B: [Name]
- Visual: [description]
- Text overlay: "[text]"
- Complements titles: #2, #4

## Recommended Combo

Title #[X] + Thumbnail Concept [Y] because [reasoning]
```

"Pick your title and thumbnail direction."
- Go with recommended combo
- Mix and match (pick different title + thumbnail)
- Request more options
- Adjust the angle

**This is a mandatory human checkpoint.**

### Step 6: Save

Save the approved packaging as `packaging-{slug}.md`.

## Key Principles

- **Title and thumbnail are ONE system.** They must work together. The thumbnail should NOT repeat the title - they should complement each other. Title says what, thumbnail shows the emotion/intrigue.
- **No clickbait without substance.** Titles should be compelling but honest. Every promise in the title must be delivered in the video.
- **Search + browse balance.** For evergreen content, include searchable keywords. For trending content, prioritize curiosity and urgency.
- **Mobile-first thumbnails.** Most YouTube browsing happens on mobile. Thumbnails must be readable at small sizes.
- **Under 60 characters.** Titles get truncated on mobile. The most important words should be in the first 40 characters.
