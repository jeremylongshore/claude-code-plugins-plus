# clade-prod-checklist — One-Pager

Pre-launch verification checklist for Claude-powered applications.

## The Problem

Shipping a Claude integration without verifying security, error handling, cost controls, and monitoring leads to production incidents — exposed API keys, runaway costs, silent failures, and poor user experience under load.

## The Solution

A structured, verifiable checklist covering every production concern: authentication and key management, error handling for all Anthropic error codes, streaming configuration, cost controls (model selection, max_tokens, caching), monitoring (latency, tokens, error rates), reliability (retries, timeouts, degradation), content compliance, and performance benchmarks.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Backend engineers and DevOps preparing a Claude app for launch |
| **What** | Comprehensive go/no-go checklist across 8 production domains |
| **When** | After feature-complete, before deploying to production |

## Key Features

1. **Security audit items** — API key rotation, server-side enforcement, input validation, injection guardrails
2. **Error handling matrix** — Specific actions for 429 (backoff), 529 (fallback), 401 (alert), 400 (log), and network errors
3. **Cost and performance gates** — Realistic max_tokens, prompt caching, model-right-sizing, p95 latency targets

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
