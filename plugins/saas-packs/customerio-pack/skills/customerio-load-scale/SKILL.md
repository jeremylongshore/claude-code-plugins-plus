---
name: customerio-load-scale
description: |
  Implement Customer.io load testing and horizontal scaling.
  Use when preparing for high traffic, running load tests,
  or designing queue-based architectures for scale.
  Trigger: "customer.io load test", "customer.io scale",
  "customer.io high volume", "customer.io k6", "customer.io performance test".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(kubectl:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, load-testing, scaling, performance]

---
# Customer.io Load & Scale

## Overview

Load testing and scaling strategies for high-volume Customer.io integrations: k6 load test scripts, scaling architecture selection based on volume tier, Kubernetes HPA autoscaling, message queue buffering, and rate-limit-aware batch processing.

## Scaling Architecture by Volume

| Daily Events | Architecture | Key Components |
|-------------|--------------|----------------|
| < 100K | Direct API | Singleton client, retry, connection pooling |
| 100K - 1M | Batched API | Event queue, batch processor, rate limiter |
| 1M - 10M | Queue-backed | Redis/Kafka queue, worker pool, backpressure |
| > 10M | Distributed | Multiple workspaces, sharded queues, regional routing |

Customer.io rate limit is ~100 req/sec per workspace. Plan your architecture around this.

## Instructions

### Step 1: k6 Load Test Script

```javascript
// load-tests/customerio.js
// Run: k6 run --vus 10 --duration 60s load-tests/customerio.js
import http from "k6/http";
import { check, sleep } from "k6";
import { Counter, Trend } from "k6/metrics";

const SITE_ID = __ENV.CUSTOMERIO_SITE_ID;
const API_KEY = __ENV.CUSTOMERIO_TRACK_API_KEY;
const BASE_URL = "https://track.customer.io/api/v1";
const AUTH = `${SITE_ID}:${API_KEY}`;

const identifyLatency = new Trend("cio_identify_latency");
const trackLatency = new Trend("cio_track_latency");
const errors = new Counter("cio_errors");

export const options = {
  scenarios: {
    identify_load: {
      executor: "ramping-arrival-rate",
      startRate: 10,
      timeUnit: "1s",
      preAllocatedVUs: 20,
      maxVUs: 50,
      stages: [
        { duration: "30s", target: 50 },   // Ramp to 50/sec
        { duration: "60s", target: 80 },   // Hold at 80/sec (near limit)
        { duration: "30s", target: 10 },   // Cool down
      ],
    },
  },
  thresholds: {
    cio_identify_latency: ["p(95)<500", "p(99)<2000"],
    cio_track_latency: ["p(95)<500", "p(99)<2000"],
    cio_errors: ["count<50"],
  },
};

export default function () {
  const userId = `k6-load-${__VU}-${__ITER}`;
  const headers = {
    "Content-Type": "application/json",
    Authorization: `Basic ${encoding.b64encode(AUTH)}`,
  };

  // Identify
  const identifyRes = http.put(
    `${BASE_URL}/customers/${userId}`,
    JSON.stringify({
      email: `${userId}@loadtest.example.com`,
      _load_test: true,
      created_at: Math.floor(Date.now() / 1000),
    }),
    { headers }
  );

  identifyLatency.add(identifyRes.timings.duration);
  check(identifyRes, { "identify 200": (r) => r.status === 200 }) || errors.add(1);

  // Track event
  const trackRes = http.post(
    `${BASE_URL}/customers/${userId}/events`,
    JSON.stringify({
      name: "load_test_event",
      data: { iteration: __ITER, vu: __VU },
    }),
    { headers }
  );

  trackLatency.add(trackRes.timings.duration);
  check(trackRes, { "track 200": (r) => r.status === 200 }) || errors.add(1);

  sleep(0.1); // Small delay between iterations
}

// Cleanup function — suppress test users after test
export function teardown() {
  console.log("Load test complete. Clean up k6-load-* users in CIO dashboard.");
}
```

Run:
```bash
k6 run --env CUSTOMERIO_SITE_ID="$CUSTOMERIO_SITE_ID" \
       --env CUSTOMERIO_TRACK_API_KEY="$CUSTOMERIO_TRACK_API_KEY" \
       load-tests/customerio.js
```

### Step 2: Queue-Based Architecture

