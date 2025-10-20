---
description: Add rate limiting to API endpoints
shortcut: ratelimit
---

# Add Rate Limiting to API Endpoints

Implement production-ready rate limiting with token bucket, sliding window, or fixed window algorithms using Redis for distributed state management.

## When to Use This Command

Use `/add-rate-limiting` when you need to:
- Protect APIs from abuse and DDoS attacks
- Enforce fair usage policies across user tiers
- Prevent resource exhaustion from runaway clients
- Comply with downstream API rate limits
- Implement freemium pricing models with usage tiers
- Control costs for expensive operations (AI inference, video processing)

DON'T use this when:
- Building internal-only APIs with trusted clients (use circuit breakers instead)
- Single-user applications (no shared resource contention)
- Already behind API gateway with built-in rate limiting (avoid double limiting)

## Design Decisions

This command implements **Token Bucket algorithm with Redis** as the primary approach because:
- Allows burst traffic while maintaining average rate (better UX)
- Distributed state enables horizontal scaling
- Redis atomic operations prevent race conditions
- Standard algorithm with well-understood behavior

**Alternative considered: Sliding Window**
- More accurate rate limiting (no reset boundary issues)
- Higher Redis memory usage (stores timestamp per request)
- Slightly higher computational overhead
- Recommended for strict compliance requirements

**Alternative considered: Fixed Window**
- Simplest implementation (single counter)
- Burst at window boundaries (2x limit possible)
- Lower memory footprint
- Recommended only for non-critical rate limiting

**Alternative considered: Leaky Bucket**
- Constant output rate (smooths bursty traffic)
- Complex to explain to users
- Less common in practice
- Recommended for queuing systems, not APIs

## Prerequisites

Before running this command:
1. Redis server installed and accessible (standalone or cluster)
2. Node.js/Python runtime for middleware implementation
3. API framework that supports middleware (Express, FastAPI, etc.)
4. Understanding of your API usage patterns and SLO requirements
5. Monitoring infrastructure to track rate limit metrics

## Implementation Process

### Step 1: Choose Rate Limiting Strategy
Select algorithm based on requirements: Token Bucket for user-facing APIs, Sliding Window for strict compliance, Fixed Window for internal APIs.

### Step 2: Configure Redis Connection
Set up Redis client with connection pooling, retry logic, and failover handling for high availability.

### Step 3: Implement Rate Limiter Middleware
Create middleware that intercepts requests, checks Redis state, and enforces limits with proper HTTP headers.

### Step 4: Define Rate Limit Tiers
Configure different limits for user segments (anonymous, free, premium, enterprise) based on business requirements.

### Step 5: Add Monitoring and Alerting
Instrument rate limiter with metrics for blocked requests, Redis latency, and tier usage patterns.

## Output Format

The command generates:
- `rate-limiter.js` or `rate_limiter.py` - Core rate limiting middleware
- `redis-config.js` - Redis connection configuration with failover
- `rate-limit-tiers.json` - Tiered limit definitions
- `rate-limiter.test.js` - Comprehensive test suite
- `README.md` - Integration guide and configuration options
- `docker-compose.yml` - Redis setup for local development

## Code Examples

### Example 1: Token Bucket Rate Limiter with Express and Redis

