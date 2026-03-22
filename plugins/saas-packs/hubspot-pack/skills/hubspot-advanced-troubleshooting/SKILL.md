---
name: hubspot-advanced-troubleshooting
description: |
  Debug complex HubSpot API issues with systematic isolation and evidence collection.
  Use when standard troubleshooting fails, investigating intermittent CRM errors,
  or preparing evidence bundles for HubSpot support escalation.
  Trigger with phrases like "hubspot hard bug", "hubspot mystery error",
  "hubspot intermittent failure", "hubspot deep debug", "hubspot support ticket".
allowed-tools: Read, Grep, Bash(kubectl:*), Bash(curl:*), Bash(tcpdump:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Advanced Troubleshooting

## Overview

Deep debugging techniques for complex HubSpot API issues: systematic layer testing, timing analysis, correlation ID tracking, and support escalation.

## Prerequisites

- Access to application logs
- `curl` and `jq` available
- HubSpot access token for manual testing

## Instructions

### Step 1: Systematic Layer Testing

Test each layer independently to isolate the failure:

```bash
#!/bin/bash
# hubspot-layer-test.sh

echo "=== HubSpot Layer-by-Layer Diagnostic ==="

# Layer 1: DNS Resolution
echo "1. DNS Resolution"
dig api.hubapi.com +short || echo "FAIL: DNS resolution"

# Layer 2: TCP Connectivity
echo "2. TCP Connectivity"
timeout 5 bash -c 'echo > /dev/tcp/api.hubapi.com/443' 2>/dev/null \
  && echo "OK" || echo "FAIL: Cannot reach port 443"

# Layer 3: TLS Handshake
echo "3. TLS Handshake"
echo | openssl s_client -connect api.hubapi.com:443 2>/dev/null | grep "Verify return code"

# Layer 4: HTTP Response (unauthenticated)
echo "4. HTTP Response (no auth)"
curl -so /dev/null -w "HTTP %{http_code} in %{time_total}s\n" \
  https://api.hubapi.com/crm/v3/objects/contacts?limit=1

# Layer 5: Authenticated Request
echo "5. Authenticated Request"
RESPONSE=$(curl -s -w "\n%{http_code}" \
  https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN")
HTTP_CODE=$(echo "$RESPONSE" | tail -1)
BODY=$(echo "$RESPONSE" | head -n -1)
echo "HTTP $HTTP_CODE"

if [ "$HTTP_CODE" = "200" ]; then
  echo "OK: API accessible"
  echo "Records: $(echo $BODY | jq '.results | length')"
else
  echo "FAIL: $(echo $BODY | jq -r '.category // .message')"
  echo "Correlation ID: $(echo $BODY | jq -r '.correlationId // "none"')"
fi

# Layer 6: Rate Limit State
echo "6. Rate Limit State"
curl -sI https://api.hubapi.com/crm/v3/objects/contacts?limit=1 \
  -H "Authorization: Bearer $HUBSPOT_ACCESS_TOKEN" \
  | grep -i "ratelimit" | sed 's/^/   /'
```

### Step 2: Correlation ID Tracking

Every HubSpot error response includes a `correlationId`. Track these for support:

```typescript
import * as hubspot from '@hubspot/api-client';

// Collect correlation IDs from errors
const errorLog: Array<{
  timestamp: string;
  correlationId: string;
  statusCode: number;
  category: string;
  message: string;
  endpoint: string;
}> = [];

async function debuggedApiCall<T>(
  endpoint: string,
  operation: () => Promise<T>
): Promise<T> {
  try {
    return await operation();
  } catch (error: any) {
    const body = error?.body || {};
    const entry = {
      timestamp: new Date().toISOString(),
      correlationId: body.correlationId || 'unknown',
      statusCode: error?.code || error?.statusCode || 500,
      category: body.category || 'UNKNOWN',
      message: body.message || error.message,
      endpoint,
    };
    errorLog.push(entry);
    console.error('HubSpot error:', entry);
    throw error;
  }
}

// Dump error log for support ticket
function getErrorReport(): string {
  return errorLog.map(e =>
    `[${e.timestamp}] ${e.statusCode} ${e.category} | ${e.correlationId} | ${e.endpoint}: ${e.message}`
  ).join('\n');
}
```

### Step 3: Timing Analysis

```typescript
async function timingAnalysis() {
  const operations = [
    {
      name: 'GET contacts (single)',
      fn: () => client.crm.contacts.basicApi.getPage(1, undefined, ['email']),
    },
    {
      name: 'SEARCH contacts',
      fn: () => client.crm.contacts.searchApi.doSearch({
        filterGroups: [{
          filters: [{ propertyName: 'lifecyclestage', operator: 'EQ', value: 'lead' }],
        }],
        properties: ['email'], limit: 1, after: 0, sorts: [],
      }),
    },
    {
      name: 'GET pipelines',
      fn: () => client.crm.pipelines.pipelinesApi.getAll('deals'),
    },
    {
      name: 'GET properties',
      fn: () => client.crm.properties.coreApi.getAll('contacts'),
    },
  ];

  console.log('=== HubSpot Timing Analysis ===');
  for (const op of operations) {
    const times: number[] = [];
    for (let i = 0; i < 5; i++) {
      const start = performance.now();
      try {
        await op.fn();
        times.push(performance.now() - start);
      } catch {
        times.push(-1); // mark failures
      }
    }

    const successful = times.filter(t => t >= 0);
    if (successful.length > 0) {
      console.log(`${op.name}:
  Min: ${Math.min(...successful).toFixed(0)}ms
  Max: ${Math.max(...successful).toFixed(0)}ms
  Avg: ${(successful.reduce((a, b) => a + b, 0) / successful.length).toFixed(0)}ms
  Failures: ${times.length - successful.length}/5`);
    } else {
      console.log(`${op.name}: ALL FAILED`);
    }
  }
}
```

### Step 4: Reproduce Specific Error

```typescript
// Reproduce common intermittent issues

// Test 1: Rapid sequential calls (rate limit sensitivity)
async function testRateLimit(requestCount = 20) {
  console.log(`Sending ${requestCount} rapid requests...`);
  let success = 0, rateLimited = 0, errors = 0;

  for (let i = 0; i < requestCount; i++) {
    try {
      await client.crm.contacts.basicApi.getPage(1, undefined, ['email']);
      success++;
    } catch (error: any) {
      if (error?.code === 429) rateLimited++;
      else errors++;
    }
  }
  console.log(`Results: ${success} ok, ${rateLimited} rate limited, ${errors} errors`);
}

// Test 2: Concurrent requests (connection pool issues)
async function testConcurrency(concurrent = 10) {
  console.log(`Sending ${concurrent} concurrent requests...`);
  const results = await Promise.allSettled(
    Array.from({ length: concurrent }, () =>
      client.crm.contacts.basicApi.getPage(1, undefined, ['email'])
    )
  );

  const fulfilled = results.filter(r => r.status === 'fulfilled').length;
  const rejected = results.filter(r => r.status === 'rejected').length;
  console.log(`Results: ${fulfilled} ok, ${rejected} failed`);

  const failures = results.filter(r => r.status === 'rejected') as PromiseRejectedResult[];
  for (const f of failures) {
    console.log(`  Error: ${f.reason?.code} ${f.reason?.body?.category}`);
  }
}
```

### Step 5: Support Escalation Template

```markdown
## HubSpot Support Escalation

**Severity:** P[1-4]
**Portal ID:** [your portal ID]
**Correlation IDs:** [list from error log]

### Issue Summary
[1-2 sentence description]

### Steps to Reproduce
1. Make API call: POST /crm/v3/objects/contacts/search
2. With body: { "filterGroups": [...], "properties": ["email"], "limit": 10 }
3. Observe: 500 Internal Server Error

### Error Response
```json
{
  "status": "error",
  "message": "[exact error message]",
  "correlationId": "[exact ID]",
  "category": "[exact category]"
}
```

### Environment
- SDK: @hubspot/api-client v[version]
- Node.js: v[version]
- Auth: Private app token

### Timeline
- [time]: First occurrence
- [time]: Frequency increased
- [time]: Pattern identified

### What We've Tried
1. [Workaround 1] - Result
2. [Workaround 2] - Result
```

## Output

- Layer-by-layer diagnostic isolating the failure point
- Correlation ID collection for support tickets
- Timing analysis identifying latency patterns
- Reproduction scripts for rate limit and concurrency issues
- Support escalation template with all required evidence

## Error Handling

| Scenario | Diagnostic | Next Step |
|----------|-----------|-----------|
| DNS fails | Check resolver config | Try `8.8.8.8` resolver |
| TLS fails | Certificate issue | Check system CA bundle |
| 401 after working | Token rotated | Regenerate in Settings |
| Intermittent 500 | HubSpot server issue | Collect correlation IDs, file ticket |
| Latency spikes | Network or HubSpot load | Run timing analysis over time |

## Resources

- [HubSpot Support Portal](https://help.hubspot.com/)
- [HubSpot Developer Community](https://community.hubspot.com/t5/APIs-Integrations/bd-p/integration)
- [Error Handling Guide](https://developers.hubspot.com/docs/api-reference/error-handling)

## Next Steps

For load testing, see `hubspot-load-scale`.
