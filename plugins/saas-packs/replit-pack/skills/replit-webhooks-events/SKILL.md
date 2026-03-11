---
name: replit-webhooks-events
description: |
  Implement Replit webhook signature validation and event handling.
  Use when setting up webhook endpoints, implementing signature verification,
  or handling Replit event notifications securely.
  Trigger with phrases like "replit webhook", "replit events",
  "replit webhook signature", "handle replit events", "replit notifications".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Replit Webhooks & Events

## Overview
Handle Replit deployment and workspace events for CI/CD integration. Replit provides deployment hooks and the Replit Extensions API for responding to workspace changes, deployment status updates, and collaboration events.

## Prerequisites
- Replit account with Deployments enabled (Replit Core or Teams)
- Replit API token stored in `REPLIT_TOKEN` environment variable
- HTTPS endpoint for receiving deployment notifications
- Understanding of Replit deployment types (Static, Autoscale, Reserved VM)

## Event Types

| Event | Trigger | Payload |
|-------|---------|---------|
| `deployment.started` | Deploy begins | Repl ID, deployment type |
| `deployment.succeeded` | Deploy completes | Deployment URL, build logs |
| `deployment.failed` | Deploy errors | Error message, build output |
| `deployment.promoted` | Staging to prod | Deployment ID, environment |
| `repl.forked` | Repl forked | Source repl, fork owner |
| `health_check.failed` | Health endpoint down | Deployment ID, response code |

## Instructions

### Step 1: Configure Deployment Webhook
```typescript
import express from "express";

const app = express();
app.use(express.json());

app.post("/webhooks/replit", async (req, res) => {
  const token = req.headers["x-replit-token"] as string;

  if (token !== process.env.REPLIT_WEBHOOK_SECRET) {
    return res.status(401).json({ error: "Unauthorized" });  # HTTP 401 Unauthorized
  }

  const { event, data, timestamp } = req.body;
  res.status(200).json({ received: true });  # HTTP 200 OK

  await handleReplitEvent(event, data);
});

async function handleReplitEvent(event: string, data: any) {
  switch (event) {
    case "deployment.succeeded":
      await handleDeploySuccess(data);
      break;
    case "deployment.failed":
      await handleDeployFailure(data);
      break;
    case "health_check.failed":
      await handleHealthCheckFailure(data);
      break;
  }
}
```

### Step 2: Process Deployment Events
```typescript
async function handleDeploySuccess(data: any) {
  const { replId, deploymentUrl, buildDuration, deploymentType } = data;

  console.log(`Deployment successful: ${deploymentUrl} (${buildDuration}s)`);

  // Run post-deploy smoke tests
  const healthCheck = await fetch(`${deploymentUrl}/health`);
  const isHealthy = healthCheck.ok;

  await slackNotify("#deployments", {
    text: `Replit deploy complete\nURL: ${deploymentUrl}\nType: ${deploymentType}\nHealth: ${isHealthy ? "OK" : "FAILING"}`,
  });
}

async function handleDeployFailure(data: any) {
  const { replId, error, buildOutput } = data;

  console.error(`Deployment failed for ${replId}: ${error}`);

  await alerting.createIncident({
    title: `Replit deployment failed: ${replId}`,
    severity: "high",
    details: buildOutput,
  });
}
```

### Step 3: Monitor Deployment Health
```typescript
async function handleHealthCheckFailure(data: any) {
  const { deploymentId, statusCode, responseTime } = data;

  const failures = await getRecentFailures(deploymentId);

  if (failures.length >= 3) {
    console.log(`Rolling back deployment ${deploymentId}`);
    await rollbackDeployment(deploymentId);
  }
}

async function rollbackDeployment(deploymentId: string) {
  const response = await fetch(
    `https://api.replit.com/v1/deployments/${deploymentId}/rollback`,
    {
      method: "POST",
      headers: { "Authorization": `Bearer ${process.env.REPLIT_TOKEN}` },
    }
  );
  return response.json();
}
```

### Step 4: Deploy via API
```bash
set -euo pipefail
# Trigger deployment via Replit API
curl -X POST https://api.replit.com/v1/repls/$REPL_ID/deploy \
  -H "Authorization: Bearer $REPLIT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{"type": "autoscale", "webhook_url": "https://api.yourapp.com/webhooks/replit"}'
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Deploy timeout | Large dependencies | Optimize package.json, use .replit config |
| Health check fails | Wrong port | Verify internal port matches .replit config |
| Webhook not received | Network issue | Check Replit firewall and endpoint accessibility |
| Build failure | Missing env vars | Set secrets in Replit Secrets tab |

## Examples

### Deployment Status Dashboard
```typescript
async function getDeploymentHistory(replId: string) {
  const response = await fetch(
    `https://api.replit.com/v1/repls/${replId}/deployments`,
    { headers: { "Authorization": `Bearer ${process.env.REPLIT_TOKEN}` } }
  );
  return response.json();
}
```

## Resources
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Replit API Reference](https://docs.replit.com/api)
- [Replit Extensions](https://docs.replit.com/extensions)

## Next Steps
For multi-environment setup, see `replit-multi-env-setup`.

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale