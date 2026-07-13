# clade-incident-runbook — One-Pager

Respond to Anthropic API outages and degraded performance with a structured five-step runbook.

## The Problem

When the Anthropic API starts returning 529 errors, timing out, or going fully down, teams scramble to figure out whether it is their code, their API key, or an Anthropic-side incident. Without a pre-built runbook, the response is ad hoc: wrong severity classification, no fallback activated, and users left in the dark.

## The Solution

This skill provides a five-step incident response process: confirm the issue via status page and direct API test, classify severity (Low/Medium/High) based on symptom patterns, activate model fallback (downgrade from Opus to Sonnet to Haiku), communicate to stakeholders, and run a post-incident review with impact calculation.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | SREs, on-call engineers, and backend developers running Claude in production |
| **What** | Five-step runbook: confirm, classify severity, activate fallback, communicate, post-incident review |
| **When** | When production Claude calls start failing — sustained 529s, timeouts, auth errors, or a status page incident |

## Key Features

1. **Severity Classification Table** — Maps symptoms (intermittent 529, sustained 529, 401/403, timeouts) to severity levels with specific actions for each
2. **Model Fallback Code** — TypeScript function that catches 529/500 errors and automatically downgrades from Opus to Sonnet to Haiku
3. **Status Page Automation** — curl commands to query `status.anthropic.com` API for current status and recent incidents

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
