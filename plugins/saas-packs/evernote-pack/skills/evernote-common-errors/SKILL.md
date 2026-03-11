---
name: evernote-common-errors
description: |
  Diagnose and fix common Evernote API errors.
  Use when encountering Evernote API exceptions, debugging failures,
  or troubleshooting integration issues.
  Trigger with phrases like "evernote error", "evernote exception",
  "fix evernote issue", "debug evernote", "evernote troubleshooting".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Common Errors

## Overview
Comprehensive guide to diagnosing and resolving Evernote API errors, including EDAMUserException, EDAMSystemException, and EDAMNotFoundException.

## Prerequisites
- Basic Evernote SDK setup
- Understanding of Evernote data model

## Instructions

1. See implementation guide for detailed steps.

2. For full implementation details and code examples, load:
3. `references/implementation-guide.md`

## Output
- Understanding of all Evernote exception types
- Error code reference with solutions
- Reusable error handling service
- Rate limit retry implementation

## Error Handling
| Exception | When Thrown |
|-----------|-------------|
| `EDAMUserException` | Client error - invalid input, permissions |
| `EDAMSystemException` | Server error - rate limits, maintenance |
| `EDAMNotFoundException` | Resource not found - invalid GUID |

## Resources
- [Error Handling](https://dev.evernote.com/doc/articles/error_handling.php)
- [Rate Limits](https://dev.evernote.com/doc/articles/rate_limits.php)
- [API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For debugging tools and techniques, see `evernote-debug-bundle`.

## Examples

**Basic usage**: Apply evernote common errors to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote common errors for production environments with multiple constraints and team-specific requirements.