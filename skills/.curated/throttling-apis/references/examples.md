# API Throttling Examples

## Concurrency Limiter Middleware

```javascript
// middleware/throttle.js
function concurrencyLimiter(maxConcurrent = 10) {
  let inFlight = 0;

  return (req, res, next) => {
    if (inFlight >= maxConcurrent) {
      res.set('Retry-After', '5');
      return res.status(503).json({
        title: 'Service Unavailable',
        detail: `Max concurrent requests (${maxConcurrent}) reached`,
        retryAfter: 5,
      });
    }

    inFlight++;
    res.on('finish', () => { inFlight--; });
    next();
  };
}

// Apply to expensive endpoints
app.get('/api/reports/generate',
  concurrencyLimiter(10),
  generateReport
);
```

## Priority Queue by API Tier

```javascript
// middleware/priority-queue.js
const queues = {
  enterprise: { maxConcurrent: 100, reserved: 0.5 },
  pro:        { maxConcurrent: 25, reserved: 0.3 },
  free:       { maxConcurrent: 5, reserved: 0.2 },
};

function priorityThrottle(req, res, next) {
  const tier = req.apiTier || 'free';
  const queue = queues[tier];

  if (queue.current >= queue.maxConcurrent) {
    // Check if any lower-tier capacity can be borrowed
    const canBorrow = Object.entries(queues)
      .filter(([t]) => tierPriority(t) < tierPriority(tier))
      .some(([, q]) => q.current < q.maxConcurrent);

    if (!canBorrow) {
      return res.status(503).json({
        detail: `${tier} tier throttle limit reached`,
        retryAfter: 10,
      });
    }
  }

  queue.current = (queue.current || 0) + 1;
  res.on('finish', () => { queue.current--; });
  next();
}
```

## Circuit Breaker

```javascript
// middleware/circuit-breaker.js
const CircuitBreaker = require('opossum');

function createCircuitBreaker(serviceCall, options = {}) {
  const breaker = new CircuitBreaker(serviceCall, {
    timeout: options.timeout || 10000,
    errorThresholdPercentage: options.errorThreshold || 50,
    resetTimeout: options.resetTimeout || 30000,
    volumeThreshold: options.volumeThreshold || 10,
  });

  breaker.on('open', () => logger.warn(`Circuit OPEN: ${options.name}`));
  breaker.on('halfOpen', () => logger.info(`Circuit HALF-OPEN: ${options.name}`));
  breaker.on('close', () => logger.info(`Circuit CLOSED: ${options.name}`));

  breaker.fallback(() => ({
    status: 503,
    body: { title: 'Service Unavailable', retryAfter: 30 },
  }));

  return breaker;
}

// Usage
const paymentBreaker = createCircuitBreaker(
  (data) => fetch('https://payment-service/charge', { method: 'POST', body: JSON.stringify(data) }),
  { name: 'payment-service', timeout: 5000, errorThreshold: 30 }
);

app.post('/api/orders', async (req, res) => {
  const result = await paymentBreaker.fire(req.body);
  if (result.status === 503) return res.status(503).json(result.body);
  res.json(result);
});
```

## Adaptive Throttling

```javascript
// middleware/adaptive-throttle.js
let currentLimit = 100;
const MIN_LIMIT = 10;
const MAX_LIMIT = 200;

async function adjustThrottleLimits() {
  const p95 = await getMetric('http_request_duration_seconds', { quantile: 0.95 });
  const errorRate = await getMetric('http_error_rate_percent');

  if (p95 > 1.0 || errorRate > 5) {
    currentLimit = Math.max(MIN_LIMIT, Math.floor(currentLimit * 0.8));
    logger.warn(`Throttle tightened to ${currentLimit} (p95=${p95}s, errors=${errorRate}%)`);
  } else if (p95 < 0.3 && errorRate < 1) {
    currentLimit = Math.min(MAX_LIMIT, Math.floor(currentLimit * 1.1));
    logger.info(`Throttle relaxed to ${currentLimit}`);
  }
}

setInterval(adjustThrottleLimits, 10000); // Adjust every 10s

function adaptiveThrottle(req, res, next) {
  return concurrencyLimiter(currentLimit)(req, res, next);
}
```

## Graceful Degradation

```javascript
const degradationStrategies = {
  // Serve cached response when throttled
  cached: async (req, res) => {
    const cached = await redis.get(`cache:${req.path}`);
    if (cached) {
      res.set('X-Degraded', 'cached');
      return res.json(JSON.parse(cached));
    }
    return res.status(503).json({ detail: 'Service temporarily unavailable' });
  },

  // Return partial results
  partial: async (req, res) => {
    const partial = await db.query('SELECT id, name FROM users LIMIT 10');
    res.set('X-Degraded', 'partial');
    return res.json({ data: partial, partial: true, detail: 'Partial results due to high load' });
  },

  // Queue for later processing
  queued: async (req, res) => {
    const jobId = await queue.add(req.body);
    return res.status(202).json({ jobId, statusUrl: `/jobs/${jobId}` });
  },
};
```

## Throttle State Headers

```javascript
function throttleHeaders(req, res, next) {
  res.set('X-Throttle-Limit', String(currentLimit));
  res.set('X-Throttle-Remaining', String(Math.max(0, currentLimit - inFlight)));
  res.set('X-Throttle-Reset', String(Math.ceil(Date.now() / 1000) + 10));
  next();
}
```

## Load Test Verification

```bash
# Verify throttle engages at threshold
k6 run --env BASE_URL=http://localhost:3000 - <<'EOF'
import http from 'k6/http';
import { check } from 'k6';

export const options = {
  stages: [
    { duration: '30s', target: 50 },
    { duration: '30s', target: 200 },  // Exceed throttle
    { duration: '30s', target: 50 },   // Recovery
  ],
};

export default function () {
  const res = http.get(`${__ENV.BASE_URL}/api/reports/generate`);
  check(res, {
    'not throttled or 503': (r) => [200, 503].includes(r.status),
    'has retry-after on 503': (r) => r.status !== 503 || r.headers['Retry-After'],
  });
}
EOF
```

## curl: Throttle Behavior

```bash
# Normal request
curl -i http://localhost:3000/api/reports/generate
# X-Throttle-Limit: 100
# X-Throttle-Remaining: 95

# Under heavy load
curl -i http://localhost:3000/api/reports/generate
# 503 Service Unavailable
# Retry-After: 5
# {"title":"Service Unavailable","detail":"Max concurrent requests (10) reached"}

# Degraded response
curl -i http://localhost:3000/api/users
# X-Degraded: partial
# {"data":[...],"partial":true}
```

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
