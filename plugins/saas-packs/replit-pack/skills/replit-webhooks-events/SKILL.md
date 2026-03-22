---
name: replit-webhooks-events
description: |
  Handle Replit deployment events, build Replit Extensions, and set up Agents & Automations.
  Use when integrating with Replit deployment lifecycle, building workspace extensions,
  or creating automated workflows with Replit Agent.
  Trigger with phrases like "replit webhook", "replit events", "replit extension",
  "replit automation", "replit notifications", "replit agent automation".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, replit, webhooks, extensions, automation]

---
# Replit Webhooks & Events

## Overview
Integrate with Replit's event ecosystem: deployment lifecycle hooks, Replit Extensions API for workspace customization, and Agents & Automations for scheduled tasks and chatbots. Also covers external webhook endpoints hosted on Replit.

## Prerequisites
- Replit account with Deployments enabled (Core or Teams)
- For Extensions: familiarity with React and TypeScript
- For Automations: Replit Agent access

## Instructions

### Step 1: Deployment Lifecycle Monitoring
Monitor deployment events by polling or building a status dashboard:

```typescript
// src/deploy-monitor.ts — Track deployment health
import express from 'express';

const app = express();
app.use(express.json());

// Health endpoint that deployment monitoring can ping
app.get('/health', async (req, res) => {
  res.json({
    status: 'healthy',
    environment: process.env.REPL_SLUG,
    region: process.env.REPLIT_DEPLOYMENT_REGION,
    deployedAt: process.env.REPLIT_DEPLOYMENT_TIMESTAMP || 'unknown',
    uptime: process.uptime(),
  });
});

// Post-deploy smoke test endpoint
app.get('/api/readiness', async (req, res) => {
  const checks = {
    database: await checkDB(),
    storage: await checkStorage(),
    secrets: checkSecrets(),
  };

  const allHealthy = Object.values(checks).every(Boolean);
  res.status(allHealthy ? 200 : 503).json({ ready: allHealthy, checks });
});

async function checkDB(): Promise<boolean> {
  try {
    const { Pool } = await import('pg');
    const pool = new Pool({ connectionString: process.env.DATABASE_URL });
    await pool.query('SELECT 1');
    await pool.end();
    return true;
  } catch { return false; }
}

async function checkStorage(): Promise<boolean> {
  try {
    const { Client } = await import('@replit/object-storage');
    const storage = new Client();
    await storage.list({ maxResults: 1 });
    return true;
  } catch { return false; }
}

function checkSecrets(): boolean {
  const required = ['DATABASE_URL', 'JWT_SECRET'];
  return required.every(k => !!process.env[k]);
}
```

### Step 2: External Webhook Receiver
Host webhook endpoints on Replit to receive events from external services:

```typescript
// src/webhooks.ts — Receive webhooks from GitHub, Stripe, etc.
import express from 'express';
import crypto from 'crypto';

const router = express.Router();

// Webhook signature verification
function verifySignature(
  payload: string,
  signature: string,
  secret: string
): boolean {
  const expected = crypto
    .createHmac('sha256', secret)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(signature),
    Buffer.from(`sha256=${expected}`)
  );
}

// GitHub webhook receiver
router.post('/webhooks/github', express.raw({ type: '*/*' }), (req, res) => {
  const signature = req.headers['x-hub-signature-256'] as string;
  const secret = process.env.GITHUB_WEBHOOK_SECRET!;

  if (!verifySignature(req.body.toString(), signature, secret)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = req.headers['x-github-event'] as string;
  const payload = JSON.parse(req.body.toString());

  // Respond immediately, process async
  res.status(200).json({ received: true });

  handleGitHubEvent(event, payload).catch(console.error);
});

async function handleGitHubEvent(event: string, payload: any) {
  switch (event) {
    case 'push':
      console.log(`Push to ${payload.ref} by ${payload.pusher.name}`);
      // Replit auto-syncs from connected GitHub — no manual deploy needed
      break;
    case 'pull_request':
      console.log(`PR #${payload.number}: ${payload.action}`);
      break;
    case 'issues':
      console.log(`Issue #${payload.issue.number}: ${payload.action}`);
      break;
  }
}