```javascript
// rate-limiter.js
const Redis = require('ioredis');

class TokenBucketRateLimiter {
  constructor(redisClient, options = {}) {
    this.redis = redisClient;
    this.defaultOptions = {
      points: 100,        // Number of tokens
      duration: 60,       // Time window in seconds
      blockDuration: 60,  // Block duration after limit exceeded
      keyPrefix: 'rl',    // Redis key prefix
      ...options
    };
  }

  /**
   * Token bucket algorithm using Redis
   * Returns: { allowed: boolean, remaining: number, resetTime: number }
   */
  async consume(identifier, points = 1, options = {}) {
    const opts = { ...this.defaultOptions, ...options };
    const key = `${opts.keyPrefix}:${identifier}`;
    const now = Date.now();

    // Lua script for atomic token bucket operations
    const luaScript = `
      local key = KEYS[1]
      local capacity = tonumber(ARGV[1])
      local refill_rate = tonumber(ARGV[2])
      local requested = tonumber(ARGV[3])
      local now = tonumber(ARGV[4])
      local ttl = tonumber(ARGV[5])

      -- Get current state or initialize
      local tokens = tonumber(redis.call('HGET', key, 'tokens'))
      local last_refill = tonumber(redis.call('HGET', key, 'last_refill'))

      if not tokens then
        tokens = capacity
        last_refill = now
      end

      -- Calculate tokens to add since last refill
      local time_passed = now - last_refill
      local tokens_to_add = math.floor(time_passed * refill_rate)
      tokens = math.min(capacity, tokens + tokens_to_add)
      last_refill = now

      -- Check if we can fulfill request
      if tokens >= requested then
        tokens = tokens - requested
        redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
        redis.call('EXPIRE', key, ttl)
        return {1, tokens, last_refill}
      else
        redis.call('HMSET', key, 'tokens', tokens, 'last_refill', last_refill)
        redis.call('EXPIRE', key, ttl)
        return {0, tokens, last_refill}
      end
    `;

    const refillRate = opts.points / opts.duration;
    const result = await this.redis.eval(
      luaScript,
      1,
      key,
      opts.points,
      refillRate,
      points,
      now,
      opts.duration
    );

    const [allowed, remaining, lastRefill] = result;
    const resetTime = lastRefill + (opts.duration * 1000);

    return {
      allowed: allowed === 1,
      remaining: Math.floor(remaining),
      resetTime: new Date(resetTime).toISOString(),
      retryAfter: allowed === 1 ? null : Math.ceil((opts.duration * 1000 - (now - lastRefill)) / 1000)
    };
  }

  /**
   * Express middleware factory
   */
  middleware(getTier = null) {
    return async (req, res, next) => {
      try {
        // Determine identifier (user ID or IP)
        const identifier = req.user?.id || req.ip;

        // Get tier configuration
        const tier = getTier ? await getTier(req) : 'default';
        const tierConfig = this.getTierConfig(tier);

        // Consume tokens
        const result = await this.consume(identifier, 1, tierConfig);

        // Set rate limit headers
        res.set({
          'X-RateLimit-Limit': tierConfig.points,
          'X-RateLimit-Remaining': result.remaining,
          'X-RateLimit-Reset': result.resetTime
        });

        if (!result.allowed) {
          res.set('Retry-After', result.retryAfter);
          return res.status(429).json({
            error: 'Too Many Requests',
            message: `Rate limit exceeded. Try again in ${result.retryAfter} seconds.`,
            retryAfter: result.retryAfter
          });
        }

        next();
      } catch (error) {
        console.error('Rate limiter error:', error);
        // Fail open to avoid blocking all traffic on Redis failure
        next();
      }
    };
  }

  getTierConfig(tier) {
    const tiers = {
      anonymous: { points: 20, duration: 60 },
      free: { points: 100, duration: 60 },
      premium: { points: 1000, duration: 60 },
      enterprise: { points: 10000, duration: 60 }
    };
    return tiers[tier] || tiers.free;
  }
}

// Usage example
const redis = new Redis({
  host: process.env.REDIS_HOST || 'localhost',
  port: process.env.REDIS_PORT || 6379,
  retryStrategy: (times) => Math.min(times * 50, 2000),
  maxRetriesPerRequest: 3
});

const rateLimiter = new TokenBucketRateLimiter(redis);

// Apply to all routes
app.use(rateLimiter.middleware(async (req) => {
  if (req.user?.subscription === 'enterprise') return 'enterprise';
  if (req.user?.subscription === 'premium') return 'premium';
  if (req.user) return 'free';
  return 'anonymous';
}));

// Apply stricter limit to specific expensive endpoint
app.post('/api/ai/generate',
  rateLimiter.middleware(() => ({ points: 10, duration: 3600 })),
  handleGenerate
);

module.exports = TokenBucketRateLimiter;
```

### Example 2: Sliding Window Rate Limiter in Python with FastAPI

