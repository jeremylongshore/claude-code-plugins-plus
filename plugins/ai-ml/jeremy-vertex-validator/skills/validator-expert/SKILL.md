---
name: validator-expert
description: 'Validate production readiness of Vertex AI Agent Engine deployments
  across

  security, monitoring, performance, compliance, and best practices. Generates

  weighted scores (0-100%) with actionable remediation plans. Use when asked to

  validate a deployment, run a production readiness check, audit security posture,

  or verify compliance for Vertex AI agents. Trigger with "validate deployment",

  "production readiness", "security audit", "compliance check", "is this agent

  ready for prod", "check my ADK agent", "review before deploy", or

  "production readiness check". Make sure to use this skill whenever validating

  ADK agents for Agent Engine.

  '
allowed-tools: Read,Grep,Glob,Bash(gcloud:*),Bash(python:*),Bash(pylint:*),Bash(flake8:*),Bash(mypy:*),Bash(bandit:*),Bash(pytest:*)
version: 2.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
tags:
- vertex-ai
- security
- compliance
- validation
- production-readiness
- gcp
model: inherit
effort: high
argument-hint: '[project-id]'
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Validator Expert

## Current State
!`gcloud config get-value project 2>/dev/null || echo 'no active project'`
!`gcloud auth list --filter=status:ACTIVE --format="value(account)" 2>/dev/null || echo 'not authenticated'`

## Overview

Validate production readiness of Vertex AI Agent Engine deployments by executing weighted checks across five categories: security (30 points), monitoring (20 points), performance (25 points), compliance (15 points), and best practices (10 points). This skill produces a 0-100% composite score with pass/fail per check and prioritized remediation recommendations.

## Prerequisites

- `gcloud` CLI authenticated with `roles/aiplatform.viewer`, `roles/iam.securityReviewer`, and `roles/monitoring.viewer`
- Access to the target Google Cloud project and Vertex AI Agent Engine deployment
- Cloud Monitoring API and Cloud Logging API enabled in the project
- Knowledge of the deployment's expected SLOs (latency targets, error rate thresholds)
- Read-only access to IAM policies, VPC-SC configurations, and service account bindings

## Instructions

1. Retrieve the deployment configuration using the Python SDK (`vertexai.Client().agent_engines.get(name)`) or REST API (`GET https://{LOCATION}-aiplatform.googleapis.com/v1/projects/{PROJECT}/locations/{LOCATION}/reasoningEngines/{ID}`) and parse model, scaling, and feature settings
2. Run the security validation suite (see [security checklist](references/security-checklist.md)):
   - Check if Agent Identity is enabled (recommended over service accounts for 2025+ deployments)
   - If using service accounts, verify IAM roles follow least-privilege (`roles/aiplatform.expressUser`, not `roles/aiplatform.admin`)
   - Confirm VPC Service Controls perimeter is active and correctly scoped
   - Check encryption at rest (CMEK or Google-managed) and in-transit (TLS 1.3)
   - Scan configuration files and environment variables for hardcoded secrets
   - Validate Model Armor is enabled with `roles/modelarmor.user` granted
   - Check Memory Bank IAM Conditions for multi-tenant agents
3. Run the monitoring validation suite:
   - Verify Cloud Monitoring dashboards exist with required panels (request count, error rate, latency)
   - Confirm alerting policies cover error rate spikes, latency SLO breaches, and cost thresholds
   - Check token usage tracking is enabled with per-model granularity
   - Validate structured logging with severity levels and correlation IDs
   - Confirm latency SLOs are defined with p95 and p99 targets
4. Run the performance validation suite:
   - Verify auto-scaling is configured with appropriate min/max instance counts
   - Check resource limits (CPU, memory) match expected workload profile
   - Confirm caching strategy is implemented for repeated prompts or embeddings
   - Validate Code Execution Sandbox TTL is set between 7-14 days
   - Check Memory Bank retention policy (min 100 memories, auto-cleanup enabled)
5. Run the compliance validation suite:
   - Confirm audit logging is enabled for all admin and data access operations
   - Verify data residency meets regional requirements
   - Check privacy policies and data retention schedules
   - Validate backup and disaster recovery configuration
6. Calculate weighted scores per category and compute the overall production readiness percentage
7. Generate a prioritized recommendation list sorted by score impact per remediation effort

## Output

- Production readiness score: 0-100% with status (READY >= 85%, NEEDS WORK 70-84%, NOT READY < 70%)
- Per-category breakdown: security (x/30), monitoring (x/20), performance (x/25), compliance (x/15), best practices (x/10)
- Pass/fail table for each individual check with evidence notes
- Prioritized remediation plan: action items ranked by score improvement per effort
- Comparison to previous validation run (if available) showing score delta

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Insufficient IAM permissions | Viewer roles not granted on target project | Request `roles/aiplatform.viewer` and `roles/iam.securityReviewer` from project admin |
| Agent deployment not found | Incorrect agent ID or deployment deleted | Verify agent ID with `vertexai.Client().agent_engines.list()` or REST `GET .../reasoningEngines`; confirm deployment region |
| Monitoring API returns no data | API not enabled or agent has zero traffic | Enable Monitoring API; generate synthetic traffic to populate baseline metrics |
| VPC-SC configuration inaccessible | Organization policy restricts VPC-SC reads | Request `roles/accesscontextmanager.policyReader` at organization level |
| Compliance check inconclusive | Audit logs not enabled or retention too short | Enable Data Access audit logs; set log retention to minimum 365 days |

## Examples

**Scenario 1: Pre-Launch Validation** -- Validate a new ADK agent before production launch. Run all five validation categories. Target score: 85%+ overall, with security score at 28/30 minimum. Generate remediation plan for any failing checks.

**Scenario 2: Post-Incident Security Audit** -- After a permission escalation incident, re-validate security posture. Focus on IAM least-privilege, service account bindings, and VPC-SC perimeter integrity. Compare scores against the last passing validation.

**Scenario 3: Quarterly Compliance Review** -- Execute compliance and monitoring validation suites for SOC 2 audit preparation. Verify audit logging coverage, data residency compliance, and backup/DR configuration. Export results as evidence artifacts.

## Resources

**Validation checklists** (read the relevant one during each validation step):
- [Security checklist](references/security-checklist.md) — IAM, VPC-SC, encryption, Model Armor (30% weight)
- [Monitoring checklist](references/monitoring-checklist.md) — dashboards, alerts, SLOs, logging (20% weight)
- [Performance & compliance checklist](references/performance-compliance-checklist.md) — auto-scaling, caching, audit logs, DR (40% weight)

**Official Google Cloud documentation:**
- [Vertex AI Security Best Practices](https://cloud.google.com/vertex-ai/docs/security)
- [Cloud Monitoring Alerting](https://cloud.google.com/monitoring/alerts)
- [VPC Service Controls](https://cloud.google.com/vpc-service-controls/docs)
- [Model Armor](https://cloud.google.com/vertex-ai/docs/generative-ai/model-armor)
- [Cloud Audit Logs](https://cloud.google.com/logging/docs/audit)