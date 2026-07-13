# ARD: Vertex Engine Inspector

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Vertex Engine Inspector is a read-only diagnostic skill that queries a live Agent Engine deployment and its surrounding GCP infrastructure to produce a scored readiness report.

```
                    ┌─────────────────────┐
                    │  Agent Engine (GCP)  │
                    │  ├─ Runtime Config   │
                    │  ├─ Code Exec Sandbox│
                    │  ├─ Memory Bank      │
                    │  └─ A2A Endpoints    │
                    └──────────┬──────────┘
                               │
Developer Request ──→ [Vertex Engine Inspector] ──→ YAML Inspection Report
                               │
                    ┌──────────┴──────────┐
                    │  GCP Services        │
                    │  ├─ IAM Policies     │
                    │  ├─ VPC-SC Perimeter │
                    │  ├─ Cloud Monitoring │
                    │  └─ Cloud Logging    │
                    └─────────────────────┘
```

## Data Flow

1. **Input**: Project ID, Agent Engine ID, and optional location (defaults to `us-central1`). The skill receives these as arguments or parses them from the user request.
2. **Processing**: Connect to Agent Engine via Python SDK to retrieve metadata. Sequentially validate each of 7 categories: parse runtime config, check sandbox TTL/type, verify Memory Bank settings, probe A2A endpoints with curl, audit IAM/VPC-SC/encryption via gcloud, query Cloud Monitoring for 24h metrics, and assess observability configuration. Score each category with weighted criteria.
3. **Output**: A YAML inspection report with per-category scores (0-100%), an overall weighted readiness percentage, a compliance matrix for A2A endpoints, performance metrics summary, and a prioritized recommendation list with estimated score improvement per item.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python SDK for Agent Engine | `vertexai.Client()` not gcloud CLI | No gcloud CLI surface exists for Agent Engine — SDK is the only programmatic interface |
| Read-only inspection | Never modify the deployment | Safety: inspectors should observe, not change production systems |
| YAML output format | YAML over JSON or Markdown | Machine-parseable for CI pipelines while remaining human-readable for operators |
| Weighted scoring | Category weights reflecting production impact | Security and reliability weighted higher than monitoring; matches real incident severity |
| 24-hour metric window | Query last 24h by default | Balances recency with statistical significance for error rates and latency |
| Sequential category checks | Run categories one at a time, not parallel | Allows early categories to inform later ones (e.g., runtime config affects security audit) |
| Prioritized recommendations | Score improvement estimate per item | Helps teams focus remediation effort where it matters most |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Parse existing inspection reports, agent configuration files, and IAM policy exports |
| Grep | Search for hardcoded credentials, security anti-patterns, and configuration values in agent source |
| Glob | Discover agent project files, deployment configs, and monitoring setup files |
| Bash(cmd:*) | Execute Python SDK commands, gcloud IAM/monitoring queries, curl for A2A endpoint probing |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Authentication failure | `PermissionDenied` or `Unauthenticated` from SDK/gcloud | Verify `gcloud auth list`, check `roles/aiplatform.user` binding, re-authenticate |
| Agent not found | `NotFound` from `agent_engines.get()` | List available agents with `agent_engines.list()` and suggest the closest match |
| A2A endpoint unreachable | curl returns non-200 or connection timeout | Mark A2A checks as FAIL, note the endpoint is not configured, continue scoring other categories |
| Monitoring data empty | Cloud Monitoring query returns no time series | Check if Monitoring API is enabled and agent has received traffic; skip performance scoring with explanation |
| VPC-SC access blocked | `VPC_SERVICE_CONTROLS` error in API response | Advise adding inspector SA to access level; provide the gcloud command to create the access policy |

## Extension Points

- Custom scoring weights: override default category weights by passing a weights config for org-specific priorities
- Additional inspection categories: add new check functions following the `{category}_check() -> {score, findings}` pattern
- CI/CD integration: pipe the YAML output into a quality gate that blocks deployment below a threshold score
- Historical tracking: store inspection reports in GCS or BigQuery to track readiness trends over time
- Alert integration: feed critical findings directly into PagerDuty or Slack via webhook
- Multi-agent fleet inspection: iterate over all agents in a project to produce a fleet-wide readiness dashboard
- Compliance profiles: define inspection profiles for SOC2, HIPAA, or FedRAMP with stricter thresholds per category
