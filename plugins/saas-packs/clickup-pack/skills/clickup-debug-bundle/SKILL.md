---
name: clickup-debug-bundle
description: |
  Collect ClickUp API diagnostic information for troubleshooting and support.
  Use when encountering persistent issues, preparing support tickets,
  or collecting API connectivity and rate limit diagnostics.
  Trigger: "clickup debug", "clickup diagnostics", "clickup support bundle",
  "collect clickup logs", "clickup health check".
allowed-tools: Read, Bash(curl:*), Bash(tar:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, productivity, clickup]
compatible-with: claude-code
---

# ClickUp Debug Bundle

## Overview

Collect diagnostic information for troubleshooting ClickUp API v2 issues. Generates a redacted bundle safe for sharing with support.

## Quick Health Check

```bash
#!/bin/bash
echo "=== ClickUp Quick Health Check ==="

# 1. Auth verification
echo -n "Auth: "
AUTH_RESULT=$(curl -s -w "\n%{http_code}" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN")
HTTP_CODE=$(echo "$AUTH_RESULT" | tail -1)
[ "$HTTP_CODE" = "200" ] && echo "OK (200)" || echo "FAILED ($HTTP_CODE)"

# 2. Rate limit status
echo -n "Rate limits: "
HEADERS=$(curl -s -D - -o /dev/null \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN" 2>&1)
REMAINING=$(echo "$HEADERS" | grep -i "X-RateLimit-Remaining" | awk '{print $2}' | tr -d '\r')
LIMIT=$(echo "$HEADERS" | grep -i "X-RateLimit-Limit" | awk '{print $2}' | tr -d '\r')
echo "${REMAINING}/${LIMIT} remaining"

# 3. Workspace access
echo "Workspaces:"
curl -s https://api.clickup.com/api/v2/team \
  -H "Authorization: $CLICKUP_API_TOKEN" | \
  python3 -c "import sys,json; [print(f'  {t[\"id\"]}: {t[\"name\"]}') for t in json.load(sys.stdin).get('teams',[])]" 2>/dev/null

# 4. ClickUp platform status
echo -n "ClickUp status: "
curl -s https://status.clickup.com/api/v2/summary.json 2>/dev/null | \
  python3 -c "import sys,json; print(json.load(sys.stdin)['status']['description'])" 2>/dev/null || echo "Unable to check"

# 5. API latency
echo -n "API latency: "
LATENCY=$(curl -s -o /dev/null -w "%{time_total}" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN")
echo "${LATENCY}s"
```

## Full Debug Bundle Script

```bash
#!/bin/bash
# clickup-debug-bundle.sh - Generates redacted diagnostic archive

BUNDLE_DIR="clickup-debug-$(date +%Y%m%d-%H%M%S)"
mkdir -p "$BUNDLE_DIR"

cat > "$BUNDLE_DIR/summary.txt" <<HEADER
ClickUp Debug Bundle
Generated: $(date -Iseconds)
Hostname: $(hostname)
Node: $(node --version 2>/dev/null || echo 'N/A')
CLICKUP_API_TOKEN: ${CLICKUP_API_TOKEN:+[SET (${#CLICKUP_API_TOKEN} chars)]}
HEADER

# Auth check with full response headers
echo -e "\n--- Auth Check ---" >> "$BUNDLE_DIR/summary.txt"
curl -s -D "$BUNDLE_DIR/auth-headers.txt" -o "$BUNDLE_DIR/auth-response.json" \
  https://api.clickup.com/api/v2/user \
  -H "Authorization: $CLICKUP_API_TOKEN"
echo "HTTP status: $(head -1 "$BUNDLE_DIR/auth-headers.txt")" >> "$BUNDLE_DIR/summary.txt"

# Rate limit headers
echo -e "\n--- Rate Limit Headers ---" >> "$BUNDLE_DIR/summary.txt"
grep -i "ratelimit" "$BUNDLE_DIR/auth-headers.txt" >> "$BUNDLE_DIR/summary.txt" 2>/dev/null

# Workspace enumeration
echo -e "\n--- Workspaces ---" >> "$BUNDLE_DIR/summary.txt"
curl -s https://api.clickup.com/api/v2/team \
  -H "Authorization: $CLICKUP_API_TOKEN" > "$BUNDLE_DIR/teams.json"

# Redact sensitive fields from all JSON files
for f in "$BUNDLE_DIR"/*.json; do
  [ -f "$f" ] && sed -i 's/"email":"[^"]*"/"email":"[REDACTED]"/g' "$f"
done

# Remove raw auth headers (may contain token)
rm -f "$BUNDLE_DIR/auth-headers.txt"

# Package
tar -czf "$BUNDLE_DIR.tar.gz" "$BUNDLE_DIR"
rm -rf "$BUNDLE_DIR"
echo "Bundle: $BUNDLE_DIR.tar.gz"
```

## Programmatic Diagnostics

```typescript
interface ClickUpDiagnostics {
  auth: { ok: boolean; userId?: number; username?: string };
  rateLimit: { limit: number; remaining: number; resetAt: string };
  workspaces: Array<{ id: string; name: string; memberCount: number }>;
  latencyMs: number;
  platformStatus: string;
}

async function collectDiagnostics(): Promise<ClickUpDiagnostics> {
  const start = Date.now();
  const response = await fetch('https://api.clickup.com/api/v2/user', {
    headers: { 'Authorization': process.env.CLICKUP_API_TOKEN! },
  });
  const latencyMs = Date.now() - start;

  const rateLimit = {
    limit: parseInt(response.headers.get('X-RateLimit-Limit') ?? '0'),
    remaining: parseInt(response.headers.get('X-RateLimit-Remaining') ?? '0'),
    resetAt: new Date(
      parseInt(response.headers.get('X-RateLimit-Reset') ?? '0') * 1000
    ).toISOString(),
  };

  let auth: ClickUpDiagnostics['auth'];
  if (response.ok) {
    const data = await response.json();
    auth = { ok: true, userId: data.user.id, username: data.user.username };
  } else {
    auth = { ok: false };
  }

  // Get workspaces
  const teamsRes = await fetch('https://api.clickup.com/api/v2/team', {
    headers: { 'Authorization': process.env.CLICKUP_API_TOKEN! },
  });
  const teams = teamsRes.ok ? await teamsRes.json() : { teams: [] };

  return {
    auth,
    rateLimit,
    workspaces: teams.teams.map((t: any) => ({
      id: t.id, name: t.name, memberCount: t.members?.length ?? 0,
    })),
    latencyMs,
    platformStatus: auth.ok ? 'reachable' : 'auth_failed',
  };
}
```

## Error Handling

| Issue | Diagnostic Check | Solution |
|-------|-----------------|----------|
| Auth failing | Check HTTP status on /user | Regenerate token |
| High latency (>2s) | Check latencyMs | Network/region issue |
| Rate limited (0 remaining) | Check X-RateLimit-Remaining | Wait for reset or upgrade plan |
| Workspace missing | Check teams.json | Re-authorize workspace |

## Resources

- [ClickUp Status Page](https://status.clickup.com)
- [ClickUp Common Errors](https://developer.clickup.com/docs/common_errors)
- [ClickUp Support](https://help.clickup.com)

## Next Steps

For rate limit issues, see `clickup-rate-limits`.
