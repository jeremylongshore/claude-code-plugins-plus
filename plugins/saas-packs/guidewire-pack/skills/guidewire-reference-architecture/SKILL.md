---
name: guidewire-reference-architecture
description: |
  Enterprise reference architecture for Guidewire InsuranceSuite Cloud deployments.
  Trigger: "guidewire reference architecture", "reference-architecture".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Reference Architecture

## Overview

Architecture: Jutro Frontend -> Cloud API Gateway -> PolicyCenter/ClaimCenter/BillingCenter -> Integration Gateway -> External Systems. Data warehouse via Guidewire DataHub. Analytics via Guidewire Explore. All managed in GCC.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
