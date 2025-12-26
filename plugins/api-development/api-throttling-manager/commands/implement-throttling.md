---
name: implement-throttling
description: Implement API throttling and quotas
shortcut: thro
---
# Implement API Throttling

Implement sophisticated API throttling with dynamic rate limits, quota management, tiered pricing, and advanced traffic control strategies to ensure fair usage and optimal performance.

## When to Use This Command

Use `/implement-throttling` when you need to:
- Protect APIs from abuse and overload
- Implement usage-based billing and quotas
- Provide differentiated service tiers (free/premium)
- Ensure fair resource allocation among users
- Prevent cascade failures from traffic spikes
- Comply with third-party API rate limits

DON'T use this when:
- Building internal-only APIs with trusted clients (may be overkill)
- Prototype or MVP phase (premature optimization)
- Already using API gateway with throttling (avoid duplication)

## Design Decisions

This command implements **Token Bucket + Sliding Window** as the primary approach because:
- Allows burst traffic while maintaining overall limits
- Provides smooth rate limiting without hard cutoffs
- Memory-efficient for high-traffic scenarios
- Supports dynamic rate adjustment
- Works well with distributed systems
- Industry-proven algorithm combination

**Alternative considered: Fixed Window**
- Simpler implementation
- Susceptible to thundering herd at window boundaries
- Less smooth traffic distribution
- Recommended for simple use cases

**Alternative considered: Leaky Bucket**
- Constant output rate
- Better for streaming scenarios
- Less flexible for burst traffic
- Recommended for bandwidth limiting

## Prerequisites

Before running this command:
1. Define rate limit tiers and quotas
2. Choose storage backend (Redis recommended)
3. Determine billing/pricing model if applicable
4. Plan graceful degradation strategy
5. Set up monitoring and alerting

## Implementation Process

### Step 1: Configure Rate Limit Storage
Set up Redis or similar for distributed rate limit tracking.

### Step 2: Implement Throttling Algorithms
Deploy token bucket and sliding window algorithms with configurable parameters.

### Step 3: Create Middleware
Build middleware for automatic rate limit enforcement.

### Step 4: Add Usage Tracking
Implement detailed usage tracking for analytics and billing.

### Step 5: Set Up Management API
Create API for managing rate limits, quotas, and user tiers.

## Output Format

The command generates:
- `middleware/rate-limiter.js` - Core throttling middleware
- `services/throttling-manager.js` - Rate limit management service
- `models/usage-tracking.js` - Usage data models
- `config/rate-limits.json` - Tier configurations
- `api/rate-limit-api.js` - Management endpoints
- `monitoring/throttling-metrics.js` - Prometheus metrics

## Code Examples

### Example 1: Advanced Token Bucket + Sliding Window Implementation

