# vercel-performance-tuning

## Skill Scaffold

```
vercel-performance-tuning/
  SKILL.md
```

## File Descriptions

### 1. SKILL.md
**Purpose:** Optimize Vercel API performance with caching, batching, connection pooling, and pagination strategies.
**Workflow:** Applied after basic integration works to optimize for production scale.
**Relates to:** Follows vercel-webhooks-events; complements vercel-cost-tuning for cost optimization

## Summary

This skill focuses on performance optimization for Vercel integrations. It covers latency benchmarks for different operations (cold start, builds), response caching with LRU-cache and Redis, request batching with DataLoader, connection pooling with keep-alive, async generator-based pagination for large datasets, and performance monitoring wrappers. The goal is to reduce API latency by 50% or more through these techniques.
