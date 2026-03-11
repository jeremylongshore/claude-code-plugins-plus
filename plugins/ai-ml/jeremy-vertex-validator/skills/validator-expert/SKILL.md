---
name: validator-expert
description: |
  Validate production readiness of Vertex AI Agent Engine deployments across security, monitoring, performance, compliance, and best practices. Generates weighted scores (0-100%) with actionable recommendations. Use when asked to "validate deploymen... Trigger with phrases like 'validate', 'check', or 'verify'.
allowed-tools: Read, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Validator Expert

## Overview

Validate production readiness of Vertex AI Agent Engine deployments by executing weighted checks across five categories: security (30 points), monitoring (20 points), performance (25 points), compliance (15 points), and reliability (10 points). This skill produces a 0-100% composite score with pass/fail per check and prioritized remediation recommendations.

## Prerequisites

- `gcloud` CLI authenticated with `roles/aiplatform.viewer`, `roles/iam.securityReviewer`, and `roles/monitoring.viewer`
- Access to the target Google Cloud project and Vertex AI Agent Engine deployment
- Cloud Monitoring API and Cloud Logging API enabled in the project
- Knowledge of the deployment's expected SLOs (latency targets, error rate thresholds)
- Read-only access to IAM policies, VPC-SC configurations, and service account bindings

## Instructions

1. Retrieve the deployment configuration using `gcloud ai agents describe` and parse model, scaling, and feature settings
2. Run the security validation suite:
   - Verify IAM roles follow least-privilege by auditing service account bindings against required permissions
   - Confirm VPC Service Controls perimeter is active and correctly scoped
   - Check encryption at rest (CMEK or Google-managed) and in-transit (TLS 1.3)
   - Scan configuration files and environment variables for hardcoded secrets
   - Validate service account key rotation policy (max 90 days)
   - Confirm Model Armor is enabled for ADK-based agents
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
- Per-category breakdown: security (x/30), monitoring (x/20), performance (x/25), compliance (x/15), reliability (x/10)
- Pass/fail table for each individual check with evidence notes
- Prioritized remediation plan: action items ranked by score improvement per effort
- Comparison to previous validation run (if available) showing score delta

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Insufficient IAM permissions | Viewer roles not granted on target project | Request `roles/aiplatform.viewer` and `roles/iam.securityReviewer` from project admin |
| Agent deployment not found | Incorrect agent ID or deployment deleted | Verify agent ID with `gcloud ai agents list`; confirm deployment region |
| Monitoring API returns no data | API not enabled or agent has zero traffic | Enable Monitoring API; generate synthetic traffic to populate baseline metrics |
| VPC-SC configuration inaccessible | Organization policy restricts VPC-SC reads | Request `roles/accesscontextmanager.policyReader` at organization level |
| Compliance check inconclusive | Audit logs not enabled or retention too short | Enable Data Access audit logs; set log retention to minimum 365 days |

## Examples

**Scenario 1: Pre-Launch Validation** -- Validate a new ADK agent before production launch. Run all five validation categories. Target score: 85%+ overall, with security score at 28/30 minimum. Generate remediation plan for any failing checks.

**Scenario 2: Post-Incident Security Audit** -- After a permission escalation incident, re-validate security posture. Focus on IAM least-privilege, service account bindings, and VPC-SC perimeter integrity. Compare scores against the last passing validation.

**Scenario 3: Quarterly Compliance Review** -- Execute compliance and monitoring validation suites for SOC 2 audit preparation. Verify audit logging coverage, data residency compliance, and backup/DR configuration. Export results as evidence artifacts.

## Resources

- [Vertex AI Security Best Practices](https://cloud.google.com/vertex-ai/docs/security) -- IAM, encryption, VPC-SC
- [Cloud Monitoring Alerting](https://cloud.google.com/monitoring/alerts) -- policy configuration
- [VPC Service Controls](https://cloud.google.com/vpc-service-controls/docs) -- perimeter setup
- [Model Armor Documentation](https://cloud.google.com/vertex-ai/docs/generative-ai/model-armor) -- prompt injection protection
- [Cloud Audit Logs](https://cloud.google.com/logging/docs/audit) -- admin and data access logging