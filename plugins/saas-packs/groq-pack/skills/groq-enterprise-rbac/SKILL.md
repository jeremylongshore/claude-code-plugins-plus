---
name: groq-enterprise-rbac
description: |
  Use when you run Groq inference for multiple teams and need per-team model
  allow-lists, spending caps, rate limits, and key rotation — because Groq API
  keys have no built-in scopes, so access control must live in your gateway.
  Configure Groq organization management, API key scoping, spending controls,
  and team access patterns. Trigger with phrases like "groq organization",
  "groq RBAC", "groq enterprise", "groq team access", "groq spending limits",
  "groq multi-team".
allowed-tools: Read, Write, Edit
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- rbac
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Enterprise Access Management

## Overview

Manage team access to Groq's inference API through API key strategy, model-level routing controls, spending limits, and usage monitoring. Groq uses flat API keys (`gsk_` prefix) with no built-in scoping -- access control is implemented at the application layer, in a gateway that sits between your teams and Groq.

## Groq Access Model

- **API keys** are per-organization, not per-user
- **No built-in scopes** -- every key has full API access
- **Rate limits** are per-organization, shared across all keys
- **Spending limits** are configurable in the Groq Console
- **Projects** allow creating isolated API keys with separate limits

## Prerequisites

- A Groq organization with Console access (console.groq.com) and billing configured.
- Permission to create Groq **Projects** — one per team/service, each yielding its own `gsk_` key.
- A secret manager (AWS Secrets Manager, GCP Secret Manager, Vault, etc.) to store per-team keys.
- A gateway/service layer (Node/TypeScript in these examples) that every team's traffic passes through — Groq enforces nothing per-team, so your gateway is the control point.
- `groq-sdk` and `p-queue` installed if you use the reference gateway.

## Instructions

Access control is enforced in your own gateway. The full, copy-paste implementation for every
step lives in [references/implementation.md](references/implementation.md); the high-level flow:

1. **API key strategy** — one Groq Project (and key) per team/environment, named `{team}-{environment}-{purpose}`. Register keys in a lookup:

   ```typescript
   // Key naming convention: {team}-{environment}-{purpose}
   const KEY_REGISTRY = {
     "chatbot-prod":    "gsk_...",  // Project: chatbot-production
     "chatbot-staging": "gsk_...",  // Project: chatbot-staging
     "analytics-prod":  "gsk_...",  // Project: analytics-production
   } as const;
   ```

2. **Model access control** — define a per-team config (`allowedModels`, `maxTokensPerRequest`, `monthlyBudgetUsd`, `rateLimitRPM`) and a `validateRequest(team, model, maxTokens)` guard that throws before any unauthorized model or oversized request reaches Groq.
3. **API gateway** — `groqGateway(team, messages, model, maxTokens)` validates permissions, checks the monthly budget, rate-limits per team via `p-queue`, calls Groq with the team's key, and records usage.
4. **Spending controls** — set an org-level cap + alerts in the Groq Console (50/80/95%, auto-pause), and track application-level per-team spend with `recordTeamUsage`, which logs threshold alerts.
5. **Key rotation** — zero-downtime rotation: create a new key in the same Project, deploy alongside the old key, update the secret manager, restart, monitor 24h, then delete the old key.

See [references/implementation.md](references/implementation.md) for the complete code for each step.

## Output

Applying this skill produces a working per-team access layer in front of Groq:

- A **key registry** mapping each team/environment to its own Groq Project key.
- A **`TEAM_CONFIGS` policy object** — the source of truth for which models, token ceilings, budgets, and rate limits each team gets.
- A **gateway function** that rejects unauthorized model/token/budget requests before they reach Groq and rate-limits per team.
- **Per-team spend tracking** with 80%/95% threshold alerts, plus a weekly cost/token report table.
- A documented **key-rotation runbook** for zero-downtime credential changes.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `429 rate_limit_exceeded` | Org-level RPM/TPM hit | Teams share org limits; reduce aggregate volume |
| `401 invalid_api_key` | Key deleted or rotated | Update secret manager, restart services |
| Budget exhausted | Monthly cap reached | Increase cap or wait for billing cycle reset |
| Wrong model used | No server-side enforcement | Validate model against team config before calling Groq |

## Examples

Two worked examples — a weekly per-team usage dashboard and a request that gets blocked by
the model allow-list — are in [references/examples.md](references/examples.md).

The gateway rejects an out-of-scope model before it ever bills Groq:

```typescript
// analytics is scoped to llama-3.1-8b-instant only
await groqGateway("analytics", messages, "llama-3.3-70b-versatile", 512);
// throws: "Team analytics not authorized for model llama-3.3-70b-versatile"
```

## Resources

- [Groq Projects](https://console.groq.com/docs/projects)
- [Groq Spend Limits](https://console.groq.com/docs/spend-limits)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)
- [Groq API Keys](https://console.groq.com/keys)
- [Full implementation walkthrough](references/implementation.md)
- [Worked examples](references/examples.md)
- For migration strategies, see the `groq-migration-deep-dive` skill.
