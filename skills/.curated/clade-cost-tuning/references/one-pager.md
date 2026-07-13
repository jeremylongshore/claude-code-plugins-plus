# clade-cost-tuning — One-Pager

Cut Anthropic API costs by up to 97% with model selection, caching, batches, and token reduction.

## The Problem

Anthropic charges per token, and costs escalate fast at scale. Developers default to expensive models for every task, send bloated system prompts on every call, process bulk workloads synchronously at full price, and have no visibility into per-request spend. A 10,000-document pipeline on Opus costs $225; the same job optimized costs $5.

## The Solution

This skill provides a five-step cost reduction framework: right-size models per task complexity (Haiku for classification, Sonnet for coding, Opus for reasoning), enable prompt caching for 90% savings on repeated system prompts, use Message Batches for 50% off non-urgent work, reduce token counts by trimming conversation history and setting tight `max_tokens`, and log per-request costs. Includes a full pricing table and a worked cost comparison example.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Teams with active Anthropic API usage looking to reduce spend |
| **What** | Model selection, prompt caching, batch processing, token reduction, and usage monitoring strategies |
| **When** | After initial integration works and you need to optimize for production-scale costs |

## Key Features

1. **Model right-sizing** — Match task complexity to model: Haiku ($0.80/MTok input) for simple extraction, Sonnet ($3/MTok) for general tasks, Opus ($15/MTok) for complex reasoning
2. **Prompt caching** — Cache system prompts with `cache_control: { type: 'ephemeral' }` for 90% input token savings after the first call (5-minute TTL, 1024+ token minimum)
3. **Message Batches** — Process bulk workloads at 50% off with a 24-hour SLA via `client.messages.batches.create()`
4. **Token reduction** — Trim conversation history to last N turns, set tight `max_tokens`, use concise system prompts
5. **Usage monitoring** — Log `input_tokens` and `output_tokens` per request with cost calculations per model tier

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
