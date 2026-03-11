---
name: deepgram-incident-runbook
description: |
  Execute Deepgram incident response procedures for production issues.
  Use when handling Deepgram outages, debugging production failures,
  or responding to service degradation.
  Trigger with phrases like "deepgram incident", "deepgram outage",
  "deepgram production issue", "deepgram down", "deepgram emergency".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Incident Runbook

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Standardized procedures for responding to Deepgram-related incidents with initial triage script, severity-based response (SEV1-SEV4), fallback activation, degradation investigation, and post-incident review templates.

## Prerequisites
- Monitoring and alerting configured
- On-call rotation established
- Fallback/queueing system available
- Communication channels defined

## Instructions

### Step 1: Run Initial Triage (First 5 Minutes)
Execute triage script: check Deepgram status page, query error rate from Prometheus, check P95 latency, and test API connectivity with curl.

### Step 2: Classify Severity
SEV1 (immediate): 100% failure, 5xx errors. SEV2 (<15min): 50%+ error rate. SEV3 (<1hr): elevated latency. SEV4 (<24hr): single feature affected.

### Step 3: Respond to SEV1 (Complete Outage)
Acknowledge in PagerDuty/Slack. Verify API key validity. Check network. Activate fallback: queue requests for later replay, or switch to backup STT provider. Notify affected customers.

### Step 4: Respond to SEV2 (Major Degradation)
Test transcription across multiple samples and models. Identify if specific model, feature, or audio type is affected. Mitigate: reduce request rate, disable non-critical features, switch models, enable retries.

### Step 5: Respond to SEV3 (Minor Degradation)
Increase timeouts to 60s, enable aggressive retry (5 attempts), switch to simpler model (Nova), disable diarization. Monitor for improvement.

### Step 6: Conduct Post-Incident Review
Document timeline, root cause, impact (duration, failed requests, revenue). List what went well and areas for improvement. Create action items with owners and due dates.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Automated triage script
- Severity classification guide
- Fallback activation procedures
- Degradation investigation playbook
- Post-incident review template

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| All transcriptions failing | API outage | Activate fallback queue |
| 50%+ error rate | Partial degradation | Test models, reduce features |
| Elevated latency | Overload | Increase timeouts, reduce rate |
| Single feature broken | API regression | Disable feature, report to Deepgram |

## Examples

### Quick Reference
| Resource | URL |
|----------|-----|
| Deepgram Status | https://status.deepgram.com |
| Deepgram Console | https://console.deepgram.com |
| Support | support@deepgram.com |

### Severity Levels
| Level | Definition | Response Time |
|-------|------------|---------------|
| SEV1 | Complete outage | Immediate |
| SEV2 | Major degradation | < 15 min |
| SEV3 | Minor degradation | < 1 hour |
| SEV4 | Minor issue | < 24 hours |

### Escalation Contacts
| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | First response |
| L2 | Team lead | 15 min without resolution |
| L3 | Deepgram support | Confirmed Deepgram issue |
| L4 | Engineering director | SEV1 > 1 hour |

## Resources
- [Deepgram Status Page](https://status.deepgram.com)
- [Deepgram Support](https://developers.deepgram.com/support)
- [Internal Runbooks](https://wiki.example.com/deepgram)