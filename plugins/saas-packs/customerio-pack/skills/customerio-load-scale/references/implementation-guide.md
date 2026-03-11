# Customer.io Load & Scale - Implementation Guide

## Load Test Script (k6)

```javascript
// load-tests/customerio.js
import http from 'k6/http';
import { check, sleep } from 'k6';
import { Rate, Trend } from 'k6/metrics';

const errorRate = new Rate('errors');
const identifyDuration = new Trend('identify_duration');
const trackDuration = new Trend('track_duration');

const BASE_URL = 'https://track.customer.io/api/v1';
const AUTH = __ENV.CUSTOMERIO_AUTH; // base64(site_id:api_key)

export const options = {
  scenarios: {
    identify_load: {
      executor: 'ramping-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      stages: [
        { target: 50, duration: '1m' },
        { target: 100, duration: '2m' },
        { target: 100, duration: '5m' },
        { target: 0, duration: '1m' },
      ],
      exec: 'identifyScenario',
    },
    track_load: {
      executor: 'ramping-rate',
      startRate: 10,
      timeUnit: '1s',
      preAllocatedVUs: 50,
      stages: [
        { target: 50, duration: '1m' },
        { target: 100, duration: '2m' },
        { target: 100, duration: '5m' },
        { target: 0, duration: '1m' },
      ],
      exec: 'trackScenario',
    },
  },
  thresholds: {
    'errors': ['rate<0.01'],
    'identify_duration': ['p95<500'],
    'track_duration': ['p95<500'],
  },
};

export function identifyScenario() {
  const userId = `load-test-${__VU}-${__ITER}`;
  const payload = JSON.stringify({
    email: `${userId}@loadtest.com`,
    _load_test: true,
    created_at: Math.floor(Date.now() / 1000),
  });

  const start = new Date();
  const res = http.post(
    `${BASE_URL}/customers/${userId}`,
    payload,
    {
      headers: {
        'Authorization': `Basic ${AUTH}`,
        'Content-Type': 'application/json',
      },
    }
  );
  identifyDuration.add(new Date() - start);

  const success = check(res, {
    'identify status is 200': (r) => r.status === 200,
  });
  errorRate.add(!success);

  sleep(0.1);
}

export function trackScenario() {
  const userId = `load-test-${__VU}-${__ITER}`;
  const payload = JSON.stringify({
    name: 'load_test_event',
    data: {
      source: 'k6',
      timestamp: new Date().toISOString(),
    },
  });

  const start = new Date();
  const res = http.post(
    `${BASE_URL}/customers/${userId}/events`,
    payload,
    {
      headers: {
        'Authorization': `Basic ${AUTH}`,
        'Content-Type': 'application/json',
      },
    }
  );
  trackDuration.add(new Date() - start);

  const success = check(res, {
    'track status is 200': (r) => r.status === 200,
  });
  errorRate.add(!success);

  sleep(0.1);
}
```

## Horizontal Scaling (Kubernetes)

```yaml
# k8s/scaled-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: customerio-worker
spec:
  replicas: 3
  selector:
    matchLabels:
      app: customerio-worker
  template:
    metadata:
      labels:
        app: customerio-worker
    spec:
      containers:
        - name: worker
          image: customerio-worker:latest
          resources:
            requests:
              cpu: "500m"
              memory: "256Mi"
            limits:
              cpu: "1000m"
              memory: "512Mi"
          env:
            - name: CONCURRENCY
              value: "10"
---
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: customerio-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: customerio-worker
  minReplicas: 3
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: External
      external:
        metric:
          name: pubsub.googleapis.com|subscription|num_undelivered_messages
          selector:
            matchLabels:
              resource.labels.subscription_id: customerio-events
        target:
          type: AverageValue
          averageValue: 1000
```

## Message Queue Architecture (Kafka)

```typescript
// lib/scaled-processor.ts
import { Kafka, Consumer, EachMessagePayload } from 'kafkajs';
import { TrackClient, RegionUS } from '@customerio/track';

const kafka = new Kafka({
  clientId: 'customerio-worker',
  brokers: process.env.KAFKA_BROKERS!.split(',')
});

const consumer = kafka.consumer({
  groupId: 'customerio-workers',
  sessionTimeout: 30000,
  heartbeatInterval: 3000
});

const client = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_API_KEY!,
  { region: RegionUS }
);

interface CustomerIOEvent {
  type: 'identify' | 'track';
  userId: string;
  payload: any;
}

async function processMessage(message: EachMessagePayload): Promise<void> {
  const event: CustomerIOEvent = JSON.parse(message.message.value!.toString());

  if (event.type === 'identify') {
    await client.identify(event.userId, event.payload);
  } else if (event.type === 'track') {
    await client.track(event.userId, {
      name: event.payload.event,
      data: event.payload.properties
    });
  }
}

async function start(): Promise<void> {
  await consumer.connect();
  await consumer.subscribe({ topic: 'customerio-events', fromBeginning: false });

  await consumer.run({
    partitionsConsumedConcurrently: 10,
    eachMessage: async (payload) => {
      try {
        await processMessage(payload);
      } catch (error) {
        console.error('Processing error:', error);
        // Dead letter or retry logic
      }
    }
  });
}

start().catch(console.error);
```

