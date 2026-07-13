# navan-observability — One-Pager

Monitors Navan API integrations with structured logging, latency tracking, error rate dashboards, and alerting.

## The Problem

Navan API integrations fail silently. An expired OAuth token returns 401 errors for hours before anyone notices. Rate limit exhaustion at 429 causes booking sync gaps. Without structured observability, teams rely on user complaints to discover integration problems, leading to missing expense reports, failed reimbursements, and finance reconciliation headaches.

## The Solution

This skill implements a full observability stack for Navan API integrations: structured request/response logging with correlation IDs, latency percentile tracking, error rate monitoring with automatic classification (auth failures vs. rate limits vs. data errors), and alerting rules for Datadog, CloudWatch, or Prometheus. Every API call is instrumented to provide full visibility into integration health.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | SRE teams, DevOps engineers, platform teams operating Navan integrations in production |
| **What** | Structured logging middleware, Datadog/CloudWatch/Prometheus metric configurations, alert rules, dashboard JSON definitions |
| **When** | Deploying a Navan integration to production, investigating intermittent sync failures, setting up on-call alerting for travel platform health |

## Key Features

1. **Structured API Logging** — Correlation IDs, request/response capture, and PII redaction for every Navan API call
2. **Multi-Platform Dashboards** — Pre-built configurations for Datadog, CloudWatch, and Prometheus/Grafana showing latency p50/p95/p99, error rates, and token refresh health
3. **Intelligent Alerting** — Differentiated alerts for auth failures (401), rate limits (429), and server errors (5xx) with appropriate severity and escalation paths

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
