# Schema: jeremy-vertex-validator

Machine-readable specification for the Vertex AI Production Readiness Validator.

## Validation Categories

| Category | Weight | Checks | Threshold |
|----------|--------|--------|-----------|
| Security | 30% | IAM, VPC-SC, CMEK, Model Armor, Secrets, Agent Identity | ≥ 80% READY |
| Performance | 25% | Auto-scaling, Resource Limits, Latency, Error Rate, Caching | ≥ 70% READY |
| Monitoring | 20% | Alerts, SLOs, Dashboards, Logging, Tracing | ≥ 70% READY |
| Compliance | 15% | Audit Logs, Data Residency, Privacy, Backup/DR | ≥ 80% READY |
| Best Practices | 10% | Agent Config, Memory Bank, A2A Protocol, Code Quality | ≥ 60% READY |

## Scoring

- **READY**: ≥ 80% weighted score
- **NEEDS WORK**: 50–79% weighted score
- **NOT READY**: < 50% weighted score

## Check Result Schema

```json
{
  "category": "Security | Monitoring | Performance | Compliance | Best Practices",
  "check": "Human-readable check name",
  "status": "PASS | FAIL | WARNING | SKIP",
  "evidence": "What was found (gcloud output, SDK response, etc.)",
  "remediation": "How to fix if FAIL/WARNING",
  "weight": 0.0,
  "doc_link": "https://cloud.google.com/..."
}
```

## Report Schema

```json
{
  "project_id": "string",
  "agent_id": "string",
  "region": "string",
  "timestamp": "ISO-8601",
  "overall_score": 0.0,
  "overall_status": "READY | NEEDS WORK | NOT READY",
  "categories": {
    "security": { "score": 0.0, "checks": [] },
    "monitoring": { "score": 0.0, "checks": [] },
    "performance": { "score": 0.0, "checks": [] },
    "compliance": { "score": 0.0, "checks": [] },
    "best_practices": { "score": 0.0, "checks": [] }
  },
  "recommendations": [
    { "priority": "HIGH | MEDIUM | LOW", "action": "string", "impact": "string" }
  ]
}
```

## SDK Requirements

| Package | Min Version | Purpose |
|---------|------------|---------|
| google-cloud-aiplatform | 1.112.0 | Agent Engine SDK (vertexai.Client) |
| google-cloud-monitoring | 2.21.0 | Alert policies, SLOs, metrics |
| google-cloud-logging | 3.10.0 | Log sinks, retention, audit |
| google-cloud-resource-manager | 1.12.0 | IAM policies, audit configs |
| google-cloud-secret-manager | 2.20.0 | Secret rotation checks |

## API Surface

No gcloud CLI exists for Agent Engine. Management uses:

- **Python SDK**: `vertexai.Client().agent_engines.*` (list, get, create, delete)
- **REST**: `https://{LOC}-aiplatform.googleapis.com/v1/projects/{P}/locations/{L}/reasoningEngines`
- **ADK CLI**: `adk deploy agent_engine` (deployment only)
- **Terraform**: `google_vertex_ai_reasoning_engine` resource
