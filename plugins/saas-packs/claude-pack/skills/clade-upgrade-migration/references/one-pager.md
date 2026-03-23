# clade-upgrade-migration — One-Pager

Upgrade Anthropic SDK versions and migrate between Claude model generations safely.

## The Problem

Anthropic releases new SDK versions and model generations regularly. Upgrading without a process risks breaking changes from deprecated methods, stale model IDs returning 404s, output quality regressions from untested model swaps, and cost surprises from changed token limits — all hitting production at once.

## The Solution

A structured upgrade workflow: check current SDK version, review the changelog for breaking changes, grep the codebase for all model ID references, run integration tests against both old and new models, compare outputs for quality regression, and use environment variable-based model selection (`CLAUDE_MODEL`) for gradual rollout without redeployment.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Teams maintaining production Claude integrations across SDK and model updates |
| **What** | SDK upgrade commands, model ID migration, output comparison, env-var-based gradual rollout |
| **When** | When a new Anthropic SDK version or Claude model generation is released |

## Key Features

1. **SDK upgrade commands** — One-line upgrade for both TypeScript (`npm install @claude-ai/sdk@latest`) and Python (`pip install --upgrade anthropic`) with changelog links
2. **Model migration checklist** — Six-step process: read model card, grep and replace model IDs, test against both models, compare outputs, update max_tokens, gradual rollout
3. **Environment-based rollout** — `process.env.CLAUDE_MODEL` pattern for switching models per environment without code changes, enabling canary deployments

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
