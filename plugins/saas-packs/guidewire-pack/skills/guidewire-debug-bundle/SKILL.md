---
name: guidewire-debug-bundle
description: |
  Collect Guidewire diagnostic info including Cloud API responses, Gosu stack traces, and server logs.
  Trigger: "guidewire debug bundle", "debug-bundle".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Debug Bundle

## Overview

Collect: OAuth token status, API endpoint responses, Gosu server logs from GCC > Logging, batch process status, integration gateway logs. Use GCC > Monitoring for real-time metrics.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
