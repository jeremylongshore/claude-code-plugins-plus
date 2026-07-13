# API Gateway Builder Examples

## Route Configuration

```yaml
# gateway/config/routes.yaml
routes:
  - prefix: /users
    upstream: http://user-service:3001
    auth: required
    rateLimit: { requests: 1000, window: 60 }
    circuitBreaker: { threshold: 5, timeout: 30000 }
  - prefix: /orders
    upstream: http://order-service:3002
    auth: required
    rateLimit: { requests: 500, window: 60 }
  - prefix: /products
    upstream: http://product-service:3003
    auth: optional
    cache: { ttl: 300, methods: [GET] }
```

## Express Gateway with Proxy

```javascript
const express = require('express');
const { createProxyMiddleware } = require('http-proxy-middleware');
const yaml = require('js-yaml');
const fs = require('fs');

const app = express();
const routes = yaml.load(fs.readFileSync('./config/routes.yaml')).routes;

app.use(correlationId);
app.use(requestLogger);

for (const route of routes) {
  const mw = [];
  if (route.auth === 'required') mw.push(requireAuth);
  if (route.rateLimit) mw.push(rateLimiter(route.rateLimit));
  if (route.circuitBreaker) mw.push(circuitBreaker(route.upstream, route.circuitBreaker));

  mw.push(createProxyMiddleware({
    target: route.upstream,
    changeOrigin: true,
    pathRewrite: { [`^${route.prefix}`]: '' },
    onProxyReq: (proxyReq, req) => {
      if (req.user) {
        proxyReq.setHeader('X-User-ID', req.user.id);
        proxyReq.setHeader('X-User-Roles', req.user.roles.join(','));
      }
      proxyReq.setHeader('X-Correlation-ID', req.correlationId);
    },
  }));
  app.use(route.prefix, ...mw);
}
```

## Circuit Breaker

```javascript
const CircuitBreaker = require('opossum');

function circuitBreaker(upstream, opts) {
  const breaker = new CircuitBreaker(
    async (req) => {
      const resp = await fetch(`${upstream}${req.path}`, {
        method: req.method, headers: req.headers,
        body: req.method !== 'GET' ? JSON.stringify(req.body) : undefined,
        signal: AbortSignal.timeout(opts.timeout || 10000),
      });
      if (!resp.ok) throw new Error(`Upstream ${resp.status}`);
      return resp;
    },
    { timeout: opts.timeout || 10000, errorThresholdPercentage: 50,
      resetTimeout: 30000, volumeThreshold: opts.threshold || 5 }
  );

  breaker.on('open', () => console.warn(`Circuit OPEN: ${upstream}`));

  return async (req, res, next) => {
    try {
      const upstreamRes = await breaker.fire(req);
      res.status(upstreamRes.status).json(await upstreamRes.json());
    } catch {
      if (breaker.opened) {
        return res.status(503).json({ title: 'Service Unavailable', retryAfter: 30 });
      }
      res.status(502).json({ title: 'Bad Gateway' });
    }
  };
}
```

## Response Aggregation (BFF)

```javascript
app.get('/dashboard', requireAuth, async (req, res) => {
  const userId = req.user.id;
  const headers = { 'X-Correlation-ID': req.correlationId, 'X-User-ID': userId };

  const [user, orders, notifications] = await Promise.allSettled([
    fetch(`http://user-service:3001/users/${userId}`, { headers }),
    fetch(`http://order-service:3002/users/${userId}/orders?limit=5`, { headers }),
    fetch(`http://notification-service:3004/users/${userId}/unread`, { headers }),
  ]);

  res.json({
    user: user.status === 'fulfilled' ? await user.value.json() : null,
    recentOrders: orders.status === 'fulfilled' ? await orders.value.json() : [],
    unreadNotifications: notifications.status === 'fulfilled'
      ? await notifications.value.json() : { count: 0 },
  });
});
```

## Aggregated Health Check

```javascript
app.get('/health', async (req, res) => {
  const checks = await Promise.allSettled(
    routes.filter(r => r.upstream !== 'internal').map(async (route) => {
      const start = Date.now();
      const resp = await fetch(`${route.upstream}/health`, { signal: AbortSignal.timeout(3000) });
      return { service: route.prefix, status: resp.ok ? 'healthy' : 'unhealthy', latencyMs: Date.now() - start };
    })
  );

  const results = checks.map((c, i) =>
    c.status === 'fulfilled' ? c.value : { service: routes[i].prefix, status: 'unreachable' }
  );
  const overall = results.every(r => r.status === 'healthy') ? 'healthy'
    : results.some(r => r.status === 'healthy') ? 'degraded' : 'unhealthy';

  res.status(overall === 'unhealthy' ? 503 : 200).json({ status: overall, services: results });
});
```

## curl: Gateway Requests

```bash
# Route through gateway
curl http://localhost:8080/users/42 -H "Authorization: Bearer $TOKEN"

# BFF aggregation
curl http://localhost:8080/dashboard -H "Authorization: Bearer $TOKEN"
# {"user":{...},"recentOrders":[...],"unreadNotifications":{"count":3}}

# Health check
curl http://localhost:8080/health
# {"status":"degraded","services":[{"service":"/users","status":"healthy"},{"service":"/orders","status":"unreachable"}]}

# Circuit open
curl http://localhost:8080/orders/1
# 503 {"title":"Service Unavailable","retryAfter":30}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
