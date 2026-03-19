---
name: langchain-debug-bundle
description: |
  Collect LangChain debug evidence for troubleshooting and support.
  Use when preparing bug reports, collecting traces,
  or gathering diagnostic information for complex issues.
  Trigger with phrases like "langchain debug bundle", "langchain diagnostics",
  "langchain support info", "collect langchain logs", "langchain trace".
allowed-tools: Read, Write, Edit, Bash(python:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Debug Bundle

## Current State
!`node --version 2>/dev/null || echo 'N/A'`
!`python3 --version 2>/dev/null || echo 'N/A'`
!`uname -a`

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Collect comprehensive debug information for LangChain issues including traces, versions, and reproduction steps.

## Prerequisites
- LangChain installed
- Reproducible error condition
- Access to logs and environment

## Instructions

### Step 1: Collect Environment Info
Run `pip show` on all LangChain packages to gather versions, Python version, and platform info.

### Step 2: Enable Full Tracing
Set `langchain.debug = True` and enable LangSmith tracing. Attach a `DebugCallback` that logs all LLM start/end/error events with timestamps.

### Step 3: Create Minimal Reproduction
Write a standalone script that reproduces the issue with minimal code and redacted API keys.

### Step 4: Generate Debug Bundle
Combine environment info, trace logs, and reproduction steps into a `debug_bundle.json` file.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete debug callback and bundle generator code.

## Output
- `debug_bundle.json` with full diagnostic information
- `minimal_repro.py` for issue reproduction
- Environment and version information
- Trace logs with timestamps

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Callback not capturing | Not attached to LLM | Pass via `callbacks=` parameter |
| Large trace logs | Long-running operation | Filter by time range |
| API key in logs | Missing redaction | Always redact before sharing |

## Examples


**Basic usage**: Apply langchain debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize langchain debug bundle for production environments with multiple constraints and team-specific requirements.

## Resources
- [LangChain GitHub Issues](https://github.com/langchain-ai/langchain/issues)
- [LangSmith Tracing](https://docs.smith.langchain.com/)
- [LangChain Discord](https://discord.gg/langchain)

## Next Steps
Use `langchain-common-errors` for quick fixes or escalate with the bundle.