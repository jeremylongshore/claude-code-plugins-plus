---
name: guidewire-rate-limits
description: |
  Manage Guidewire Cloud API rate limits, quotas, and throttling for high-volume integrations.
  Trigger: "guidewire rate limits", "rate-limits".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Rate Limits

## Overview

Cloud API enforces per-tenant rate limits. Batch operations use the batch API endpoint. Implement exponential backoff on 429 responses. Use API Gateway throttling in GCC. Optimize with bulk endpoints for batch processing.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
