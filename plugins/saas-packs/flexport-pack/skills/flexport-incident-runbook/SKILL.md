---
name: flexport-incident-runbook
description: |
  Execute Flexport incident response for API outages, webhook failures,
  and supply chain data sync issues with triage and mitigation steps.
  Trigger: "flexport incident", "flexport outage", "flexport down", "flexport emergency".
allowed-tools: Read, Bash(curl:*), Bash(jq:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, logistics, flexport]
compatible-with: claude-code
---

# Flexport Incident Runbook

## Triage Decision Tree

```
Is Flexport API responding?
├── NO → Check status.flexport.com → Flexport outage → Enable circuit breaker
└── YES
    ├── Getting 401/403? → Key issue → Check API key, rotate if compromised
    ├── Getting 429? → Rate limited → Reduce concurrency, honor Retry-After
    ├── Getting 5xx? → Transient → Enable retry with backoff
    └── Data stale? → Webhook issue → Check webhook endpoint health
```

## Step 1: Assess Impact

```bash
#!/bin/bash
echo "=== Flexport Incident Triage ==="

# Check API health
echo -n "API Status: "
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: Bearer $FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1
echo ""

# Check status page
echo -n "Platform: "
curl -s https://status.flexport.com/api/v2/status.json | jq -r '.status.description'

# Check error rates from your metrics
echo -n "Rate Limit Remaining: "
curl -s -H "Authorization: Bearer $FLEXPORT_API_KEY" \
  -H "Flexport-Version: 2" \
  https://api.flexport.com/shipments?per=1 -D - -o /dev/null 2>/dev/null | \
  grep -i "x-ratelimit-remaining" | awk '{print $2}'
```

## Step 2: Mitigate

### Circuit Breaker (Flexport Down)

```typescript
class FlexportCircuitBreaker {
  private failures = 0;
  private lastFailure = 0;
  private state: 'closed' | 'open' | 'half-open' = 'closed';

  async execute<T>(fn: () => Promise<T>, fallback: () => T): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > 60_000) {
        this.state = 'half-open';  // Try again after 60s
      } else {
        return fallback();
      }
    }
    try {
      const result = await fn();
      this.failures = 0;
      this.state = 'closed';
      return result;
    } catch {
      this.failures++;
      this.lastFailure = Date.now();
      if (this.failures >= 3) this.state = 'open';
      return fallback();
    }
  }
}

// Usage: serve cached data when Flexport is down
const breaker = new FlexportCircuitBreaker();
const shipments = await breaker.execute(
  () => flexport('/shipments?per=100'),
  () => ({ data: { records: cachedShipments } }),  // Stale cache fallback
);
```

## Step 3: Post-Incident

### Postmortem Template

```markdown
## Incident: [Title]
- **Duration**: [start] to [end]
- **Impact**: [affected shipments/users]
- **Root cause**: [Flexport outage / key expiry / webhook endpoint down]
- **Detection**: [alert / user report / monitoring]
- **Mitigation**: [circuit breaker / cache fallback / key rotation]
- **Action items**:
  - [ ] Improve monitoring for [specific metric]
  - [ ] Add circuit breaker to [specific endpoint]
  - [ ] Implement webhook replay for missed events
```

## Severity Matrix

| Scenario | Severity | Response |
|----------|----------|----------|
| Full API outage | P1 | Circuit breaker + cached data + notify stakeholders |
| Webhook delivery failure | P2 | Check endpoint, replay missed events, run sync job |
| Rate limit exhaustion | P2 | Reduce concurrency, cache more, notify team |
| Stale shipment data | P3 | Run manual sync job, check webhook health |
| Key rotation needed | P3 | Generate new key, deploy, revoke old |

## Resources

- [Flexport Status](https://status.flexport.com)
- [Flexport Support](https://support.flexport.com)

## Next Steps

For data handling compliance, see `flexport-data-handling`.
