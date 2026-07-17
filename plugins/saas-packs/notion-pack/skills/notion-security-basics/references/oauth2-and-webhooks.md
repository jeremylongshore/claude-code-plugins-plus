# Token Rotation, OAuth2, and Webhook Verification

Full walkthrough for Step 3: rotating internal integration tokens, the OAuth2
authorization-code flow for public integrations, and webhook endpoint
verification. All examples target the `2022-06-28` API version.

## Token Rotation for Internal Integrations

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

## OAuth2 Flow for Public Integrations

Public integrations use OAuth2 to let users authorize access without sharing raw
tokens. This is required when distributing your integration to other Notion
workspaces.

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

## Webhook Verification

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
