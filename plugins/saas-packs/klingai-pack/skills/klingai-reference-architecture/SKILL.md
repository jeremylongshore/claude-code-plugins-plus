---
name: klingai-reference-architecture
description: |
  Execute production-ready reference architecture for Kling AI video platforms. Use when designing
  scalable video generation systems. Trigger with phrases like 'klingai architecture',
  'kling ai system design', 'video platform architecture', 'klingai production setup'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Klingai Reference Architecture

## Overview

This skill provides production-ready reference architectures for building scalable video generation platforms using Kling AI, including microservices design, event-driven patterns, and infrastructure recommendations.

## Prerequisites

- Understanding of distributed systems
- Cloud infrastructure experience (AWS/GCP/Azure)
- Docker/Kubernetes knowledge helpful

## Instructions

Follow these steps to design your architecture:

1. **Choose Pattern**: Select appropriate architecture pattern
2. **Design Components**: Map out service boundaries
3. **Plan Infrastructure**: Choose cloud services
4. **Implement Resilience**: Add fault tolerance
5. **Monitor & Scale**: Set up observability

## Output

Successful execution produces:
- Scalable video generation platform
- Event-driven processing pipeline
- Container-ready deployment configs
- Auto-scaling based on queue depth

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI API](https://docs.klingai.com/api)
- [Kubernetes Documentation](https://kubernetes.io/docs/)
- [Redis Queues](https://redis.io/docs/data-types/lists/)
