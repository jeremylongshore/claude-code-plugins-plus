---
name: guidewire-local-dev-loop
description: |
  Configure Guidewire Studio local development with Gosu debugging, hot reload, and test data.
  Trigger: "guidewire local dev loop", "local-dev-loop".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Local Dev Loop

## Overview

Guidewire Studio (IntelliJ-based): Gosu debugging with breakpoints, hot deploy of Gosu changes, GUnit tests, local test data via sample data loader. Use gradle runServer for local InsuranceSuite instance.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
