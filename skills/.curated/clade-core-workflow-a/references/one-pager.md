# clade-core-workflow-a — One-Pager

Entry point that routes you to the primary Claude workflow: the Messages API.

## The Problem

New users of the claude-pack need a clear starting point for the most common Claude integration task — calling the Messages API with streaming, vision, structured output, and multi-turn conversations. Without a signpost, they may not know which skill to reach for first.

## The Solution

This skill acts as a redirect to `clade-model-inference`, which contains the complete Messages API guide. Rather than duplicating content, it points you to the canonical skill and lists exactly what it covers: streaming with `client.messages.stream()`, vision (image inputs), structured JSON output, and multi-turn conversation management.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Developers new to the claude-pack looking for the primary workflow |
| **What** | Redirect to `clade-model-inference` for all Messages API patterns |
| **When** | When you search for "anthropic workflow" or "claude main workflow" and need to find the right skill |

## Key Features

1. **Clear redirect** — Points directly to `clade-model-inference` as the canonical Messages API skill
2. **Topic index** — Lists covered topics: streaming, vision, structured JSON output, multi-turn conversations
3. **Quick example** — Includes a minimal `client.messages.stream()` snippet so you can verify you are in the right place

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
