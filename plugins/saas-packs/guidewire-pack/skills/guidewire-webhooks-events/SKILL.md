---
name: guidewire-webhooks-events
description: |
  Implement Guidewire App Events and webhook integrations for event-driven architecture.
  Trigger: "guidewire webhooks events", "webhooks-events".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(gradle:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, insurance, guidewire]
compatible-with: claude-code
---

# Guidewire Webhooks Events

## Overview

Guidewire App Events: configure outbound events in GCC for entity changes (claim created, policy issued). Events published to message queue (AWS SQS/SNS). Build event consumers that process InsuranceSuite state changes in near-real-time.

For detailed implementation, see: [implementation guide](references/implementation-guide.md)

## Resources

- [Guidewire Developer Portal](https://developer.guidewire.com/)
- [Cloud API Reference](https://docs.guidewire.com/cloud/pc/202503/apiref/)
- [Guidewire Cloud Console](https://gcc.guidewire.com)
- [Gosu Language Guide](https://gosu-lang.github.io/)
