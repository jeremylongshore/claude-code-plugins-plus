---
name: coreweave-webhooks-events
description: |
  Monitor CoreWeave cluster events and GPU workload status.
  Use when tracking pod lifecycle events, monitoring GPU utilization,
  or alerting on inference service health changes.
  Trigger with phrases like "coreweave events", "coreweave monitoring",
  "coreweave pod alerts", "coreweave gpu monitoring".
allowed-tools: Read, Write, Edit, Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, gpu-cloud, kubernetes, inference, coreweave]
compatible-with: claude-code
---

# CoreWeave Webhooks & Events

## Overview
CoreWeave emits Kubernetes-native events and custom status callbacks for GPU workload lifecycle management. Monitor instance readiness, job completion, volume attachment, and node health to build automated scaling, alerting, and recovery pipelines for GPU-accelerated inference and training workloads.

## Webhook Registration
```typescript
const response = await fetch("https://api.coreweave.com/v1/webhooks", {
  method: "POST",
  headers: {
    "Authorization": `Bearer ${process.env.COREWEAVE_API_KEY}`,
    "Content-Type": "application/json",
  },
  body: JSON.stringify({
    url: "https://yourapp.com/webhooks/coreweave",
    events: ["instance.ready", "job.completed", "volume.attached", "node.unhealthy"],
    secret: process.env.COREWEAVE_WEBHOOK_SECRET,
  }),
});
```

## Signature Verification
```typescript
import crypto from "crypto";
import { Request, Response, NextFunction } from "express";

function verifyCoreWeaveSignature(req: Request, res: Response, next: NextFunction) {
  const signature = req.headers["x-coreweave-signature"] as string;
  const timestamp = req.headers["x-coreweave-timestamp"] as string;
  const payload = `${timestamp}.${req.body.toString()}`;
  const expected = crypto.createHmac("sha256", process.env.COREWEAVE_WEBHOOK_SECRET!)
    .update(payload).digest("hex");
  if (!crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected))) {
    return res.status(401).json({ error: "Invalid signature" });
  }
  next();
}
```

## Event Handler
```typescript
import express from "express";
const app = express();

app.post("/webhooks/coreweave", express.raw({ type: "application/json" }), verifyCoreWeaveSignature, (req, res) => {
  const event = JSON.parse(req.body.toString());
  res.status(200).json({ received: true });

  switch (event.type) {
    case "instance.ready":
      registerEndpoint(event.data.instance_id, event.data.gpu_type); break;
    case "job.completed":
      collectArtifacts(event.data.job_id, event.data.output_path); break;
    case "volume.attached":
      mountStorage(event.data.volume_id, event.data.node_name); break;
    case "node.unhealthy":
      drainAndReschedule(event.data.node_id, event.data.reason); break;
  }
});
```

## Event Types
| Event | Payload Fields | Use Case |
|-------|---------------|----------|
| `instance.ready` | `instance_id`, `gpu_type`, `ip_address` | Register inference endpoint |
| `job.completed` | `job_id`, `output_path`, `duration_seconds` | Collect training artifacts |
| `volume.attached` | `volume_id`, `node_name`, `mount_path` | Confirm storage availability |
| `node.unhealthy` | `node_id`, `reason`, `gpu_count` | Drain node and reschedule pods |
| `instance.terminated` | `instance_id`, `exit_code`, `gpu_type` | Clean up resources and alert |

## Retry & Idempotency
```typescript
const processed = new Set<string>();

async function handleIdempotent(event: { id: string; type: string; data: any }) {
  if (processed.has(event.id)) return;
  await routeEvent(event);
  processed.add(event.id);
  if (processed.size > 10_000) {
    const entries = Array.from(processed);
    entries.slice(0, entries.length - 10_000).forEach((id) => processed.delete(id));
  }
}
```

## Error Handling
| Issue | Cause | Fix |
|-------|-------|-----|
| Signature mismatch | Clock skew between clusters | Validate timestamp within 5-minute window |
| Duplicate `instance.ready` | Rescheduled pod on same node | Track instance IDs for deduplication |
| Stale `node.unhealthy` | Transient GPU memory error | Wait for consecutive events before draining |
| Missing `output_path` | Job failed before writing | Check `exit_code` before collecting artifacts |

## Resources
- [CoreWeave Kubernetes Docs](https://docs.coreweave.com/coreweave-kubernetes/)

## Next Steps
See `coreweave-security-basics`.
