---
name: speak-performance-tuning
description: |
  Optimize Speak API performance with caching, audio preprocessing, and connection pooling.
  Use when experiencing slow API responses, implementing caching strategies,
  or optimizing request throughput for language learning applications.
  Trigger with phrases like "speak performance", "optimize speak",
  "speak latency", "speak caching", "speak slow", "speak audio optimization".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak Performance Tuning

## Overview
Optimize Speak API performance with caching, audio preprocessing, and connection pooling for language learning applications.

## Prerequisites
- Speak SDK installed
- Understanding of async patterns
- Redis or in-memory cache available (optional)
- Performance monitoring in place

## Instructions
1. **Latency Benchmarks**
2. **Audio Optimization**
3. **Caching Strategy**
4. **Connection Optimization**
5. **Request Batching**
6. **Performance Monitoring**

For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output
- Reduced API latency
- Audio preprocessing pipeline
- Caching layer implemented
- Request batching enabled
- Connection pooling configured

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Cache miss storm | TTL expired | Use stale-while-revalidate |
| Audio too large | No compression | Optimize audio format |
| Connection exhausted | No pooling | Configure max sockets |
| Memory pressure | Cache too large | Set max cache entries |
| Batch timeout | Too many items | Reduce batch size |

## Examples
### Quick Performance Wrapper
```typescript
const withPerformance = <T>(name: string, fn: () => Promise<T>) =>
  measuredSpeakCall(name, () =>
    cachedWithRedis(`cache:${name}`, fn, 300)  # 300: timeout: 5 minutes
  );
```

## Resources
- [Speak Performance Guide](https://developer.speak.com/docs/performance)
- [Web Audio API](https://developer.mozilla.org/en-US/docs/Web/API/Web_Audio_API)
- [DataLoader Documentation](https://github.com/graphql/dataloader)
- [LRU Cache Documentation](https://github.com/isaacs/node-lru-cache)

## Next Steps
For cost optimization, see `speak-cost-tuning`.