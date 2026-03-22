---
name: guidewire-common-errors
description: |
  Diagnose and fix common Guidewire Cloud API errors including Gosu exceptions, validation failures, and integration issues.
  Trigger: "guidewire common errors", "common-errors".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Common Errors

## Overview

Fix 400 (validation), 401 (OAuth token expired), 403 (missing API role), 404 (wrong endpoint path), 409 (stale checksum - re-GET and retry), 422 (business rule violation - read userMessage). Gosu errors: ClassNotFoundException (wrong module), NPE (null entity reference), ValidationException (missing required fields).

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
