---
name: deepgram-cost-tuning
description: |
  Optimize Deepgram costs and usage for budget-conscious deployments.
  Use when reducing transcription costs, implementing usage controls,
  or optimizing pricing tier utilization.
  Trigger with phrases like "deepgram cost", "reduce deepgram spending",
  "deepgram pricing", "deepgram budget", "optimize deepgram usage".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Cost Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize Deepgram usage and costs through budget-aware transcription, smart model selection, audio preprocessing to reduce duration, usage dashboards, and multi-level cost alerts.

## Prerequisites
- Active Deepgram project with usage data
- Understanding of Deepgram pricing tiers
- Budget limits defined
- Monitoring infrastructure

## Instructions

### Step 1: Build Budget-Aware Transcription Service
Track monthly spend and minutes used. Check budget before each request. Throw error if projected cost exceeds monthly limit. Warn at configurable threshold (e.g., 80%).

### Step 2: Reduce Audio Duration
Use ffmpeg to remove silence (threshold -30dB, min 0.5s) and optionally speed up audio (1.25x). Measure savings as percentage reduction.

### Step 3: Implement Usage Dashboard
Query Deepgram's usage API to aggregate minutes and cost by model and by day. Calculate monthly projections from daily averages.

### Step 4: Configure Cost Alerts
Set daily ($10), weekly ($50), and monthly ($200) spend limits. Deduplicate alerts per day. Send via Slack, email, or webhook.

### Step 5: Smart Model Selection
Recommend cheapest model that meets quality requirements and fits remaining budget. Nova-2 and Nova at $0.0043/min for high quality; Base at $0.0048/min for basic needs.

### Step 6: Disable Expensive Features When Possible
Skip diarization (+$0.0044/min) when speaker identification is not needed. Keep smart formatting (included free).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Budget-aware transcription with auto-blocking
- Audio duration reduction pipeline
- Usage analytics dashboard
- Multi-level cost alerts
- Cost-optimized model selection

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Budget exceeded | No controls | Enable budget check before transcription |
| Unexpected charges | Diarization on | Disable unneeded features |
| Usage spike | Batch job | Set concurrency limits |
| Alert fatigue | Low thresholds | Tune alert levels, deduplicate |

## Examples

### Deepgram Pricing
| Model | Price/Minute | Best For |
|-------|-------------|----------|
| Nova-2 | $0.0043 | General transcription |
| Nova | $0.0043 | General transcription |
| Whisper Cloud | $0.0048 | Multilingual |
| Base | $0.0048 | Basic transcription |
| Diarization | +$0.0044 | Speaker identification |

### Cost Optimization Strategies
| Strategy | Savings | Effort |
|----------|---------|--------|
| Remove silence | 10-40% | Low |
| Disable diarization | ~50% | Low |
| Use Base model | Variable | Low |
| Cache results | 20-60% | Medium |
| Speed up audio | 10-20% | Low |

## Resources
- [Deepgram Pricing](https://deepgram.com/pricing)
- [Usage API Reference](https://developers.deepgram.com/reference/get-usage)
- [Cost Optimization Guide](https://developers.deepgram.com/docs/cost-optimization)
