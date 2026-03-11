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
- Architecture 1: Next.js Full-Stack Application
- Architecture 2: Microservices with Shared Auth
- Architecture 3: Multi-Tenant SaaS
- Architecture 4: Mobile + Web with Shared Backend

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
