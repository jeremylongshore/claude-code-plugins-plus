---
name: yt-research
description: Research competitor channels, niches, and trending topics for YouTube content
argument-hint: [channel-urls-or-topic]
allowed-tools: Read, Write, Edit, Bash, Grep, Glob, Task, WebSearch, AskUserQuestion
model: sonnet
---

Run the YouTube Research skill. This is Stage 1 of the content production workflow - researching competitor channels, analyzing niches, identifying features and topics worth covering.

Read the skill definition at `skills/yt-research/SKILL.md` and follow its workflow exactly.

**You are the orchestrator.** Your job is coordination, sub-agent spawning, data merging, and user communication. Delegate scraping work to `yt-scraper` sub-agents and analysis work to `channel-analyzer` sub-agents.