## Rate Limiter

```typescript
// lib/rate-limiter.ts
import Bottleneck from 'bottleneck';

// Respect Customer.io's 100 req/sec limit
// Leave headroom for other services
const limiter = new Bottleneck({
  reservoir: 80, // 80 tokens
  reservoirRefreshAmount: 80,
  reservoirRefreshInterval: 1000, // per second
  maxConcurrent: 20,
  minTime: 10 // Minimum 10ms between requests
});

limiter.on('depleted', () => {
  console.warn('Rate limiter depleted, requests queued');
});

limiter.on('error', (error) => {
  console.error('Rate limiter error:', error);
});

export async function rateLimitedIdentify(
  client: TrackClient,
  userId: string,
  attributes: Record<string, any>
): Promise<void> {
  return limiter.schedule(() => client.identify(userId, attributes));
}

export async function rateLimitedTrack(
  client: TrackClient,
  userId: string,
  event: string,
  data?: Record<string, any>
): Promise<void> {
  return limiter.schedule(() =>
    client.track(userId, { name: event, data })
  );
}

export function getLimiterStats() {
  return {
    running: limiter.running(),
    queued: limiter.queued(),
    done: limiter.done(),
    reservoir: limiter.reservoir
  };
}
```

## Batch Processing

```typescript
// lib/batch-sender.ts
interface BatchConfig {
  maxBatchSize: number;
  maxWaitMs: number;
  concurrency: number;
}

class BatchSender {
  private batch: Array<{ userId: string; operation: 'identify' | 'track'; data: any }> = [];
  private timer: NodeJS.Timer | null = null;
  private processing = false;

  constructor(
    private client: TrackClient,
    private config: BatchConfig = { maxBatchSize: 100, maxWaitMs: 1000, concurrency: 10 }
  ) {}

  add(userId: string, operation: 'identify' | 'track', data: any): void {
    this.batch.push({ userId, operation, data });

    if (this.batch.length >= this.config.maxBatchSize) {
      this.flush();
    } else if (!this.timer) {
      this.timer = setTimeout(() => this.flush(), this.config.maxWaitMs);
    }
  }

  async flush(): Promise<void> {
    if (this.processing || this.batch.length === 0) return;

    if (this.timer) {
      clearTimeout(this.timer);
      this.timer = null;
    }

    this.processing = true;
    const items = this.batch.splice(0, this.config.maxBatchSize);

    for (let i = 0; i < items.length; i += this.config.concurrency) {
      const chunk = items.slice(i, i + this.config.concurrency);
      await Promise.allSettled(chunk.map(item => this.processItem(item)));
    }

    this.processing = false;
  }

  private async processItem(item: { userId: string; operation: string; data: any }): Promise<void> {
    if (item.operation === 'identify') {
      await this.client.identify(item.userId, item.data);
    } else {
      await this.client.track(item.userId, {
        name: item.data.event,
        data: item.data.properties
      });
    }
  }
}
```

## Load Test Execution Script

```bash
#!/bin/bash
# scripts/run-load-test.sh

# Set credentials
export CUSTOMERIO_AUTH=$(echo -n "$CIO_SITE_ID:$CIO_API_KEY" | base64)

# Run k6 load test
k6 run \
  --out json=results.json \
  --out influxdb=http://localhost:8086/k6 \
  load-tests/customerio.js

# Generate report
k6 run --summary-export=summary.json load-tests/customerio.js

echo "Load test complete. Results in results.json"
```

## Capacity Planning Reference

### Rate Limits
| Endpoint | Limit | Notes |
|----------|-------|-------|
| Track API (identify/track) | 100 req/sec | Per workspace |
| App API (transactional) | 100 req/sec | Per workspace |
| Webhooks (outbound) | Varies | Based on plan |

### Scaling Targets
| Volume | Architecture | Notes |
|--------|--------------|-------|
| < 1M events/day | Single service | Direct API calls |
| 1-10M events/day | Queue-based | Message queue buffer |
| > 10M events/day | Distributed | Multiple workers |
