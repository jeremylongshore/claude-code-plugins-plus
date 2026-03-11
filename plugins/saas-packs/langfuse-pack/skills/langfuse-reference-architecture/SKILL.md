---
name: langfuse-reference-architecture
description: |
  Production-grade Langfuse architecture patterns and best practices.
  Use when designing LLM observability infrastructure, planning Langfuse deployment,
  or implementing enterprise-grade tracing architecture.
  Trigger with phrases like "langfuse architecture", "langfuse design",
  "langfuse infrastructure", "langfuse enterprise", "langfuse at scale".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Langfuse Reference Architecture

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Production-grade architecture patterns for Langfuse LLM observability at scale, covering singleton SDK, context propagation, queue-based ingestion, and multi-environment configs.

## Prerequisites
- Understanding of distributed systems
- Knowledge of cloud infrastructure
- Familiarity with observability patterns

## Instructions

### Step 1: Implement Singleton SDK Pattern
Create a singleton Langfuse client with graceful shutdown handlers for SIGTERM/SIGINT.

### Step 2: Add Trace Context Propagation
Use `AsyncLocalStorage` to propagate trace context across async operations. Add Express middleware to auto-create traces.

### Step 3: Implement Queue-Based Ingestion
For high-volume (10M+ traces/day), buffer events through SQS/Kafka with async worker consumers.

### Step 4: Configure Multi-Environment Settings
Set environment-specific flush intervals, batch sizes, and sampling rates (dev: 100%, staging: 50%, prod: 10%).

### Step 5: Implement Service Mesh Tracing
Inject/extract trace headers (`x-langfuse-trace-id`) for cross-service trace correlation.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Singleton SDK pattern with graceful shutdown
- Trace context propagation via AsyncLocalStorage
- Queue-based async ingestion for high volume
- Multi-environment configuration
- Service mesh header injection

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Multiple instances | No singleton | Use singleton pattern |
| Lost traces | No shutdown handler | Register SIGTERM handler |
| Cross-service gaps | No propagation | Implement header injection |
| Scale issues | Direct ingestion | Add message queue buffer |

## Examples

### Architecture Decision Matrix
| Pattern | Use Case | Complexity | Scale |
|---------|----------|------------|-------|
| Basic Cloud | Small apps | Low | 100K traces/day |
| Self-Hosted | Data privacy | Medium | 1M traces/day |
| Queue-Based | High volume | High | 10M+ traces/day |

## Resources
- [Langfuse Self-Hosting](https://langfuse.com/docs/deployment/self-host)
- [Langfuse Architecture](https://langfuse.com/docs)
- [OpenTelemetry Context](https://opentelemetry.io/docs/concepts/context-propagation/)