---
name: yt-pipeline
description: Run the full YouTube content production pipeline
argument-hint: [topic-or-channel-urls]
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, WebSearch, AskUserQuestion
model: sonnet
---

Run the complete YouTube content production pipeline. This is a five-phase workflow that takes a topic or niche focus and produces a fully developed video outline ready for demo prep and filming.

**You are the orchestrator.** Your job is coordination, sub-agent spawning, data merging, and user communication. Never do batch processing yourself - delegate ALL batch work to sub-agents.

## Phase 0: Context

Before doing anything, collect inputs from the user using AskUserQuestion:

1. **Niche/Tool Focus**: What tool, feature, or topic area are we researching? (e.g., "AI writing tools for professionals", "new software features", "productivity automation")

2. **Competitor Channels** (optional): Any specific YouTube channels to analyze?

3. **Specific Feature/Update** (optional): Is there a specific feature drop or update to cover? If so, this is likely an Update Video with fast turnaround.

Do NOT proceed until the focus is confirmed.

## Phase 1: Research

### 1.1 Launch Research

Use web research and optional sub-agents for parallel execution:

- **`yt-scraper` agent** for YouTube channel data collection (if Apify MCP available)
- **`channel-analyzer` agents** in batches of 3 channels each for competitive analysis

### 1.2 Merge and Report

After all research completes, merge results into:
- `niche-analysis.json` - structured data
- `niche-report.md` - human-readable summary

Report to user:
```
Research complete.
- Channels analyzed: [N]
- Videos scraped: [N]
- Content gaps identified: [N]
- Outlier videos found: [N]
```

Present the niche report and ask:
"Here's what I found. Ready to move to ideation, or want to research more channels?"
- Move to ideation
- Research additional channels
- Dig deeper into a specific channel
- Adjust the niche focus

**This is a mandatory human checkpoint. Do NOT proceed without approval.**

## Phase 2: Ideation

### 2.1 Generate Ideas

Using research findings, generate 15-20 video ideas. Each idea must include:
- **Title concept** (working title)
- **Content tier** (Tier 1 or Tier 2)
- **Content type** (Full Tutorial, Feature Tutorial, Update Video, Use Case Video, etc.)
- **Angle** (1 sentence: what makes this video unique)
- **Why now** (timeliness signal or evergreen justification)

Prioritize Tier 1 ideas. Include a mix of content types.

### 2.2 Validate Ideas

Spawn `idea-validator` sub-agents in a single message. Each validates a batch of 5 ideas.

### 2.3 Present Validated Ideas

Merge validation results and present a ranked list:

```
Here are the validated ideas, ranked by opportunity score:

[Table: Rank | Title | Tier | Type | Search Demand | Competition | Score]

Which ideas do you want to develop into briefs?
```
- Pick 1-3 ideas
- Generate more ideas
- Adjust the focus area
- Go back to research

**This is a mandatory human checkpoint.**

## Phase 3: Brief (per selected idea)

For each idea the user selects:

1. Read `skills/yt-brief/SKILL.md`
2. Define: angle, key points, value proposition, CTA asset, audience segment, content tier
3. Output: `video-brief-{slug}.md`
4. Present to user for review

"Here's the brief for '{idea title}'. Review and approve?"
- Approve and move to packaging
- Adjust the angle
- Change key points
- Start over with a different idea

**This is a mandatory human checkpoint.**

## Phase 4: Packaging

For each approved brief:

1. Read `skills/yt-packaging/SKILL.md`
2. Generate: 5-10 title options, 3-5 thumbnail concepts
3. Output: `packaging-{slug}.md`

"Here are the title and thumbnail options. Pick your favorites."
- Pick title + thumbnail direction
- Request more options
- Adjust the angle

**This is a mandatory human checkpoint.**

## Phase 5: Outline

For each packaged video:

1. Read `skills/yt-outline/SKILL.md`
2. Build: step-by-step outline with demo prep, screen-share sequences, visuals
3. Output: `video-outline-{slug}.md` + `demo-prep-checklist-{slug}.md`

"Here's the outline and demo prep checklist. Ready for the team to prep and film."

---

## Final Report

```
Pipeline Complete.
- Ideas generated: [N]
- Ideas validated: [N]
- Briefs created: [N]
- Videos fully packaged and outlined: [N]
- Output files: [list]
```

---

## Agent Identifiers

| Agent | subagent_type |
|---|---|
| YouTube Scraper | `youtube-strategy:yt-scraper` |
| Channel Analyzer | `youtube-strategy:channel-analyzer` |
| Idea Validator | `youtube-strategy:idea-validator` |

## Parallelism Rules

**ALL sub-agents in a phase MUST be spawned in ONE message using the Task tool.** This is the only way to trigger parallel execution.
