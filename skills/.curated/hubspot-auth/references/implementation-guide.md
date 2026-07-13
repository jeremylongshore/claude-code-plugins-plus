# HubSpot Auth — Implementation Guide

Production patterns for auth integration across languages, secret store integrations, token rotation runbook, and OAuth flow implementation. The TypeScript token-cache and multi-portal router patterns live in `SKILL.md`; this document covers Python equivalents, secret store wiring, and the rotation runbook.

## Python Implementation

### Private app (server-to-server)

```python
import os
from hubspot import HubSpot
from hubspot.crm.contacts import ApiException

client = HubSpot(access_token=os.environ["HUBSPOT_ACCESS_TOKEN"])

def verify_token() -> bool:
    try:
        page = client.crm.contacts.basic_api.get_page(limit=1)
        return True
    except ApiException as e:
        if e.status == 401:
            print("Token invalid or revoked")
        elif e.status == 403:
            print(f"Scope missing: {e.body}")
        return False
```

### OAuth token cache (Python)

```python
import time
import threading
import requests

_lock = threading.Lock()
_token: str | None = None
_expires_at: float = 0.0

def get_access_token() -> str:
    global _token, _expires_at
    # Refresh at 80% TTL (1800s * 0.8 = 1440s; refresh at 360s before expiry)
    with _lock:
        if _token and time.time() < _expires_at - 360:
            return _token
        _token, _expires_at = _refresh_token()
        return _token

def _refresh_token() -> tuple[str, float]:
    resp = requests.post(
        "https://api.hubapi.com/oauth/v1/token",
        data={
            "grant_type": "refresh_token",
            "client_id": os.environ["HUBSPOT_CLIENT_ID"],
            "client_secret": os.environ["HUBSPOT_CLIENT_SECRET"],
            "redirect_uri": os.environ["HUBSPOT_REDIRECT_URI"],
            "refresh_token": _load_refresh_token(),
        },
    )
    resp.raise_for_status()
    body = resp.json()
    _validate_scopes(body)
    return body["access_token"], time.time() + body["expires_in"]

def _validate_scopes(token_info: dict) -> None:
    # Call token-info endpoint to get granted scopes
    info = requests.get(
        f"https://api.hubapi.com/oauth/v1/access-tokens/{token_info['access_token']}"
    ).json()
    granted = set(info.get("scopes", []))
    required = {"crm.objects.contacts.read", "crm.objects.deals.read"}
    missing = required - granted
    if missing:
        raise ValueError(f"Scope drift: missing {missing}")
```

## Secret Store Integrations

### AWS Secrets Manager

```typescript
import { SecretsManagerClient, GetSecretValueCommand } from "@aws-sdk/client-secrets-manager";

const sm = new SecretsManagerClient({ region: process.env.AWS_REGION });

async function readSecret(secretId: string): Promise<string> {
  const { SecretString } = await sm.send(
    new GetSecretValueCommand({ SecretId: secretId })
  );
  return SecretString!;
}

// For rotation: update the secret, then signal process
async function rotateHubSpotToken(newToken: string): Promise<void> {
  const { PutSecretValueCommand } = await import("@aws-sdk/client-secrets-manager");
  await sm.send(new PutSecretValueCommand({
    SecretId: "hubspot/access-token",
    SecretString: newToken,
  }));
  // Invalidate in-process cache
  cached = null;
}
```

### GCP Secret Manager

```python
from google.cloud import secretmanager

client = secretmanager.SecretManagerServiceClient()
PROJECT = os.environ["GCP_PROJECT"]

def read_secret(name: str) -> str:
    resource = f"projects/{PROJECT}/secrets/{name}/versions/latest"
    response = client.access_secret_version(request={"name": resource})
    return response.payload.data.decode("utf-8")

def write_secret(name: str, value: str) -> None:
    parent = f"projects/{PROJECT}/secrets/{name}"
    client.add_secret_version(
        request={"parent": parent, "payload": {"data": value.encode()}}
    )
```

### Environment variable (local dev / simple deploys)

```bash
# Load from .env file (never committed)
export HUBSPOT_ACCESS_TOKEN="$(pass show hubspot/access-token)"
export HUBSPOT_CLIENT_ID="$(pass show hubspot/client-id)"
export HUBSPOT_CLIENT_SECRET="$(pass show hubspot/client-secret)"
```

## OAuth Public App Flow

### Step 1: Authorization URL

