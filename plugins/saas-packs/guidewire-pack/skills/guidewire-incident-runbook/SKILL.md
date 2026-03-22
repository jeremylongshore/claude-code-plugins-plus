---
name: guidewire-incident-runbook
description: |
  Respond to Guidewire production incidents: triage, mitigation, and recovery.
  Trigger: "guidewire incident runbook", "incident-runbook".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Incident Runbook

## Overview

Triage: Check GCC > Monitoring for system health. API errors -> check OAuth tokens and API roles. Batch failures -> review batch logs in GCC. Performance degradation -> check JVM metrics and query performance. Escalate to Guidewire Support with GCC ticket.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
