# ARD: ADK Deployment Specialist

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The ADK Deployment Specialist bridges local ADK agent development and production Agent Engine hosting. It interacts with the local codebase for implementation, the ADK SDK for agent construction, and Google Cloud for deployment and validation.

```
Local Agent Code
       ↓
[ADK Deployment Specialist]
  ├── Reads: agent source, configs, requirements
  ├── Writes: agent code, deploy scripts, smoke tests
  └── Calls: pytest, ADK CLI, Python SDK, gcloud, curl
       ↓
Vertex AI Agent Engine
  ├── AgentCard endpoint
  ├── Task Send/Status APIs
  ├── Code Execution Sandbox
  └── Memory Bank
```

## Data Flow

1. **Input**: Agent name or project ID, desired architecture (single/multi-agent), orchestration pattern, and tool requirements from user request
2. **Processing**: Scaffold or patch agent code with A2A interfaces, configure Code Execution Sandbox (TTL 7-14 days, SECURE_ISOLATED), set up Memory Bank if stateful conversations needed, run local tests, then deploy via `vertexai.Client().agent_engines.create()` with validated requirements
3. **Output**: Deployed agent with verified A2A endpoints, deployment confirmation with endpoint URLs, health check commands, and observability configuration (logs, dashboards, retry policies)

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Python SDK for deployment | `vertexai.Client().agent_engines.create()` | No gcloud CLI surface for Agent Engine; SDK provides full control |
| A2A-first interface design | Define AgentCard + task contracts before implementation | Ensures inter-agent compatibility and testable contracts |
| Local-first testing | Run all tests locally before any cloud deployment | Catches issues early; avoids costly failed deployments |
| Sandbox defaults | TTL 7-14 days, SECURE_ISOLATED type | Balances state retention with security; matches Google's recommended production config |
| Sequential orchestration as starting point | Default to SequentialAgent for multi-agent flows | Predictable debugging path; upgrade to Parallel/Loop when performance requires it |
| Requirements isolation | Production deps only in deployed package | Test and dev deps increase package size and cold start time without benefit |
| Smoke tests for validation | Automated endpoint verification post-deploy | Catches deployment issues immediately rather than waiting for user traffic |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect existing agent code, A2A contracts, deployment configs, and requirements files |
| Write | Create agent entrypoints, tool modules, deploy scripts, and smoke test files |
| Edit | Patch existing agents to add A2A endpoints, fix deployment issues, update requirements |
| Grep | Search for import patterns, API usage, credential references, and configuration values |
| Glob | Discover project structure — agent files, test suites, deployment artifacts |
| Bash(cmd:*) | Run pytest, ADK commands, Python SDK deployment, gcloud IAM setup, curl for endpoint validation |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Package dependency conflict | `pip install` or Agent Engine returns `requirements parse error` | Pin all deps with `==` versions; remove local paths from requirements.txt |
| Agent Engine creation timeout | SDK call exceeds 300s without completion | Reduce package size (exclude tests/docs); retry in `us-central1` for best capacity |
| A2A endpoint 404 | curl to `/.well-known/agent-card` returns 404 | Verify agent is configured for A2A protocol; check A2A enablement in agent config |
| IAM permission denied | `PermissionDenied` during deployment or endpoint access | Grant `roles/aiplatform.user` and `roles/aiplatform.deployer` to the deploying identity |
| Memory Bank initialization failure | Memory Bank returns errors or empty state | Verify Firestore is provisioned in the project; check Memory Bank API enablement |

## Extension Points

- Custom orchestration patterns: replace Sequential with Parallel or Loop agents by changing the pipeline definition
- Additional A2A endpoints: extend the agent card with custom capabilities and task types
- CI/CD integration: wrap deployment commands in GitHub Actions with WIF authentication (see gh-actions-validator)
- Blue-green deployment: deploy new version alongside existing, validate, then switch traffic
- Multi-region deployment: extend deploy scripts to target multiple regions with traffic splitting
- Automated rollback: add rollback scripts that revert to previous agent version on validation failure
- Custom health checks: extend post-deploy validation with application-specific probes beyond A2A endpoints
