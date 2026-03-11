---
name: deepgram-reference-architecture
description: |
  Implement Deepgram reference architecture for scalable transcription systems.
  Use when designing transcription pipelines, building production architectures,
  or planning Deepgram integration at scale.
  Trigger with phrases like "deepgram architecture", "transcription pipeline",
  "deepgram system design", "deepgram at scale", "enterprise deepgram".
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Deepgram Reference Architecture

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Reference architectures for scalable transcription systems: synchronous API for short files, async queue (BullMQ) for batch processing, WebSocket streaming for real-time, and hybrid routing with enterprise multi-region deployment.

## Prerequisites
- Deepgram API access
- Redis for queue-based patterns
- WebSocket support for streaming
- Monitoring infrastructure

## Instructions

### Step 1: Choose Architecture Pattern
Select based on use case: Sync API for files under 60s, Async Queue for batch/long files, Streaming for real-time transcription, or Hybrid for mixed workloads.

### Step 2: Implement Synchronous Pattern
Direct API calls via Express endpoint. Store results in database. Best for low-latency, short audio requirements.

### Step 3: Implement Async Queue Pattern
Use BullMQ with Redis for job queuing. Configure workers with concurrency (10), retry (3 attempts, exponential backoff). Notify clients on completion.

### Step 4: Implement Streaming Pattern
Create WebSocket server that proxies audio between client and Deepgram Live API. Forward transcripts back to client in real-time with interim results.

### Step 5: Build Hybrid Router
Auto-select pattern based on audio duration: sync for <60s, async for >300s. Allow explicit mode override via request parameter.

### Step 6: Scale to Enterprise
Deploy multi-region with load balancing. Use Redis cluster for cross-region coordination. Configure per-region worker pools with 20 concurrency and 5 retries.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Output
- Synchronous transcription endpoint
- Queue-based async processing pipeline
- Real-time WebSocket streaming server
- Hybrid router with auto-selection
- Enterprise multi-region architecture
- Prometheus monitoring integration

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Timeout on large files | Sync pattern | Switch to async queue |
| WebSocket disconnect | Network issue | Auto-reconnect with backoff |
| Queue backlog | Worker overload | Scale workers, increase concurrency |
| Region failover | Regional outage | Route to healthy region |

## Examples

### Architecture Selection Guide
| Pattern | Best For | Latency | Throughput |
|---------|----------|---------|------------|
| Sync API | Short files (<60s) | Low | Low |
| Async Queue | Batch processing | Medium | High |
| Streaming | Live transcription | Real-time | Medium |
| Hybrid | Mixed workloads | Varies | High |

## Resources
- [Deepgram Architecture Guide](https://developers.deepgram.com/docs/architecture)
- [High Availability Patterns](https://developers.deepgram.com/docs/high-availability)
- [Scaling Best Practices](https://developers.deepgram.com/docs/scaling)
