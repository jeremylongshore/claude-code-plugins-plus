# PRD: Vertex AI Validator Expert

**Version:** 2.1.0
**Author:** Jeremy Longshore
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Deploying AI agents to Vertex AI Agent Engine without validation leads to security gaps, monitoring blind spots, and compliance failures that surface in production. Teams discover missing IAM bindings, absent alerting, or unscoped VPC-SC perimeters after launch — when the cost of remediation is highest. There is no single tool that scores deployment readiness across security, monitoring, performance, and compliance in one pass.

The Validator Expert skill provides a weighted 0-100% production readiness score with actionable remediation before any agent goes live.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| ADK developers | Pre-launch validation | Know if their agent is production-ready before deploying |
| Platform/SRE teams | Ongoing governance | Enforce security and monitoring baselines across all agents |
| Security engineers | Post-incident audit | Verify IAM least-privilege and VPC-SC after a security event |
| Compliance officers | SOC 2 / regulatory prep | Generate audit evidence for agent deployments |

## Success Criteria

1. **Score accuracy**: Weighted score reflects actual production risk (validated against post-deploy incidents)
2. **Coverage**: All 5 categories checked (security 30%, performance 25%, monitoring 20%, compliance 15%, best practices 10%)
3. **Actionable output**: Every failing check includes a specific remediation command or configuration change
4. **Speed**: Full validation completes in under 5 minutes for a single agent deployment
5. **Regression tracking**: Score comparison against previous runs shows improvement/degradation

## Functional Requirements

1. Retrieve Agent Engine deployment config via Python SDK or REST API
2. Execute security checks: Agent Identity, IAM roles, VPC-SC, encryption, secrets scanning, Model Armor, Memory Bank conditions
3. Execute monitoring checks: dashboards, alerting policies, token tracking, structured logging, latency SLOs
4. Execute performance checks: auto-scaling, resource limits, caching, sandbox TTL, memory retention
5. Execute compliance checks: audit logging, data residency, privacy policies, backup/DR
6. Calculate weighted composite score (0-100%)
7. Generate prioritized remediation plan sorted by score-impact-per-effort
8. Compare against previous validation run if available

## Non-Functional Requirements

- Read-only operations only — validator never modifies deployment state
- Works with viewer-level IAM permissions (no admin roles required)
- Outputs structured data (score, pass/fail table, remediation list) for CI integration
- Handles missing permissions gracefully (marks check as "inconclusive", not "failed")

## Dependencies

- `gcloud` CLI authenticated with viewer roles
- Cloud Monitoring API and Cloud Logging API enabled
- Target project's IAM policies accessible
- Knowledge of deployment's expected SLOs

## Out of Scope

- Automated remediation (this skill validates and reports, doesn't fix)
- Load testing or synthetic traffic generation
- Cost optimization analysis (separate concern)
- Multi-cloud validation (GCP only)
