# PRD: Vertex Engine Inspector

**Version:** 2.1.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Vertex AI Agent Engine deployments involve seven interconnected configuration surfaces (runtime, Code Execution Sandbox, Memory Bank, A2A protocol, security, performance, monitoring) that are validated manually and inconsistently. Teams deploy agents without knowing their production readiness score, leading to security gaps (unhardened IAM, missing VPC-SC), reliability issues (no alerting, stale memory), and protocol non-compliance (broken A2A endpoints). Without a systematic inspection, problems surface only after production incidents.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Platform Engineer | Preparing a new Agent Engine deployment for production launch | Comprehensive readiness score with prioritized fix list before go-live |
| Security Auditor | Reviewing IAM, VPC-SC, and encryption posture after configuration changes | Targeted security inspection confirming least-privilege and perimeter integrity |
| SRE / On-Call Engineer | Investigating elevated error rates or latency on a deployed agent | Performance metrics retrieval with root-cause correlation (scaling, tokens, errors) |
| DevOps Lead | Establishing baseline quality gates for agent deployments | Repeatable inspection producing consistent scores across all team deployments |

## Success Criteria

1. Inspect all seven categories (runtime, sandbox, memory, A2A, security, performance, monitoring) in a single invocation
2. Generate a weighted production-readiness score (0-100%) with per-category breakdowns
3. Produce actionable recommendations with estimated score improvement per remediation item
4. Complete a full inspection within 5 minutes for a standard deployment
5. Security category catches 100% of missing VPC-SC, overprivileged IAM, and unencrypted configurations
6. A2A compliance matrix clearly shows pass/fail for each protocol endpoint

## Functional Requirements

1. Retrieve agent metadata via the Python SDK (`vertexai.Client().agent_engines.get()`) and parse runtime configuration
2. Validate Code Execution Sandbox settings: TTL range (7-14 days), sandbox type (`SECURE_ISOLATED`), scoped IAM
3. Check Memory Bank: enabled status, retention policy (min 100 memories), Firestore encryption, indexing, auto-cleanup
4. Test A2A protocol endpoints: `/.well-known/agent-card`, `POST /v1/tasks:send`, `GET /v1/tasks/<id>`
5. Audit security posture: IAM least-privilege, VPC-SC perimeter, Model Armor, encryption, no hardcoded credentials
6. Query Cloud Monitoring for 24-hour metrics: error rate, latency percentiles (p50/p95/p99), token usage, cost
7. Assess observability: dashboards, alerting policies, structured logging, OpenTelemetry, Cloud Error Reporting
8. Calculate weighted scores and generate a prioritized recommendation list

## Non-Functional Requirements

- Read-only inspection: skill must not modify the inspected deployment or its configuration
- All Agent Engine operations use the Python SDK, never gcloud CLI (no gcloud surface exists for Agent Engine)
- Inspection must work from outside VPC-SC perimeters when access levels are properly configured
- Output format is YAML for machine-parseability and human readability
- Scoring weights must reflect production impact: security and reliability weighted higher than monitoring
- Inspection must handle partial failures gracefully (skip unavailable categories, still produce report)
- Results must be deterministic: same deployment state always produces the same score

## Dependencies

- `google-cloud-aiplatform[agent_engines]>=1.120.0` Python SDK
- `gcloud` CLI authenticated for IAM and monitoring queries
- IAM roles: `roles/aiplatform.user` and `roles/monitoring.viewer` on target project
- Cloud Monitoring API enabled
- `curl` for A2A endpoint testing

## Out of Scope

- Modifying or remediating Agent Engine configurations (inspection only, never writes)
- Deploying new agents or updating existing deployments (handled by adk-deployment-specialist)
- Infrastructure provisioning with Terraform (handled by adk-infra-expert)
- Cost optimization recommendations beyond basic model selection guidance
- Load testing or performance benchmarking (inspection uses existing metrics only)
- Cross-project inspection (each invocation targets a single project/agent pair)
