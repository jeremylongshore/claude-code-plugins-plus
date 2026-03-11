---
name: mistral-prod-checklist
description: |
  Execute Mistral AI production deployment checklist and rollback procedures.
  Use when deploying Mistral AI integrations to production, preparing for launch,
  or implementing go-live procedures.
  Trigger with phrases like "mistral production", "deploy mistral",
  "mistral go-live", "mistral launch checklist".
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Production Checklist

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Complete checklist for deploying Mistral AI integrations to production. Covers credential verification, code quality checks, health endpoints, circuit breaker resilience, gradual rollout, and rollback procedures.

## Prerequisites
- Staging environment tested and verified
- Production API keys available
- Deployment pipeline configured
- Monitoring and alerting ready

## Instructions

### Step 1: Pre-Deployment Configuration
Store production API key in secure vault (AWS Secrets Manager, GCP Secret Manager). Set environment variables in deployment platform. Validate key with test request to `https://api.mistral.ai/v1/models`. Prepare fallback configuration.

### Step 2: Code Quality Verification
Run full test suite, typecheck, and lint. Scan for hardcoded credentials (`grep -r "sk-" src/`). Verify error handling covers 401, 429, and 500+ status codes. Confirm rate limiting/backoff is implemented and logging excludes sensitive data.

### Step 3: Infrastructure Setup
Implement `/health` endpoint that tests Mistral API connectivity with latency measurement. Configure readiness and liveness probes. Set up Prometheus/Datadog metrics, alert rules (error rate, latency, rate limits), and dashboard.

### Step 4: Implement Circuit Breaker
Build `MistralCircuitBreaker` with failure threshold (5), reset timeout (60s), and fallback support. Circuit opens after threshold failures and auto-resets after timeout. Provides graceful degradation when Mistral is unavailable.

### Step 5: Documentation Requirements
Create incident runbook, key rotation procedure, rollback procedure, on-call escalation path, and API usage limits documentation.

### Step 6: Gradual Rollout
Deploy to canary (10% traffic), monitor 10 minutes for errors, expand to 50%, then complete to 100%. Use `kubectl rollout pause/resume` for staged deployment.

### Step 7: Post-Deployment Verification
Hit health endpoint, test chat endpoint with sample request, check logs for errors. Verify monitoring dashboards show expected metrics.

## Alert Configuration

| Alert | Condition | Severity |
|-------|-----------|----------|
| API Down | 5xx errors > 10/min | P1 - Critical |
| High Latency | p99 > 5000ms for 5min | P2 - High |
| Rate Limited | 429 errors > 5/min | P2 - High |
| Auth Failures | 401 errors > 0 | P1 - Critical |
| Circuit Open | Circuit breaker triggered | P2 - High |

## Output
- Deployed Mistral AI integration with verified credentials
- Health checks passing with latency monitoring
- Circuit breaker resilience active
- Monitoring and alerting configured
- Rollback procedure documented and tested

## Error Handling
| Issue | Detection | Resolution |
|-------|-----------|------------|
| Deployment failure | kubectl rollout status | Rollback with `kubectl rollout undo` |
| Health check failing | 503 response | Check Mistral API status, verify credentials |
| Circuit breaker open | Alert triggered | Investigate Mistral availability, wait for reset |
| High error rate | Monitoring alert | Check logs, consider rollback |

## Examples

### Quick Health Check
```bash
set -euo pipefail
curl -sf https://yourapp.com/health | jq '.services.mistral'
```

### Emergency Rollback
```bash
set -euo pipefail
kubectl rollout undo deployment/mistral-app
kubectl rollout status deployment/mistral-app
curl -sf https://yourapp.com/health | jq
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Mistral AI Status](https://status.mistral.ai/)
- [Mistral AI Console](https://console.mistral.ai/)