---
name: yt-ideate
description: Generate and validate video ideas aligned with content pillars
argument-hint: [topic-or-niche-focus]
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, WebSearch, AskUserQuestion
model: sonnet
---

Run the YouTube Ideation skill. This is the ideation stage of the content production workflow - generating video ideas within the right content pillars and priority tiers, then validating them against search demand and competition.

Read the skill definition at `skills/yt-ideation/SKILL.md` and follow its workflow exactly.

**You are the orchestrator.** Delegate idea validation to `idea-validator` sub-agents in parallel batches of 5 ideas each.
