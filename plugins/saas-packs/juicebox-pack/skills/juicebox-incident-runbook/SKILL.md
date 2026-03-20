---
name: juicebox-incident-runbook
description: |
  Execute Juicebox incident response procedures.
  Use when responding to production incidents, troubleshooting outages,
  or following incident management protocols.
  Trigger with phrases like "juicebox incident", "juicebox outage",
  "juicebox down", "juicebox emergency".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Incident Runbook

## Overview

Structured incident response for Juicebox integration failures. Covers quick diagnostics (API health, auth, rate limits), triage decision tree, specific response procedures for each failure mode, and post-mortem documentation. Juicebox uses token-based auth (`Authorization: token {username}:{api_token}`) and rate-limits at the account level.

## Prerequisites

- `JUICEBOX_USERNAME` and `JUICEBOX_API_TOKEN` environment variables set
- kubectl access to the cluster running your Juicebox integration
- Slack webhook URL for incident notifications (`SLACK_WEBHOOK_URL`)
- Access to monitoring dashboards (Grafana/Datadog)

## Instructions

### Step 1: Quick Diagnostics

Run these three checks immediately when an incident is suspected:

```bash
#!/bin/bash
# juicebox-quick-diag.sh
echo "=== Juicebox Quick Diagnostics ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. API Health Check
echo ""
echo "--- API Health ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  --connect-timeout 5 \
  https://api.juicebox.ai/v1/health)
echo "Health endpoint: HTTP $HTTP_CODE"

# 2. Auth Test
echo ""
echo "--- Auth Test ---"
AUTH_RESPONSE=$(curl -s -w "\nHTTP_STATUS:%{http_code}" \
  --connect-timeout 5 \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/auth/me)
AUTH_STATUS=$(echo "$AUTH_RESPONSE" | grep "HTTP_STATUS" | cut -d: -f2)
echo "Auth endpoint: HTTP $AUTH_STATUS"

# 3. Rate Limit Check
echo ""
echo "--- Rate Limit Status ---"
RATE_RESPONSE=$(curl -s -D - -o /dev/null \
  --connect-timeout 5 \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/usage)
echo "$RATE_RESPONSE" | grep -i "x-ratelimit"
```

### Step 2: Incident Triage Decision Tree

Follow this sequence to classify the incident:

1. **Is `api.juicebox.ai/v1/health` returning non-200?**
   - YES: Juicebox platform outage. Go to **Step 3: API Down**.
   - NO: Continue.

2. **Is auth endpoint returning 401 or 403?**
   - YES: Credentials invalid or revoked. Go to **Step 4: Auth Failures**.
   - NO: Continue.

3. **Are you seeing 429 responses or `x-ratelimit-remaining: 0`?**
   - YES: Account rate-limited. Go to **Step 5: Rate Limiting**.
   - NO: Continue.

4. **Are requests timing out (no response within 30s)?**
   - YES: Go to **Step 6: Timeouts**.
   - NO: Collect logs and escalate to Juicebox support with a debug bundle (`juicebox-debug-bundle`).

### Step 3: API Down -- Failover to Cache

When the Juicebox API is unreachable, serve cached candidate data and queue new requests.

```typescript
// lib/juicebox-failover.ts
import NodeCache from "node-cache";

const profileCache = new NodeCache({ stdTTL: 3600 });
let failoverActive = false;

export async function searchWithFailover(query: string): Promise<SearchResult> {
  if (!failoverActive) {
    try {
      const result = await juiceboxClient.search(query);
      profileCache.set(`search:${query}`, result);
      return result;
    } catch (err: any) {
      if (err.status >= 500 || err.code === "ECONNREFUSED") {
        failoverActive = true;
        console.error("[FAILOVER] Juicebox API unreachable, switching to cache");
      } else {
        throw err;
      }
    }
  }

  const cached = profileCache.get<SearchResult>(`search:${query}`);
  if (cached) {
    return { ...cached, _fromCache: true };
  }
  throw new Error("Juicebox API down and no cached results available");
}

// Re-check every 60 seconds
setInterval(async () => {
  if (!failoverActive) return;
  try {
    await fetch("https://api.juicebox.ai/v1/health", { signal: AbortSignal.timeout(5000) });
    failoverActive = false;
    console.log("[FAILOVER] Juicebox API recovered, resuming live requests");
  } catch {
    // Still down
  }
}, 60_000);
```

kubectl command to enable failover immediately:

```bash
kubectl set env deployment/juicebox-integration JUICEBOX_FAILOVER_ENABLED=true
kubectl rollout status deployment/juicebox-integration --timeout=120s
```

### Step 4: Auth Failures -- Token Rotation

```bash
# Verify current token works
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  https://api.juicebox.ai/v1/auth/me

# If 401: generate new token at https://juicebox.ai/settings/api
# Then update the secret:
kubectl create secret generic juicebox-creds \
  --from-literal=username="${JUICEBOX_USERNAME}" \
  --from-literal=api_token="NEW_TOKEN_HERE" \
  --dry-run=client -o yaml | kubectl apply -f -

# Restart pods to pick up new secret
kubectl rollout restart deployment/juicebox-integration
kubectl rollout status deployment/juicebox-integration --timeout=120s
```

### Step 5: Rate Limiting -- Throttle and Queue

