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
---
# Apollo Incident Runbook

## Overview
Structured incident response procedures for Apollo.io integration issues. Covers severity classification, quick diagnosis commands, mitigation steps, circuit breaker implementation, and post-incident review templates.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+
- Completed `apollo-install-auth` setup

## Instructions

### Step 1: Classify Incident Severity
```
Severity | Criteria                                    | Response Time
---------+---------------------------------------------+--------------
P1       | Apollo API completely unreachable            | 15 min
         | All enrichments/searches failing             |
P2       | Partial failures (>10% error rate)           | 1 hour
         | Rate limiting blocking critical workflows    |
P3       | Intermittent errors, degraded performance    | 4 hours
         | Non-critical endpoint failures               |
P4       | Cosmetic issues, minor data inconsistencies  | Next sprint
```

### Step 2: Run Quick Diagnosis
```bash
#!/bin/bash
# scripts/apollo-diagnosis.sh
set -euo pipefail

echo "=== Apollo Quick Diagnosis ==="
echo "Timestamp: $(date -u +%Y-%m-%dT%H:%M:%SZ)"

# 1. Check Apollo status page
echo -e "\n--- Status Page ---"
curl -s https://status.apollo.io/api/v2/status.json | \
  python3 -c "import sys,json; d=json.load(sys.stdin); print(f'Status: {d[\"status\"][\"description\"]}')" \
  2>/dev/null || echo "Could not reach status page"

# 2. Test API connectivity
echo -e "\n--- API Connectivity ---"
HTTP_CODE=$(curl -s -o /dev/null -w "%{http_code}" \
  -X POST https://api.apollo.io/v1/people/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$APOLLO_API_KEY\", \"per_page\": 1}")
echo "HTTP Status: $HTTP_CODE"

# 3. Check rate limit status
echo -e "\n--- Rate Limits ---"
curl -s -D - -o /dev/null \
  -X POST https://api.apollo.io/v1/people/search \
  -H "Content-Type: application/json" \
  -d "{\"api_key\": \"$APOLLO_API_KEY\", \"per_page\": 1}" \
  2>/dev/null | grep -i "x-rate-limit" || echo "No rate limit headers found"

# 4. DNS resolution
echo -e "\n--- DNS Resolution ---"
dig +short api.apollo.io 2>/dev/null || nslookup api.apollo.io 2>/dev/null
```

### Step 3: Implement a Circuit Breaker
```typescript
// src/resilience/circuit-breaker.ts
type CircuitState = 'closed' | 'open' | 'half-open';

export class CircuitBreaker {
  private state: CircuitState = 'closed';
  private failures = 0;
  private lastFailure = 0;
  private successesInHalfOpen = 0;

  constructor(
    private failureThreshold: number = 5,
    private resetTimeoutMs: number = 60_000,   // 1 minute
    private halfOpenSuccesses: number = 3,
  ) {}

  async execute<T>(fn: () => Promise<T>, fallback?: () => T): Promise<T> {
    if (this.state === 'open') {
      if (Date.now() - this.lastFailure > this.resetTimeoutMs) {
        this.state = 'half-open';
        this.successesInHalfOpen = 0;
      } else {
        if (fallback) return fallback();
        throw new Error('Circuit breaker is OPEN — Apollo API calls blocked');
      }
    }

    try {
      const result = await fn();
      this.onSuccess();
      return result;
    } catch (err) {
      this.onFailure();
      if (fallback) return fallback();
      throw err;
    }
  }

  private onSuccess() {
    if (this.state === 'half-open') {
      this.successesInHalfOpen++;
      if (this.successesInHalfOpen >= this.halfOpenSuccesses) {
        this.state = 'closed';
        this.failures = 0;
      }
    }
    this.failures = 0;
  }

  private onFailure() {
    this.failures++;
    this.lastFailure = Date.now();
    if (this.failures >= this.failureThreshold) {
      this.state = 'open';
    }
  }

  get status(): { state: CircuitState; failures: number } {
    return { state: this.state, failures: this.failures };
  }
}
```

### Step 4: Define Response Procedures by Severity
```typescript
// src/resilience/response-actions.ts
import { CircuitBreaker } from './circuit-breaker';

const breaker = new CircuitBreaker(5, 60_000);

// P1: Total outage
async function handleP1() {
  console.error('[P1] Apollo API is unreachable');
  // 1. Open circuit breaker immediately
  // 2. Enable cached/stale data fallback
  // 3. Notify on-call via PagerDuty/Slack
  // 4. Post status to internal status page
  // 5. Open Apollo support ticket

  // Fallback: serve cached data
  return breaker.execute(
    () => apolloClient.post('/people/search', { per_page: 1 }),
    () => ({ data: { people: [], source: 'cache' } }),
  );
}

// P2: Partial failures / rate limiting
async function handleP2() {
  console.warn('[P2] Apollo API degraded');
  // 1. Reduce request concurrency to 1
  // 2. Enable aggressive caching
  // 3. Defer non-critical enrichments
  // 4. Alert team via Slack
}

// P3: Intermittent errors
async function handleP3() {
  console.info('[P3] Apollo API intermittent issues');
  // 1. Enable retry with backoff
  // 2. Monitor error rate
  // 3. Log to tracking issue
}
```

### Step 5: Post-Incident Review Template
```markdown
## Post-Incident Review

**Incident ID:** INC-YYYY-MM-DD-NNN
**Severity:** P1 / P2 / P3
**Duration:** HH:MM start → HH:MM resolved (X minutes)
**Apollo Status:** Was Apollo reporting an outage? Y/N

### Timeline
| Time (UTC) | Event |
|------------|-------|
| HH:MM | First alert fired |
| HH:MM | On-call acknowledged |
| HH:MM | Root cause identified |
| HH:MM | Mitigation applied |
| HH:MM | Service restored |

### Root Cause
[Description of what caused the incident]

### Impact
- Searches affected: N
- Enrichments failed: N
- Sequences paused: N
- Users impacted: N

### Action Items
- [ ] Action 1 (owner, due date)
- [ ] Action 2 (owner, due date)
```

## Output
- Severity classification matrix (P1-P4) with response time SLAs
- Bash diagnostic script testing status page, API, rate limits, and DNS
- Circuit breaker class (closed/open/half-open) with configurable thresholds
- Response procedures for each severity level
- Post-incident review template in markdown

## Error Handling
| Issue | Escalation |
|-------|------------|
| P1 > 15 min | Page on-call lead, open Apollo support ticket |
| P2 > 2 hours | Notify engineering management |
| Recurring P3 | Promote to P2 tracking issue |
| Apollo outage confirmed | Check [status.apollo.io](https://status.apollo.io), switch to cache fallback |

## Examples

### Use Circuit Breaker in Production
```typescript
const breaker = new CircuitBreaker(5, 60_000);

async function safeSearch(params: any) {
  return breaker.execute(
    () => client.post('/people/search', params),
    () => {
      console.warn('Circuit open, returning cached results');
      return getCachedSearchResults(params);
    },
  );
}

// Monitor circuit state
setInterval(() => {
  const { state, failures } = breaker.status;
  if (state !== 'closed') {
    console.warn(`Circuit breaker: ${state} (${failures} failures)`);
  }
}, 30_000);
```

## Resources
- [Apollo Status Page](https://status.apollo.io)
- [Apollo Support Portal](https://support.apollo.io)
- [Google SRE On-Call Handbook](https://sre.google/workbook/on-call/)

## Next Steps
Proceed to `apollo-data-handling` for data management.
