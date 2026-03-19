---
name: gamma-debug-bundle
description: |
  Comprehensive debugging toolkit for Gamma integration issues.
  Use when you need detailed diagnostics, request tracing,
  or systematic debugging of Gamma API problems.
  Trigger with phrases like "gamma debug bundle", "gamma diagnostics",
  "gamma trace", "gamma inspect", "gamma detailed logs".
allowed-tools: Read, Write, Edit, Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Gamma Debug Bundle

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
Comprehensive debugging toolkit for systematic troubleshooting of Gamma integration issues including request tracing, environment checks, and exportable debug bundles.

## Prerequisites
- Active Gamma integration with issues
- Node.js 18+ for debug tools
- Access to application logs

## Instructions

### Step 1: Create Debug Client
Wrap GammaClient with request/response/error interceptors that log method, path, duration, status, and full payloads.

### Step 2: Run Diagnostic Script
Sequential tests: authentication (ping), API access (list presentations), generation (dry-run create), and rate limit status check.

### Step 3: Check Environment
Verify GAMMA_API_KEY is set, NODE_ENV is correct, and Node.js version is compatible.

### Step 4: Export Debug Bundle
Package environment info, request logs, and config into a JSON file for sharing with support.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for debug client with interceptors, diagnostic script, environment checker, and bundle export code.

## Output
- Debug client with full request tracing
- Diagnostic report with pass/fail for each subsystem
- Environment verification report
- Exportable JSON debug bundle

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Auth test fails | Invalid API key | Verify GAMMA_API_KEY env var |
| List returns empty | No presentations | Create test presentation first |
| Generation fails | Rate limit or quota | Check rate limit status |
| Timeout errors | Network issues | Check connectivity to gamma.app |

## Examples

### Quick Diagnostic
```bash
npx ts-node debug/diagnose.ts
# Output: 4 tests with pass/fail and request log summary
```

## Resources
- [Gamma Debug Guide](https://gamma.app/docs/debugging)
- [Gamma Support Portal](https://gamma.app/support)

## Next Steps
Proceed to `gamma-rate-limits` for rate limit management.