// Generic webhook receiver
router.post('/webhooks/:service', express.json(), (req, res) => {
  const { service } = req.params;
  console.log(`Webhook from ${service}:`, JSON.stringify(req.body).slice(0, 200));
  res.status(200).json({ received: true });
});

export default router;
```

### Step 3: Replit Extensions
Build custom IDE extensions that integrate into the Replit Workspace:

```typescript
// Extension entry point — React-based UI panel
import { useReplitClient } from '@replit/extensions-react';

function MyExtension() {
  const { data: files, error } = useReplitClient().fs.readDir('/');

  if (error) return <div>Error: {error.message}</div>;

  return (
    <div>
      <h2>Project Files</h2>
      <ul>
        {files?.map(f => <li key={f.path}>{f.path}</li>)}
      </ul>
    </div>
  );
}

// Extensions can access:
// - File system (read/write files)
// - Theme (match Replit's UI)
// - Database (Replit DB)
// - User info
// Each tab has isolated permissions
```

```markdown
Publishing an Extension:
1. Create Extension from template (Extensions > Build)
2. Develop in the provided Repl workspace
3. Test with the Extensions DevTools
4. Release on the Extensions Store (public or private)
```

### Step 4: Agents & Automations (Beta)
Create automated workflows using natural language:

```markdown
Replit Agents & Automations can:
- Run on a schedule (cron-like)
- Respond to Slack/Telegram messages
- Process incoming webhooks
- Execute database queries automatically

Setup:
1. Open your Repl > Automations tab
2. Create new automation:
   - Trigger: Schedule (e.g., "every day at 9am")
   - Action: Natural language instruction
     "Query the database for users who signed up yesterday,
      format as CSV, and send to Slack #new-users channel"
3. Test and activate

Example automations:
- Daily database backup to Object Storage
- Slack bot that queries your app's API
- Scheduled data cleanup (delete old records)
- Webhook-to-Slack notification bridge
```

### Step 5: Deployment Event Notifications
Set up external monitoring for deployment status changes:

```typescript
// src/deploy-notifier.ts — Notify team on deployment events
async function notifySlack(message: string) {
  const webhookUrl = process.env.SLACK_WEBHOOK_URL;
  if (!webhookUrl) return;

  await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ text: message }),
  });
}

// Call after successful startup
const startTime = Date.now();
app.listen(PORT, '0.0.0.0', async () => {
  const bootTime = ((Date.now() - startTime) / 1000).toFixed(1);
  await notifySlack(
    `Deployment started: ${process.env.REPL_SLUG}\n` +
    `Boot time: ${bootTime}s\n` +
    `URL: https://${process.env.REPL_SLUG}.replit.app`
  );
});

// Graceful shutdown notification
process.on('SIGTERM', async () => {
  await notifySlack(`Deployment stopping: ${process.env.REPL_SLUG}`);
  process.exit(0);
});
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Webhook not received | Repl sleeping | Use Deployments for always-on |
| Signature verification fails | Wrong secret | Verify secret matches provider config |
| Extension not loading | API version mismatch | Update `@replit/extensions-react` |
| Automation not triggering | Schedule syntax error | Verify cron expression in automation settings |
| Webhook timeout | Processing too slow | Respond 200 immediately, process async |

## Resources
- [Replit Extensions](https://docs.replit.com/extensions/)
- [Replit Extensions API](https://docs.replit.com/extensions/extensions)
- [Replit Deployments](https://docs.replit.com/hosting/deployments)
- [Monitoring Deployments](https://docs.replit.com/cloud-services/deployments/monitoring-a-deployment)

## Next Steps
For multi-environment setup, see `replit-multi-env-setup`.
