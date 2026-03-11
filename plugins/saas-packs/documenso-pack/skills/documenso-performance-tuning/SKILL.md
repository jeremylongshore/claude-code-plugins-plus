---
name: documenso-performance-tuning
description: |
  Optimize Documenso integration performance with caching, batching, and efficient patterns.
  Use when improving response times, reducing API calls,
  or optimizing bulk document operations.
  Trigger with phrases like "documenso performance", "optimize documenso",
  "documenso caching", "documenso batch operations".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Documenso Performance Tuning

## Overview
Optimize Documenso integrations for speed, efficiency, and scalability.

## Prerequisites
- Working Documenso integration
- Performance monitoring in place
- Redis or caching layer (recommended)

## Instructions

### Step 1: Caching Strategies
import Redis from "ioredis";
### Step 2: Batch Operations
import PQueue from "p-queue";
### Step 3: Connection Pooling
import { Documenso } from "@documenso/sdk-typescript";
### Step 4: Response Size Optimization
// Efficient pagination
### Step 5: Async Processing
import Bull from "bull";
### Step 6: Performance Monitoring
class PerformanceMonitor {
### Step 7: Performance Checklist
Implement performance checklist.

For detailed implementation code and configurations, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Caching Strategies
- Batch Operations
- Connection Pooling
- Response Size Optimization
- Async Processing
- Performance Monitoring

## Error Handling
| Performance Issue | Cause | Solution |
|------------------|-------|----------|
| Slow responses | No caching | Add caching layer |
| Rate limits | Too many requests | Use queue/batching |
| Memory issues | Large responses | Use pagination |
| Timeout errors | Slow processing | Use background jobs |

## Resources
- [Redis Caching](https://redis.io/docs/manual/patterns/)
- [Bull Queue](https://github.com/OptimalBits/bull)
- [p-queue](https://github.com/sindresorhus/p-queue)

## Next Steps
For cost optimization, see `documenso-cost-tuning`.