```typescript
function buildAuthUrl(state: string): string {
  const params = new URLSearchParams({
    client_id: process.env.HUBSPOT_CLIENT_ID!,
    redirect_uri: process.env.HUBSPOT_REDIRECT_URI!,
    scope: [
      "crm.objects.contacts.read",
      "crm.objects.contacts.write",
      "crm.objects.deals.read",
    ].join(" "),
  });
  // state param prevents CSRF — generate per-session random string
  params.set("state", state);
  return `https://app.hubspot.com/oauth/authorize?${params}`;
}
```

### Step 2: Callback handler

```typescript
// Express/Next.js route: GET /oauth/callback?code=...&state=...
async function handleCallback(code: string, state: string, sessionState: string) {
  if (state !== sessionState) throw new Error("OAuth state mismatch (CSRF check)");

  const res = await fetch("https://api.hubapi.com/oauth/v1/token", {
    method: "POST",
    headers: { "Content-Type": "application/x-www-form-urlencoded" },
    body: new URLSearchParams({
      grant_type: "authorization_code",
      client_id: process.env.HUBSPOT_CLIENT_ID!,
      client_secret: process.env.HUBSPOT_CLIENT_SECRET!,
      redirect_uri: process.env.HUBSPOT_REDIRECT_URI!,
      code,
    }),
  });
  if (!res.ok) throw new Error(`Token exchange failed: ${await res.text()}`);

  const { access_token, refresh_token, expires_in } = await res.json();

  // Persist refresh token to secret store
  await writeSecret(`hubspot/refresh-token/${portalId}`, JSON.stringify({
    token: refresh_token,
    lastUsed: Date.now(),
  }));

  // Seed the cache
  cached = { value: access_token, expiresAt: Date.now() + expires_in * 1000 };
}
```

## Token Rotation Runbook

Use when a private-app token has been leaked (found in git history, logs, or error messages) or when rotating on schedule.

**Time to complete:** ~5 minutes. No downtime with staged rotation.

1. **Assess blast radius**

   ```bash
   # Find all systems using this token
   grep -r "pat-na1-" ~/.env* || true
   # Check logs for accidental token output
   grep "pat-na1-" /var/log/app/*.log || true
   ```

2. **Generate new token**
   - Go to HubSpot → Settings → Integrations → Private Apps → your app → Auth tab
   - Click "Rotate token" — HubSpot generates a new token and **immediately revokes the old one**
   - Copy the new token

3. **Update secret store** (before any process restarts)

   ```bash
   # AWS
   aws secretsmanager put-secret-value --secret-id hubspot/access-token --secret-string "pat-na1-NEW..."
   # GCP
   echo -n "pat-na1-NEW..." | gcloud secrets versions add hubspot-access-token --data-file=-
   # pass
   pass edit hubspot/access-token
   ```

4. **Invalidate in-process cache** (trigger hot reload or restart)

   ```bash
   # If SIGHUP is wired to reload secrets:
   kill -HUP $(pgrep -f your-service)
   # Or restart
   systemctl restart your-service
   ```

5. **Verify new token**

   ```bash
   curl -s "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
     -H "Authorization: Bearer pat-na1-NEW..." | jq '.results | length'
   # Should return 0 or 1, not an error
   ```

6. **Remove leaked token from git history** (if applicable)

   ```bash
   git filter-branch --force --index-filter \
     "git rm --cached --ignore-unmatch .env" \
     --prune-empty --tag-name-filter cat -- --all
   git push origin --force --all
   # Notify all collaborators to re-clone
   ```

## Monitoring Recommendations

Log these events to detect auth failures before they cascade:

| Event | Log level | Action |
|---|---|---|
| Token refresh succeeded | DEBUG | — |
| Token refresh failed (will retry) | WARN | Alert if 3 consecutive failures |
| Scope drift detected | ERROR | Page on-call; portal admin required |
| Daily rate limit at 80% | WARN | Throttle non-critical calls |
| Daily rate limit exhausted | CRITICAL | Stop all non-essential requests |
| Refresh token age > 300 days | WARN | Schedule user reconnect before day 365 |

```typescript
// Structured log example
console.log(JSON.stringify({
  event: "hubspot_token_refresh",
  portal: portalSlug,
  success: true,
  expiresIn: expires_in,
  dailyRemaining: parseInt(res.headers.get("X-HubSpot-RateLimit-Daily-Remaining") ?? "0"),
}));
```
