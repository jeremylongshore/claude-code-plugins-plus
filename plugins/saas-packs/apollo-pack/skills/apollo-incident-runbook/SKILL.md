---
name: apollo-incident-runbook
description: |
  Apollo.io incident response procedures.
  Use when handling Apollo outages, debugging production issues,
  or responding to integration failures.
  Trigger with phrases like "apollo incident", "apollo outage",
  "apollo down", "apollo production issue", "apollo emergency".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, debugging, incident-response]

---
# Apollo Incident Runbook

## Overview
Structured incident response for Apollo.io API failures. Covers severity classification, quick diagnosis, circuit breaker implementation, graceful degradation, and post-incident review. Apollo's public status page is at [status.apollo.io](https://status.apollo.io).

## Prerequisites
- Valid Apollo API key
- Access to monitoring dashboards

## Instructions

### Step 1: Classify Severity
```
Severity | Criteria                                    | Response Time
---------+---------------------------------------------+--------------
P1       | Apollo API completely unreachable            | 15 min
         | All enrichments/searches returning 5xx       |
P2       | Partial failures (>10% error rate)           | 1 hour
         | Rate limiting blocking critical workflows    |
P3       | Intermittent errors (<10%), degraded latency | 4 hours
         | Non-critical endpoint failures               |
P4       | Cosmetic issues, minor data inconsistencies  | Next sprint
```

### Step 2: Quick Diagnosis Script
```bash
#!/bin/bash
# scripts/apollo-diagnosis.sh
set -euo pipefail
echo "=== Apollo Quick Diagnosis $(date -u +%Y-%m-%dT%H:%M:%SZ) ==="

# 1. Check Apollo status page
echo -e "\n--- Status Page ---"
curl -s https://status.apollo.io/api/v2/status.json 2>/dev/null | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"][\"description\"]}')" \
  2>/dev/null || echo "Could not reach status page"

# 2. Test auth
echo -e "\n--- Auth Check ---"
curl -s -w "HTTP %{http_code} in %{time_total}s\n" \
  -H "x-api-key: $APOLLO_API_KEY" \
  "https://api.apollo.io/api/v1/auth/health" | head -1

# 3. Test people search (free endpoint)
echo -e "\n--- People Search ---"
curl -s -w "HTTP %{http_code} in %{time_total}s\n" -o /dev/null \
  -X POST -H "Content-Type: application/json" -H "x-api-key: $APOLLO_API_KEY" \
  -d '{"q_organization_domains_list":["apollo.io"],"per_page":1}' \
  "https://api.apollo.io/api/v1/mixed_people/api_search"

# 4. Check rate limit headers
echo -e "\n--- Rate Limits ---"
curl -s -D - -o /dev/null \
  -X POST -H "Content-Type: application/json" -H "x-api-key: $APOLLO_API_KEY" \
  -d '{"q_organization_domains_list":["apollo.io"],"per_page":1}' \
  "https://api.apollo.io/api/v1/mixed_people/api_search" 2>/dev/null | grep -i "x-rate-limit" || echo "No rate limit headers"

# 5. DNS resolution
echo -e "\n--- DNS ---"
dig +short api.apollo.io 2>/dev/null || nslookup api.apollo.io 2>/dev/null || echo "DNS lookup failed"
```

### Step 3: Circuit Breaker
```typescript
// src/resilience/circuit-breaker.ts
type State = 'closed' | 'open' | 'half-open';

export class CircuitBreaker {
  private state: State = 'closed';
  private failures = 0;
  private lastFailure = 0;
  private halfOpenSuccesses = 0;

  constructor(
    private failureThreshold: number = 5,
    private resetTimeoutMs: number = 60_000,
    private requiredSuccesses: number = 3,
  ) {}

  async execute<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetTimeoutMs) {
        this.state = 'half-open';
        this.halfOpenSuccesses = 0;
      } else {
        if (fallback) return fallback();
        throw new Error(`Circuit OPEN — Apollo calls blocked for ${Math.round((this.resetTimeoutMs - (Date.now() - this.lastFailure)) / 1000)}s`);
      }
    }

    try {
      const result = await fn();
      if (this.state === 'half-open') {
        this.halfOpenSuccesses++;
        if (this.halfOpenSuccesses >= this.requiredSuccesses) {
          this.state = 'closed';
          this.failures = 0;
        }
      } else {
        this.failures = 0;
      }
      return result;
    } catch (err) {
      this.failures++;
      this.lastFailure = Date.now();
      if (this.failures >= this.failureThreshold) this.state = 'open';
      if (fallback) return fallback();
      throw err;
    }
  }

  get status() { return { state: this.state, failures: this.failures }; }
}
```

### Step 4: Graceful Degradation by Severity
```typescript
import { CircuitBreaker } from './circuit-breaker';

const breaker = new CircuitBreaker(5, 60_000);

// P1: Total outage — serve cached data
async function handleP1() {
  console.error('[P1] Apollo API unreachable');
  return breaker.execute(
    () => client.post('/mixed_people/api_search', { per_page: 1 }),
    () => {
      console.warn('Serving cached search results');
      return { data: { people: [], source: 'cache', degraded: true } };
    },
  );
}

// P2: Partial failures — reduce load
async function handleP2() {
  console.warn('[P2] Apollo degraded — reducing concurrency');
  // Disable bulk enrichment, reduce search concurrency to 1
  // Continue serving search from cache where possible
}

// P3: Intermittent — retry with backoff
async function handleP3() {
  console.info('[P3] Intermittent errors — backoff enabled');
  // Retry with longer delays, log for monitoring
}
```

### Step 5: Post-Incident Review Template
```markdown
## Post-Incident Review: Apollo Integration

**Incident ID:** INC-YYYY-MM-DD-NNN
**Severity:** P1 / P2 / P3
**Duration:** HH:MM start to HH:MM resolved (X minutes)
**Apollo Status Page:** Reporting outage? Y/N

### Timeline
| Time (UTC) | Event |
|------------|-------|
| HH:MM | First alert fired (source: Prometheus/PagerDuty) |
| HH:MM | On-call acknowledged |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied (circuit breaker / cache fallback) |
| HH:MM | Apollo API restored |
| HH:MM | Circuit breaker closed, normal operations resumed |

### Impact
- Searches affected: N requests failed / served from cache
- Enrichments failed: N (credits not consumed)
- Sequences paused: N contacts delayed
- Revenue impact: $X (estimated pipeline delay)

### Root Cause
[Apollo-side outage / rate limiting / key rotation / network issue]

### Action Items
- [ ] Add/improve circuit breaker coverage (owner, due)
- [ ] Increase cache TTL for critical data (owner, due)
- [ ] Add alerting for [specific gap] (owner, due)
```

## Output
- Severity classification matrix (P1-P4) with response times
- Bash diagnostic script (status page, auth, search, rate limits, DNS)
- Circuit breaker with closed/open/half-open states
- Graceful degradation procedures per severity level
- Post-incident review template

## Error Handling
| Issue | Escalation |
|-------|------------|
| P1 > 15 min | Page on-call, open Apollo support ticket |
| P2 > 2 hours | Notify engineering management |
| Recurring P3 | Promote to P2 tracking issue |
| Apollo outage | Verify at [status.apollo.io](https://status.apollo.io), enable cache fallback |

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support](https://support.apollo.io)
- [API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)

## Next Steps
Proceed to `apollo-data-handling` for data management.
