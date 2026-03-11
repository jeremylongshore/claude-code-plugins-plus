---
name: twinmind-cost-tuning
description: |
  Optimize TwinMind costs across Free, Pro, and Enterprise tiers.
  Use when analyzing usage patterns, reducing costs,
  or choosing the right pricing tier for your needs.
  Trigger with phrases like "twinmind cost", "reduce twinmind spending",
  "twinmind pricing optimization", "twinmind budget".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# TwinMind Cost Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize TwinMind costs through usage analysis, tier selection, budget monitoring, token optimization, and quota management.

## Prerequisites
- TwinMind account with billing access
- Understanding of usage patterns
- Access to usage analytics

## Instructions

### Step 1: Understand Pricing Structure
Model the Free ($0, unlimited transcription, 500K tokens), Pro ($10/mo, Ear-3 model, 2M tokens), and Enterprise (custom pricing, unlimited tokens) tiers with `TierPricing` interface.

### Step 2: Analyze Current Usage
Build a `CostAnalysis` that fetches last-30-day usage (transcription hours, API requests, AI tokens, storage) and calculates estimated cost per tier to recommend the optimal plan.

### Step 3: Implement Cost Monitoring
Create a `CostMonitor` with configurable budget thresholds (warning at 80%, critical at 95%). Check hourly and send Slack/email alerts when thresholds are crossed.

### Step 4: Optimize Token Usage
Analyze token usage by feature (summary, chat, memory_search). Offer brief (200 tokens), standard (500), and detailed (800) summary options. Implement response caching.

### Step 5: Implement Usage Quotas
Build `QuotaManager` with daily limits for transcription hours, API requests, and AI tokens. Add Express middleware to reject requests when quotas are exceeded (429).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete pricing models, cost analyzer, budget monitor, and quota manager code.

## Output
- Pricing structure analysis
- Usage cost analyzer
- Budget monitoring system
- Token optimization strategies
- Quota management

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Unexpected charges | Usage spike | Set up budget alerts |
| Quota exceeded | High usage | Implement rate limiting |
| Wrong tier | Poor planning | Analyze usage patterns quarterly |

## Examples


**Basic usage**: Apply twinmind cost tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize twinmind cost tuning for production environments with multiple constraints and team-specific requirements.

## Pricing Comparison

| Feature | Free | Pro ($10/mo) | Enterprise |
|---------|------|--------------|------------|
| Transcription | Unlimited | Unlimited | Unlimited |
| API Access | No | Yes | Yes |
| Ear-3 Model | No | Yes | Yes |
| Context Tokens | 500K | 2M | Unlimited |
| Rate Limits | 30/min | 60/min | 300/min |

## Resources
- [TwinMind Pricing](https://twinmind.com/pricing)
- [Usage Dashboard](https://twinmind.com/settings/usage)
- [Enterprise Plans](https://twinmind.com/enterprise)

## Next Steps
For reference architecture, see `twinmind-reference-architecture`.