```typescript
// lib/juicebox-throttle.ts
import PQueue from "p-queue";

const queue = new PQueue({
  concurrency: 2,
  intervalCap: 10,     // max 10 requests
  interval: 60_000,    // per 60 seconds
});

export async function throttledSearch(query: string): Promise<SearchResult> {
  return queue.add(async () => {
    const response = await fetch("https://api.juicebox.ai/v1/search", {
      method: "POST",
      headers: {
        "Authorization": `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`,
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ query }),
    });

    if (response.status === 429) {
      const retryAfter = parseInt(response.headers.get("retry-after") || "60", 10);
      console.warn(`[RATE-LIMIT] Retry after ${retryAfter}s, queue size: ${queue.size}`);
      await new Promise((r) => setTimeout(r, retryAfter * 1000));
      return throttledSearch(query); // Retry once
    }

    return response.json();
  });
}
```

### Step 6: Timeouts -- Circuit Breaker

```typescript
// lib/juicebox-circuit-breaker.ts
type CircuitState = "closed" | "open" | "half-open";

class CircuitBreaker {
  private state: CircuitState = "closed";
  private failures = 0;
  private readonly threshold = 5;
  private readonly resetTimeout = 30_000;

  async call<T>(fn: () => Promise<T>, fallback: () => T): Promise<T> {
    if (this.state === "open") {
      return fallback();
    }

    try {
      const controller = new AbortController();
      const timeout = setTimeout(() => controller.abort(), 10_000);

      const result = await fn();
      clearTimeout(timeout);
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      if (this.state === "open") {
        return fallback();
      }
      throw err;
    }
  }

  private onSuccess(): void {
    this.failures = 0;
    this.state = "closed";
  }

  private onFailure(): void {
    this.failures++;
    if (this.failures >= this.threshold) {
      this.state = "open";
      setTimeout(() => { this.state = "half-open"; }, this.resetTimeout);
    }
  }
}

export const juiceboxBreaker = new CircuitBreaker();
```

### Step 7: Incident Communication Template

Post to Slack immediately after classifying the incident:

```bash
curl -X POST "$SLACK_WEBHOOK_URL" \
  -H "Content-Type: application/json" \
  -d '{
    "text": ":rotating_light: *Juicebox Integration Incident*",
    "blocks": [
      {
        "type": "section",
        "text": {
          "type": "mrkdwn",
          "text": "*Severity:* P2 - Degraded\n*Impact:* Candidate searches returning cached results\n*Status:* Investigating\n*Started:* '"$(date -u +%H:%M)"' UTC\n*Next update:* 30 min"
        }
      }
    ]
  }'
```

### Step 8: Post-Mortem Template

Create `postmortem-YYYY-MM-DD.md` after every P1/P2 incident:

```markdown
# Post-Mortem: [Brief Title]

**Date:** YYYY-MM-DD
**Severity:** P1/P2
**Duration:** X hours Y minutes
**Author:** [Name]

## Summary
[One paragraph describing what happened and the user impact]

## Timeline (UTC)
- HH:MM - Alert fired: [description]
- HH:MM - On-call acknowledged
- HH:MM - Root cause identified: [description]
- HH:MM - Mitigation applied
- HH:MM - Full recovery confirmed

## Root Cause
[Technical explanation of the failure]

## Impact
- Candidate searches affected: [count]
- AI agent matches delayed: [duration]
- Users notified: [yes/no]

## Action Items
| Action | Owner | Due | Status |
|--------|-------|-----|--------|
| Add circuit breaker to search path | @engineer | YYYY-MM-DD | Open |
| Set up rate-limit alerting at 80% | @sre | YYYY-MM-DD | Open |
| Document token rotation runbook | @devops | YYYY-MM-DD | Open |
```

## Output

- `juicebox-quick-diag.sh` -- diagnostic script covering health, auth, and rate limits
- `lib/juicebox-failover.ts` -- cache-based failover for API outages
- `lib/juicebox-throttle.ts` -- request queue with rate-limit backoff
- `lib/juicebox-circuit-breaker.ts` -- circuit breaker for timeout protection
- `postmortem-YYYY-MM-DD.md` -- post-mortem document from template

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `ECONNREFUSED` to api.juicebox.ai | Juicebox platform outage | Activate cache failover (Step 3), monitor status page |
| `401 Unauthorized` on all requests | API token revoked or expired | Rotate token via dashboard, update k8s secret (Step 4) |
| `429 Too Many Requests` | Account-level rate limit exceeded | Enable throttle queue, check `retry-after` header (Step 5) |
| Requests hang for 30s+ then fail | Network issue or Juicebox overloaded | Activate circuit breaker, serve cached data (Step 6) |
| kubectl secret update has no effect | Pods not restarted after secret change | Run `kubectl rollout restart` after secret update |

## Examples

**Run quick diagnostics from your terminal:**

```bash
export JUICEBOX_USERNAME="your_username"
export JUICEBOX_API_TOKEN="your_api_token"
bash juicebox-quick-diag.sh
```

**Use the circuit breaker around a search call:**

```typescript
import { juiceboxBreaker } from "./lib/juicebox-circuit-breaker";

const results = await juiceboxBreaker.call(
  () => juiceboxClient.search("VP Engineering fintech NYC"),
  () => ({ profiles: [], _fromCache: true, _circuitOpen: true })
);
```

## Resources

- [Juicebox Status Page](https://status.juicebox.ai)
- [Juicebox Support](https://juicebox.ai/support)
- [Juicebox API Documentation](https://juicebox.ai/docs/api)

## Next Steps

After resolving the incident, run `juicebox-debug-bundle` to collect evidence for the support ticket, then complete the post-mortem. See `juicebox-observability` for setting up proactive alerting.