```javascript
// services/throttling-manager.js
const Redis = require('ioredis');
const crypto = require('crypto');

class ThrottlingManager {
  constructor(redisClient = new Redis()) {
    this.redis = redisClient;
    this.tiers = {
      free: {
        rateLimit: 100,        // requests per hour
        burst: 10,             // burst allowance
        dailyQuota: 1000,      // daily limit
        monthlyQuota: 10000,   // monthly limit
        priority: 1            // queue priority (lower = higher priority)
      },
      basic: {
        rateLimit: 1000,
        burst: 50,
        dailyQuota: 10000,
        monthlyQuota: 250000,
        priority: 2
      },
      premium: {
        rateLimit: 10000,
        burst: 200,
        dailyQuota: 100000,
        monthlyQuota: 3000000,
        priority: 3
      },
      enterprise: {
        rateLimit: -1,         // unlimited rate
        burst: 1000,
        dailyQuota: -1,        // unlimited daily
        monthlyQuota: -1,      // unlimited monthly
        priority: 4
      }
    };
  }

  async checkRateLimit(userId, tier = 'free', weight = 1) {
    const config = this.tiers[tier];
    if (!config) {
      throw new Error(`Unknown tier: ${tier}`);
    }

    // Skip rate limiting for unlimited tiers
    if (config.rateLimit === -1) {
      return {
        allowed: true,
        limit: -1,
        remaining: -1,
        resetAt: null
      };
    }

    // Token bucket algorithm
    const tokenBucket = await this.checkTokenBucket(
      userId,
      config.rateLimit,
      config.burst,
      weight
    );

    if (!tokenBucket.allowed) {
      return tokenBucket;
    }

    // Check quotas
    const quotaCheck = await this.checkQuotas(userId, config, weight);

    return quotaCheck.allowed ? tokenBucket : quotaCheck;
  }

  async checkTokenBucket(userId, limit, burst, weight) {
    const now = Date.now();
    const window = 3600000; // 1 hour in ms
    const key = `throttle:bucket:${userId}`;

    // Lua script for atomic token bucket
    const luaScript = `
      local key = KEYS[1]
      local limit = tonumber(ARGV[1])
      local burst = tonumber(ARGV[2])
      local weight = tonumber(ARGV[3])
      local now = tonumber(ARGV[4])
      local window = tonumber(ARGV[5])

      local bucket = redis.call('HMGET', key, 'tokens', 'last_refill')
      local tokens = tonumber(bucket[1]) or limit
      local last_refill = tonumber(bucket[2]) or now

      -- Calculate tokens to add based on time passed
      local time_passed = now - last_refill
      local tokens_to_add = (time_passed / window) * limit
      tokens = math.min(tokens + tokens_to_add, limit + burst)

      -- Check if request can be served
      if tokens >= weight then
        tokens = tokens - weight
        redis.call('HMSET', key, 'tokens', tokens, 'last_refill', now)
        redis.call('EXPIRE', key, window / 1000)
        return {1, math.floor(tokens), now + (window * weight / limit)}
      else
        local wait_time = ((weight - tokens) * window) / limit
        return {0, math.floor(tokens), now + wait_time}
      end
    `;

    const result = await this.redis.eval(
      luaScript,
      1,
      key,
      limit,
      burst,
      weight,
      now,
      window
    );

    return {
      allowed: result[0] === 1,
      limit: limit,
      remaining: result[1],
      resetAt: new Date(result[2])
    };
  }

  async checkQuotas(userId, config, weight) {
    const now = new Date();
    const dailyKey = `quota:daily:${userId}:${this.getDayKey(now)}`;
    const monthlyKey = `quota:monthly:${userId}:${this.getMonthKey(now)}`;

    // Check daily quota
    if (config.dailyQuota > 0) {
      const dailyUsage = await this.redis.incrby(dailyKey, 0);
      if (dailyUsage + weight > config.dailyQuota) {
        return {
          allowed: false,
          limit: config.dailyQuota,
          remaining: Math.max(0, config.dailyQuota - dailyUsage),
          resetAt: this.getNextDay(now),
          reason: 'Daily quota exceeded'
        };
      }
    }

    // Check monthly quota
    if (config.monthlyQuota > 0) {
      const monthlyUsage = await this.redis.incrby(monthlyKey, 0);
      if (monthlyUsage + weight > config.monthlyQuota) {
        return {
          allowed: false,
          limit: config.monthlyQuota,
          remaining: Math.max(0, config.monthlyQuota - monthlyUsage),
          resetAt: this.getNextMonth(now),
          reason: 'Monthly quota exceeded'
        };
      }
    }

    // Increment quotas
    const pipeline = this.redis.pipeline();
    if (config.dailyQuota > 0) {
      pipeline.incrby(dailyKey, weight);
      pipeline.expire(dailyKey, 86400); // 24 hours
    }
    if (config.monthlyQuota > 0) {
      pipeline.incrby(monthlyKey, weight);
      pipeline.expire(monthlyKey, 2592000); // 30 days
    }
    await pipeline.exec();

    return {
      allowed: true,
      limit: config.dailyQuota,
      remaining: Math.max(0, config.dailyQuota - (await this.redis.get(dailyKey) || 0)),
      resetAt: this.getNextDay(now)
    };
  }

  async getUsageStats(userId) {
    const now = new Date();
    const dailyKey = `quota:daily:${userId}:${this.getDayKey(now)}`;
    const monthlyKey = `quota:monthly:${userId}:${this.getMonthKey(now)}`;
    const bucketKey = `throttle:bucket:${userId}`;

    const [dailyUsage, monthlyUsage, bucket] = await Promise.all([
      this.redis.get(dailyKey),
      this.redis.get(monthlyKey),
      this.redis.hgetall(bucketKey)
    ]);

    return {
      daily: {
        used: parseInt(dailyUsage) || 0,
        resetAt: this.getNextDay(now)
      },
      monthly: {
        used: parseInt(monthlyUsage) || 0,
        resetAt: this.getNextMonth(now)
      },
      rateLimit: {
        tokens: parseFloat(bucket.tokens) || 0,
        lastRefill: bucket.last_refill ? new Date(parseInt(bucket.last_refill)) : null
      }
    };
  }

  async resetUserLimits(userId, type = 'all') {
    const keys = [];

    if (type === 'all' || type === 'rate') {
      keys.push(`throttle:bucket:${userId}`);
    }
    if (type === 'all' || type === 'daily') {
      keys.push(`quota:daily:${userId}:${this.getDayKey(new Date())}`);
    }
    if (type === 'all' || type === 'monthly') {
      keys.push(`quota:monthly:${userId}:${this.getMonthKey(new Date())}`);
    }

    if (keys.length > 0) {
      await this.redis.del(...keys);
    }
  }

  getDayKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  getMonthKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;
  }

  getNextDay(date) {
    const tomorrow = new Date(date);
    tomorrow.setDate(tomorrow.getDate() + 1);
    tomorrow.setHours(0, 0, 0, 0);
    return tomorrow;
  }

  getNextMonth(date) {
    const nextMonth = new Date(date);
    nextMonth.setMonth(nextMonth.getMonth() + 1);
    nextMonth.setDate(1);
    nextMonth.setHours(0, 0, 0, 0);
    return nextMonth;
  }
}

// middleware/rate-limiter.js
const ThrottlingManager = require('../services/throttling-manager');

function createRateLimitMiddleware(options = {}) {
  const throttling = new ThrottlingManager(options.redis);
  const {
    keyGenerator = (req) => req.user?.id || req.ip,
    tierResolver = (req) => req.user?.tier || 'free',
    weightResolver = (req) => 1,
    skipRoutes = [],
    onLimitExceeded = null
  } = options;

  return async function rateLimitMiddleware(req, res, next) {
    // Skip rate limiting for excluded routes
    if (skipRoutes.includes(req.path)) {
      return next();
    }

    const userId = keyGenerator(req);
    const tier = await tierResolver(req);
    const weight = weightResolver(req);

    try {
      const result = await throttling.checkRateLimit(userId, tier, weight);

      // Set rate limit headers
      res.set({
        'X-RateLimit-Limit': result.limit,
        'X-RateLimit-Remaining': result.remaining,
        'X-RateLimit-Reset': result.resetAt ? result.resetAt.toISOString() : ''
      });

      if (!result.allowed) {
        // Custom handler for rate limit exceeded
        if (onLimitExceeded) {
          return onLimitExceeded(req, res, result);
        }

        // Default response
        return res.status(429).json({
          error: 'Rate limit exceeded',
          message: result.reason || 'Too many requests',
          retryAfter: result.resetAt ? Math.ceil((result.resetAt - Date.now()) / 1000) : 60
        });
      }

      // Track usage for analytics
      req.rateLimitInfo = result;
      next();
    } catch (error) {
      console.error('Rate limiting error:', error);
      // Fail open - allow request if rate limiting fails
      next();
    }
  };
}

// Usage
const express = require('express');
const app = express();

app.use(createRateLimitMiddleware({
  redis: new Redis({
    host: 'localhost',
    port: 6379
  }),
  keyGenerator: (req) => {
    // Use API key if available, otherwise IP
    return req.headers['x-api-key'] || req.ip;
  },
  tierResolver: async (req) => {
    // Look up user tier from database
    if (req.headers['x-api-key']) {
      const user = await getUserByApiKey(req.headers['x-api-key']);
      return user?.tier || 'free';
    }
    return 'free';
  },
  weightResolver: (req) => {
    // Different weights for different operations
    const weights = {
      'GET': 1,
      'POST': 2,
      'PUT': 2,
      'DELETE': 3
    };
    return weights[req.method] || 1;
  },
  onLimitExceeded: (req, res, result) => {
    // Custom handling - maybe queue the request
    console.log(`Rate limit exceeded for ${req.ip}: ${result.reason}`);
    res.status(429).json({
      error: 'Rate limit exceeded',
      upgrade: 'Consider upgrading to premium for higher limits',
      resetAt: result.resetAt
    });
  }
}));
```

