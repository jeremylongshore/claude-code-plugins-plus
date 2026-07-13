# navan-upgrade-migration — One-Pager

Defensive patterns for handling Navan API changes, deprecations, and breaking updates in production integrations.

## The Problem

Navan does not publicly version their API or publish a formal changelog. API behavior can change without notice — response fields may be added, removed, or renamed, and endpoint behavior can shift between releases. Integrations that assume a fixed API contract break silently, and teams discover issues only when production data stops flowing or error rates spike.

## The Solution

This skill provides defensive coding patterns and monitoring strategies for Navan API integrations that lack formal versioning guarantees. It covers response schema validation, unknown field tolerance, deprecation signal detection, gradual rollout strategies with feature flags, and automated regression testing against live API responses. The approach treats every API response as potentially different from the last.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Integration engineers, platform teams, DevOps maintaining long-lived Navan API integrations |
| **What** | Defensive coding patterns, schema validation middleware, deprecation monitors, and rollout strategies |
| **When** | Unexpected API response changes, new field appearances, endpoint behavior shifts, proactive hardening of existing integrations |

## Key Features

1. **Schema Validation Middleware** — Runtime response validation that logs drift without breaking existing functionality
2. **Deprecation Signal Detection** — Monitors HTTP headers and response bodies for deprecation warnings or sunset notices
3. **Gradual Rollout with Feature Flags** — Canary deployment pattern for API integration changes with automatic rollback triggers

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
