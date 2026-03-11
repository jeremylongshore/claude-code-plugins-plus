---
name: maintainx-reference-architecture
description: |
  Production-grade architecture patterns for MaintainX integrations.
  Use when designing system architecture, planning integrations,
  or building enterprise-scale MaintainX solutions.
  Trigger with phrases like "maintainx architecture", "maintainx design",
  "maintainx system design", "maintainx enterprise", "maintainx patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# MaintainX Reference Architecture

## Overview
Production-grade architecture patterns for building scalable, maintainable MaintainX integrations.

## Prerequisites
- Understanding of distributed systems
- Cloud platform experience
- MaintainX API familiarity

## Instructions
Follow these high-level steps to implement maintainx-reference-architecture:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/maintainx-pack/skills/maintainx-reference-architecture/references/implementation-guide.md)`

## Output
- Event-driven architecture pattern
- Sync gateway for bi-directional sync
- Multi-tenant architecture
- CQRS with event sourcing
- Microservices integration

## Error Handling
| Issue | Solution |
|-------|----------|
| 401 Unauthorized | Verify API key in environment variables |
| 429 Rate Limited | Implement exponential backoff, reduce request frequency |
| 500 Server Error | Retry with backoff, check MaintainX status page |

## Resources
- [MaintainX API Documentation](https://maintainx.dev/)
- [Martin Fowler - Patterns](https://martinfowler.com/)
- [Microsoft - Cloud Design Patterns](https://docs.microsoft.com/en-us/azure/architecture/patterns/)

## Next Steps
For multi-environment setup, see `maintainx-multi-env-setup`.
