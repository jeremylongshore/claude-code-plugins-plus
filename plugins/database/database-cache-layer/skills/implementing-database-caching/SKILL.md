---
name: implementing-database-caching
description: |
  Process use when you need to implement multi-tier caching to improve database performance.
  This skill sets up Redis, in-memory caching, and CDN layers to reduce database load.
  Trigger with phrases like "implement database caching", "add Redis cache layer",
  "improve query performance with caching", or "reduce database load".

allowed-tools: Read, Write, Edit, Grep, Glob, Bash(redis-cli:*), Bash(docker:redis:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---
# Database Cache Layer

## Overview

Implement multi-tier caching strategies using Redis, application-level in-memory caches, and query result caching to reduce database load and improve read latency. This skill covers cache-aside, write-through, and write-behind patterns with proper invalidation strategies, TTL configuration, and cache stampede prevention.

## Prerequisites

- Redis server (6.x+) available or Docker for running `docker run redis:7-alpine`
- `redis-cli` installed for cache inspection and debugging
- Application framework with Redis client library (ioredis, redis-py, Jedis, go-redis)
- Database query profiling data identifying read-heavy and slow queries
- Understanding of data freshness requirements (how stale can cached data be)
- Monitoring tools for cache hit rate and Redis memory usage

## Instructions

1. Profile database queries to identify caching candidates. Focus on queries that: execute more than 100 times per minute, take longer than 50ms, return data that changes less frequently than every 5 minutes, and produce results smaller than 1MB. Use `pg_stat_statements` or MySQL slow query log.

2. Design the cache key schema with a consistent naming convention: `{service}:{entity}:{id}:{variant}`. Examples: `app:user:12345:profile`, `app:products:category:electronics:page:1`. Include a version prefix to enable bulk invalidation: `v2:app:user:12345`.

3. Implement the cache-aside pattern for read-heavy data:
   - Check Redis first: `GET app:user:12345:profile`
   - On cache miss: query database, then `SET app:user:12345:profile <json> EX 3600`
   - On data update: `DEL app:user:12345:profile` to invalidate
   - Wrap in a helper function that abstracts cache-then-database logic

4. Configure TTL values based on data change frequency:
   - Static reference data (countries, categories): TTL 24 hours or longer
   - User profile data: TTL 15-60 minutes
   - Product listings: TTL 5-15 minutes
   - Session data: TTL matching session timeout
   - Real-time data (inventory counts, prices): TTL 30-60 seconds or skip caching

5. Implement cache stampede prevention for high-traffic cache keys:
   - **Probabilistic early expiration**: Refresh cache at `TTL * 0.8` with probability `1 / concurrent_requests`
   - **Distributed lock**: Use `SET key:lock NX EX 5` to let one request refresh while others serve stale data
   - **Stale-while-revalidate**: Serve expired cache while refreshing in background

6. Add application-level L1 cache using an in-memory LRU cache (Node.js: `lru-cache`, Python: `cachetools`, Java: Caffeine) for per-process caching of ultra-hot data. Set L1 TTL shorter than Redis TTL (e.g., 60 seconds L1, 5 minutes Redis).

7. Configure Redis for production:
   - Set `maxmemory` to 75% of available RAM
   - Set `maxmemory-policy allkeys-lru` for cache workloads
   - Enable `save ""` (disable RDB persistence) for pure cache use
   - Configure `tcp-keepalive 60` and `timeout 300`

8. Implement cache invalidation on data mutations. After INSERT, UPDATE, or DELETE operations, delete the corresponding cache key and any aggregate/list cache keys that include the modified data. Use Redis key patterns or tag-based invalidation for related keys.

9. Add cache metrics instrumentation: track cache hit rate (`hits / (hits + misses)`), cache miss latency (time to populate from DB), Redis memory usage, eviction rate, and average key TTL remaining. Alert when hit rate drops below 80%.

10. Test cache behavior under load: verify cache hit rate reaches 90%+ for targeted queries, confirm cache invalidation works correctly on updates, and measure end-to-end latency improvement compared to direct database queries.

## Output

- **Redis configuration file** with memory limits, eviction policy, and persistence settings
- **Cache wrapper module** with get/set/invalidate functions and stampede prevention
- **Cache key schema documentation** with naming conventions and TTL values per data type
- **Invalidation logic** integrated with data access layer for automatic cache clearing on mutations
- **Monitoring dashboard queries** for cache hit rate, memory usage, and eviction tracking

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| Redis connection refused | Redis server down or network issue | Implement circuit breaker pattern; fall through to database on cache unavailability; retry with exponential backoff |
| Cache stampede on popular key expiration | Many concurrent requests hit cache miss simultaneously | Use distributed locking or probabilistic early refresh; extend TTL with jitter (`TTL + random(0, TTL*0.1)`) |
| Stale data served after database update | Cache invalidation missed or delayed | Audit invalidation paths; use publish/subscribe for cache invalidation events; reduce TTL for sensitive data |
| Redis out of memory (OOM) | Cache size exceeds `maxmemory` setting | Enable `allkeys-lru` eviction; reduce TTLs; audit large keys with `redis-cli --bigkeys`; increase maxmemory |
| Cache key collision | Different data stored under the same key pattern | Include all discriminating parameters in the cache key; add content hash to key for variant detection |

## Examples

**Caching product catalog for an e-commerce site**: Product detail pages query 3 tables (products, categories, reviews_summary). Cache the assembled product JSON in Redis with TTL of 10 minutes. Cache hit rate reaches 95% since products change rarely. Category pages use list cache keys `app:products:category:electronics:sort:price:page:1` with 5-minute TTL. On product update, invalidate both the product key and all category list keys containing that product.

**User session caching with Redis**: Store session data as Redis hashes (`HSET session:abc123 userId 456 role admin lastAccess 1705341234`). Set TTL to 30 minutes with sliding expiration on each access (`EXPIRE session:abc123 1800`). Session reads drop from 2ms (PostgreSQL) to 0.1ms (Redis), eliminating 50,000 database queries per minute.

**API response caching with stale-while-revalidate**: Dashboard endpoint takes 3 seconds to compute. Cache the response with 5-minute TTL. When TTL expires, the first request triggers an async background refresh while serving the stale cached response. Subsequent requests within the refresh window also receive the stale response. Dashboard always loads in under 5ms from the client perspective.

## Resources

- Redis documentation: https://redis.io/docs/
- Redis caching patterns: https://redis.io/docs/manual/patterns/
- Cache-aside pattern: https://docs.microsoft.com/en-us/azure/architecture/patterns/cache-aside
- ioredis (Node.js client): https://github.com/redis/ioredis
- redis-py (Python client): https://redis-py.readthedocs.io/