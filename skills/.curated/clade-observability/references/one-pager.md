# clade-observability — One-Pager

Monitor every Claude API call with structured logging for tokens, latency, costs, and errors.

## The Problem

Anthropic does not provide detailed API-level logging or per-request cost tracking. Without instrumentation, teams cannot answer basic operational questions: what is our p95 latency, how much are we spending per feature, which requests are failing, and are we approaching rate limits? Problems surface as surprise bills or user-facing outages instead of early alerts.

## The Solution

This skill provides a drop-in logging wrapper (`trackedCreate`) that captures tokens, latency, cost estimates, and errors for every Claude API call. It includes a cost estimation function with per-model pricing (Haiku/Sonnet/Opus), a metrics table with alert thresholds for error rate, p95 latency, daily cost, and 429/529 rates, plus guidance on using the Anthropic console for spending limits.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Teams running Claude in production who need operational visibility |
| **What** | Instruments every messages.create() call with structured logs covering tokens, latency, cost, model, and errors |
| **When** | Before going to production, or when debugging cost/latency/error issues in an existing deployment |

## Key Features

1. **trackedCreate Wrapper** — Drop-in replacement for client.messages.create() that logs timestamp, model, token counts, cache hits, duration, stop reason, and estimated cost
2. **Per-Model Cost Estimation** — estimateCost() function with current Opus/Sonnet/Haiku pricing per million tokens for accurate spend tracking
3. **Alert Threshold Table** — Six key metrics (error rate, p95 latency, daily cost, 429 rate, 529 rate, token budget) with recommended thresholds for production alerting

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
