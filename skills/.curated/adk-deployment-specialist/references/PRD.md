# PRD: ADK Deployment Specialist

**Version:** 2.1.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Deploying ADK multi-agent systems to Vertex AI Agent Engine involves coordinating multiple complex surfaces: agent orchestration patterns (Sequential/Parallel/Loop), A2A protocol endpoints, Code Execution Sandbox configuration, Memory Bank state management, and IAM/networking setup. Getting any one of these wrong causes silent failures, broken inter-agent communication, or security vulnerabilities. Developers spend hours debugging deployment issues that stem from misconfigured agent contracts or missing A2A endpoints.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| AI Engineer | Building a new multi-agent system for production deployment | End-to-end deployment from local agent code to live Agent Engine endpoints |
| Platform Engineer | Migrating existing agents from local dev to Agent Engine | Reliable deployment pipeline with endpoint validation and rollback guidance |
| DevOps Engineer | Setting up CI/CD for agent deployments | Automated deployment commands with health checks and observability hooks |

## Success Criteria

1. Deploy an ADK agent to Agent Engine with verified A2A endpoints in under 15 minutes
2. All A2A protocol endpoints (AgentCard, task send, task status) respond correctly post-deployment
3. Code Execution Sandbox configured with 7-14 day TTL and SECURE_ISOLATED sandbox type
4. Memory Bank enabled with minimum 100-memory retention and Firestore encryption
5. Deployment includes observability: structured logging, retry/backoff, and health monitoring
6. Agent package excludes test files and dev dependencies (minimized cold start)

## Functional Requirements

1. Confirm the desired architecture (single vs multi-agent) and orchestration pattern (Sequential/Parallel/Loop)
2. Define AgentCard and A2A interfaces: inputs, outputs, task submission, and status polling contracts
3. Implement agent(s) with the minimum required tool surface including Code Execution Sandbox and Memory Bank as needed
4. Test locally with representative prompts and failure cases, then generate smoke tests for post-deploy
5. Deploy to Vertex AI Agent Engine using the Python SDK (`vertexai.Client.agent_engines.create()`)
6. Validate deployed endpoints: `/.well-known/agent-card`, `POST /v1/tasks:send`, `GET /v1/tasks/<id>`
7. Configure observability: structured logs, Cloud Monitoring dashboards, and retry/backoff for transient failures

## Non-Functional Requirements

- All deployments use OIDC/WIF for authentication; never commit long-lived service account keys
- Agent packages must exclude test files and dev dependencies to minimize cold start time
- Deployment commands must be idempotent (safe to re-run without side effects)
- Support for both greenfield deployments and updates to existing Agent Engine instances
- Local tests must pass before any deployment attempt (fail-fast principle)
- All generated code must include error handling for transient failures (retries with backoff)
- Deployment scripts must provide clear rollback instructions if validation fails

## Dependencies

- Google Cloud project with Vertex AI API enabled and Agent Engine permissions
- ADK installed and pinned to the project's supported version
- Python SDK `google-cloud-aiplatform[agent_engines]>=1.120.0`
- `gcloud` CLI authenticated with deployment permissions
- A test runner (pytest) available in the repository

## Out of Scope

- Infrastructure provisioning with Terraform (handled by adk-infra-expert)
- Post-deployment inspection and scoring (handled by vertex-engine-inspector)
- CI/CD pipeline creation for GitHub Actions (handled by gh-actions-validator)
- Cost optimization and model selection strategy
- Agent application logic design (handled by adk-engineer)
- Multi-region deployment with traffic splitting
