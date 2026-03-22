---
name: castai-webhooks-events
description: |
  Configure CAST AI webhook notifications for cluster events and audit logs.
  Use when setting up alerts for node scaling, cost threshold events,
  or integrating CAST AI events with Slack, PagerDuty, or custom endpoints.
  Trigger with phrases like "cast ai webhooks", "cast ai notifications",
  "cast ai slack alerts", "cast ai events".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, kubernetes, cost-optimization, castai]
compatible-with: claude-code
---

# CAST AI Webhooks & Events

## Overview

CAST AI emits events for node lifecycle changes, autoscaler decisions, and security findings. Configure webhook endpoints or use the audit log API to track all cluster operations. Integrates with Slack, PagerDuty, and custom HTTP endpoints.

## Prerequisites

- CAST AI cluster connected and active
- HTTPS endpoint for receiving webhooks (or Slack webhook URL)
- API key with Full Access

## Instructions

### Step 1: Configure Notification Channels in Console

Navigate to console.cast.ai > your cluster > Notifications. Available channels:

- **Slack**: Webhook URL integration
- **Email**: Per-user notifications
- **PagerDuty**: Incident escalation
- **Custom webhook**: Any HTTPS endpoint

### Step 2: Query Audit Log via API

```bash
# Get recent cluster operations
curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
  "https://api.cast.ai/v1/kubernetes/clusters/${CASTAI_CLUSTER_ID}/audit-log?limit=20" \
  | jq '.items[] | {
    time: .createdAt,
    action: .action,
    initiator: .initiatedBy,
    details: .details
  }'
```

### Step 3: Build a Custom Notification Handler

```typescript
// castai-webhook-handler.ts
import express from "express";

const app = express();
app.use(express.json());

interface CastAIEvent {
  eventType: string;
  clusterId: string;
  clusterName: string;
  timestamp: string;
  data: {
    nodeName?: string;
    instanceType?: string;
    lifecycle?: string;
    action?: string;
    savingsImpact?: number;
  };
}

app.post("/castai/events", async (req, res) => {
  const event: CastAIEvent = req.body;

  switch (event.eventType) {
    case "node.added":
      console.log(
        `Node added: ${event.data.nodeName} (${event.data.instanceType}, ${event.data.lifecycle})`
      );
      await notifySlack(
        `New ${event.data.lifecycle} node: ${event.data.instanceType}`
      );
      break;

    case "node.removed":
      console.log(`Node removed: ${event.data.nodeName}`);
      break;

    case "node.spot_interrupted":
      console.log(`Spot interruption: ${event.data.nodeName}`);
      await notifyPagerDuty("Spot instance interrupted", event);
      break;

    case "savings.threshold":
      console.log(`Savings threshold crossed: ${event.data.savingsImpact}%`);
      break;

    default:
      console.log(`Unhandled event: ${event.eventType}`);
  }

  res.status(200).json({ received: true });
});

async function notifySlack(message: string): Promise<void> {
  await fetch(process.env.SLACK_WEBHOOK_URL!, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({
      text: `:kubernetes: CAST AI: ${message}`,
    }),
  });
}

app.listen(3000, () => console.log("CAST AI webhook handler on :3000"));
```

### Step 4: Kubernetes-Native Event Monitoring

```bash
# Watch CAST AI events in the cluster
kubectl get events -n castai-agent --watch \
  --field-selector=source=castai

# Or use a CronJob to post daily summaries
```

```yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: castai-daily-summary
spec:
  schedule: "0 9 * * *"
  jobTemplate:
    spec:
      template:
        spec:
          containers:
            - name: summary
              image: curlimages/curl
              command:
                - sh
                - -c
                - |
                  SAVINGS=$(curl -s -H "X-API-Key: ${CASTAI_API_KEY}" \
                    "https://api.cast.ai/v1/kubernetes/clusters/${CLUSTER_ID}/savings")
                  curl -X POST ${SLACK_WEBHOOK_URL} \
                    -H "Content-Type: application/json" \
                    -d "{\"text\": \"Daily CAST AI savings: $(echo $SAVINGS | jq -r '.monthlySavings') USD/month\"}"
          restartPolicy: Never
```

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not firing | Wrong URL in console | Verify endpoint is reachable |
| Slack message empty | Payload format changed | Check current event schema |
| Duplicate events | No idempotency | Track event IDs in your handler |
| Events delayed | Queue backlog | Monitor CAST AI status page |

## Resources

- [CAST AI Notifications](https://docs.cast.ai/docs/getting-started)
- [CAST AI API Reference](https://api.cast.ai/v1/spec/openapi.json)

## Next Steps

For performance optimization, see `castai-performance-tuning`.
