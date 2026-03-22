---
name: guidewire-observability
description: |
  Monitor Guidewire InsuranceSuite: logging, metrics, tracing, and alerting via GCC.
  Trigger: "guidewire observability", "observability".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Observability

## Overview

GCC provides: application logs, performance metrics, batch process monitoring, API call analytics. Export to Datadog/Splunk via GCC integrations. Alert on: API error rates, batch failures, queue depth, response latency.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
