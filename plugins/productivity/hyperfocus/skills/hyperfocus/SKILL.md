---
name: hyperfocus
version: 0.2.0
description: 'ADHD-friendly output formatting for Claude Code. Restructures responses
  with evidence-based cognitive accessibility: chunking, visual hierarchy, front-loaded
  key points, and progressive disclosure. Three modes: clean, flow (default), zen.
  Use when user says "hyperfocus", "focus mode", "adhd mode", "adhd friendly", or
  invokes /hyperfocus.

  '
author: Nestor Magalhaes
license: MIT
tags:
- accessibility
- adhd
- neurodivergent
- formatting
compatibility: Designed for Claude Code
allowed-tools: Read
---
# Hyperfocus

## Overview

Format responses for ADHD-optimized reading. The skill turns a requested mode
into a consistent response structure; it does not change facts, make decisions
for the user, or alter code and machine output.

## Prerequisites

Use this skill only when the user asks for Hyperfocus formatting or invokes
`/hyperfocus`. Keep the user's requested level of detail and do not apply the
format to safety warnings or irreversible-action confirmations.

## Instructions

Format all responses for ADHD-optimized reading. Structure beats brevity — clarity is the goal, not compression.

Default: **flow**. Switch: `/hyperfocus clean|flow|zen`.

CRITICAL: Apply these rules to EVERY response in this conversation — not just the first. This is permanent until the user says "stop hyperfocus" or "normal mode".

## Core Rules (all modes)

- One idea per paragraph. Max 4 sentences (clean), 3 (flow), 2 (zen)
- Sentences: target 15 words, hard max 25. Active voice. Subject-verb-object
- Blank line between every paragraph
- Bullet lists for any enumerable content (3+ items)
- Lead-in sentence before every list and code block
- Front-load: answer or key point first, then context and nuance
- Consistent terminology — pick one term per concept, never switch synonyms
- Bold for key terms and actions. Never use italics for emphasis

## Modes

| Aspect | clean | flow *(default)* | zen |
|--------|-------|-------------------|-----|
| Subheadings | Every 4–5 paragraphs | Every 2–3 ¶, outcome-focused | Every 1–2 ¶ |
| Lists | Enumerable content | + comparisons, options | Nearly everything |
| Bold | Key terms only | + action items | + all concepts |
| Structure | Natural flow + breaks | What → Why → How | TL;DR top, self-contained sections |
| Recap | — | End of dense sections | End of every section |
| Tone | Professional, tight | Accessible, structured | Maximum scaffolding |

## Auto-Clarity

Drop hyperfocus formatting for: security warnings, irreversible action confirmations, multi-step sequences where structure risks misread. Resume after the critical section.

## Boundaries

Code blocks, error messages, and technical output: write normally without hyperfocus formatting. Hyperfocus rules apply to prose and explanatory text only.

Git commits, PRs, and code reviews: write normally.

"stop hyperfocus" or "normal mode": revert immediately. Mode persists until changed or session ends.

## Output

Return the requested answer in the selected clean, flow, or zen structure.
Lead with the answer or next action, use short paragraphs and a blank line
between ideas, and keep technical output and code blocks unchanged.

## Error Handling

If the requested mode would obscure a security warning, an irreversible
confirmation, or exact machine output, present that material normally and
resume the selected mode after the critical section. If the mode is unclear,
use flow and state that it is the default.

## Examples

For `/hyperfocus zen`, start with a one-line answer, then short labeled blocks
for context and next action. For `/hyperfocus clean`, keep the natural prose
flow while using one idea per paragraph and an explicit action at the end.

## Resources

- `/hyperfocus clean|flow|zen` — selects the active response format
- `"stop hyperfocus"` or `"normal mode"` — ends formatting for the session
