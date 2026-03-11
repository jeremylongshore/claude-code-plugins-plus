---
name: langfuse-cost-tuning
description: |
  Monitor and optimize LLM costs using Langfuse analytics and dashboards.
  Use when tracking LLM spending, identifying cost anomalies,
  or implementing cost controls for AI applications.
  Trigger with phrases like "langfuse costs", "LLM spending",
  "track AI costs", "langfuse token usage", "optimize LLM budget".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Langfuse Cost Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Track, analyze, and optimize LLM costs using Langfuse observability data with token tracking, cost alerts, model selection optimization, and automated reporting.

## Prerequisites
- Langfuse tracing with token usage
- Understanding of LLM pricing models
- Access to Langfuse analytics dashboard

## Instructions

### Step 1: Track Token Usage in Generations
Record prompt and completion tokens on each `generation.end()` call. Calculate cost using per-model pricing tables and store as metadata.

### Step 2: Create Cost Dashboard Queries
Fetch generations from Langfuse and aggregate costs by model, by day, and by token type. Calculate total cost and generation count.

### Step 3: Implement Cost Alerts
Build a CostMonitor that tracks hourly and daily spend. Define thresholds (e.g., $100/day warn, $500/day notify, $1/request warn). Send Slack/PagerDuty notifications on breaches.

### Step 4: Optimize Model Selection
Route simple tasks (summarize, classify, extract) and short inputs to cheaper models (GPT-4o-mini). Reserve expensive models for complex tasks (analyze, reason, code).

### Step 5: Add Caching and Prompt Optimization
Cache LLM responses with TTL. Strip redundant whitespace and filler words from prompts to reduce token count.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Token usage tracking per generation
- Cost analytics aggregation
- Real-time cost alerts
- Smart model selection
- Response caching and prompt optimization

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Missing usage data | SDK not capturing | Verify generation.end() includes usage |
| Inaccurate costs | Wrong pricing | Update MODEL_PRICING regularly |
| Budget exceeded | No alerts | Implement cost alerts |
| Report failures | API limits | Add pagination to fetchGenerations |

## Examples

### LLM Cost Reference
| Model | Input (per 1M) | Output (per 1M) |
|-------|----------------|-----------------|
| GPT-4 Turbo | $10.00 | $30.00 |
| GPT-4o | $5.00 | $15.00 |
| GPT-4o-mini | $0.15 | $0.60 |
| Claude 3 Opus | $15.00 | $75.00 |
| Claude 3 Sonnet | $3.00 | $15.00 |
| Claude 3 Haiku | $0.25 | $1.25 |

### Cost Optimization Strategies
| Strategy | Potential Savings | Effort |
|----------|-------------------|--------|
| Model downgrade | 50-90% | Low |
| Prompt optimization | 10-30% | Low |
| Response caching | 20-60% | Medium |
| Batch processing | 10-20% | Medium |

## Resources
- [Langfuse Analytics](https://langfuse.com/docs/analytics)
- [OpenAI Pricing](https://openai.com/pricing)
- [Anthropic Pricing](https://www.anthropic.com/pricing)
