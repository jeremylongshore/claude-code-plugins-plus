---
name: notion-security-basics
description: |
  Apply Notion API security best practices for integration tokens, OAuth2 flows,
  least-privilege capabilities, and page-level access control.
  Use when securing integration tokens, configuring OAuth2 for public integrations,
  rotating credentials, or auditing which pages an integration can access.
  Trigger with phrases like "notion security", "notion secrets",
  "secure notion", "notion API key security", "notion token rotation",
  "notion OAuth2", "notion permissions audit".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, notion]
compatible-with: claude-code
---

# Notion Security Basics

## Overview

Security fundamentals for the Notion API: integration token management, internal vs public integration models, principle of least privilege for capabilities, page-level access auditing, token rotation, OAuth2 flows for public integrations, and webhook verification. All examples use `@notionhq/client` v2.x and target the `2022-06-28` API version.

## Prerequisites

- Notion integration created at [notion.so/my-integrations](https://www.notion.so/my-integrations)
- Node.js 18+ with `@notionhq/client` installed (`npm install @notionhq/client`)
- Understanding of environment variables and `.env` file patterns
- For public integrations: OAuth2 client ID and secret from the integration dashboard

## Instructions

### Step 1: Secure Token Storage and `.env` Management

Integration tokens are secrets with the same sensitivity as database passwords. Notion tokens use the `ntn_` prefix (current) or `secret_` prefix (legacy). Both grant full access to every page shared with the integration.

```bash
# .gitignore — add these patterns BEFORE creating .env
.env
.env.local
.env.*.local
.env.production
.env.staging

# .env.example — commit this template (no real values)
NOTION_TOKEN=ntn_your_internal_integration_token_here
NOTION_OAUTH_CLIENT_ID=
NOTION_OAUTH_CLIENT_SECRET=
NOTION_OAUTH_REDIRECT_URI=http://localhost:3000/auth/notion/callback
```

```typescript
import { Client } from '@notionhq/client';

// Always load tokens from environment — never hardcode
const token = process.env.NOTION_TOKEN;

if (!token) {
  throw new Error(
    'NOTION_TOKEN is required. ' +
    'Create an integration at https://www.notion.so/my-integrations ' +
    'and set the token in your .env file.'
  );
}

// Validate token format before using it
if (!token.startsWith('ntn_') && !token.startsWith('secret_')) {
  throw new Error(
    'NOTION_TOKEN has an unexpected format. ' +
    'Internal integration tokens start with ntn_ (or legacy secret_).'
  );
}

const notion = new Client({ auth: token });
```

**Git secret scanning** to catch accidental commits:

```yaml
# .github/workflows/secret-scan.yml
name: Secret Scan
on: [push, pull_request]
jobs:
  scan:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for Notion tokens
        run: |
          # Scan for internal integration tokens
          if grep -rE "(ntn_|secret_)[a-zA-Z0-9]{30,}" \
            --include="*.ts" --include="*.js" --include="*.json" \
            --include="*.yaml" --include="*.yml" --include="*.env" .; then
            echo "::error::Notion token found in source code! Rotate immediately."
            exit 1
          fi
```

### Step 2: Least-Privilege Capabilities and Access Auditing

Configure integration capabilities at the [integration dashboard](https://www.notion.so/my-integrations). Each integration should request only the capabilities it actually uses.

| Capability | Grant when... | Do NOT grant for... |
|------------|---------------|---------------------|
| Read content | Reading pages, databases, blocks | Write-only bots (form submissions) |
| Update content | Modifying existing page properties/blocks | Read-only dashboards |
| Insert content | Creating new pages, appending blocks | Analytics/reporting tools |
| Read comments | Listing and reading page comments | Data sync pipelines |
| Create comments | Adding comments to discussions | Read-only integrations |
| Read user info (with email) | User lookup by email address | Most integrations |
| Read user info (without email) | Resolving user references in properties | None (safe default) |

**Separate integrations by responsibility:**

```typescript
// Create distinct integrations with different capabilities:
// "acme-reader" — Read content only
// "acme-writer" — Read + Update + Insert content

const readerNotion = new Client({ auth: process.env.NOTION_READ_TOKEN });
const writerNotion = new Client({ auth: process.env.NOTION_WRITE_TOKEN });

// Dashboards and reporting use the reader
const results = await readerNotion.databases.query({
  database_id: process.env.NOTION_DATABASE_ID!,
  filter: {
    property: 'Status',
    select: { equals: 'Published' },
  },
});

// Mutations use the writer only when needed
await writerNotion.pages.update({
  page_id: pageId,
  properties: {
    'Last Synced': {
      date: { start: new Date().toISOString() },
    },
  },
});
```

**Audit which pages are shared with an integration:**

```typescript
async function auditIntegrationAccess(notion: Client): Promise<void> {
  // Search with empty query returns all pages the integration can access
  let hasMore = true;
  let startCursor: string | undefined;
  const accessiblePages: Array<{ id: string; title: string; type: string }> = [];

  while (hasMore) {
    const response = await notion.search({
      start_cursor: startCursor,
      page_size: 100,
    });

    for (const result of response.results) {
      if (result.object === 'page') {
        const titleProp = Object.values((result as any).properties || {})
          .find((p: any) => p.type === 'title') as any;
        const title = titleProp?.title?.[0]?.plain_text || '(untitled)';
        accessiblePages.push({ id: result.id, title, type: 'page' });
      } else if (result.object === 'database') {
        const title = (result as any).title?.[0]?.plain_text || '(untitled)';
        accessiblePages.push({ id: result.id, title, type: 'database' });
      }
    }

    hasMore = response.has_more;
    startCursor = response.next_cursor ?? undefined;
  }

  console.log(`Integration has access to ${accessiblePages.length} objects:`);
  for (const page of accessiblePages) {
    console.log(`  [${page.type}] ${page.title} (${page.id})`);
  }
}
```

**Page sharing hierarchy rules:**
- Sharing a parent page grants access to all child pages and databases
- Sharing a child page alone does NOT grant access to its parent
- Removing integration access from a parent cascades to all children
- The API returns `object_not_found` for both non-existent pages and unshared pages — this is intentional to prevent information leakage

### Step 3: Token Rotation, OAuth2, and Webhook Verification

#### Token Rotation for Internal Integrations

```bash
# 1. Go to notion.so/my-integrations → select integration
#    Click "Show" under Internal Integration Secret → "Regenerate"
#    WARNING: regeneration immediately invalidates the old token

# 2. Update the secret in your deployment platform FIRST
# AWS Secrets Manager:
aws secretsmanager update-secret \
  --secret-id notion/integration-token \
  --secret-string "ntn_new_token_value"

# GCP Secret Manager:
echo -n "ntn_new_token_value" | \
  gcloud secrets versions add notion-integration-token --data-file=-

# Vault:
vault kv put secret/notion token="ntn_new_token_value"

# 3. Restart services to pick up the new secret

# 4. Verify the new token works
curl -s https://api.notion.com/v1/users/me \
  -H "Authorization: Bearer ${NOTION_TOKEN}" \
  -H "Notion-Version: 2022-06-28" | jq '.name // .bot'

# 5. Old token is already invalidated (step 1), no separate revocation needed
```

#### OAuth2 Flow for Public Integrations

Public integrations use OAuth2 to let users authorize access without sharing raw tokens. This is required when distributing your integration to other Notion workspaces.

```typescript
import { Client } from '@notionhq/client';
import express from 'express';

const app = express();
const OAUTH_CLIENT_ID = process.env.NOTION_OAUTH_CLIENT_ID!;
const OAUTH_CLIENT_SECRET = process.env.NOTION_OAUTH_CLIENT_SECRET!;
const REDIRECT_URI = process.env.NOTION_OAUTH_REDIRECT_URI!;

// Step A: Redirect user to Notion's authorization page
app.get('/auth/notion', (req, res) => {
  const authUrl = new URL('https://api.notion.com/v1/oauth/authorize');
  authUrl.searchParams.set('client_id', OAUTH_CLIENT_ID);
  authUrl.searchParams.set('response_type', 'code');
  authUrl.searchParams.set('redirect_uri', REDIRECT_URI);
  authUrl.searchParams.set('owner', 'user'); // or 'workspace'

  // Generate and store a state parameter to prevent CSRF
  const state = crypto.randomUUID();
  req.session.oauthState = state;
  authUrl.searchParams.set('state', state);

  res.redirect(authUrl.toString());
});

// Step B: Exchange authorization code for access token
app.get('/auth/notion/callback', async (req, res) => {
  const { code, state } = req.query;

  // Verify state parameter matches what we sent
  if (state !== req.session.oauthState) {
    return res.status(403).send('Invalid state parameter — possible CSRF attack');
  }

  // Exchange code for token using Basic auth (client_id:client_secret)
  const credentials = Buffer.from(
    `${OAUTH_CLIENT_ID}:${OAUTH_CLIENT_SECRET}`
  ).toString('base64');

  const tokenResponse = await fetch('https://api.notion.com/v1/oauth/token', {
    method: 'POST',
    headers: {
      'Authorization': `Basic ${credentials}`,
      'Content-Type': 'application/json',
      'Notion-Version': '2022-06-28',
    },
    body: JSON.stringify({
      grant_type: 'authorization_code',
      code,
      redirect_uri: REDIRECT_URI,
    }),
  });

  const tokenData = await tokenResponse.json();

  if (!tokenResponse.ok) {
    console.error('OAuth token exchange failed:', tokenData);
    return res.status(400).send('Authorization failed');
  }

  // tokenData contains:
  // - access_token: the integration token for this workspace
  // - workspace_id: the workspace that authorized the integration
  // - workspace_name, workspace_icon, bot_id, owner
  // Store access_token securely (encrypted in database, not in cookies)
  await storeToken(tokenData.workspace_id, tokenData.access_token);

  // Use the token with the Notion client
  const notion = new Client({ auth: tokenData.access_token });
  const me = await notion.users.me({});
  console.log(`Authorized for workspace: ${tokenData.workspace_name}`);

  res.redirect('/dashboard');
});
```

#### Webhook Verification

```typescript
// Notion webhooks require URL verification during setup
// and should be validated on every incoming request

app.post('/webhooks/notion', express.json(), async (req, res) => {
  // Notion verifies your endpoint during registration
  if (req.body.type === 'url_verification') {
    return res.json({ challenge: req.body.challenge });
  }

  // Validate the payload structure
  if (!req.body.type || !req.body.data) {
    return res.status(400).json({ error: 'Invalid webhook payload' });
  }

  // Always respond 200 quickly — process the event asynchronously
  res.status(200).json({ ok: true });

  // Process event outside the request cycle
  try {
    await processWebhookEvent(req.body);
  } catch (error) {
    console.error('Webhook processing failed:', error);
  }
});

// Additional hardening:
// 1. Only accept HTTPS connections (terminate TLS at load balancer)
// 2. Validate Content-Type is application/json
// 3. Rate limit the webhook endpoint (e.g., 100 req/min)
// 4. Log all incoming events for audit trail
```

## Output

After applying this skill:
- Integration tokens stored in environment variables, never in source code
- `.gitignore` configured to exclude all `.env` variants
- Git secret scanning workflow catches accidental token commits
- Integration capabilities set to the minimum required for each role
- Page access audited — you know exactly which pages the integration can reach
- Token rotation procedure documented with cloud provider commands
- OAuth2 flow implemented for public integrations (if applicable)
- Webhook endpoint validates payloads and responds asynchronously

## Error Handling

| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token committed to git | CI secret scan, `git log -p -S 'ntn_'` | Rotate immediately, rewrite git history with `git filter-repo` |
| Over-privileged integration | Capability audit at dashboard | Create new integration with minimal capabilities, migrate |
| Stale access to removed pages | Access audit script returns unexpected pages | Revoke page sharing, re-audit |
| Token never rotated | Track `created_time` of integration | Schedule quarterly rotation, automate with secrets manager |
| OAuth state mismatch | CSRF validation in callback | Reject the request, log the attempt |
| Webhook replay attacks | Duplicate event IDs | Track processed event IDs, skip duplicates |

## Examples

### Full `.env` Setup for Dual Integration Architecture

```bash
# .env — never committed
# Reader integration (Read content only)
NOTION_READ_TOKEN=ntn_reader_integration_token

# Writer integration (Read + Update + Insert)
NOTION_WRITE_TOKEN=ntn_writer_integration_token

# OAuth2 (public integration only)
NOTION_OAUTH_CLIENT_ID=abc123
NOTION_OAUTH_CLIENT_SECRET=secret_abc123
NOTION_OAUTH_REDIRECT_URI=https://app.example.com/auth/notion/callback

# Target resources
NOTION_DATABASE_ID=your_database_id
```

### Startup Validation Script

```typescript
// validate-notion-config.ts — run at application startup
import { Client } from '@notionhq/client';

async function validateNotionConfig(): Promise<void> {
  const requiredVars = ['NOTION_READ_TOKEN', 'NOTION_DATABASE_ID'];
  const missing = requiredVars.filter((v) => !process.env[v]);

  if (missing.length > 0) {
    throw new Error(`Missing required env vars: ${missing.join(', ')}`);
  }

  const notion = new Client({ auth: process.env.NOTION_READ_TOKEN });

  // Verify token is valid
  try {
    const me = await notion.users.me({});
    console.log(`Notion auth OK: bot "${me.name}" (${me.id})`);
  } catch (error: any) {
    if (error.code === 'unauthorized') {
      throw new Error('NOTION_READ_TOKEN is invalid or expired — rotate at notion.so/my-integrations');
    }
    throw error;
  }

  // Verify database is accessible
  try {
    await notion.databases.retrieve({
      database_id: process.env.NOTION_DATABASE_ID!,
    });
    console.log('Notion database access OK');
  } catch (error: any) {
    if (error.code === 'object_not_found') {
      throw new Error(
        'NOTION_DATABASE_ID not found — ensure the database is shared with the integration'
      );
    }
    throw error;
  }
}

validateNotionConfig().catch((err) => {
  console.error('Notion configuration validation failed:', err.message);
  process.exit(1);
});
```

## Resources

- [Notion API Authorization](https://developers.notion.com/docs/authorization) — token types, OAuth2 flow, scopes
- [Create a Notion Integration](https://developers.notion.com/docs/create-a-notion-integration) — capabilities configuration
- [API Key Best Practices](https://developers.notion.com/docs/best-practices-for-handling-api-keys) — storage and rotation
- [@notionhq/client npm](https://www.npmjs.com/package/@notionhq/client) — official SDK documentation
- [Notion API Reference](https://developers.notion.com/reference/intro) — full endpoint reference

## Next Steps

For production deployment checklists, see `notion-prod-checklist`. For rate limit handling and retry strategies, see `notion-rate-limits`. For enterprise RBAC patterns with Notion, see `notion-enterprise-rbac`.
