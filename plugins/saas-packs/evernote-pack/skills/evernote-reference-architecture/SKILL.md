---
name: evernote-reference-architecture
description: |
  Reference architecture for Evernote integrations.
  Use when designing system architecture, planning integrations,
  or building scalable Evernote applications.
  Trigger with phrases like "evernote architecture", "design evernote system",
  "evernote integration pattern", "evernote scale".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Evernote Reference Architecture

## Overview
Production-ready architecture patterns for building scalable, maintainable Evernote integrations.

## Prerequisites
- Understanding of microservices architecture
- Cloud platform familiarity (AWS, GCP, or Azure)
- Knowledge of message queues and caching

## Instructions

1. See implementation guide for detailed steps.

2. For full implementation details and code examples, load:
3. `references/implementation-guide.md`

## Output
- Complete architecture patterns
- Component implementation examples
- Database schema design
- Infrastructure configuration
- Scaling guidelines

## Resources
- [AWS Well-Architected](https://aws.amazon.com/architecture/well-architected/)
- [Twelve-Factor App](https://12factor.net/)
- [Evernote API Reference](https://dev.evernote.com/doc/reference/)

## Next Steps
For multi-environment setup, see `evernote-multi-env-setup`.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with design |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply evernote reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize evernote reference architecture for production environments with multiple constraints and team-specific requirements.