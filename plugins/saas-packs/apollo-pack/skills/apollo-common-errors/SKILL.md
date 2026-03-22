---
name: apollo-common-errors
description: |
  Diagnose and fix common Apollo.io API errors.
  Use when encountering Apollo API errors, debugging integration issues,
  or troubleshooting failed requests.
  Trigger with phrases like "apollo error", "apollo api error",
  "debug apollo", "apollo 401", "apollo 429", "apollo troubleshoot".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, apollo, api, debugging]

---
# Apollo Common Errors

## Overview
Comprehensive guide to diagnosing and fixing Apollo.io API errors. Apollo uses `x-api-key` header authentication and the base URL `https://api.apollo.io/api/v1/`. Apollo distinguishes between **master** and **standard** API keys — many endpoints require master keys.

## Prerequisites
- Valid Apollo.io API credentials
- Node.js 18+ or Python 3.10+

## Instructions

### Step 1: Identify the Error Category
```typescript
// src/apollo/error-handler.ts
import { AxiosError } from 'axios';

type ErrorCategory = 'auth' | 'permission' | 'rate_limit' | 'validation' | 'server' | 'network';

function categorizeError(err: AxiosError): ErrorCategory {
  if (!err.response) return 'network';
  switch (err.response.status) {
    case 401: return 'auth';
    case 403: return 'permission';
    case 429: return 'rate_limit';
    case 400: case 422: return 'validation';
    default: return err.response.status >= 500 ? 'server' : 'validation';
  }
}
```

### Step 2: Handle 401 — Invalid API Key
```typescript
// Most common cause: missing x-api-key header or wrong key format
async function diagnoseAuth() {
  try {
    const response = await fetch('https://api.apollo.io/api/v1/auth/health', {
      headers: { 'x-api-key': process.env.APOLLO_API_KEY! },
    });
    const data = await response.json();
    if (data.is_logged_in) {
      console.log('API key is valid');
    } else {
      console.error('API key is invalid or expired');
      console.error('  Generate a new one at: Apollo > Settings > Integrations > API Keys');
    }
  } catch (err: any) {
    console.error('Cannot reach Apollo API:', err.message);
  }
}
```

**Common 401 causes:**
1. Using `api_key` query parameter instead of `x-api-key` header
2. Key was revoked or regenerated in the dashboard
3. Key has trailing whitespace (check with `echo -n "$APOLLO_API_KEY" | wc -c`)

### Step 3: Handle 403 — Wrong Key Type
```
Standard API key: search + enrichment only
Master API key:   full access (contacts, sequences, deals, tasks)
```

Endpoints that **require a master key**:
- `POST /contacts` (create/update)
- `POST /emailer_campaigns/search` (sequences)
- `POST /emailer_campaigns/{id}/add_contact_ids`
- `POST /opportunities` (deals)
- `POST /tasks` (tasks)
- `DELETE /contacts/{id}`

```typescript
// Diagnose: test a master-key-only endpoint
async function diagnoseMasterKey() {
  try {
    await client.post('/contacts/search', { per_page: 1 });
    console.log('Master API key confirmed');
  } catch (err: any) {
    if (err.response?.status === 403) {
      console.error('Your API key is a standard key. Master key required.');
      console.error('  Go to Apollo > Settings > Integrations > API Keys');
      console.error('  Generate a new key with "Master Key" type');
    }
  }
}
```

### Step 4: Handle 429 — Rate Limiting
Apollo uses fixed-window rate limiting per endpoint category:

```
Endpoint Category         | Limit      | Window  | Burst
--------------------------+------------+---------+------
People Search             | 100/min    | 1 min   | 10/sec
People Enrichment         | 100/min    | 1 min   | 10/sec
Bulk People Enrichment    | 10/min     | 1 min   | 2/sec
Organization Enrichment   | 100/min    | 1 min   | 10/sec
Contacts (CRUD)           | 100/min    | 1 min   | 10/sec
Sequences                 | 100/min    | 1 min   | 10/sec
```

