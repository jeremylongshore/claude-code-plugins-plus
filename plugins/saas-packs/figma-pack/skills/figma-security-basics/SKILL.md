---
name: figma-security-basics
description: |
  Secure Figma API tokens, configure scopes, and validate webhook signatures.
  Use when securing API keys, implementing least-privilege scopes,
  or auditing Figma security configuration.
  Trigger with phrases like "figma security", "figma secrets",
  "secure figma token", "figma scopes", "figma webhook verify".
allowed-tools: Read, Write, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, figma]
compatible-with: claude-code
---

# Figma Security Basics

## Overview
Secure your Figma API integration: store tokens safely, apply least-privilege scopes, rotate credentials, and verify webhook signatures.

## Prerequisites
- Figma PAT or OAuth app configured
- Understanding of environment variables
- `.gitignore` configured for secret files

## Instructions

### Step 1: Token Storage
```bash
# .env (NEVER commit)
FIGMA_PAT="figd_your-personal-access-token"
FIGMA_OAUTH_CLIENT_SECRET="your-oauth-secret"

# .gitignore
.env
.env.local
.env.*.local
*.pem
```

```typescript
// Validate token exists before any API call
function getToken(): string {
  const token = process.env.FIGMA_PAT;
  if (!token) throw new Error('FIGMA_PAT is not set');
  if (!token.startsWith('figd_')) {
    console.warn('Token does not have expected figd_ prefix');
  }
  return token;
}
```

### Step 2: Least-Privilege Scopes
Assign the minimum scopes needed for each use case:

| Use Case | Required Scopes |
|----------|----------------|
| Read file structure | `file_content:read` |
| Export images | `file_content:read` |
| Post comments | `file_comments:write` |
| Read variables (Enterprise) | `file_variables:read` |
| Manage webhooks | `webhooks:write` |
| Read team components | `team_library_content:read` |
| Dev mode resources | `file_dev_resources:read` |

**Deprecated scope:** `files:read` is deprecated. Use specific scopes like `file_content:read`, `file_comments:read` instead.

### Step 3: Token Rotation
```bash
# PATs have a maximum 90-day lifetime
# Schedule rotation before expiry

# 1. Generate new token in Figma Settings > Personal access tokens
# 2. Test new token
curl -s -H "X-Figma-Token: ${NEW_TOKEN}" \
  https://api.figma.com/v1/me | jq '.handle'

# 3. Update environment
# For CI: gh secret set FIGMA_PAT --body "${NEW_TOKEN}"
# For production: update your secret manager

# 4. Verify old token is revoked in Figma Settings
```

### Step 4: Webhook Passcode Verification
Figma webhooks use a `passcode` field (not HMAC signatures) for verification:

```typescript
// When creating a webhook, you provide a passcode:
// POST /v2/webhooks
// { "event_type": "FILE_UPDATE", "team_id": "...", "endpoint": "...", "passcode": "my-secret" }

// Figma sends the passcode back in the webhook payload body
interface FigmaWebhookPayload {
  event_type: string;
  passcode: string;      // Your secret, echoed back
  timestamp: string;
  file_key?: string;
  file_name?: string;
  webhook_id: string;
}

function verifyFigmaWebhook(
  payload: FigmaWebhookPayload,
  expectedPasscode: string
): boolean {
  // Timing-safe comparison to prevent timing attacks
  if (payload.passcode.length !== expectedPasscode.length) return false;

  const a = Buffer.from(payload.passcode);
  const b = Buffer.from(expectedPasscode);
  return crypto.timingSafeEqual(a, b);
}

// Express handler
app.post('/webhooks/figma', express.json(), (req, res) => {
  const payload: FigmaWebhookPayload = req.body;

  if (!verifyFigmaWebhook(payload, process.env.FIGMA_WEBHOOK_PASSCODE!)) {
    console.warn('Invalid webhook passcode');
    return res.status(401).json({ error: 'Invalid passcode' });
  }

  // Process the event
  handleFigmaEvent(payload);
  res.status(200).json({ received: true });
});
```

### Step 5: Security Checklist
```markdown
- [ ] PAT stored in environment variable, not in code
- [ ] `.env` files listed in `.gitignore`
- [ ] Token uses minimum required scopes
- [ ] Token rotation scheduled before 90-day expiry
- [ ] Webhook passcode verified on every incoming request
- [ ] OAuth client secret stored in secret manager (not repo)
- [ ] No tokens in frontend/client-side code
- [ ] Git history scanned for leaked tokens (use `git log -p | grep figd_`)
- [ ] Different tokens for dev/staging/prod environments
```

## Output
- Secure token storage configured
- Minimum-privilege scopes applied
- Webhook passcode verification implemented
- Rotation schedule documented

## Error Handling
| Security Issue | Detection | Mitigation |
|----------------|-----------|------------|
| Token in git history | `git log -p \| grep figd_` | Revoke immediately, rotate, use BFG Repo Cleaner |
| Expired PAT | 403 errors in production | Set calendar reminder for 80-day mark |
| Over-scoped token | Audit in Figma Settings | Regenerate with minimum scopes |
| Webhook spoofing | Missing passcode check | Always verify passcode before processing |

## Resources
- [Figma API Scopes](https://developers.figma.com/docs/rest-api/scopes/)
- [Figma Authentication](https://developers.figma.com/docs/rest-api/authentication/)
- [Managing PATs](https://help.figma.com/hc/en-us/articles/8085703771159)

## Next Steps
For production deployment, see `figma-prod-checklist`.
