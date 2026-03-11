---
name: apollo-reference-architecture
description: |
  Implement Apollo.io reference architecture.
  Use when designing Apollo integrations, establishing patterns,
  or building production-grade sales intelligence systems.
  Trigger with phrases like "apollo architecture", "apollo system design",
  "apollo integration patterns", "apollo best practices architecture".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Apollo Reference Architecture

## Overview
Production-ready reference architecture for Apollo.io integrations covering system design, data flows, and integration patterns.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions
Follow these high-level steps to implement apollo-reference-architecture:

1. Review the prerequisites and ensure your environment is configured
2. Follow the detailed implementation guide for step-by-step code examples
3. Validate your implementation against the output checklist below

For full implementation details, load: `Read(plugins/saas-packs/apollo-pack/skills/apollo-reference-architecture/references/implementation-guide.md)`

## Output
- Layered architecture (client, service, job, model)
- Background job processing with Bull
- Database models with TypeORM
- RESTful API endpoints
- CRM integration patterns
- Event-driven architecture

## Error Handling
| Layer | Strategy |
|-------|----------|
| Client | Retry with backoff |
| Service | Graceful degradation |
| Jobs | Dead letter queue |
| API | Structured error responses |

## Resources
- [NestJS Documentation](https://docs.nestjs.com/)
- [Bull Queue](https://github.com/OptimalBits/bull)
- [TypeORM](https://typeorm.io/)
- [Event Sourcing Patterns](https://martinfowler.com/eaaDev/EventSourcing.html)

## Next Steps
Proceed to `apollo-multi-env-setup` for environment configuration.

## Examples

**Basic usage**: Apply apollo reference architecture to a standard project setup with default configuration options.

**Advanced scenario**: Customize apollo reference architecture for production environments with multiple constraints and team-specific requirements.