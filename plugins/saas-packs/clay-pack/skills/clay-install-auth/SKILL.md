---
name: clay-install-auth
description: |
  Set up Clay account access, API keys, webhook URLs, and provider connections.
  Use when onboarding to Clay, connecting data providers, configuring API keys,
  or setting up webhook endpoints for programmatic data flow.
  Trigger with phrases like "install clay", "setup clay", "clay auth",
  "configure clay API key", "connect clay providers".
allowed-tools: Read, Write, Edit, Bash(curl:*), Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, clay, api, authentication]

---
# Clay Install & Auth

## Overview

Clay is a web-based data enrichment platform — there is no SDK to install. Integration happens through webhook URLs (inbound data), HTTP API enrichment columns (outbound calls from Clay), and the Enterprise API (programmatic people/company lookups). This skill covers account setup, API key management, provider connections, and webhook configuration.

## Prerequisites

- Clay account at [clay.com](https://www.clay.com) (free tier available)
- For Enterprise API: Enterprise plan subscription
- For webhook integration: HTTPS endpoint or tunneling tool (ngrok)

## Instructions

### Step 1: Get Your Clay API Key (Enterprise Only)

Navigate to **Settings > API** in your Clay workspace. Copy your API key. Clay's Enterprise API is limited to people and company data lookups — it is not a general-purpose table API.

```bash
# Store your Clay API key securely
export CLAY_API_KEY="clay_ent_your_api_key_here"

# Verify with a test lookup (Enterprise API)
curl -s -X POST "https://api.clay.com/v1/people/enrich" \
  -H "Authorization: Bearer $CLAY_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"email": "test@example.com"}' | jq .
```

### Step 2: Configure Webhook Inbound Source

Every Clay table can receive data via a unique webhook URL. This is the primary way to send data into Clay programmatically.

1. Open a Clay workbook (or create one)
2. Click **+ Add** at the bottom of the table
3. Search for **Webhooks** and click **Monitor webhook**
4. Copy the generated webhook URL

```bash
# Store your table's webhook URL
export CLAY_WEBHOOK_URL="https://app.clay.com/api/v1/webhooks/your-unique-id"

# Send a test record to your Clay table
curl -X POST "$CLAY_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "email": "jane@acme.com",
    "first_name": "Jane",
    "last_name": "Doe",
    "company": "Acme Corp",
    "title": "VP of Sales"
  }'
```

The record appears as a new row in your Clay table within seconds.

### Step 3: Connect Data Provider API Keys

Clay supports 150+ enrichment providers. Connecting your own API keys saves 70-80% on Clay credits.

1. Go to **Settings > Connections** in Clay
2. Click **Add Connection** for each provider
3. Paste your API key

**Common providers to connect:**

| Provider | Key Location | Credit Savings |
|----------|-------------|----------------|
| Apollo.io | Settings > API Keys | 2 credits/lookup saved |
| Clearbit | Dashboard > API | 2-5 credits saved |
| People Data Labs | Dashboard > API Keys | 3 credits saved |
| Hunter.io | Dashboard > API | 2 credits saved |
| ZoomInfo | Admin > API | 5-13 credits saved |
| Prospeo | Dashboard > API Key | 2 credits saved |

When you use your own API keys, **0 Clay credits** are consumed — credits only apply when using Clay's managed provider accounts.

### Step 4: Create .env for Local Integration Code

```bash
# .env — for local scripts that interact with Clay
CLAY_API_KEY=clay_ent_your_key          # Enterprise API (if applicable)
CLAY_WEBHOOK_URL=https://app.clay.com/api/v1/webhooks/abc123  # Table webhook
CLAY_WORKSPACE_ID=ws_your_workspace     # Found in Settings > Workspace

# Provider keys (optional — for direct provider calls outside Clay)
APOLLO_API_KEY=your_apollo_key
CLEARBIT_API_KEY=your_clearbit_key
HUNTER_API_KEY=your_hunter_key
```

### Step 5: Verify Webhook Authentication

Secure your webhook endpoint with a shared secret in the header:

```bash
# Send authenticated webhook data
curl -X POST "$CLAY_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -H "X-Webhook-Secret: your-shared-secret" \
  -d '{"email": "test@acme.com", "source": "auth-verification"}'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `401 Unauthorized` | Invalid or expired API key | Regenerate key in Settings > API |
| `403 Forbidden` | Feature not on your plan | Enterprise API requires Enterprise plan |
| `422 Unprocessable` | Malformed webhook payload | Ensure valid JSON with Content-Type header |
| `429 Too Many Requests` | Explorer plan: 400 records/hour | Throttle webhook submissions or upgrade |
| Webhook URL expired | Table deleted or webhook limit hit | Create new webhook (50K submission limit per webhook) |
| Provider connection failed | Invalid third-party API key | Verify key in provider's own dashboard |

## Output

- Clay workspace configured with API access
- Webhook URL ready to receive programmatic data
- Provider API keys connected for credit savings
- `.env` file with all required credentials

## Resources

- [Clay University — HTTP API Overview](https://university.clay.com/docs/http-api-integration-overview)
- [Clay University — Webhook Integration Guide](https://university.clay.com/docs/webhook-integration-guide)
- [Clay Plans & Billing](https://university.clay.com/docs/plans-and-billing)

## Next Steps

After auth setup, proceed to `clay-hello-world` to send your first enrichment through Clay.