### Example 2: Distributed Rate Limiting with Priority Queues

```javascript
// services/priority-queue-throttler.js
const Bull = require('bull');
const Redis = require('ioredis');

class PriorityQueueThrottler {
  constructor(options = {}) {
    this.redis = options.redis || new Redis();
    this.queues = new Map();
    this.processors = new Map();
    this.config = {
      maxConcurrent: options.maxConcurrent || 100,
      processingTimeout: options.processingTimeout || 30000,
      retryAttempts: options.retryAttempts || 3
    };

    // Initialize priority queues
    this.initializeQueues();
  }

  initializeQueues() {
    const priorities = ['critical', 'high', 'normal', 'low'];

    priorities.forEach(priority => {
      const queue = new Bull(`api-requests-${priority}`, {
        redis: this.redis,
        defaultJobOptions: {
          removeOnComplete: true,
          removeOnFail: false,
          attempts: this.config.retryAttempts,
          backoff: {
            type: 'exponential',
            delay: 2000
          }
        }
      });

      this.queues.set(priority, queue);

      // Set up queue processor
      queue.process(this.config.maxConcurrent, async (job) => {
        return await this.processRequest(job.data);
      });

      // Queue event handlers
      queue.on('completed', (job, result) => {
        console.log(`Request ${job.id} completed with priority ${priority}`);
      });

      queue.on('failed', (job, err) => {
        console.error(`Request ${job.id} failed:`, err);
      });
    });
  }

  async queueRequest(request, priority = 'normal') {
    const queue = this.queues.get(priority);
    if (!queue) {
      throw new Error(`Invalid priority: ${priority}`);
    }

    // Check if user has too many pending requests
    const pendingCount = await this.getPendingCount(request.userId);
    const maxPending = this.getMaxPending(request.tier);

    if (pendingCount >= maxPending) {
      throw new Error('Too many pending requests');
    }

    // Add request to queue with priority
    const job = await queue.add(request, {
      priority: this.getPriorityValue(priority),
      delay: this.calculateDelay(request.tier, pendingCount)
    });

    // Store job info for tracking
    await this.redis.setex(
      `job:${job.id}`,
      3600,
      JSON.stringify({
        userId: request.userId,
        priority,
        createdAt: Date.now()
      })
    );

    return {
      jobId: job.id,
      position: await this.getQueuePosition(job.id, priority),
      estimatedTime: await this.estimateProcessingTime(priority)
    };
  }

  async processRequest(request) {
    const startTime = Date.now();

    try {
      // Simulate API processing
      const result = await this.executeApiRequest(request);

      // Record metrics
      await this.recordMetrics({
        userId: request.userId,
        duration: Date.now() - startTime,
        success: true
      });

      return result;
    } catch (error) {
      await this.recordMetrics({
        userId: request.userId,
        duration: Date.now() - startTime,
        success: false,
        error: error.message
      });

      throw error;
    }
  }

  async getPendingCount(userId) {
    const priorities = ['critical', 'high', 'normal', 'low'];
    let total = 0;

    for (const priority of priorities) {
      const queue = this.queues.get(priority);
      const jobs = await queue.getJobs(['waiting', 'active']);
      total += jobs.filter(job => job.data.userId === userId).length;
    }

    return total;
  }

  getMaxPending(tier) {
    const limits = {
      free: 5,
      basic: 20,
      premium: 50,
      enterprise: 200
    };
    return limits[tier] || 5;
  }

  getPriorityValue(priority) {
    const values = {
      critical: 1,
      high: 2,
      normal: 3,
      low: 4
    };
    return values[priority] || 3;
  }

  calculateDelay(tier, pendingCount) {
    // Add progressive delay based on pending requests
    const baseDelay = {
      free: 1000,
      basic: 500,
      premium: 100,
      enterprise: 0
    };

    const delay = baseDelay[tier] || 1000;
    return delay * Math.max(1, pendingCount / 2);
  }

  async getQueuePosition(jobId, priority) {
    const queue = this.queues.get(priority);
    const jobs = await queue.getJobs(['waiting']);
    const position = jobs.findIndex(job => job.id === jobId);
    return position + 1;
  }

  async estimateProcessingTime(priority) {
    const queue = this.queues.get(priority);
    const [waiting, active] = await Promise.all([
      queue.getWaitingCount(),
      queue.getActiveCount()
    ]);

    const avgProcessingTime = 500; // ms per request
    const totalPending = waiting + active;
    const estimatedMs = (totalPending * avgProcessingTime) / this.config.maxConcurrent;

    return Math.ceil(estimatedMs / 1000); // Return in seconds
  }

  async recordMetrics(metrics) {
    const key = `metrics:${metrics.userId}:${this.getDayKey(new Date())}`;

    await this.redis.hincrby(key, metrics.success ? 'success' : 'failed', 1);
    await this.redis.hincrby(key, 'total_duration', metrics.duration);
    await this.redis.expire(key, 86400); // Keep for 24 hours
  }

  async executeApiRequest(request) {
    // Simulate actual API request processing
    return new Promise((resolve) => {
      setTimeout(() => {
        resolve({
          success: true,
          data: request.data,
          processedAt: Date.now()
        });
      }, Math.random() * 1000);
    });
  }

  getDayKey(date) {
    return `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}-${String(date.getDate()).padStart(2, '0')}`;
  }

  async getQueueStats() {
    const stats = {};

    for (const [priority, queue] of this.queues) {
      const [waiting, active, completed, failed] = await Promise.all([
        queue.getWaitingCount(),
        queue.getActiveCount(),
        queue.getCompletedCount(),
        queue.getFailedCount()
      ]);

      stats[priority] = {
        waiting,
        active,
        completed,
        failed
      };
    }

    return stats;
  }
}

// API for queue management
const express = require('express');
const router = express.Router();
const throttler = new PriorityQueueThrottler();

router.post('/api/queue', async (req, res) => {
  try {
    const priority = req.user?.tier === 'enterprise' ? 'high' : 'normal';

    const result = await throttler.queueRequest({
      userId: req.user?.id || req.ip,
      tier: req.user?.tier || 'free',
      data: req.body
    }, priority);

    res.status(202).json({
      message: 'Request queued',
      ...result
    });
  } catch (error) {
    res.status(429).json({
      error: error.message
    });
  }
});

router.get('/api/queue/:jobId/status', async (req, res) => {
  // Get job status
  const job = await queue.getJob(req.params.jobId);

  if (!job) {
    return res.status(404).json({ error: 'Job not found' });
  }

  res.json({
    id: job.id,
    status: await job.getState(),
    progress: job.progress(),
    result: job.returnvalue,
    failedReason: job.failedReason
  });
});

module.exports = router;
```

