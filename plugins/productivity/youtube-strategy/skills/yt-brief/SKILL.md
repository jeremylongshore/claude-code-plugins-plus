---
name: yt-brief
description: |
  Refine a YouTube video idea into a structured production brief with angle, key points, value proposition,
  CTA asset, and audience segment. Use this skill whenever the user says "create a brief", "brief this idea",
  "develop this idea", "write a video brief", "production brief", or has selected a video idea from ideation
  and wants to define the angle and structure before packaging and outlining.
allowed-tools: WebSearch, Read, Write
version: 1.0.0
author: Claude Code Plugins <plugins@claudecodeplugins.io>
license: MIT
---

# YouTube Brief

You are creating a structured production brief for a YouTube video. The brief is the bridge between an idea and a filmable video - it defines what the video IS.

## Before You Start

You need from the user:

1. **The video idea** - Either a validated idea from `/yt-ideate` (with title, tier, type, angle) or a raw idea the user wants to develop
2. **Any constraints** - Timeline, specific features to include/exclude, target length, team capacity

If the user is coming from the ideation flow, load `validated_ideas.json` for the full context on the selected idea.

## The Briefing Process

### Step 1: Research the Topic

Before writing the brief, understand the topic deeply:
- What does this feature/tool actually do? (Use WebSearch if needed)
- What are the common pain points or confusion points?
- What existing content exists? What angle would differentiate this video?
- What's the practical value for the target audience?

### Step 2: Define the Video Identity

Work with the user to lock in:

**Content Type & Tier:**
- Confirm which tier and category this falls under
- This determines the format, length, and production approach

**The Angle:**
- What's the unique take? Why would someone click THIS video over alternatives?
- The angle should be specific and defensible, not generic
- Good: "How to use MCP integrations to automate your marketing reporting without any code"
- Bad: "MCP tutorial"

**Target Audience Segment:**
- Who is the primary viewer?
- What's their starting knowledge level for this topic?

### Step 3: Write the Brief

The brief must include:

1. **Title (working)** - Will be refined in packaging, but needs a clear working title
2. **Content tier & type** - e.g., Tier 1 / Feature Tutorial
3. **The angle** - 1-2 sentences: what makes this video unique
4. **Target audience** - Who exactly is this for, and what do they already know
5. **Key points** - 5-8 main things the viewer will learn or see demonstrated
6. **Value proposition** - After watching, the viewer will be able to [specific outcome]
7. **CTA asset** - What free asset can be given away? (template, skill, workflow, plugin)
8. **Prerequisites** - What does the viewer need to have set up before watching?
9. **Demo requirements** - What tools, accounts, or setups are needed for filming?
10. **Estimated length** - Target duration based on content type
11. **Urgency/timing** - Is this time-sensitive (update video) or evergreen?

### Step 4: Review with User

Present the complete brief and ask:

"Here's the brief for '[title]'. Review it:"

```
[Full brief in clean markdown format]
```

"What would you like to adjust?"
- Approve - move to packaging
- Adjust the angle
- Add/remove key points
- Change the CTA asset
- Change the target audience
- Start over with a different approach

**This is a mandatory human checkpoint. Do NOT proceed without approval.**

### Step 5: Save the Brief

Save the approved brief as `video-brief-{slug}.md` in the working directory.

## Key Principles

- **The angle is everything.** A brief without a clear, differentiated angle will produce a generic video. Push the user to be specific.
- **Practical value first.** Every key point should contribute to the viewer being able to DO something. No filler sections.
- **CTA integration.** The CTA asset should feel like a natural extension of the video content, not a bolted-on pitch.
- **Honest about scope.** If a topic is too big for one video, say so and suggest splitting it. Don't try to cram a Full Tutorial into a Feature Tutorial.
- **Team-ready.** The brief should contain enough detail that a team member could start demo prep without asking follow-up questions.
