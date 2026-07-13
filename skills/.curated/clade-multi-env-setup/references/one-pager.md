# clade-multi-env-setup — One-Pager

Configure Claude with different API keys, models, and limits across dev, staging, and production environments.

## The Problem

Using the same Claude configuration across all environments leads to either wasted money (Sonnet/Opus prices in development) or unreliable production behavior (dev-level retries and token limits in production). Without separate API keys, a single compromised key exposes your entire billing account, and spending anomalies in dev are invisible against production usage.

## The Solution

This skill provides a typed environment configuration pattern that maps each environment to the right model (Haiku for dev, Sonnet for staging/prod, Opus for complex prod tasks), appropriate maxTokens and retry counts, and separate API keys with per-environment spending alerts. Configuration is driven by NODE_ENV with type-safe defaults.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Teams deploying Claude integrations across multiple environments |
| **What** | Creates environment-specific Anthropic configs with separate keys, models, token limits, and retry policies |
| **When** | When moving beyond a single-environment prototype to a proper dev/staging/prod deployment pipeline |

## Key Features

1. **Typed Environment Config** — TypeScript interface-driven configuration that selects model, maxTokens, and maxRetries based on NODE_ENV
2. **Separate API Keys Per Environment** — Isolated keys with per-environment spending alerts ($10 dev, $50 staging, baseline+50% prod)
3. **Model Selection Strategy** — Clear table mapping environments to models with rationale (Haiku for speed/cost, Sonnet for quality, Opus for reasoning)

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
