---
description: Implement multi-tier database caching with Redis, in-memory, and CDN layers for 10-100x performance improvement
shortcut: caching
---

# Database Cache Layer

Implement production-grade multi-tier caching architecture for databases using Redis (distributed cache), in-memory caching (L1), and CDN (static assets) to reduce database load by 80-95%, improve query latency from 50ms to 1-5ms, and support horizontal scaling with cache-aside, write-through, and read-through patterns.

## When to Use This Command

Use `/caching` when you need to:
- Reduce database load by caching frequently accessed data (80% hit rate)
- Improve query response times from 50-100ms to 1-5ms
- Handle traffic spikes without database scaling (cache absorbs load)
- Support read-heavy workloads with minimal database reads
- Implement distributed caching across multiple application servers
- Enable horizontal scaling with stateless application servers

DON'T use this when:
- Data changes frequently and cache hit rate would be <50%
- Application has strict real-time data requirements (< 1s staleness)
- Database is already fast enough (<10ms query latency)
- You lack cache invalidation strategy (stale data risk)
- Small dataset fits entirely in database memory (shared_buffers)
- Write-heavy workload (caching provides minimal benefit)

## Design Decisions

This command implements **multi-tier caching with intelligent invalidation** because:
- L1 in-memory cache (1-5ms) for hot data per server
- L2 distributed Redis cache (5-10ms) shared across servers
- Cache-aside pattern provides fallback to database on miss
- TTL-based and event-based invalidation prevents stale data
- Write-through caching maintains consistency for critical data

**Alternative considered: Read-through caching**
- Simpler implementation (cache handles database queries)
- Less control over cache population strategy
- Not suitable when database schema differs from cached format
- Recommended for simple key-value lookups

**Alternative considered: Database query result caching (pg_stat_statements)**
- Built into PostgreSQL (no external dependencies)
- Limited to identical queries (parameter changes = cache miss)
- Cannot cache across multiple queries
- Recommended for development/small workloads only

## Prerequisites

Before running this command:
1. Redis server deployed (standalone, Sentinel, or Cluster)
2. Understanding of cache invalidation needs (TTL vs event-driven)
3. Monitoring for cache hit rate and memory usage
4. Connection pooling configured for Redis clients
5. Fallback strategy for cache failures (graceful degradation)

## Implementation Process

### Step 1: Design Cache Key Strategy
Define hierarchical cache keys for easy invalidation (e.g., `user:123:profile`).

### Step 2: Implement Cache-Aside Pattern
Check cache first, query database on miss, populate cache with result.

### Step 3: Configure TTL and Eviction
Set appropriate TTL based on data freshness requirements and memory limits.

### Step 4: Implement Invalidation Logic
Invalidate cache on data updates using event listeners or explicit invalidation.

### Step 5: Monitor Cache Performance
Track hit rate, miss rate, latency, and memory usage with Prometheus/Grafana.

## Output Format

The command generates:
- `caching/redis_client.py` - Redis connection pool and wrapper
- `caching/cache_decorator.py` - Python decorator for automatic caching
- `caching/cache_invalidation.js` - Event-driven invalidation logic
- `caching/cache_monitoring.yml` - Prometheus metrics and alerts
- `caching/cache_warming.sql` - SQL queries for cache preloading

## Code Examples

### Example 1: Python Multi-Tier Cache with Redis and In-Memory

