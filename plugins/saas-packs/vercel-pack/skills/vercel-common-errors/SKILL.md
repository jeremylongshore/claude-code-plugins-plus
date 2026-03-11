---
name: vercel-common-errors
description: |
  Execute diagnose and fix Vercel common errors and exceptions.
  Use when encountering Vercel errors, debugging failed requests,
  or troubleshooting integration issues.
  Trigger with phrases like "vercel error", "fix vercel",
  "vercel not working", "debug vercel".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Vercel Common Errors

## Prerequisites
- Vercel SDK installed
- API credentials configured
- Access to error logs

## Instructions

### Step 1: Identify the Error
Check error message and code in your logs or console.

### Step 2: Find Matching Error Below
Match your error to one of the documented cases.

### Step 3: Apply Solution
Follow the solution steps for your specific error.

## Output
- Identified error cause
- Applied fix
- Verified resolution

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [Vercel Status Page](https://www.vercel-status.com)
- [Vercel Support](https://vercel.com/docs/support)
- [Vercel Error Codes](https://vercel.com/docs/errors)

## Overview

Execute diagnose and fix Vercel common errors and exceptions.