---
name: clerk-reference-architecture
description: |
  Reference architecture patterns for Clerk authentication.
  Use when designing application architecture, planning auth flows,
  or implementing enterprise-grade authentication.
  Trigger with phrases like "clerk architecture", "clerk design",
  "clerk system design", "clerk integration patterns".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clerk Reference Architecture

## Overview
Reference architectures for implementing Clerk in various application types.

## Prerequisites
- Understanding of web application architecture
- Familiarity with authentication patterns
- Knowledge of your tech stack

## Instructions
1. Architecture 1: Next.js Full-Stack Application
2. Architecture 2: Microservices with Shared Auth
3. Architecture 3: Multi-Tenant SaaS
4. Architecture 4: Mobile + Web with Shared Backend

For full implementation details and code examples, load:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Architecture pattern selected
- Component diagram defined
- Implementation patterns ready
- Data flow documented

## Resources
- [Clerk Architecture Guide](https://clerk.com/docs/architecture)
- [Multi-tenant Patterns](https://clerk.com/docs/organizations/overview)
- [Backend Integration](https://clerk.com/docs/backend-requests/overview)

## Next Steps
Proceed to `clerk-multi-env-setup` for multi-environment configuration.

## Error Handling

| Error | Cause | Resolution |
|-------|-------|------------|
| Authentication failure | Invalid or expired credentials | Refresh tokens or re-authenticate with authentication |
| Configuration conflict | Incompatible settings detected | Review and resolve conflicting parameters |
| Resource not found | Referenced resource missing | Verify resource exists and permissions are correct |

## Examples

**Basic usage**: Apply clerk reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize clerk reference architecture for production environments with multiple constraints and team-specific requirements.