```python
# rate_limiter.py
import time
import redis.asyncio as aioredis
from fastapi import Request, Response, HTTPException
from typing import Optional, Callable
import asyncio

class SlidingWindowRateLimiter:
    def __init__(self, redis_client: aioredis.Redis, window_size: int = 60, max_requests: int = 100):
        self.redis = redis_client
        self.window_size = window_size
        self.max_requests = max_requests
        self.key_prefix = "rate_limit"

    async def is_allowed(self, identifier: str, tier_config: dict = None) -> dict:
        """
        Sliding window algorithm using Redis sorted set
        Each request is a member with score = timestamp
        """
        config = tier_config or {'max_requests': self.max_requests, 'window_size': self.window_size}
        now = time.time()
        window_start = now - config['window_size']
        key = f"{self.key_prefix}:{identifier}"

        # Redis pipeline for atomic operations
        pipe = self.redis.pipeline()

        # Remove old entries outside the window
        pipe.zremrangebyscore(key, 0, window_start)

        # Count requests in current window
        pipe.zcard(key)

        # Add current request
        pipe.zadd(key, {str(now): now})

        # Set expiration
        pipe.expire(key, config['window_size'] + 10)

        results = await pipe.execute()
        request_count = results[1]

        if request_count >= config['max_requests']:
            # Get oldest request in window to calculate retry time
            oldest = await self.redis.zrange(key, 0, 0, withscores=True)
            if oldest:
                oldest_time = oldest[0][1]
                retry_after = int(config['window_size'] - (now - oldest_time)) + 1
            else:
                retry_after = config['window_size']

            return {
                'allowed': False,
                'remaining': 0,
                'reset_time': int(now + retry_after),
                'retry_after': retry_after
            }

        remaining = config['max_requests'] - request_count - 1
        reset_time = int(now + config['window_size'])

        return {
            'allowed': True,
            'remaining': remaining,
            'reset_time': reset_time,
            'retry_after': None
        }

    def middleware(self, get_tier: Optional[Callable] = None):
        """FastAPI middleware factory"""
        async def rate_limit_middleware(request: Request, call_next):
            # Get identifier (user ID or IP)
            identifier = getattr(request.state, 'user_id', None) or request.client.host

            # Get tier configuration
            tier_config = None
            if get_tier:
                tier_config = await get_tier(request)

            # Check rate limit
            result = await self.is_allowed(identifier, tier_config)

            # Always set rate limit headers
            response = None
            if result['allowed']:
                response = await call_next(request)
            else:
                response = Response(
                    content=f'{{"error": "Rate limit exceeded", "retry_after": {result["retry_after"]}}}',
                    status_code=429,
                    media_type="application/json"
                )

            response.headers['X-RateLimit-Limit'] = str(tier_config['max_requests'] if tier_config else self.max_requests)
            response.headers['X-RateLimit-Remaining'] = str(result['remaining'])
            response.headers['X-RateLimit-Reset'] = str(result['reset_time'])

            if not result['allowed']:
                response.headers['Retry-After'] = str(result['retry_after'])

            return response

        return rate_limit_middleware

# Usage in FastAPI
from fastapi import FastAPI
from contextlib import asynccontextmanager

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    app.state.redis = await aioredis.from_url("redis://localhost:6379")
    app.state.rate_limiter = SlidingWindowRateLimiter(app.state.redis)
    yield
    # Shutdown
    await app.state.redis.close()

app = FastAPI(lifespan=lifespan)

async def get_user_tier(request: Request) -> dict:
    """Determine user tier from request"""
    user = getattr(request.state, 'user', None)
    if not user:
        return {'max_requests': 20, 'window_size': 60}  # Anonymous
    elif user.get('subscription') == 'enterprise':
        return {'max_requests': 10000, 'window_size': 60}
    elif user.get('subscription') == 'premium':
        return {'max_requests': 1000, 'window_size': 60}
    else:
        return {'max_requests': 100, 'window_size': 60}  # Free tier

# Apply rate limiting middleware
app.middleware("http")(app.state.rate_limiter.middleware(get_user_tier))
```

