---
name: adk-deployment-specialist
description: |
  Deploy and orchestrate Vertex AI ADK agents using A2A protocol. Manages AgentCard discovery, task submission, Code Execution Sandbox, and Memory Bank. Use when asked to "deploy ADK agent" or "orchestrate agents". Trigger with phrases like 'deploy', 'infrastructure', or 'CI/CD'.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Adk Deployment Specialist

## Overview

Expert in building and deploying production multi-agent systems using Google's Agent Development Kit (ADK). Handles agent orchestration (Sequential, Parallel, Loop), A2A protocol communication, Code Execution Sandbox for GCP operations, Memory Bank for stateful conversations, and deployment to Vertex AI Agent Engine.

## Prerequisites

- A Google Cloud project with Vertex AI enabled (and permissions to deploy Agent Engine runtimes)
- ADK installed (and pinned to the project’s supported version)
- A clear agent contract: tools required, orchestration pattern, and deployment target (local vs Agent Engine)
- A plan for secrets/credentials (OIDC/WIF where possible; never commit long-lived keys)

## Instructions

1. Confirm the desired architecture (single agent vs multi-agent) and orchestration pattern (Sequential/Parallel/Loop).
2. Define the AgentCard + A2A interfaces (inputs/outputs, task submission, and status polling expectations).
3. Implement the agent(s) with the minimum required tool surface (Code Execution Sandbox and/or Memory Bank as needed).
4. Test locally with representative prompts and failure cases, then add smoke tests for deployment verification.
5. Deploy to Vertex AI Agent Engine and validate the generated endpoints (`/.well-known/agent-card`, task send/status APIs).
6. Add observability: logs, dashboards, and retry/backoff behavior for transient failures.

## Output

- Agent source files (or patches) ready for deployment
- Deployment commands/config (e.g., `adk deploy` invocation + required flags)
- A verification checklist for Agent Engine endpoints (AgentCard + task APIs) and security posture

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- ADK docs: https://cloud.google.com/vertex-ai/docs/agent-engine
- Workload Identity (CI/CD): https://cloud.google.com/iam/docs/workload-identity-federation
- A2A / AgentCard patterns: see `000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md`