---
name: gamma-performance-tuning
description: |
  Optimize Gamma API performance and reduce latency.
  Use when experiencing slow response times, optimizing throughput,
  or improving user experience with Gamma integrations.
  Trigger with phrases like "gamma performance", "gamma slow",
  "gamma latency", "gamma optimization", "gamma speed".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Gamma Performance Tuning

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize Gamma API integration performance through client configuration, caching, connection pooling, and parallel request patterns.

## Prerequisites
- Working Gamma integration
- Performance monitoring tools
- Understanding of caching concepts

## Instructions

### Step 1: Optimize Client Configuration
Enable keep-alive, compression, and configure max sockets (10). Set retry conditions for 5xx and 429 errors.

### Step 2: Implement Response Caching
Use `node-cache` with 5-minute TTL. Invalidate on `presentation.updated` events.

### Step 3: Parallelize Requests
Replace sequential loops with `p-limit` (concurrency 5) for bulk operations. Use batch API where available.

### Step 4: Add Pagination with Generators
Use async generators for memory-efficient iteration over large presentation lists.

### Step 5: Optimize Request Payloads
Request only needed fields to reduce response size. Use `returnImmediately` for creation operations.

### Step 6: Configure Connection Pooling
Create shared HTTP/HTTPS agents with keep-alive, 25 max sockets, and 60s timeout.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Optimized client configuration
- Response caching layer
- Parallel request patterns
- Connection pooling setup
- Performance monitoring

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| High latency | No connection reuse | Enable keep-alive and pooling |
| Memory growth | Unbounded cache | Set TTL and max cache size |
| Rate limiting | Too many parallel requests | Use `p-limit` with concurrency cap |

## Examples

### Performance Targets
| Operation | Target | Action if Exceeded |
|-----------|--------|-------------------|
| Simple GET | < 200ms | Check network, use caching |
| List (100 items) | < 500ms | Reduce page size |
| Create presentation | < 5s | Use async pattern |
| Export PDF | < 30s | Use webhook notification |

## Resources
- [Gamma Performance Guide](https://gamma.app/docs/performance)
- [Node.js Performance](https://nodejs.org/en/docs/guides/dont-block-the-event-loop)
