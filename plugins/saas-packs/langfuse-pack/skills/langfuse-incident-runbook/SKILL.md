---
name: langfuse-incident-runbook
description: |
  Troubleshoot and respond to Langfuse-related incidents and outages.
  Use when experiencing Langfuse outages, debugging production issues,
  or responding to LLM observability incidents.
  Trigger with phrases like "langfuse incident", "langfuse outage",
  "langfuse down", "langfuse production issue", "langfuse troubleshoot".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Langfuse Incident Runbook

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Step-by-step procedures for responding to Langfuse-related incidents, from initial triage through resolution and post-incident review.

## Prerequisites
- Access to Langfuse dashboard
- Application logs access
- Metrics/monitoring dashboards
- Escalation contacts

## Instructions

### Step 1: Initial Assessment (2 minutes)
Run the quick diagnosis script: check Langfuse status page, API connectivity, auth test, and application metrics.

### Step 2: Determine Incident Type
| Symptom | Likely Cause | Action |
|---------|--------------|--------|
| No traces appearing | SDK not flushing | Check shutdown handlers, reduce batch size |
| 401/403 errors | Auth issue | Verify keys match project, check rotation |
| High latency | Rate limits | Increase batching, implement circuit breaker |
| Missing data | Partial failures | Ensure spans end in `finally` blocks |
| Complete outage | Langfuse service | Enable fallback, queue locally |

### Step 3: Apply Resolution
Follow the section-specific resolution steps. For outages, activate graceful degradation mode.

### Step 4: Post-Incident Review
Verify traces appearing, check error rates normalized, schedule post-mortem for P1/P2.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Incident severity classified
- Root cause identified
- Resolution applied
- Post-incident checklist completed

## Error Handling
| Severity | Description | Response Time |
|----------|-------------|---------------|
| P1 | Complete outage | 15 min |
| P2 | Degraded, partial loss | 1 hour |
| P3 | Slow/delayed traces | 4 hours |
| P4 | Minor issues | 24 hours |

## Examples

### Escalation Contacts
| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | All incidents |
| L2 | Platform team lead | P1/P2 unresolved 30min |
| L3 | Langfuse support | Service-side issues |

## Resources
- [Langfuse Status](https://status.langfuse.com)
- [Langfuse Discord](https://langfuse.com/discord)
- [Langfuse GitHub Issues](https://github.com/langfuse/langfuse/issues)
