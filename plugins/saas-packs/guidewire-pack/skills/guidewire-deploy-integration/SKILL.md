---
name: guidewire-deploy-integration
description: |
  Deploy Guidewire integrations to Cloud Platform with configuration packages and release management.
  Trigger: "guidewire deploy integration", "deploy-integration".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Deploy Integration

## Overview

Deploy via GCC: build configuration package with gradle, upload to GCC > Deployments, promote through environments (dev > staging > prod). Use deployment slots for zero-downtime releases. Rollback via GCC if issues detected.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
