---
name: lindy-performance-tuning
description: |
  Optimize Lindy AI agent performance and response times.
  Use when improving latency, optimizing throughput,
  or reducing response times.
  Trigger with phrases like "lindy performance", "lindy slow",
  "optimize lindy", "lindy latency".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Lindy AI Performance Tuning

## Overview
Optimize Lindy AI agent execution speed and reliability. Lindy agents run as multi-step automations where each step (LLM call, tool execution, API call) adds latency.

## Prerequisites
- Lindy workspace with active agents
- Access to agent configuration and run history
- Understanding of agent step execution flow

## Instructions

### Step 1: Identify Slow Steps
### Step 2: Consolidate LLM Steps
### Step 3: Cache Agent Context Data
### Step 4: Parallelize Independent Steps
### Step 5: Optimize Trigger Configuration

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Agent timeout (>60s) | Too many sequential steps | Consolidate steps, add parallel execution |
| Step retry loop | Transient API failure | Set max retries to 2, add fallback step |
| Slow LLM step | Prompt too long or complex | Shorten prompt, use focused instructions |
| High run frequency | Trigger firing too often | Add filters to trigger configuration |

## Examples

**Basic usage**: Apply lindy performance tuning to a standard project setup with default configuration options.

**Advanced scenario**: Customize lindy performance tuning for production environments with multiple constraints and team-specific requirements.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale

See [ORM implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.

## Resources

- Official ORM documentation
- Community best practices and patterns
- Related skills in this plugin pack