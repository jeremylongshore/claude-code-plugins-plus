---
name: linear-reference-architecture
description: |
  Production-grade Linear integration architecture patterns.
  Use when designing system architecture, planning integrations,
  or reviewing architectural decisions.
  Trigger with phrases like "linear architecture", "linear system design",
  "linear integration patterns", "linear best practices architecture".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Linear Reference Architecture

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Production-grade architectural patterns for Linear integrations. Covers simple, service-oriented, event-driven, and CQRS architectures.

## Prerequisites
- Understanding of distributed systems
- Experience with cloud infrastructure
- Familiarity with event-driven architecture

## Instructions

### Step 1: Choose Architecture Pattern
| Pattern | Best For | Complexity |
|---------|----------|------------|
| Simple Integration | Small teams, single app | Low |
| Service-Oriented | Medium teams, multiple apps | Medium |
| Event-Driven | Large teams, real-time needs | High |
| CQRS + Event Sourcing | Complex domains, audit needs | Very High |

### Step 2: Implement Core Components
1. **Linear Gateway** - Centralized API access with rate limiting and caching
2. **Webhook Ingester** - Receive and validate Linear webhook events
3. **Event Processor** - Apply business logic to incoming events
4. **State Store** - Persist synchronized data locally

### Step 3: Configure Infrastructure
- Set up caching layer (Redis for multi-service, in-memory for simple)
- Configure rate limiting (stay under 1500 req/min Linear limit)
- Deploy webhook endpoint with signature verification
- Set up monitoring and health checks

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for full code examples of all four architecture patterns plus project structure.

## Output
- Architecture pattern selected and justified
- Core infrastructure components configured
- Rate limiting and caching in place
- Webhook handling operational

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Rate limit exceeded | Too many API calls | Implement gateway with rate limiter |
| Stale cache | TTL too long | Invalidate on webhook events |
| Event loss | Webhook failures | Use message queue with retries |
| Schema drift | API version changes | Pin SDK version, test upgrades |

## Examples

### Quick Start: Simple Integration
```typescript
import { LinearClient } from "@linear/sdk";

const client = new LinearClient({ apiKey: process.env.LINEAR_API_KEY! });
const teams = await client.teams();
console.log(teams.nodes.map(t => t.name));
```

## Resources
- [Linear API Best Practices](https://developers.linear.app/docs/graphql/best-practices)
- [Event-Driven Architecture](https://martinfowler.com/articles/201701-event-driven.html)
- [CQRS Pattern](https://martinfowler.com/bliki/CQRS.html)

## Next Steps
Configure multi-environment setup with `linear-multi-env-setup`.
