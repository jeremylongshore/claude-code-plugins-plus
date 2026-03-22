---
name: guidewire-prod-checklist
description: |
  Production deployment readiness for Guidewire Cloud including configuration promotion and testing.
  Trigger: "guidewire prod checklist", "prod-checklist".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Prod Checklist

## Overview

Verify: all Gosu compiles without errors, GUnit tests pass, Cloud API roles configured, integration gateway endpoints tested, batch processes scheduled, monitoring alerts configured, configuration promoted through dev > staging > production via GCC.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
