---
name: guidewire-multi-env-setup
description: |
  Configure Guidewire multi-environment: dev, staging, and production with configuration promotion.
  Trigger: "guidewire multi env setup", "multi-env-setup".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Multi Env Setup

## Overview

GCC manages environments: dev (rapid iteration), staging (UAT), production. Configuration promotion via GCC pipeline. Environment-specific OAuth credentials. Separate integration gateway endpoints per environment. Data isolation enforced by GCC.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
