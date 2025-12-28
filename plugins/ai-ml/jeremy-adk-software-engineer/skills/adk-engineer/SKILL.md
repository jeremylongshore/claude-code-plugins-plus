---
name: adk-engineer
description: |
  Software engineer specializing in creating production-ready ADK agents with best practices, code structure, testing, and deployment automation. Use when asked to "build ADK agent", "create agent code", or "engineer ADK application". Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# ADK Engineer

Engineer production-ready Agent Development Kit (ADK) agents and multi-agent systems: clean structure, testability, safe tool usage, and deployment automation.

## Overview

Use this skill to design and implement ADK agent code that is maintainable and shippable: clear module boundaries, structured tool interfaces, regression tests, and a deployment checklist (local or Agent Engine).

## Prerequisites

- A target runtime (Python/Java/Go) consistent with the project’s pinned versions
- ADK installed (and any required model/provider SDKs configured)
- A test runner available in the repo (unit tests at minimum)
- If deploying: access to a Google Cloud project and permissions for the chosen deployment target

## Instructions

1. Clarify requirements: agent goals, tool surface, latency/cost constraints, and deployment target.
2. Propose architecture: single agent vs multi-agent, orchestration pattern, state strategy (Memory Bank / external store).
3. Scaffold structure: agent entrypoint(s), tool modules, config, and tests.
4. Implement incrementally:
   - add one tool at a time with input validation and structured outputs
   - add regression tests for each tool and critical prompt flows
5. Add operational guardrails: retries/backoff, timeouts, logging, and safe error messages.
6. Validate locally (tests + smoke prompts) and provide a deployment plan (when requested).

## Output

- A concrete architecture plan and file layout
- Agent and tool implementations (or patches) with tests
- A validation checklist (commands to run, expected outputs, and failure triage)
- Optional: deployment instructions and post-deploy health checks

## Error Handling

- Build/test failures: isolate the failing module, minimize the repro, fix, and add a regression test.
- Tool/runtime errors: enforce structured error responses and safe retries where appropriate.
- Deployment failures: provide the exact failing command, logs to inspect, and least-privilege IAM fixes.

## Examples

**Example: Productionizing an existing ADK agent**
- Request: “Refactor this agent into a clean module structure and add tests before we deploy.”
- Result: reorganized `src/` layout, tool boundaries, a test suite, and a deployment checklist.

**Example: Multi-agent workflow**
- Request: “Build a validator + deployer + monitor agent team with a sequential orchestrator.”
- Result: orchestrator skeleton, per-agent responsibilities, and smoke tests for each step.

## Resources

- Full detailed playbook (kept for reference): `{baseDir}/references/SKILL.full.md`
- Repo standards (source of truth):
  - `000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md`
  - `000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md`
- ADK / Agent Engine docs: https://cloud.google.com/vertex-ai/docs/agent-engine
