---
name: guidewire-ci-integration
description: |
  Configure CI/CD pipelines for Guidewire with Gosu compilation, GUnit tests, and configuration deployment.
  Trigger: "guidewire ci integration", "ci-integration".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Ci Integration

## Overview

GitHub Actions/Jenkins: gradle compileGosu, gradle test (GUnit), gradle buildConfiguration, deploy configuration package via GCC API. Separate pipelines for Gosu changes vs configuration-only changes.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