```python
#!/usr/bin/env python3
"""
Production-ready multi-tier caching system with L1 (in-memory) and
L2 (Redis) caches, automatic invalidation, and performance monitoring.
"""

import redis
import pickle
from typing import Optional, Callable, Any
from functools import wraps
from datetime import timedelta
import time
import logging
from cachetools import TTLCache
import hashlib
import json

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MultiTierCache:
    """
    Two-tier caching system with L1 (in-memory) and L2 (Redis).

    L1: Fast in-memory cache (1-5ms) for hot data
    L2: Distributed Redis cache (5-10ms) shared across servers
    """

    def __init__(
        self,
        redis_url: str = "redis://localhost:6379/0",
        l1_max_size: int = 1000,
        l1_ttl_seconds: int = 60,
        l2_ttl_seconds: int = 3600,
        enabled: bool = True
    ):
        """
        Initialize multi-tier cache.

        Args:
            redis_url: Redis connection URL
            l1_max_size: Max entries in L1 cache
            l1_ttl_seconds: L1 cache TTL (default: 1 minute)
            l2_ttl_seconds: L2 cache TTL (default: 1 hour)
            enabled: Enable/disable caching (useful for debugging)
        """
        self.enabled = enabled

        if not enabled:
            logger.warning("Caching is disabled")
            return

        # L1: In-memory cache (per server)
        self.l1_cache = TTLCache(maxsize=l1_max_size, ttl=l1_ttl_seconds)
        self.l1_ttl = l1_ttl_seconds

        # L2: Redis cache (distributed)
        self.redis_client = redis.from_url(
            redis_url,
            decode_responses=False,  # Store binary data
            socket_connect_timeout=5,
            socket_timeout=5,
            retry_on_timeout=True
        )
        self.l2_ttl = l2_ttl_seconds

        # Metrics
        self.metrics = {
            'l1_hits': 0,
            'l1_misses': 0,
            'l2_hits': 0,
            'l2_misses': 0,
            'db_queries': 0,
            'errors': 0
        }

    def _generate_key(self, prefix: str, *args, **kwargs) -> str:
        """
        Generate cache key from function arguments.

        Args:
            prefix: Cache key prefix (e.g., 'user:profile')
            args: Positional arguments
            kwargs: Keyword arguments

        Returns:
            Cache key string
        """
        # Create deterministic key from arguments
        key_parts = [str(arg) for arg in args]
        key_parts.extend(f"{k}={v}" for k, v in sorted(kwargs.items()))
        key_suffix = hashlib.md5(
            "|".join(key_parts).encode()
        ).hexdigest()[:8]

        return f"{prefix}:{key_suffix}"

    def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache (checks L1 then L2).

        Args:
            key: Cache key

        Returns:
            Cached value or None if not found
        """
        if not self.enabled:
            return None

        # Try L1 cache first
        if key in self.l1_cache:
            self.metrics['l1_hits'] += 1
            logger.debug(f"L1 cache hit: {key}")
            return self.l1_cache[key]

        self.metrics['l1_misses'] += 1

        # Try L2 cache (Redis)
        try:
            cached_data = self.redis_client.get(key)
            if cached_data:
                self.metrics['l2_hits'] += 1
                logger.debug(f"L2 cache hit: {key}")

                # Deserialize and populate L1 cache
                value = pickle.loads(cached_data)
                self.l1_cache[key] = value

                return value

            self.metrics['l2_misses'] += 1
            return None

        except redis.RedisError as e:
            logger.error(f"Redis error: {e}")
            self.metrics['errors'] += 1
            return None

    def set(
        self,
        key: str,
        value: Any,
        l1_ttl: Optional[int] = None,
        l2_ttl: Optional[int] = None
    ) -> bool:
        """
        Set value in both cache layers.

        Args:
            key: Cache key
            value: Value to cache
            l1_ttl: L1 TTL override (seconds)
            l2_ttl: L2 TTL override (seconds)

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            # Store in L1 cache
            self.l1_cache[key] = value

            # Store in L2 cache (Redis)
            serialized = pickle.dumps(value)
            ttl = l2_ttl or self.l2_ttl
            self.redis_client.setex(key, ttl, serialized)

            logger.debug(f"Cached: {key} (TTL: {ttl}s)")
            return True

        except redis.RedisError as e:
            logger.error(f"Failed to cache {key}: {e}")
            self.metrics['errors'] += 1
            return False

    def delete(self, key: str) -> bool:
        """
        Delete key from both cache layers.

        Args:
            key: Cache key to delete

        Returns:
            True if successful
        """
        if not self.enabled:
            return False

        try:
            # Delete from L1
            self.l1_cache.pop(key, None)

            # Delete from L2
            self.redis_client.delete(key)

            logger.info(f"Invalidated cache: {key}")
            return True

        except redis.RedisError as e:
            logger.error(f"Failed to delete {key}: {e}")
            self.metrics['errors'] += 1
            return False

    def delete_pattern(self, pattern: str) -> int:
        """
        Delete all keys matching pattern (L2 only).

        Args:
            pattern: Redis key pattern (e.g., 'user:123:*')

        Returns:
            Number of keys deleted
        """
        if not self.enabled:
            return 0

        try:
            # Scan and delete matching keys
            cursor = 0
            deleted_count = 0

            while True:
                cursor, keys = self.redis_client.scan(
                    cursor,
                    match=pattern,
                    count=100
                )

                if keys:
                    deleted_count += self.redis_client.delete(*keys)

                if cursor == 0:
                    break

            # Clear L1 cache (simpler than pattern matching)
            self.l1_cache.clear()

            logger.info(f"Invalidated {deleted_count} keys matching: {pattern}")
            return deleted_count

        except redis.RedisError as e:
            logger.error(f"Failed to delete pattern {pattern}: {e}")
            self.metrics['errors'] += 1
            return 0

    def get_metrics(self) -> dict:
        """
        Get cache performance metrics.

        Returns:
            Dictionary with hit rates and counts
        """
        total_l1 = self.metrics['l1_hits'] + self.metrics['l1_misses']
        total_l2 = self.metrics['l2_hits'] + self.metrics['l2_misses']

        l1_hit_rate = (
            self.metrics['l1_hits'] / total_l1 * 100
            if total_l1 > 0 else 0
        )

        l2_hit_rate = (
            self.metrics['l2_hits'] / total_l2 * 100
            if total_l2 > 0 else 0
        )

        overall_hit_rate = (
            (self.metrics['l1_hits'] + self.metrics['l2_hits']) /
            (total_l1 + total_l2) * 100
            if (total_l1 + total_l2) > 0 else 0
        )

        return {
            'l1_hits': self.metrics['l1_hits'],
            'l1_misses': self.metrics['l1_misses'],
            'l1_hit_rate': round(l1_hit_rate, 2),
            'l2_hits': self.metrics['l2_hits'],
            'l2_misses': self.metrics['l2_misses'],
            'l2_hit_rate': round(l2_hit_rate, 2),
            'overall_hit_rate': round(overall_hit_rate, 2),
            'db_queries': self.metrics['db_queries'],
            'errors': self.metrics['errors']
        }


# Global cache instance
cache = MultiTierCache()


def cached(
    prefix: str,
    l2_ttl: int = 3600,
    invalidate_on_update: bool = False
):
    """
    Decorator to automatically cache function results.

    Args:
        prefix: Cache key prefix
        l2_ttl: Redis cache TTL (seconds)
        invalidate_on_update: Auto-invalidate on data updates

    Usage:
        @cached('user:profile', l2_ttl=1800)
        def get_user_profile(user_id: int):
            return db.query(...).fetchone()
    """
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Generate cache key
            cache_key = cache._generate_key(prefix, *args, **kwargs)

            # Try to get from cache
            cached_result = cache.get(cache_key)
            if cached_result is not None:
                return cached_result

            # Cache miss - call function
            cache.metrics['db_queries'] += 1
            result = func(*args, **kwargs)

            # Cache result
            cache.set(cache_key, result, l2_ttl=l2_ttl)

            return result

        return wrapper
    return decorator


# Example usage with database queries
@cached('user:profile', l2_ttl=1800)
def get_user_profile(user_id: int):
    """
    Get user profile with automatic caching.

    First call: Database query (50ms)
    Subsequent calls: L1 cache (1ms) or L2 cache (5ms)
    """
    import psycopg2
    conn = psycopg2.connect("postgresql://...")
    with conn.cursor() as cur:
        cur.execute("SELECT * FROM users WHERE id = %s", (user_id,))
        return cur.fetchone()


@cached('user:orders', l2_ttl=600)
def get_user_orders(user_id: int, limit: int = 10):
    """Get user orders with caching."""
    import psycopg2
    conn = psycopg2.connect("postgresql://...")
    with conn.cursor() as cur:
        cur.execute(
            "SELECT * FROM orders WHERE user_id = %s ORDER BY created_at DESC LIMIT %s",
            (user_id, limit)
        )
        return cur.fetchall()


def invalidate_user_cache(user_id: int):
    """
    Invalidate all cached data for a user.

    Call this after updating user data:
    - User profile updates
    - User orders/transactions
    - User preferences
    """
    cache.delete_pattern(f"user:{user_id}:*")


# Example: Invalidate cache on database update
def update_user_profile(user_id: int, **updates):
    """Update user profile and invalidate cache."""
    import psycopg2
    conn = psycopg2.connect("postgresql://...")
    with conn.cursor() as cur:
        # Update database
        set_clause = ", ".join(f"{k} = %s" for k in updates.keys())
        cur.execute(
            f"UPDATE users SET {set_clause} WHERE id = %s",
            (*updates.values(), user_id)
        )
        conn.commit()

    # Invalidate cached data
    invalidate_user_cache(user_id)
    logger.info(f"Updated and invalidated cache for user {user_id}")


if __name__ == "__main__":
    # Test caching performance
    print("Testing cache performance...")

    # First call (cache miss - database query)
    start = time.time()
    profile1 = get_user_profile(123)
    db_time = (time.time() - start) * 1000
    print(f"Database query: {db_time:.2f}ms")

    # Second call (L1 cache hit)
    start = time.time()
    profile2 = get_user_profile(123)
    cache_time = (time.time() - start) * 1000
    print(f"L1 cache hit: {cache_time:.2f}ms")
    print(f"Speedup: {db_time / cache_time:.1f}x")

    # Print metrics
    print("\nCache metrics:")
    print(json.dumps(cache.get_metrics(), indent=2))
```

