---
name: guidewire-cost-tuning
description: |
  Optimize Guidewire Cloud costs: license management, API usage, compute right-sizing.
  Trigger: "guidewire cost tuning", "cost-tuning".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Cost Tuning

## Overview

Right-size cloud instances via GCC, optimize batch process scheduling (off-peak), reduce API calls with caching, use bulk endpoints instead of individual calls, monitor license utilization. Review GCC billing dashboard monthly.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
