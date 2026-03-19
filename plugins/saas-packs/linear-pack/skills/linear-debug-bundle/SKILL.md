---
name: linear-debug-bundle
description: |
  Comprehensive debugging toolkit for Linear integrations.
  Use when setting up logging, tracing API calls,
  or building debug utilities for Linear.
  Trigger with phrases like "debug linear integration", "linear logging",
  "trace linear API", "linear debugging tools", "linear troubleshooting".
allowed-tools: Read, Write, Edit, Grep, Bash(node:*), Bash(npx:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Linear Debug Bundle

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
Comprehensive debugging tools for Linear API integrations: debug client wrapper with request/response logging, request tracer with performance metrics, health check endpoint, interactive debug console, and environment validator.

## Prerequisites
- Linear SDK configured
- Node.js environment
- Optional: logging library (pino, winston)

## Instructions

### Step 1: Create Debug Client Wrapper
Build `createDebugClient()` that wraps `LinearClient` with a custom `fetch` interceptor. Log all requests (query preview + variables), responses (duration, error presence, data keys), and errors (duration, message). Support `onRequest`, `onResponse`, and `onError` callback hooks for custom integrations.

### Step 2: Request Tracer
Implement `LinearTracer` class that records trace entries (id, operation, start/end time, duration, success, error, metadata). Provide `startTrace()`/`endTrace()` lifecycle, `getSlowTraces(thresholdMs)` for performance analysis, `getFailedTraces()` for error tracking, and `getSummary()` for aggregate stats (total, completed, failed, avg/max duration). Cap at 100 traces with automatic trimming.

### Step 3: Health Check Utility
Create `checkLinearHealth()` that parallel-fetches viewer info and teams, returning latency, user details, team count, and healthy/unhealthy status. Expose as an Express/Koa endpoint via `healthEndpoint()` returning 200 or 503.

### Step 4: Debug Console Commands
Build an interactive REPL with readline that provides commands: `me` (current user), `teams` (list teams with keys), `issues` (recent 10 issues), `states` (workflow states per team), `help`, and `exit`.

### Step 5: Environment Validator
Create `validateLinearEnv()` that checks `LINEAR_API_KEY` presence and format (`lin_api_` prefix), warns about missing `LINEAR_WEBHOOK_SECRET`, and flags non-production keys in production environments. Auto-run on import with console output.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for complete debug client, tracer, health check, CLI console, and environment validator code.

## Output
- Debug client with request/response logging
- Request tracer with performance metrics
- Health check endpoint (200/503)
- Interactive debug console (REPL)
- Environment validator with warnings

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Circular JSON | Logging full Linear objects | Use selective logging |
| Memory leak | Unbounded trace storage | Set maxTraces limit |
| Missing env | Validation failed | Check environment setup |

## Examples


**Basic usage**: Apply linear debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize linear debug bundle for production environments with multiple constraints and team-specific requirements.

## Resources
- [Linear SDK Source](https://github.com/linear/linear)
- [Node.js Debugging](https://nodejs.org/en/docs/guides/debugging-getting-started)
- [Performance Tracing](https://nodejs.org/api/perf_hooks.html)

## Next Steps
Learn rate limiting strategies with `linear-rate-limits`.