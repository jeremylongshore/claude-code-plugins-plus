---
name: openevidence-performance-tuning
description: |
  Optimize OpenEvidence clinical query performance and response times.
  Use when improving latency, optimizing query efficiency,
  or tuning caching for clinical AI applications.
  Trigger with phrases like "openevidence performance", "openevidence slow",
  "optimize openevidence", "openevidence latency", "speed up clinical queries".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# OpenEvidence Performance Tuning

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize OpenEvidence clinical query performance for point-of-care response times. Covers query optimization, intelligent caching with TTL management, connection pooling, request batching, and performance monitoring.

## Prerequisites
- OpenEvidence integration running
- Monitoring configured (see `openevidence-observability`)
- Redis for caching
- Access to performance metrics

## Performance Targets

| Metric | Target | Critical |
|--------|--------|----------|
| Clinical Query P50 | < 3s | > 10s |
| Clinical Query P95 | < 8s | > 15s |
| Cache Hit Rate | > 70% | < 50% |
| DeepConsult Start | < 5s | > 15s |

## Instructions

### Step 1: Optimize Query Construction
Remove filler words from questions, limit context to top 5 conditions and 10 medications, set `maxCitations: 5` for faster responses.

### Step 2: Implement Intelligent Caching
Build `ClinicalQueryCache` with SHA-256 key generation. Use dynamic TTL: 5min for stat/urgent, 24hr for pharmacokinetics/mechanisms, 1hr for guidelines, default for others.

### Step 3: Enable Connection Pooling
Configure HTTPS agent with `keepAlive: true`, 10 max sockets, 5 max free sockets. Pre-warm connections on startup.

### Step 4: Set Up Request Batching
Use DataLoader to batch concurrent queries (max 5 per batch, 50ms scheduling window) within rate limits.

### Step 5: Add Performance Monitoring
Instrument queries with Prometheus histograms for latency by specialty/urgency/cached, plus cache hit/miss counters.

## Output
- Optimized query construction
- Intelligent caching with dynamic TTL management
- Connection pooling with keep-alive
- Request batching via DataLoader
- Performance metrics and monitoring

## Error Handling
| Performance Issue | Detection | Resolution |
|-------------------|-----------|------------|
| High P95 latency | Metrics alert | Check cache hit rate, optimize queries |
| Low cache hit rate | < 50% hits | Review TTL strategy, check key normalization |
| Connection timeouts | Timeout errors | Check keep-alive config, increase pool size |
| Memory pressure | Redis alerts | Implement LRU eviction, reduce TTLs |

## Examples

### Cache TTL Strategy
```
Stat/urgent queries:      5 minutes
Pharmacokinetics/mechanisms: 24 hours
Treatment guidelines:     1 hour
Default clinical queries: configurable (default 1hr)
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Redis Caching Best Practices](https://redis.io/docs/manual/client-side-caching/)
- [DataLoader Documentation](https://github.com/graphql/dataloader)
