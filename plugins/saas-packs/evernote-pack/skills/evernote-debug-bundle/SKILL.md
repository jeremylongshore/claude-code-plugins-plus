---
name: evernote-debug-bundle
description: |
  Debug Evernote API issues with diagnostic tools and techniques.
  Use when troubleshooting API calls, inspecting requests/responses,
  or diagnosing integration problems.
  Trigger with phrases like "debug evernote", "evernote diagnostic",
  "troubleshoot evernote", "evernote logs", "inspect evernote".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Debug Bundle

## Overview
Comprehensive debugging toolkit for Evernote API integrations, including request logging, ENML validation, token inspection, and diagnostic utilities.

## Prerequisites
- Evernote SDK installed
- Node.js environment
- Understanding of common Evernote errors

## Instructions

### Step 1: Debug Logger

### Step 2: Instrumented Client Wrapper

### Step 3: ENML Validator

### Step 4: Token Inspector

### Step 5: Diagnostic CLI

### Step 6: Package.json Scripts

For full implementation details and code examples, load:
`references/implementation-guide.md`

## Output
- Debug logger with request/response tracking
- Instrumented client wrapper for automatic logging
- ENML validator with auto-fix capability
- Token and account inspector
- Diagnostic CLI script

## Error Handling
| Issue | Diagnostic | Solution |
|-------|------------|----------|
| Auth failures | Check token in logs | Re-authenticate |
| ENML errors | Use ENMLValidator | Auto-fix with validator |
| Rate limits | Check request frequency in logs | Add delays |
| Missing data | Inspect response logs | Check API parameters |

## Resources
- [Error Handling](https://dev.evernote.com/doc/articles/error_handling.php)
- [ENML DTD](http://xml.evernote.com/pub/enml2.dtd)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For rate limit handling, see `evernote-rate-limits`.

## Examples

**Basic usage**: Apply evernote debug bundle to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote debug bundle for production environments with multiple constraints and team-specific requirements.