### Example 3: DDoS Protection with Multi-Layer Rate Limiting

```javascript
// advanced-rate-limiter.js - Multi-layer protection
const Redis = require('ioredis');

class MultiLayerRateLimiter {
  constructor(redisClient) {
    this.redis = redisClient;
  }

  /**
   * Layered rate limiting strategy:
   * 1. IP-based (DDoS protection)
   * 2. User-based (fair usage)
   * 3. Endpoint-specific (expensive operations)
   */
  async checkLayers(req) {
    const layers = [
      // Layer 1: IP-based rate limiting (DDoS protection)
      {
        name: 'ip',
        identifier: req.ip,
        limits: { points: 1000, duration: 60 }, // 1000 req/min per IP
        priority: 'high'
      },
      // Layer 2: User-based rate limiting
      {
        name: 'user',
        identifier: req.user?.id || `anon:${req.ip}`,
        limits: this.getUserTierLimits(req.user),
        priority: 'medium'
      },
      // Layer 3: Endpoint-specific limiting
      {
        name: 'endpoint',
        identifier: `${req.user?.id || req.ip}:${req.path}`,
        limits: this.getEndpointLimits(req.path),
        priority: 'low'
      }
    ];

    for (const layer of layers) {
      const result = await this.checkLimit(layer);
      if (!result.allowed) {
        return {
          blocked: true,
          layer: layer.name,
          ...result
        };
      }
    }

    return { blocked: false };
  }

  async checkLimit(layer) {
    const key = `rl:${layer.name}:${layer.identifier}`;
    const now = Date.now();

    const count = await this.redis.incr(key);

    if (count === 1) {
      await this.redis.expire(key, layer.limits.duration);
    }

    const ttl = await this.redis.ttl(key);
    const allowed = count <= layer.limits.points;

    return {
      allowed,
      remaining: Math.max(0, layer.limits.points - count),
      resetTime: now + (ttl * 1000),
      retryAfter: allowed ? null : ttl
    };
  }

  getUserTierLimits(user) {
    if (!user) return { points: 20, duration: 60 };
    const tiers = {
      free: { points: 100, duration: 60 },
      premium: { points: 1000, duration: 60 },
      enterprise: { points: 10000, duration: 60 }
    };
    return tiers[user.subscription] || tiers.free;
  }

  getEndpointLimits(path) {
    const expensiveEndpoints = {
      '/api/ai/generate': { points: 10, duration: 3600 },  // 10/hour
      '/api/video/render': { points: 5, duration: 3600 },  // 5/hour
      '/api/export/large': { points: 20, duration: 3600 }  // 20/hour
    };
    return expensiveEndpoints[path] || { points: 1000, duration: 60 };
  }

  middleware() {
    return async (req, res, next) => {
      try {
        const result = await this.checkLayers(req);

        if (result.blocked) {
          res.set({
            'X-RateLimit-Layer': result.layer,
            'X-RateLimit-Remaining': result.remaining,
            'Retry-After': result.retryAfter
          });

          return res.status(429).json({
            error: 'Rate limit exceeded',
            layer: result.layer,
            retryAfter: result.retryAfter,
            message: `Too many requests. Please retry after ${result.retryAfter} seconds.`
          });
        }

        next();
      } catch (error) {
        console.error('Multi-layer rate limiter error:', error);
        next(); // Fail open
      }
    };
  }
}

module.exports = MultiLayerRateLimiter;
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Redis connection failed" | Redis server unreachable | Check Redis server status, verify connection string, implement connection retry |
| "Rate limiter fail-closed" | Redis timeout, middleware blocking all traffic | Implement fail-open strategy with circuit breaker pattern |
| "Inconsistent rate limits" | Clock skew across servers | Use Redis time (`TIME` command) instead of server time |
| "Memory exhaustion" | Too many keys, no TTL set | Always set TTL on rate limit keys, use key expiration monitoring |
| "False positives from NAT" | Multiple users behind same IP | Use authenticated user IDs when available, consider X-Forwarded-For |

## Configuration Options

**Rate Limit Algorithms**
- **Token Bucket**: Best for user-facing APIs with burst allowance
- **Sliding Window**: Most accurate, higher memory usage
- **Fixed Window**: Simplest, allows boundary bursts
- **Leaky Bucket**: Constant rate, complex UX

**Tier Definitions**
```json
{
  "anonymous": { "points": 20, "duration": 60 },
  "free": { "points": 100, "duration": 60 },
  "premium": { "points": 1000, "duration": 60 },
  "enterprise": { "points": 10000, "duration": 60 }
}
```

**Redis Configuration**
- **Connection pooling**: Minimum 5 connections
- **Retry strategy**: Exponential backoff up to 2s
- **Failover**: Redis Sentinel or Cluster for HA
- **Persistence**: AOF for rate limit state recovery

## Best Practices

DO:
- Return standard rate limit headers (X-RateLimit-Limit, X-RateLimit-Remaining, X-RateLimit-Reset)
- Implement graceful degradation (fail open on Redis failure)
- Use user ID over IP when authenticated (avoids NAT issues)
- Set TTL on all Redis keys to prevent memory leaks
- Monitor rate limiter performance (latency, block rate)
- Provide clear error messages with retry guidance

DON'T:
- Block legitimate traffic (tune limits based on real usage)
- Use client-side rate limiting only (easily bypassed)
- Forget to handle Redis connection failures (causes complete outage)
- Implement synchronous Redis calls (adds latency to every request)
- Use rate limiting as only defense against DDoS (need multiple layers)

TIPS:
- Start conservative, increase limits based on monitoring
- Use different limits for different operations (read vs write)
- Implement per-endpoint rate limits for expensive operations
- Cache tier lookups to reduce database queries
- Log rate limit violations for security analysis
- Provide upgrade paths for users hitting limits

## Performance Considerations

**Latency Impact**
- Token bucket: 1-2ms added to request (single Redis call)
- Sliding window: 2-4ms (multiple Redis operations)
- With pipelining: <1ms for all algorithms

**Redis Memory Usage**
- Token bucket: ~100 bytes per user
- Sliding window: ~50 bytes per request in window
- Fixed window: ~50 bytes per user per window

**Throughput**
- Redis can handle 100k+ operations/second
- Use Redis Cluster for horizontal scaling
- Pipeline Redis operations when possible
- Consider local caching for extremely high throughput

## Security Considerations

1. **DDoS Protection**: Implement IP-based rate limiting as first layer
2. **Credential Stuffing**: Add stricter limits on authentication endpoints
3. **API Scraping**: Implement progressive delays for repeated violations
4. **Distributed Attacks**: Use shared Redis across all API servers
5. **Bypass Attempts**: Validate X-Forwarded-For headers, don't trust blindly
6. **State Consistency**: Use Redis transactions to prevent race conditions

## Troubleshooting

**Rate Limits Not Enforced**
```bash
# Check Redis connectivity
redis-cli -h localhost -p 6379 ping

# Verify keys are being created
redis-cli --scan --pattern 'rl:*' | head -10

# Check TTL is set correctly
redis-cli TTL rl:user:123456
```

**Too Many False Positives**
```bash
# Review blocked requests by IP
redis-cli --scan --pattern 'rl:ip:*' | xargs redis-cli MGET

# Check tier assignments
# Review application logs for tier calculation

# Analyze legitimate traffic patterns
# Adjust limits based on p95/p99 usage
```

**Redis Memory Issues**
```bash
# Check memory usage
redis-cli INFO memory

# Count rate limit keys
redis-cli --scan --pattern 'rl:*' | wc -l

# Review keys without TTL
redis-cli --scan --pattern 'rl:*' | xargs redis-cli TTL | grep -c "^-1"
```

## Related Commands

- `/create-monitoring` - Monitor rate limit metrics and violations
- `/api-authentication-builder` - Integrate with auth for user-based limits
- `/api-load-tester` - Test rate limiter under realistic load
- `/setup-logging` - Log rate limit violations for analysis

## Version History

- v1.0.0 (2024-10): Initial implementation with token bucket and sliding window
- Planned v1.1.0: Add adaptive rate limiting based on system load