### Example 3: Adaptive Rate Limiting with Machine Learning

```python
# adaptive_throttling.py
import time
import numpy as np
from sklearn.linear_model import LinearRegression
from collections import deque
import redis
import json
from datetime import datetime, timedelta

class AdaptiveThrottling:
    """
    Machine learning-based adaptive rate limiting that adjusts
    limits based on system performance and user behavior.
    """

    def __init__(self, redis_client=None):
        self.redis = redis_client or redis.Redis()
        self.performance_history = deque(maxlen=1000)
        self.model = LinearRegression()
        self.base_limits = {
            'free': 100,
            'basic': 500,
            'premium': 2000,
            'enterprise': 10000
        }
        self.initialize_model()

    def initialize_model(self):
        """Initialize ML model with synthetic training data."""
        # Features: [hour_of_day, day_of_week, current_load, user_history]
        X_train = np.random.rand(100, 4) * [24, 7, 1, 100]
        # Target: optimal rate limit multiplier
        y_train = 1 + 0.5 * np.sin(X_train[:, 0] * np.pi / 12) + np.random.rand(100) * 0.2
        self.model.fit(X_train, y_train)

    def calculate_dynamic_limit(self, user_id, tier):
        """Calculate adaptive rate limit based on current conditions."""
        base_limit = self.base_limits.get(tier, 100)

        # Get current system metrics
        features = self.extract_features(user_id)

        # Predict optimal multiplier
        multiplier = self.model.predict([features])[0]
        multiplier = max(0.5, min(2.0, multiplier))  # Bound between 0.5x and 2x

        # Apply multiplier to base limit
        dynamic_limit = int(base_limit * multiplier)

        # Store decision for analysis
        self.redis.setex(
            f"adaptive:decision:{user_id}",
            3600,
            json.dumps({
                'base': base_limit,
                'multiplier': multiplier,
                'dynamic': dynamic_limit,
                'timestamp': time.time()
            })
        )

        return dynamic_limit

    def extract_features(self, user_id):
        """Extract features for ML model."""
        now = datetime.now()

        # Time-based features
        hour_of_day = now.hour
        day_of_week = now.weekday()

        # System load (simplified - would use actual metrics)
        current_load = self.get_system_load()

        # User behavior history
        user_history = self.get_user_history(user_id)

        return [hour_of_day, day_of_week, current_load, user_history]

    def get_system_load(self):
        """Get current system load (0-1 scale)."""
        # Simplified - would use actual CPU/memory metrics
        total_requests = self.redis.get("system:requests:current")
        max_capacity = 10000
        return min(1.0, float(total_requests or 0) / max_capacity)

    def get_user_history(self, user_id):
        """Get user's historical usage pattern."""
        history_key = f"user:history:{user_id}"
        history = self.redis.lrange(history_key, 0, -1)

        if not history:
            return 50  # Default neutral score

        # Calculate average request rate
        rates = [float(r) for r in history]
        return np.mean(rates[-10:])  # Last 10 data points

    def update_model(self):
        """Update ML model based on recent performance data."""
        if len(self.performance_history) < 100:
            return

        # Prepare training data from performance history
        X = []
        y = []

        for entry in self.performance_history:
            X.append(entry['features'])
            # Target is based on whether system performed well
            y.append(entry['performance_score'])

        # Retrain model
        self.model.fit(X, y)

        print(f"Model updated with {len(X)} samples")

    def record_performance(self, features, performance_metrics):
        """Record system performance for model updates."""
        performance_score = self.calculate_performance_score(performance_metrics)

        self.performance_history.append({
            'features': features,
            'performance_score': performance_score,
            'timestamp': time.time()
        })

        # Periodically update model
        if len(self.performance_history) % 100 == 0:
            self.update_model()

    def calculate_performance_score(self, metrics):
        """Calculate performance score from metrics."""
        # Weighted scoring based on multiple factors
        score = 0.0
        score += 0.3 * (1 - metrics.get('error_rate', 0))
        score += 0.3 * (1 - min(1, metrics.get('latency', 0) / 1000))
        score += 0.2 * (1 - metrics.get('rejection_rate', 0))
        score += 0.2 * metrics.get('throughput', 0) / 1000

        return max(0, min(1, score))

# Integration with Express.js via subprocess
if __name__ == "__main__":
    import sys

    adaptive = AdaptiveThrottling()

    # Read request from stdin
    request = json.loads(sys.stdin.read())

    # Calculate dynamic limit
    limit = adaptive.calculate_dynamic_limit(
        request['userId'],
        request['tier']
    )

    # Return result
    print(json.dumps({'limit': limit}))
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| "Redis connection failed" | Redis server down | Implement fallback to local memory |
| "Rate limit exceeded" | Too many requests | Implement retry with backoff |
| "Invalid tier" | Unknown subscription tier | Use default tier as fallback |
| "Queue overflow" | Too many pending requests | Increase queue capacity or reject requests |
| "Quota calculation error" | Time sync issues | Ensure NTP synchronization |

## Configuration Options

**Rate Limiting Algorithms**
- `token-bucket`: Allows burst traffic
- `sliding-window`: Smooth rate distribution
- `fixed-window`: Simple time-based limits
- `leaky-bucket`: Constant output rate

**Storage Backends**
- `redis`: Recommended for distributed systems
- `memory`: For single-server deployments
- `dynamodb`: For serverless architectures
- `postgresql`: For persistent quota tracking

## Best Practices

DO:
- Use distributed storage for multi-server deployments
- Implement graceful degradation when limits are reached
- Provide clear error messages with retry information
- Monitor rate limit effectiveness
- Adjust limits based on actual usage patterns
- Implement different weights for different operations

DON'T:
- Use only client-side rate limiting
- Ignore time synchronization issues
- Set limits too restrictive initially
- Forget to handle rate limiter failures
- Apply same limits to all operations

## Performance Considerations

- Use Lua scripts for atomic Redis operations
- Implement connection pooling for Redis
- Cache tier information to reduce lookups
- Use sliding window for better distribution
- Consider read-heavy vs write-heavy operations

## Monitoring and Analytics

```javascript
// monitoring/throttling-metrics.js
const promClient = require('prom-client');

// Metrics
const rateLimitHits = new promClient.Counter({
  name: 'rate_limit_hits_total',
  help: 'Total number of rate limited requests',
  labelNames: ['tier', 'reason']
});

const quotaUsage = new promClient.Gauge({
  name: 'quota_usage_ratio',
  help: 'Current quota usage ratio',
  labelNames: ['user_id', 'quota_type']
});

const requestsQueued = new promClient.Gauge({
  name: 'requests_queued',
  help: 'Number of requests in queue',
  labelNames: ['priority']
});
```

## Related Commands

- `/api-rate-limiter` - Basic rate limiting implementation
- `/api-monitoring-dashboard` - Monitor throttling metrics
- `/api-billing-system` - Usage-based billing
- `/api-gateway-builder` - Gateway-level throttling

## Version History

- v1.0.0 (2024-10): Initial implementation with token bucket and quotas
- Planned v1.1.0: Add machine learning-based adaptive throttling