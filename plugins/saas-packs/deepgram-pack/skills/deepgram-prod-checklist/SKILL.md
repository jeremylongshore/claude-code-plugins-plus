---
name: deepgram-prod-checklist
description: |
  Execute Deepgram production deployment checklist.
  Use when preparing for production launch, auditing production readiness,
  or verifying deployment configurations.
  Trigger with phrases like "deepgram production", "deploy deepgram",
  "deepgram prod checklist", "deepgram go-live", "production ready deepgram".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Production Checklist

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive checklist for deploying Deepgram integrations to production with singleton client, health checks, Prometheus metrics, alert rules, and go-live procedures.

## Prerequisites
- Completed development and staging testing
- Access to production secrets management
- Monitoring infrastructure configured
- On-call rotation established

## Instructions

### Step 1: Verify API Configuration
Create production API key with minimal scopes. Store in secrets manager (not env vars in code). Set 90-day expiration. Prepare fallback key. Understand rate limits for your tier.

### Step 2: Implement Error Handling
Catch all API errors with structured logging. Add retry logic with exponential backoff. Implement circuit breaker pattern. Define fallback behavior for API failures.

### Step 3: Configure Performance
Set up singleton client with connection pooling. Configure 30s request timeout. Limit concurrent requests. Optimize audio preprocessing. Enable response caching where applicable.

### Step 4: Set Up Health Check Endpoint
Create `/health` endpoint that tests Deepgram API connectivity and reports latency. Return 200 for healthy, 503 for unhealthy.

### Step 5: Configure Production Metrics
Define Prometheus counters for transcription total (by status), histograms for duration, counters for audio seconds processed and rate limit hits.

### Step 6: Deploy Alert Rules
Alert on error rate >5% (5min, critical), P95 latency >10s (warning), rate limit hits >10/hr (warning), and health check failure >2min (critical).

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Verified production API configuration
- Production-safe singleton client
- Health check endpoint
- Prometheus metrics and Grafana dashboard
- AlertManager rules for key thresholds

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key expired | No rotation | Set expiration alerts, auto-rotate |
| High error rate | Deepgram issue | Check status page, enable fallback |
| Rate limiting | Too many requests | Implement backoff, increase tier |
| Health check fail | Network/API issue | Verify connectivity, check status |

## Examples

### Pre-Deployment Checklist
| Category | Key Items |
|----------|-----------|
| API Config | Prod key, secrets manager, key rotation, rate limits |
| Error Handling | Retries, circuit breaker, fallback, error logging |
| Performance | Connection pooling, timeouts, caching, preprocessing |
| Security | HTTPS, input validation, PII redaction, audit logs |
| Monitoring | Health check, metrics, alerts, dashboards |

### Go-Live Timeline
| Phase | Actions |
|-------|---------|
| D-7 | Load test, security review, documentation |
| D-0 | Smoke test, dashboards open, on-call confirmed |
| D+1 | No critical alerts, error rate within SLA |

## Resources
- [Deepgram Production Guide](https://developers.deepgram.com/docs/production-guide)
- [Deepgram SLA](https://deepgram.com/sla)
- [Support Portal](https://support.deepgram.com)