```typescript
// services/cio-queue-worker.ts
import { Queue, Worker, QueueEvents } from "bullmq";
import { TrackClient, RegionUS } from "customerio-node";
import Bottleneck from "bottleneck";

const REDIS_URL = process.env.REDIS_URL ?? "redis://localhost:6379";

// Rate limiter: 80 requests per second (leave headroom under 100/sec limit)
const limiter = new Bottleneck({
  maxConcurrent: 15,
  reservoir: 80,
  reservoirRefreshAmount: 80,
  reservoirRefreshInterval: 1000,
});

const eventQueue = new Queue("cio:events", {
  connection: { url: REDIS_URL },
  defaultJobOptions: {
    attempts: 5,
    backoff: { type: "exponential", delay: 2000 },
    removeOnComplete: { count: 10000 },
    removeOnFail: { count: 50000 },
  },
});

// Producer — your application enqueues events here
export async function enqueueEvent(
  type: "identify" | "track",
  userId: string,
  data: Record<string, any>
): Promise<void> {
  await eventQueue.add(type, { userId, data, enqueuedAt: Date.now() });
}

// Consumer — workers process events with rate limiting
export function startEventWorkers(concurrency = 10): void {
  const cio = new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    { region: RegionUS }
  );

  const worker = new Worker(
    "cio:events",
    async (job) => {
      await limiter.schedule(async () => {
        if (job.name === "identify") {
          await cio.identify(job.data.userId, job.data.data);
        } else {
          await cio.track(job.data.userId, job.data.data);
        }
      });
    },
    {
      connection: { url: REDIS_URL },
      concurrency,
    }
  );

  worker.on("failed", (job, err) => {
    console.error(`CIO event failed: ${job?.id} — ${err.message}`);
  });

  // Monitor queue health
  const events = new QueueEvents("cio:events", {
    connection: { url: REDIS_URL },
  });

  setInterval(async () => {
    const counts = await eventQueue.getJobCounts();
    console.log(
      `CIO queue: waiting=${counts.waiting} active=${counts.active} ` +
      `failed=${counts.failed} completed=${counts.completed}`
    );
  }, 30000);
}
```

### Step 3: Kubernetes HPA Autoscaling

```yaml
# k8s/hpa.yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: cio-worker-hpa
spec:
  scaleTargetRef:
    apiVersion: apps/v1
    kind: Deployment
    name: cio-event-worker
  minReplicas: 2
  maxReplicas: 20
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
    - type: Pods
      pods:
        metric:
          name: cio_queue_depth
        target:
          type: AverageValue
          averageValue: "500"
  behavior:
    scaleUp:
      stabilizationWindowSeconds: 60
      policies:
        - type: Pods
          value: 4
          periodSeconds: 60
    scaleDown:
      stabilizationWindowSeconds: 300
      policies:
        - type: Pods
          value: 2
          periodSeconds: 120
```

### Step 4: Batch Sender for Bulk Operations

```typescript
// lib/cio-batch-sender.ts
import { TrackClient, RegionUS } from "customerio-node";
import Bottleneck from "bottleneck";

export async function batchSend(
  operations: Array<{
    type: "identify" | "track";
    userId: string;
    data: Record<string, any>;
  }>,
  ratePerSec = 80
): Promise<{ succeeded: number; failed: number }> {
  const cio = new TrackClient(
    process.env.CUSTOMERIO_SITE_ID!,
    process.env.CUSTOMERIO_TRACK_API_KEY!,
    { region: RegionUS }
  );

  const limiter = new Bottleneck({
    maxConcurrent: 15,
    reservoir: ratePerSec,
    reservoirRefreshAmount: ratePerSec,
    reservoirRefreshInterval: 1000,
  });

  let succeeded = 0;
  let failed = 0;

  const promises = operations.map((op, i) =>
    limiter.schedule(async () => {
      try {
        if (op.type === "identify") {
          await cio.identify(op.userId, op.data);
        } else {
          await cio.track(op.userId, op.data);
        }
        succeeded++;
      } catch {
        failed++;
      }
      if ((succeeded + failed) % 1000 === 0) {
        console.log(`Progress: ${succeeded + failed}/${operations.length}`);
      }
    })
  );

  await Promise.all(promises);
  return { succeeded, failed };
}
```

Install: `npm install bottleneck bullmq`

## Load Test Checklist

- [ ] Test against staging workspace (NEVER production)
- [ ] Start at 10% of target rate, ramp up gradually
- [ ] Monitor 429 error rate during test
- [ ] Check Customer.io dashboard for processing lag
- [ ] Verify cleanup of test users after load test
- [ ] Document baseline latency and throughput numbers
- [ ] Set up alerts before running at production scale

## Error Handling

| Issue | Solution |
|-------|----------|
| 429 during load test | Reduce rate, check limiter config |
| Queue backlog growing | Scale workers, increase concurrency |
| Memory pressure | Limit batch and queue sizes, enable GC |
| k6 VU exhaustion | Increase `preAllocatedVUs` and `maxVUs` |

## Resources

- [k6 Documentation](https://k6.io/docs/)
- [Bottleneck npm](https://www.npmjs.com/package/bottleneck)
- [BullMQ Documentation](https://bullmq.io/)
- [Kubernetes HPA](https://kubernetes.io/docs/tasks/run-application/horizontal-pod-autoscale/)

## Next Steps

After load testing, proceed to `customerio-known-pitfalls` for anti-patterns to avoid.
