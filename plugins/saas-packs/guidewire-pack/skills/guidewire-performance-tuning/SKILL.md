---
name: guidewire-performance-tuning
description: |
  Optimize Guidewire performance: Gosu query optimization, batch processing, caching, and JVM tuning.
  Trigger: "guidewire performance tuning", "performance-tuning".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Performance Tuning

## Overview

Optimize Gosu queries: use Query API with proper filters (avoid loading all entities), batch processing with BatchProcessBase, cache frequently accessed reference data, tune JVM heap via GCC. Monitor via GCC > Performance dashboard.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