```typescript
// Respect Retry-After header
async function handleRateLimit<T>(fn: () => Promise<T>): Promise<T> {
  try {
    return await fn();
  } catch (err: any) {
    if (err.response?.status === 429) {
      const retryAfter = parseInt(err.response.headers['retry-after'] ?? '60', 10);
      console.warn(`Rate limited. Waiting ${retryAfter}s...`);
      await new Promise((r) => setTimeout(r, retryAfter * 1000));
      return fn();
    }
    throw err;
  }
}
```

### Step 5: Handle 422 — Validation Errors
```typescript
// Common 422 causes:
//   - per_page > 100 on search endpoints
//   - Missing required fields on /contacts POST (first_name, last_name)
//   - Invalid email format on /people/match
//   - page > 500 on /mixed_people/api_search (50,000 record limit)

function logValidationError(err: AxiosError) {
  const body = err.response?.data as any;
  console.error('Validation error:', {
    status: err.response?.status,
    message: body?.message ?? body?.error,
    errors: body?.errors,
    url: err.config?.url,
    body: typeof err.config?.data === 'string' ? JSON.parse(err.config.data) : err.config?.data,
  });
}
```

### Step 6: Build Comprehensive Error Middleware
```typescript
// src/apollo/error-middleware.ts
import { AxiosError, AxiosInstance } from 'axios';

export function attachErrorHandler(client: AxiosInstance) {
  client.interceptors.response.use(
    (response) => response,
    (err: AxiosError) => {
      const status = err.response?.status;
      const body = err.response?.data as any;
      const endpoint = err.config?.url ?? 'unknown';

      const info = {
        status,
        endpoint,
        message: body?.message ?? err.message,
        timestamp: new Date().toISOString(),
      };

      switch (categorizeError(err)) {
        case 'auth':
          console.error('[APOLLO AUTH] Invalid x-api-key header', info);
          break;
        case 'permission':
          console.error('[APOLLO PERMISSION] Master key required for this endpoint', info);
          break;
        case 'rate_limit':
          console.warn('[APOLLO RATE LIMIT]', info);
          break;
        case 'validation':
          console.error('[APOLLO VALIDATION]', info);
          break;
        case 'server':
          console.error('[APOLLO SERVER] Check status.apollo.io', info);
          break;
        case 'network':
          console.error('[APOLLO NETWORK] Cannot reach api.apollo.io', info);
          break;
      }

      return Promise.reject(err);
    },
  );
}
```

## Error Reference
| Code | Meaning | Fix |
|------|---------|-----|
| 401 | Invalid or missing `x-api-key` header | Verify key in dashboard, check header name |
| 403 | Standard key used for master-only endpoint | Generate master API key |
| 422 | Bad request body | Check field names, per_page <= 100, page <= 500 |
| 429 | Rate limit exceeded | Read `Retry-After` header, implement backoff |
| 500 | Apollo server error | Retry with backoff, check [status.apollo.io](https://status.apollo.io) |
| ECONNREFUSED | Network/firewall | Allow outbound HTTPS to `api.apollo.io:443` |

## Examples

### Quick cURL Diagnostic
```bash
# Test auth (should return is_logged_in: true)
curl -s -H "x-api-key: $APOLLO_API_KEY" \
  https://api.apollo.io/api/v1/auth/health | python3 -m json.tool

# Test master key (returns contacts or 403)
curl -s -X POST -H "Content-Type: application/json" -H "x-api-key: $APOLLO_API_KEY" \
  -d '{"per_page":1}' https://api.apollo.io/api/v1/contacts/search | python3 -m json.tool
```

## Resources
- [Apollo API Error Reference](https://docs.apollo.io/reference/rate-limits)
- [Apollo Status Page](https://status.apollo.io)
- [Create API Keys](https://docs.apollo.io/docs/create-api-key)
- [API Usage Stats](https://docs.apollo.io/reference/view-api-usage-stats)

## Next Steps
Proceed to `apollo-debug-bundle` for collecting debug evidence.