### Example 2: Cache Warming and Preloading

```python
#!/usr/bin/env python3
"""
Cache warming strategy to preload hot data before traffic hits.
Reduces cold start latency and improves cache hit rate.
"""

import psycopg2
from concurrent.futures import ThreadPoolExecutor, as_completed
import time
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class CacheWarmer:
    """
    Preload cache with frequently accessed data.
    """

    def __init__(self, cache: MultiTierCache, db_conn_string: str):
        """
        Initialize cache warmer.

        Args:
            cache: MultiTierCache instance
            db_conn_string: Database connection string
        """
        self.cache = cache
        self.db_conn_string = db_conn_string

    def warm_user_profiles(self, user_ids: list[int]) -> dict:
        """
        Preload user profiles for given IDs.

        Args:
            user_ids: List of user IDs to warm

        Returns:
            Statistics (count, duration, errors)
        """
        start_time = time.time()
        stats = {'loaded': 0, 'errors': 0}

        logger.info(f"Warming cache for {len(user_ids)} user profiles...")

        with psycopg2.connect(self.db_conn_string) as conn:
            with conn.cursor() as cur:
                for user_id in user_ids:
                    try:
                        # Query user profile
                        cur.execute(
                            "SELECT * FROM users WHERE id = %s",
                            (user_id,)
                        )
                        profile = cur.fetchone()

                        if profile:
                            # Cache profile
                            cache_key = f"user:profile:{user_id}"
                            self.cache.set(cache_key, profile, l2_ttl=1800)
                            stats['loaded'] += 1

                    except Exception as e:
                        logger.error(f"Error warming user {user_id}: {e}")
                        stats['errors'] += 1

        duration = time.time() - start_time
        stats['duration_seconds'] = duration

        logger.info(
            f"Cache warming complete: {stats['loaded']} profiles loaded "
            f"in {duration:.2f}s ({stats['errors']} errors)"
        )

        return stats

    def warm_top_products(self, limit: int = 100) -> dict:
        """
        Preload most popular products.

        Args:
            limit: Number of top products to warm

        Returns:
            Statistics
        """
        start_time = time.time()
        stats = {'loaded': 0, 'errors': 0}

        logger.info(f"Warming cache for top {limit} products...")

        with psycopg2.connect(self.db_conn_string) as conn:
            with conn.cursor() as cur:
                # Get top products by view count
                cur.execute("""
                    SELECT p.*
                    FROM products p
                    JOIN product_analytics a ON a.product_id = p.id
                    ORDER BY a.view_count DESC
                    LIMIT %s
                """, (limit,))

                products = cur.fetchall()

                for product in products:
                    try:
                        product_id = product[0]  # Assuming ID is first column
                        cache_key = f"product:detail:{product_id}"
                        self.cache.set(cache_key, product, l2_ttl=3600)
                        stats['loaded'] += 1

                    except Exception as e:
                        logger.error(f"Error warming product: {e}")
                        stats['errors'] += 1

        duration = time.time() - start_time
        stats['duration_seconds'] = duration

        logger.info(
            f"Product cache warming complete: {stats['loaded']} products loaded "
            f"in {duration:.2f}s"
        )

        return stats

    def warm_all_hot_data(self) -> dict:
        """
        Warm all hot data concurrently.

        Returns:
            Combined statistics
        """
        logger.info("Starting full cache warm...")

        # Identify hot data (most accessed in last 24 hours)
        with psycopg2.connect(self.db_conn_string) as conn:
            with conn.cursor() as cur:
                # Get hot user IDs
                cur.execute("""
                    SELECT DISTINCT user_id
                    FROM access_logs
                    WHERE created_at > NOW() - INTERVAL '24 hours'
                    GROUP BY user_id
                    ORDER BY COUNT(*) DESC
                    LIMIT 1000
                """)
                hot_user_ids = [row[0] for row in cur.fetchall()]

        # Warm caches concurrently
        with ThreadPoolExecutor(max_workers=5) as executor:
            futures = {
                executor.submit(self.warm_user_profiles, hot_user_ids): 'users',
                executor.submit(self.warm_top_products, 100): 'products'
            }

            results = {}
            for future in as_completed(futures):
                cache_type = futures[future]
                try:
                    results[cache_type] = future.result()
                except Exception as e:
                    logger.error(f"Error warming {cache_type}: {e}")

        return results


# Scheduled cache warming (run via cron or scheduler)
if __name__ == "__main__":
    from multitiercache import cache

    warmer = CacheWarmer(
        cache=cache,
        db_conn_string="postgresql://user:pass@localhost/db"
    )

    # Warm cache (run every 30 minutes)
    results = warmer.warm_all_hot_data()
    print(f"Cache warm complete: {results}")
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Redis connection refused" | Redis server down or unreachable | Implement graceful degradation (bypass cache, query database directly) |
| "Out of memory" (Redis) | Cache size exceeds max memory | Configure eviction policy (`maxmemory-policy allkeys-lru`) or increase memory |
| "Pickle deserialization error" | Cached object structure changed | Version cache keys when data models change, invalidate old caches |
| "Cache stampede" | Many requests miss cache simultaneously | Use locking or probabilistic early expiration to prevent thundering herd |
| "Stale data returned" | TTL too long or invalidation missed | Reduce TTL, implement event-driven invalidation on updates |

## Configuration Options

**Caching Patterns**
- **Cache-aside** (lazy loading): App checks cache, queries DB on miss
- **Read-through**: Cache handles DB queries automatically
- **Write-through**: Updates written to cache and DB simultaneously
- **Write-behind**: Updates written to cache, async written to DB

**Eviction Policies** (Redis)
- **allkeys-lru**: Evict least recently used keys (recommended for general use)
- **volatile-lru**: Evict LRU keys with TTL set
- **allkeys-random**: Random eviction (simple, unpredictable)
- **volatile-ttl**: Evict keys closest to expiration

**TTL Strategies**
- **Hot data (user profiles)**: 30 minutes
- **Warm data (product catalog)**: 1-2 hours
- **Cold data (historical reports)**: 24 hours
- **Static data (configuration)**: 7 days

## Best Practices

DO:
- Set appropriate TTLs based on data freshness requirements
- Monitor cache hit rate (target: 80%+) and adjust strategy
- Implement graceful degradation when cache is unavailable
- Use hierarchical cache keys for easy pattern-based invalidation
- Warm cache with hot data during deployment
- Version cache keys when data schemas change
- Use connection pooling for Redis clients (reduce connection overhead)

DON'T:
- Cache data that changes frequently (< 50% hit rate)
- Use cache for critical consistency (financial transactions, inventory)
- Ignore cache memory limits (causes evictions and performance degradation)
- Cache large objects (> 1MB) without compression
- Forget to invalidate cache on data updates (stale data bugs)
- Use cache as primary data store (Redis is not durable)
- Over-cache (memory waste, low hit rate)

## Performance Considerations

- **L1 cache hit**: 1-5ms (in-memory)
- **L2 cache hit**: 5-10ms (Redis)
- **Database query**: 50-100ms (depending on complexity)
- **Speedup**: 10-100x faster than database queries
- **Cache hit rate target**: 80-95% for read-heavy workloads
- **Memory usage**: 1MB per 10,000 small objects (varies by data size)
- **Redis throughput**: 100,000+ ops/sec (single instance)

## Security Considerations

- Encrypt sensitive data before caching (PII, credentials)
- Use Redis AUTH and TLS for production (prevent unauthorized access)
- Isolate cache per tenant in multi-tenant applications
- Audit cache access for compliance (GDPR, HIPAA)
- Implement cache poisoning prevention (validate cached data)
- Secure Redis instance in private network (no public access)
- Rotate Redis passwords quarterly

## Related Commands

- `/database-connection-pooler` - Optimize connections when cache is unavailable
- `/database-health-monitor` - Monitor cache hit rate and database load
- `/sql-query-optimizer` - Optimize queries that are cache misses
- `/database-security-scanner` - Audit sensitive data in cache

## Version History

- v1.0.0 (2024-10): Initial implementation with Redis and in-memory caching
- Planned v1.1.0: Add memcached support, distributed tracing integration
