---
name: implementing-database-caching
description: |
  Use when you need to implement multi-tier caching to improve database performance.
  This skill sets up Redis, in-memory caching, and CDN layers to reduce database load.
  Trigger with phrases like "implement database caching", "add Redis cache layer",
  "improve query performance with caching", or "reduce database load".
  
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(redis-cli:*), Bash(docker:redis:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---
# Database Cache Layer

This skill provides automated assistance for database cache layer tasks.

## Prerequisites

Before using this skill, ensure:
- Redis server available or ability to deploy Redis container
- Understanding of application data access patterns and hotspots
- Knowledge of which queries/data benefit most from caching
- Monitoring tools to measure cache hit rates and performance
- Development environment for testing caching implementation
- Understanding of cache invalidation requirements for data consistency

## Instructions

### Step 1: Analyze Caching Requirements
1. Profile database queries to identify slow or frequently executed queries
2. Determine which data is read-heavy vs write-heavy
3. Identify data that can tolerate eventual consistency
4. Calculate expected cache size and Redis memory requirements
5. Document current database load and target performance metrics

### Step 2: Choose Caching Strategy
1. **Cache-Aside (Lazy Loading)**: Application checks cache first, loads from DB on miss
   - Best for: Read-heavy workloads, unpredictable access patterns
   - Pros: Only caches requested data, simple to implement
   - Cons: Cache misses incur database hit, stale data possible
2. **Write-Through**: Application writes to cache and database simultaneously
   - Best for: Write-heavy workloads needing consistency
   - Pros: Cache always consistent, no stale data
   - Cons: Write latency, unnecessary caching of rarely-read data
3. **Write-Behind (Write-Back)**: Application writes to cache, async writes to database
   - Best for: High write throughput requirements
   - Pros: Low write latency, batched database writes
   - Cons: Risk of data loss, complexity in implementation

### Step 3: Design Cache Architecture
1. Set up Redis as distributed cache layer (L2 cache)
2. Implement in-memory LRU cache in application (L1 cache)
3. Configure CDN for static assets (images, CSS, JS)
4. Design cache key naming convention (e.g., `user:123:profile`)
5. Define TTL (Time To Live) for different data types

### Step 4: Implement Caching Code
1. Add Redis client library to application dependencies
2. Create cache wrapper functions (get, set, delete, invalidate)
3. Modify database query code to check cache before DB query
4. Implement cache population on cache miss
5. Add error handling for cache failures (fail gracefully to database)

### Step 5: Configure Cache Invalidation
1. Implement TTL-based expiration for time-sensitive data
2. Add explicit cache invalidation on data updates/deletes
3. Use cache tags or patterns for bulk invalidation
4. Implement cache warming for critical data after deployments
5. Set up cache stampede prevention (lock/queue on miss)

### Step 6: Monitor and Optimize
1. Track cache hit rate, miss rate, and eviction rate
2. Monitor Redis memory usage and eviction policy
3. Analyze query performance improvements
4. Adjust TTLs based on data update frequency
5. Identify and cache additional hot data

## Output

This skill produces:

**Redis Configuration**: Docker Compose or config files for Redis deployment with appropriate memory and eviction settings

**Caching Code**: Application code implementing cache-aside, write-through, or write-behind patterns

**Cache Key Schema**: Documentation of cache key naming conventions and TTL settings

**Monitoring Dashboards**: Metrics for cache hit rates, memory usage, and performance improvements

**Cache Invalidation Logic**: Code for explicit and implicit cache invalidation on data changes

## Error Handling

**Cache Connection Failures**:
- Implement circuit breaker pattern to prevent cascading failures
- Fall back to database when cache is unavailable
- Log cache connection errors for monitoring
- Retry cache connections with exponential backoff
- Consider read-replica or cache cluster for high availability

**Cache Stampede**:
- Implement probabilistic early expiration (PER) for TTLs
- Use distributed locks (Redis SETNX) to prevent concurrent cache population
- Queue cache refresh requests instead of parallel execution
- Add jitter to TTLs to spread expiration times
- Use stale-while-revalidate pattern for acceptable delays

**Stale Data Issues**:
- Implement versioning in cache keys (e.g., `user:123:v2`)
- Use cache tags for related data invalidation
- Set aggressive TTLs for frequently changing data
- Implement active cache invalidation on data updates
- Monitor data consistency between cache and database

**Memory Pressure**:
- Configure Redis eviction policy (allkeys-lru recommended)
- Monitor Redis memory usage and set max memory limits
- Implement tiered caching (hot data in Redis, warm data in DB)
- Reduce TTLs for less critical data
- Scale Redis horizontally with cluster mode

## Resources

**Redis Configuration Templates**:
- Docker Compose: `{baseDir}/docker/redis-compose.yml`
- Redis config: `{baseDir}/config/redis.conf`
- Cluster config: `{baseDir}/config/redis-cluster.conf`

**Caching Code Examples**: `{baseDir}/examples/caching/`
- Cache-aside pattern (Node.js, Python, Java)
- Write-through pattern
- Cache invalidation strategies
- Distributed locking

**Cache Key Design Guide**: `{baseDir}/docs/cache-key-design.md`
**Performance Tuning**: `{baseDir}/docs/cache-performance-tuning.md`
**Monitoring Setup**: `{baseDir}/monitoring/redis-dashboard.json`

## Overview

This skill provides automated assistance for the described functionality.

## Examples

Example usage patterns will be demonstrated in context.