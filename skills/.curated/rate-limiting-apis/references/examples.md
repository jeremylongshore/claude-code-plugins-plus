# API Rate Limiting Examples

## Sliding Window (Redis Sorted Sets)

```javascript
async function slidingWindowRateLimit(identifier, limit, windowSeconds) {
  const key = `ratelimit:${identifier}`;
  const now = Date.now();
  const windowStart = now - windowSeconds * 1000;

  const pipeline = redis.pipeline();
  pipeline.zremrangebyscore(key, 0, windowStart);
  pipeline.zadd(key, now, `${now}:${Math.random()}`);
  pipeline.zcard(key);
  pipeline.expire(key, windowSeconds);

  const results = await pipeline.exec();
  const count = results[2][1];
  return {
    allowed: count <= limit,
    remaining: Math.max(0, limit - count),
    resetAt: Math.ceil((windowStart + windowSeconds * 1000) / 1000),
    limit,
  };
}
```

## Rate Limit Middleware with Headers

```javascript
function rateLimitMiddleware({ limit = 100, windowSeconds = 60, keyFn } = {}) {
  return async (req, res, next) => {
    if (req.skipRateLimit) return next();
    const id = keyFn ? keyFn(req) : req.user?.id || req.headers['x-api-key'] || req.ip;
    const result = await slidingWindowRateLimit(id, limit, windowSeconds);

    res.set('X-RateLimit-Limit', String(result.limit));
    res.set('X-RateLimit-Remaining', String(result.remaining));
    res.set('X-RateLimit-Reset', String(result.resetAt));
    res.set('RateLimit-Policy', `${limit};w=${windowSeconds}`);

    if (!result.allowed) {
      const retryAfter = Math.ceil((result.resetAt * 1000 - Date.now()) / 1000);
      res.set('Retry-After', String(retryAfter));
      return res.status(429).json({
        type: 'https://api.example.com/errors/rate-limit',
        title: 'Too Many Requests', status: 429,
        detail: `Rate limit of ${limit} per ${windowSeconds}s exceeded`,
        retryAfter,
      });
    }
    next();
  };
}
```

## Tiered Limits per Plan

```javascript
const tierLimits = {
  free:       { default: 100,  login: 5,  search: 20  },
  pro:        { default: 1000, login: 20, search: 200 },
  enterprise: { default: 10000, login: 100, search: 2000 },
};

app.get('/api/users',
  rateLimitMiddleware({
    limit: (req) => tierLimits[req.apiTier || 'free'].default,
    windowSeconds: 60,
    keyFn: (req) => req.headers['x-api-key'] || req.ip,
  }),
  listUsers
);
```

## Token Bucket (Redis Lua)

```javascript
async function tokenBucket(identifier, rate, burstSize) {
  const script = `
    local key = KEYS[1]
    local rate = tonumber(ARGV[1])
    local burst = tonumber(ARGV[2])
    local now = tonumber(ARGV[3])
    local data = redis.call('HMGET', key, 'tokens', 'last_refill')
    local tokens = tonumber(data[1]) or burst
    local last = tonumber(data[2]) or now
    tokens = math.min(burst, tokens + (now - last) * rate)
    local allowed = 0
    if tokens >= 1 then tokens = tokens - 1; allowed = 1 end
    redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
    redis.call('EXPIRE', key, 120)
    return {allowed, math.floor(tokens)}
  `;
  const [allowed, remaining] = await redis.eval(script, 1,
    `bucket:${identifier}`, rate, burstSize, Date.now() / 1000);
  return { allowed: allowed === 1, remaining };
}
```

## Login Brute-Force Protection

```javascript
const LOCKOUTS = [15 * 60, 60 * 60, 24 * 60 * 60];

async function loginProtection(req, res, next) {
  const ip = req.ip;
  const lockTTL = await redis.ttl(`login:locked:${ip}`);
  if (lockTTL > 0) {
    return res.status(429).json({ detail: 'Account locked', retryAfter: lockTTL });
  }

  req.onLoginFailure = async () => {
    const failures = await redis.incr(`login:failures:${ip}`);
    await redis.expire(`login:failures:${ip}`, 86400);
    const idx = failures >= 20 ? 2 : failures >= 10 ? 1 : failures >= 5 ? 0 : -1;
    if (idx >= 0) await redis.setex(`login:locked:${ip}`, LOCKOUTS[idx], 'locked');
  };
  req.onLoginSuccess = () => redis.del(`login:failures:${ip}`, `login:locked:${ip}`);
  next();
}
```

## curl: Rate Limit Behavior

```bash
# Normal request
curl -i http://localhost:3000/api/users -H "X-API-Key: key_free_123"
# X-RateLimit-Limit: 100
# X-RateLimit-Remaining: 99
# X-RateLimit-Reset: 1710000060

# After exceeding limit
# HTTP/1.1 429 Too Many Requests
# Retry-After: 45
# {"type":"...rate-limit","detail":"Rate limit of 100 per 60s exceeded","retryAfter":45}

# Pro tier
curl -i http://localhost:3000/api/users -H "X-API-Key: key_pro_456"
# X-RateLimit-Limit: 1000
```

## Rate Limit Tests

```javascript
describe('Rate Limiting', () => {
  it('allows within limit', async () => {
    for (let i = 0; i < 5; i++) {
      const res = await request(app).get('/api/users').set('X-API-Key', 'test');
      expect(res.status).toBe(200);
      expect(res.headers['x-ratelimit-remaining']).toBe(String(4 - i));
    }
  });
  it('rejects over limit', async () => {
    for (let i = 0; i < 5; i++) await request(app).get('/api/users').set('X-API-Key', 'test');
    const res = await request(app).get('/api/users').set('X-API-Key', 'test');
    expect(res.status).toBe(429);
    expect(res.headers['retry-after']).toBeDefined();
  });
});
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
