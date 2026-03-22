---
name: lindy-install-auth
description: |
  Set up Lindy AI account, API access, and webhook authentication.
  Use when onboarding to Lindy, configuring API keys for webhook triggers,
  or connecting Lindy agents to your application.
  Trigger with phrases like "install lindy", "setup lindy",
  "lindy auth", "configure lindy API key", "lindy webhook secret".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, lindy, api, authentication]

---
# Lindy Install & Auth

## Overview
Lindy AI is a no-code/low-code AI agent platform. Agents ("Lindies") are built in the
web dashboard at https://app.lindy.ai. External integration uses webhook endpoints,
the HTTP Request action, and optional Node.js/Python SDKs for programmatic access.

## Prerequisites
- Lindy account at https://app.lindy.ai (Free tier: 400 credits/month)
- For SDK access: Node.js 18+ or Python 3.10+
- For webhook receivers: HTTPS endpoint in your application

## Instructions

### Step 1: Obtain API Key
1. Log in at https://app.lindy.ai
2. Navigate to **Settings > API Keys**
3. Click **Generate New Key** — copy immediately (shown only once)
4. Store securely:
```bash
# Environment variable
export LINDY_API_KEY="lnd_live_xxxxxxxxxxxxxxxxxxxx"

# Or .env file (add .env to .gitignore)
echo 'LINDY_API_KEY=lnd_live_xxxxxxxxxxxxxxxxxxxx' >> .env
```

### Step 2: Install SDK (Optional)
```bash
# Node.js SDK
npm install lindy-ai

# Python SDK
pip install lindy-ai
```

### Step 3: Initialize Client
```typescript
// Node.js
import { Lindy } from 'lindy-ai';

const lindy = new Lindy({
  apiKey: process.env.LINDY_API_KEY,
});

// Verify connection
const agents = await lindy.agents.list();
console.log(`Connected: ${agents.length} agents found`);
```

```python
# Python
import os
from lindy import Lindy

client = Lindy(api_key=os.environ["LINDY_API_KEY"])

# Verify connection
agents = client.agents.list()
print(f"Connected: {len(agents)} agents found")
```

### Step 4: Configure Webhook Authentication
When creating a webhook trigger in the Lindy dashboard, generate a secret key.
Callers must include this in every request:

```
Authorization: Bearer <your-webhook-secret>
```

Your webhook endpoint URL follows the pattern:
```
https://public.lindy.ai/api/v1/webhooks/<unique-id>
```

### Step 5: Verify Webhook Connectivity
```bash
# Test your webhook trigger
curl -X POST "https://public.lindy.ai/api/v1/webhooks/YOUR_WEBHOOK_ID" \
  -H "Authorization: Bearer YOUR_SECRET" \
  -H "Content-Type: application/json" \
  -d '{"test": true, "message": "hello from setup"}'
```

## Lindy Plans & Credits

| Plan | Price | Credits/mo | Tasks | Extras |
|------|-------|-----------|-------|--------|
| Free | $0 | 400 | ~40 | Basic models |
| Pro | $49.99/mo | 5,000 | ~1,500 | +$19.99/seat, phone calls |
| Business | $299.99/mo | 30,000 | ~3,000 | 100 phone calls, 50M KB chars |
| Enterprise | Custom | Custom | Custom | SSO, SCIM, RBAC, audit logs |

Credit consumption: 1-3 credits on basic models, ~10 on large models per task.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Settings > API Keys |
| `403 Forbidden` | Key lacks required scope | Check plan tier supports API access |
| `429 Too Many Requests` | Credit limit exceeded | Upgrade plan or wait for monthly reset |
| `Webhook 401` | Missing/wrong Bearer token | Verify secret matches dashboard value |
| `ECONNREFUSED` | Lindy API unreachable | Check https://status.lindy.ai |

## Security Checklist
- [ ] API key stored in env var or secret manager — never in source code
- [ ] `.env` added to `.gitignore`
- [ ] Webhook secret generated and stored securely
- [ ] HTTPS enforced on all webhook receiver endpoints
- [ ] API key scoped to minimum required permissions

## Resources
- [Lindy Documentation](https://docs.lindy.ai)
- [Lindy Dashboard](https://app.lindy.ai)
- [Lindy Academy](https://www.lindy.ai/academy-lessons/getting-started-101)
- [Lindy Status](https://status.lindy.ai)

## Next Steps
After successful auth, proceed to `lindy-hello-world` for your first AI agent.
