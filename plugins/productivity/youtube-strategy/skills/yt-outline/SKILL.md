---
name: yt-outline
description: |
  Build detailed step-by-step YouTube video outlines with demo prep, screen-share sequences, and visual
  planning. Use this skill whenever the user says "create an outline", "outline this video", "video outline",
  "build the outline", "production outline", or has an approved brief and packaging and needs the final
  pre-production document before demo prep and filming.
allowed-tools: WebSearch, Read, Write
version: 1.0.0
author: Claude Code Plugins <plugins@claudecodeplugins.io>
license: MIT
---

# YouTube Outline

You are creating a detailed production outline for a YouTube video. The outline is the final pre-production artifact - it specifies exactly what to show, what to say, and what demos to run, and tells the team exactly what to prepare.

## Before You Start

You need:

1. **The approved brief** - Load `video-brief-{slug}.md` from the working directory
2. **The approved packaging** - Load `packaging-{slug}.md` for the final title and thumbnail direction
3. **Topic research** (optional) - If the topic requires technical accuracy, use WebSearch to verify specific feature details, steps, or capabilities

## The Outline Process

### Step 1: Research the Topic in Depth

Before writing the outline, deeply understand the feature/tool being demonstrated:
- Verify all steps work as expected (use WebSearch to check documentation)
- Identify potential gotchas or failure points
- Note any prerequisites the viewer needs
- Find the shortest path to the value proposition (minimize setup time in the video)

### Step 2: Define the Video Structure

Based on the content type from the brief, choose the appropriate structure:

**For Feature Tutorials (15-30 min):**
1. Hook (30-60 sec) - What they'll be able to do by the end
2. Context (1-2 min) - Why this matters, brief overview
3. Core demonstration (10-20 min) - Step-by-step walkthrough
4. Advanced tips (2-3 min) - Power user moves
5. CTA + wrap (1-2 min) - Asset giveaway, community mention

**For Update Videos (10-20 min):**
1. Hook (30 sec) - What just changed
2. Overview (1-2 min) - What the update includes
3. Walkthrough (8-15 min) - Demo each new feature
4. Impact (1-2 min) - What this means for you
5. CTA + wrap (1 min) - Asset giveaway

**For Use Case Videos (15-30 min):**
1. Hook (30-60 sec) - The impressive outcome
2. Problem (1-2 min) - What manual process this replaces
3. Solution overview (1-2 min) - High-level workflow
4. Step-by-step build (10-20 min) - Building the workflow live
5. Results (2-3 min) - Actual metrics and outcomes
6. CTA + wrap (1-2 min) - Asset giveaway

**For Full Tutorials (30-90+ min):**
1. Hook (1-2 min) - What they'll know by the end
2. Overview/roadmap (2-3 min) - What the tutorial covers
3. Setup (5-10 min) - Getting started from scratch
4. Core sections (20-60 min) - Organized by feature/capability
5. Advanced section (5-10 min) - Power user techniques
6. Summary + next steps (2-3 min) - Recap + what to learn next
7. CTA (1-2 min) - Asset giveaway

### Step 3: Write the Detailed Outline

For each section, specify:

**Talking points:**
- Key message for this section (not a script - bullet points)
- Transition from previous section
- Any specific phrases or analogies to use

**What's on screen:**
- Screen-share of what tool/feature
- Specific actions to perform (click here, type this, navigate there)
- Any diagrams, slides, or supporting visuals

**Demo sequence:**
- Exact steps to demonstrate
- Expected outcome the viewer should see
- What to do if something goes wrong (backup plan)

**Timing:**
- Target duration for this section
- Running total to stay within target video length

### Step 4: Create Demo Prep Checklist

For each demo in the outline, specify what the team needs to prepare:
- Accounts and tools to have logged in
- Sample data or projects to have ready
- Environment settings (clean workspace, no notifications, etc.)
- Backup plans (what if the live demo fails?)

### Step 5: Present and Review

Present the outline to the user:

```markdown
## Video Outline: [Title]

Total estimated length: [X] minutes

[Full section-by-section outline]
```

Also present the demo prep checklist separately:

```markdown
## Demo Prep Checklist: [Title]

[Full checklist organized by demo sequence]
```

"Here's the outline and demo prep list. The team can start preparing."
- Approve and start prep
- Adjust section order
- Add/remove sections
- Change demo approach
- Need more detail on a specific section

### Step 6: Save

Save two files:
- `video-outline-{slug}.md` - The full outline
- `demo-prep-checklist-{slug}.md` - The team's preparation checklist

## Key Principles

- **Show, don't tell.** Every section should have something on screen. Minimize talking-head time. The value is in the demonstration.
- **Shortest path to value.** Get to the first "wow" moment as fast as possible. Front-load the payoff, then go deeper.
- **Direct and practical.** The outline should reflect a direct, no-fluff style. No "in this section we'll cover..." filler. Just do the thing.
- **Team-ready.** The demo prep checklist should be detailed enough that a team member can prepare everything without asking questions.
- **Timing is real.** Be honest about section durations. A 20-minute video with 25 minutes of outline is a problem. Cut or restructure.
- **Failure-proofed.** For every live demo, include a backup plan. If the API call times out, if the feature bugs out - what's the fallback?
