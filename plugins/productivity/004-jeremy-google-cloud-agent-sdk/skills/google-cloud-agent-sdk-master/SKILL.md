---
name: google-cloud-agent-sdk-master
description: |
  Automatic activation for all google cloud agent development kit (adk) Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, WebFetch, WebSearch, Grep
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Google Cloud Agent SDK Master

Master Google’s Agent Development Kit (ADK) patterns for building and deploying production-grade agents with clear tool contracts, validation, and operational guardrails.

## Overview

Use this skill to quickly answer “how do I do X with Google ADK?” and to produce a safe, production-oriented plan (structure, patterns, deployment, verification) rather than ad-hoc snippets.

## Examples

**Example: Pick the right ADK pattern**
- Request: “Should this be a single agent or a multi-agent orchestrator?”
- Output: an architecture recommendation with tradeoffs, plus a minimal scaffold plan.

## Prerequisites

- The target environment (local-only vs Vertex AI Agent Engine)
- The agent’s core job, expected inputs/outputs, and required tools
- Any constraints (latency, cost, compliance/security)

## Instructions

1. Clarify requirements and choose an ADK architecture (single vs multi-agent; orchestration pattern).
2. Define tool interfaces (inputs, outputs, and error contracts) and how secrets are managed.
3. Provide an implementation plan with a minimal scaffold and incremental milestones.
4. Add validation: smoke prompts, regression tests, and deployment verification steps.

## Output

- A recommended ADK architecture and scaffold layout
- A checklist of commands to validate locally and in CI
- Optional: deployment steps and post-deploy health checks

## Error Handling

- If documentation conflicts, prefer the latest canonical standards in `000-docs/6767-*`.
- If an API feature is unavailable in a region/version, propose a compatible alternative.

## Resources

- Full detailed guide (kept for reference): `{baseDir}/references/SKILL.full.md`
- ADK / Agent Engine docs: https://cloud.google.com/vertex-ai/docs/agent-engine
- Canonical repo standards: `000-docs/6767-a-SPEC-DR-STND-claude-code-plugins-standard.md`
