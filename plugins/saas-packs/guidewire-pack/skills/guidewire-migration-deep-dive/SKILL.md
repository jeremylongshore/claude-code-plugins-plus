---
name: guidewire-migration-deep-dive
description: |
  Migrate to Guidewire Cloud from self-managed or legacy insurance systems.
  Trigger: "guidewire migration deep dive", "migration-deep-dive".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Migration Deep Dive

## Overview

Migration phases: 1) Assessment (current system audit), 2) Configuration (product model, rules), 3) Data migration (policies, claims, accounts via ETL), 4) Integration cutover (API endpoints, event consumers), 5) UAT and go-live. Use Guidewire Cloud Migration Accelerator.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
