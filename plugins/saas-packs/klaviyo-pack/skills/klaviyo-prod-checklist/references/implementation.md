# Klaviyo Production Checklist — Implementation Reference

Full code for the health check, pre-flight validation script, and rollback
procedures referenced by `SKILL.md`. Copy these verbatim into your service.

## Health Check Implementation

Expose Klaviyo connectivity through your service's `/health` endpoint so an
unhealthy Klaviyo dependency returns `503` and trips your alerting.

```typescript
// src/health/klaviyo.ts
import { ApiKeySession, AccountsApi } from 'klaviyo-api';

export async function checkKlaviyoHealth(): Promise<{
  status: 'healthy' | 'degraded' | 'down';
  latencyMs: number;
  accountId?: string;
  error?: string;
}> {
  const start = Date.now();
  try {
    const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);
    const accountsApi = new AccountsApi(session);
    const result = await accountsApi.getAccounts();

    return {
      status: 'healthy',
      latencyMs: Date.now() - start,
      accountId: result.body.data[0].id,
    };
  } catch (error: any) {
    return {
      status: error.status === 429 ? 'degraded' : 'down',
      latencyMs: Date.now() - start,
      error: `${error.status}: ${error.body?.errors?.[0]?.detail || error.message}`,
    };
  }
}

// Express health endpoint
app.get('/health', async (req, res) => {
  const klaviyo = await checkKlaviyoHealth();
  const overallStatus = klaviyo.status === 'healthy' ? 200 : 503;
  res.status(overallStatus).json({
    status: klaviyo.status,
    services: { klaviyo },
    timestamp: new Date().toISOString(),
  });
});
```

## Pre-Flight Validation Script

Run this immediately before promoting a Klaviyo change to production. It checks
the status page, verifies API auth, inspects rate-limit headroom, and confirms
the pinned SDK version.

```bash
#!/bin/bash
# scripts/preflight-klaviyo.sh
set -euo pipefail

echo "=== Klaviyo Production Pre-Flight ==="

# 1. Check Klaviyo status
echo -n "Klaviyo Status Page: "
STATUS=$(curl -s "https://status.klaviyo.com/api/v2/status.json" | python3 -c "import sys,json; print(json.load(sys.stdin)['status']['description'])" 2>/dev/null)
echo "$STATUS"
[ "$STATUS" = "All Systems Operational" ] || echo "WARNING: Klaviyo has active incidents"

# 2. Verify API key
echo -n "API Auth: "
HTTP_CODE=$(curl -s -w "%{http_code}" -o /dev/null \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/accounts/")
echo "HTTP $HTTP_CODE"
[ "$HTTP_CODE" = "200" ] || { echo "FAIL: API auth returned $HTTP_CODE"; exit 1; }

# 3. Check rate limit headroom
echo -n "Rate Limit: "
curl -s -I \
  -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
  -H "revision: 2024-10-15" \
  "https://a.klaviyo.com/api/profiles/?page[size]=1" 2>/dev/null \
  | grep -i "ratelimit-remaining" || echo "Headers not available"

# 4. Verify SDK version
echo -n "SDK Version: "
node -e "console.log(require('klaviyo-api/package.json').version)" 2>/dev/null || echo "Not installed"

echo ""
echo "=== Pre-flight complete ==="
```

## Rollback Procedure

If a Klaviyo deployment misbehaves, roll back in this order of preference — a
feature flag is instant and blast-radius-free; a git revert or Kubernetes
rollout undo are progressively heavier.

```bash
# Immediate rollback: disable Klaviyo integration
# Option 1: Feature flag (preferred)
# Set KLAVIYO_ENABLED=false in your deployment platform

# Option 2: Deploy previous version
git log --oneline -5  # Find last known-good commit
git revert HEAD        # Revert the deployment commit
# Push and deploy

# Option 3: If using Kubernetes
kubectl rollout undo deployment/your-app
kubectl rollout status deployment/your-app
```
