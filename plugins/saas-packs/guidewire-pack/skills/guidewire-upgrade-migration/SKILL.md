---
name: guidewire-upgrade-migration
description: |
  Upgrade Guidewire InsuranceSuite versions and migrate between Cloud environments.
  Trigger: "guidewire upgrade migration", "upgrade-migration".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Upgrade Migration

## Overview

Version upgrade: review release notes for breaking changes, run upgrade tool in Studio, merge configuration changes, test all Gosu customizations, validate API compatibility, promote through environments. Use GCC for cloud version management.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
