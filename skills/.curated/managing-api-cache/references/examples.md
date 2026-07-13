# API Cache Management Examples

## Cache-Aside Middleware (Express + Redis)

```javascript
// middleware/cache.js
const Redis = require('ioredis');
const redis = new Redis(process.env.REDIS_URL);

function cacheMiddleware(ttlSeconds = 300) {
  return async (req, res, next) => {
    if (req.method !== 'GET') return next();

    const key = generateCacheKey(req);
    const cached = await redis.get(key);

    if (cached) {
      res.set('X-Cache', 'HIT');
      res.set('Content-Type', 'application/json');
      return res.send(cached);
    }

    const originalJson = res.json.bind(res);
    res.json = (body) => {
      redis.setex(key, ttlSeconds, JSON.stringify(body));
      res.set('X-Cache', 'MISS');
      return originalJson(body);
    };
    next();
  };
}

function generateCacheKey(req) {
  const params = new URLSearchParams(req.query);
  params.sort();
  const userHash = req.user?.id || 'anonymous';
  return `cache:${req.method}:${req.path}:${params.toString()}:${userHash}`;
}
```

## Per-Endpoint TTL Configuration

```javascript
// config/cache-policies.js
const cachePolicies = {
  '/api/products':     { ttl: 3600, tags: ['products'] },
  '/api/products/:id': { ttl: 3600, tags: ['products'] },
  '/api/categories':   { ttl: 86400, tags: ['categories'] },
  '/api/users/:id':    { ttl: 30, tags: ['users'], perUser: true },
  '/api/dashboard':    { ttl: 30, tags: ['dashboard'], perUser: true },
};

app.get('/api/products', cacheMiddleware(3600), listProducts);
app.get('/api/users/:id', cacheMiddleware(30), getUser);
```

## Tag-Based Cache Invalidation

```javascript
// cache/invalidator.js
async function invalidateByTag(tag) {
  const keys = await redis.smembers(`cache-tag:${tag}`);
  if (keys.length > 0) {
    await redis.del(...keys);
    await redis.del(`cache-tag:${tag}`);
  }
}

async function cacheWithTags(key, value, ttl, tags) {
  const pipeline = redis.pipeline();
  pipeline.setex(key, ttl, JSON.stringify(value));
  for (const tag of tags) {
    pipeline.sadd(`cache-tag:${tag}`, key);
    pipeline.expire(`cache-tag:${tag}`, ttl);
  }
  await pipeline.exec();
}

app.post('/api/products', async (req, res) => {
  const product = await db.products.create(req.body);
  await invalidateByTag('products');
  res.status(201).json(product);
});
```

## HTTP Cache Headers with ETag

```javascript
function httpCacheHeaders({ maxAge = 300, isPublic = false } = {}) {
  return (req, res, next) => {
    res.set('Cache-Control',
      `${isPublic ? 'public' : 'private'}, max-age=${maxAge}, stale-while-revalidate=60`
    );
    const originalJson = res.json.bind(res);
    res.json = (body) => {
      const etag = crypto.createHash('md5').update(JSON.stringify(body)).digest('hex');
      res.set('ETag', `"${etag}"`);
      if (req.headers['if-none-match'] === `"${etag}"`) {
        return res.status(304).end();
      }
      return originalJson(body);
    };
    next();
  };
}
```

## Stale-While-Revalidate

```javascript
async function getWithSWR(key, ttl, fetcher) {
  const cached = await redis.get(key);
  const meta = await redis.get(`${key}:meta`);

  if (cached) {
    const { expiresAt } = JSON.parse(meta || '{}');
    if (Date.now() > expiresAt) {
      setImmediate(async () => {
        const fresh = await fetcher();
        await redis.setex(key, ttl * 2, JSON.stringify(fresh));
        await redis.setex(`${key}:meta`, ttl * 2,
          JSON.stringify({ expiresAt: Date.now() + ttl * 1000 }));
      });
    }
    return JSON.parse(cached);
  }

  const data = await fetcher();
  await redis.setex(key, ttl * 2, JSON.stringify(data));
  await redis.setex(`${key}:meta`, ttl * 2,
    JSON.stringify({ expiresAt: Date.now() + ttl * 1000 }));
  return data;
}
```

## Cache Warming on Startup

```javascript
async function warmCache() {
  const critical = [
    { key: 'cache:GET:/api/categories', fetcher: () => db.categories.findAll(), ttl: 86400 },
    { key: 'cache:GET:/api/products:popular', fetcher: () => db.products.findPopular(50), ttl: 3600 },
  ];
  for (const { key, fetcher, ttl } of critical) {
    const data = await fetcher();
    await redis.setex(key, ttl, JSON.stringify(data));
  }
}

app.listen(3000, async () => {
  await warmCache();
  console.log('Server ready with warm cache');
});
```

## curl: Cache Behavior

```bash
# First request: MISS
curl -i http://localhost:3000/api/products
# X-Cache: MISS
# Cache-Control: public, max-age=300, stale-while-revalidate=60

# Second request: HIT
curl -i http://localhost:3000/api/products
# X-Cache: HIT

# Conditional request with ETag
curl -i http://localhost:3000/api/products -H 'If-None-Match: "abc123"'
# 304 Not Modified

# After mutation, cache invalidated
curl -X POST http://localhost:3000/api/products \
  -H "Content-Type: application/json" -d '{"name":"Widget","price":29.99}'
curl -i http://localhost:3000/api/products
# X-Cache: MISS
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
