# Examples — podium-auth

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Minimal single-tenant integration (Python, async)

```python
# env: PODIUM_CLIENT_ID, PODIUM_CLIENT_SECRET, PODIUM_REFRESH_TOKEN_FILE
import asyncio, os, json, time
from pathlib import Path
from podium_auth import PodiumAuth   # the library shipped by this skill

async def main():
    path = Path(os.environ["PODIUM_REFRESH_TOKEN_FILE"])
    record = json.loads(path.read_text())

    auth = PodiumAuth(
        client_id=os.environ["PODIUM_CLIENT_ID"],
        client_secret=os.environ["PODIUM_CLIENT_SECRET"],
        refresh_token=record["refresh_token"],
    )
    token = await auth.get_token()
    print(f"access_token acquired (length={len(token)})")

asyncio.run(main())
```

## 2. Wire the cache into an HTTPX client

```python
import httpx
from podium_auth import PodiumAuth

async def podium_call(auth: PodiumAuth, method: str, path: str, **kwargs) -> httpx.Response:
    token = await auth.get_token()
    headers = {"Authorization": f"Bearer {token}", **kwargs.pop("headers", {})}
    async with httpx.AsyncClient(timeout=10) as c:
        return await c.request(method, f"https://api.podium.com{path}", headers=headers, **kwargs)

# Usage
async def list_conversations(auth: PodiumAuth, location_uid: str):
    r = await podium_call(auth, "GET", f"/v4/conversations?location_uid={location_uid}")
    r.raise_for_status()
    return r.json()
```

## 3. Bootstrap the refresh-token file from an authorization-code flow

```python
# Run this ONCE per OAuth app after a user completes /oauth/authorize and you receive
# the authorization code via your redirect URI.
import os, json, time, httpx
from pathlib import Path

CODE = os.environ["PODIUM_AUTH_CODE"]            # from redirect_uri callback
REDIRECT = os.environ["PODIUM_REDIRECT_URI"]

r = httpx.post(
    "https://accounts.podium.com/oauth/token",
    data={
        "grant_type": "authorization_code",
        "code": CODE,
        "redirect_uri": REDIRECT,
        "client_id": os.environ["PODIUM_CLIENT_ID"],
        "client_secret": os.environ["PODIUM_CLIENT_SECRET"],
    },
    timeout=10,
)
r.raise_for_status()
body = r.json()

path = Path(os.environ["PODIUM_REFRESH_TOKEN_FILE"])
path.write_text(json.dumps({
    "refresh_token": body["refresh_token"],
    "last_used_at": time.time(),
    "scopes_granted": body.get("scope", "").split(" "),
}))
path.chmod(0o600)
print("bootstrapped:", path)
```

## 4. Multi-tenant router (agency case)

```python
import json, os
from podium_auth import PodiumAuth, PodiumOrgRouter

creds = json.loads(open(os.environ["PODIUM_ORG_CREDENTIALS_MAP"]).read())
# creds = {"acme-rv": {"client_id": "...", "client_secret": "...", "refresh_token_file": "..."}, ...}

router = PodiumOrgRouter.from_credentials_map(creds)

async def write_to_org(org_slug: str, contact: dict):
    auth = router.get(org_slug)        # raises KeyError on unknown slug — by design
    token = await auth.get_token()
    # ... POST contact with this token
```

## 5. Forced refresh via the operator CLI

```bash
# Refresh the token NOW and persist the new refresh_token, regardless of current TTL.
# Use this to revive a token that is nearing 75-day decay.
python3 scripts/token_refresh.py \
  --client-id-env PODIUM_CLIENT_ID \
  --client-secret-env PODIUM_CLIENT_SECRET \
  --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE" \
  --output json
```

Output:

```json
{
  "status": "ok",
  "access_token_length": 412,
  "expires_in": 3600,
  "refresh_token_rotated": true,
  "scopes_granted": ["conversations.read", "conversations.write", "..."]
}
```

## 6. Audit scopes against the required set

```bash
python3 scripts/scope_audit.py \
  --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE" \
  --required conversations.read,conversations.write,contacts.read,contacts.write,reviews.read,reviews.write
```

Exit code 0 = all required granted; exit code 1 = drift detected and printed to stderr.

## 7. Dual-credential rotation (zero-downtime)

```bash
# Step 1: in the Podium developer console, generate a new client_secret. Both old + new are
#         valid simultaneously until you revoke the old.
# Step 2: deploy the new secret to your secret store under a versioned key
#         (e.g. /podium/client_secret_v2). The store now holds both v1 and v2.
# Step 3: signal the running process to reload. Example: SIGHUP if the process supports it,
#         or rolling restart for stateless workers.
# Step 4: run the rotation orchestrator.

python3 scripts/rotate_secret.py \
  --old-secret-env PODIUM_CLIENT_SECRET_V1 \
  --new-secret-env PODIUM_CLIENT_SECRET_V2 \
  --client-id-env  PODIUM_CLIENT_ID \
  --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE" \
  --health-check-passes 3 \
  --overlap-window-seconds 900
```

The script:

1. Refreshes a token using `v2` and verifies it via `GET /v4/me`.
2. Runs `health-check-passes` consecutive `/v4/me` calls — all must succeed.
3. Sleeps `overlap-window-seconds` to let in-flight handlers drain on the old secret.
4. Calls `/oauth/revoke` on the old secret only after all checks pass.

If any step fails, the script exits non-zero **without** revoking — you can roll back by re-pointing the cache at `v1`.

## 8. Decay monitor wired to a background task

```python
import asyncio, time
from podium_auth import check_decay, page_oncall, log_warn

async def decay_loop(refresh_token_file: str, interval_s: int = 3600):
    import json
    while True:
        try:
            record = json.loads(open(refresh_token_file).read())
            age_days = (time.time() - record["last_used_at"]) / 86400
            check_decay(record["last_used_at"])     # raises on >= 85d
            print(f"decay_monitor: age={age_days:.1f}d / 90d")
        except Exception as e:
            log_warn(f"decay_monitor exception: {e}")
        await asyncio.sleep(interval_s)
```

## 9. Verify credentials without consuming a refresh

```bash
# Cheap sanity check — does the existing access token still work?
# Does NOT trigger a refresh, so does not reset the decay clock.
python3 scripts/verify_creds.py --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE"
```

Exit code 0 = token is live; exit code 1 = token rejected; exit code 2 = endpoint reachable but ambiguous.

## 10. Pre-commit hook — block accidentally-committed credentials

```bash
#!/usr/bin/env bash
# .git/hooks/pre-commit
set -euo pipefail

# Block any staged file containing a Podium client_secret or refresh_token assignment.
if git diff --cached --name-only -z | xargs -0 grep -lE \
     "podium.*(client_secret|refresh_token)\s*=\s*['\"][^'\"]{8,}['\"]" 2>/dev/null; then
  echo "ERR_AUTH_012: Podium credential detected in staged files. Move to secret store before committing."
  exit 1
fi
```

Install with: `chmod +x .git/hooks/pre-commit`. The skill's `Edit` permission can also patch `.gitignore` if the credentials live in a tracked-by-default location.
