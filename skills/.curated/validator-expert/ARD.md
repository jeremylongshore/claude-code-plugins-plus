# ARD: Vertex AI Validator Expert

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

```
Developer invokes validation
    │
    ▼
Validator Expert Skill
    │
    ├── gcloud CLI ──→ IAM policies, VPC-SC config, audit logs
    ├── Vertex AI SDK ──→ Agent Engine deployment config
    ├── Cloud Monitoring API ──→ dashboards, alerting policies, SLOs
    └── Cloud Logging API ──→ structured log analysis
    │
    ▼
Production Readiness Report (0-100% score)
```

The validator operates read-only against GCP APIs. It never modifies infrastructure.

## Data Flow

1. **Input**: Project ID, Agent Engine deployment ID (or auto-detected from current project)
2. **Discovery**: Retrieve deployment config via `vertexai.Client().agent_engines.get()`
3. **Security scan**: Check IAM bindings, VPC-SC perimeter, encryption config, secrets in env vars
4. **Monitoring scan**: Query Cloud Monitoring for dashboards, alert policies, SLO definitions
5. **Performance scan**: Verify auto-scaling config, resource limits, caching, sandbox settings
6. **Compliance scan**: Check audit log enablement, data residency, backup config
7. **Scoring**: Weight each category, compute composite 0-100%
8. **Output**: Score card + pass/fail table + prioritized remediation

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Scoring weights | Security 30, Performance 25, Monitoring 20, Compliance 15, Best Practices 10 | Security failures have highest blast radius; performance affects users directly |
| Agent Identity over service accounts | Recommended for 2025+ | Google's direction for Agent Engine — simpler, more secure, eliminates key management |
| Read-only enforcement | Validator never writes | Trust boundary — validation tool shouldn't have deploy permissions |
| DCI for project detection | `!gcloud config get-value project` | Auto-detects active project, saves a tool call round |
| Checklist separation | 3 reference files by category | Progressive disclosure — full checklists are 100+ lines each |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| `Bash(gcloud:*)` | IAM policy reads, VPC-SC queries, audit log checks, monitoring API |
| `Bash(python:*)` | Vertex AI SDK calls for deployment config |
| `Bash(bandit:*)` | Static security analysis of agent code |
| `Bash(pylint:*)`, `Bash(flake8:*)`, `Bash(mypy:*)` | Code quality validation |
| `Bash(pytest:*)` | Verify test coverage exists |
| `Read` | Examine deployment configs, agent code |
| `Grep` | Search for hardcoded secrets, misconfigured patterns |
| `Glob` | Find config files, test files, deployment manifests |

## Error Handling Strategy

| Scenario | Behavior |
|----------|----------|
| Missing IAM permission | Mark check as "INCONCLUSIVE" (not failed), note required role |
| API not enabled | Suggest `gcloud services enable` command, skip dependent checks |
| Agent not found | Abort with clear error, suggest listing agents to verify ID |
| Timeout on API call | Retry once with backoff, then mark inconclusive |
| Previous run not available | Skip comparison, note "no baseline" |

## Extension Points

- **Custom check plugins**: Add new validation categories by creating a checklist .md and registering it in the scoring weights
- **CI integration**: `--json` output mode for pipeline consumption
- **Multi-agent batch**: Run validation across all agents in a project with `--all-agents` flag
- **Threshold gates**: Set minimum scores per category for CI pass/fail
