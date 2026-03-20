---
name: juicebox-common-errors
description: |
  Diagnose and fix common Juicebox API errors.
  Use when encountering API errors, debugging integration issues,
  or troubleshooting Juicebox connection problems.
  Trigger with phrases like "juicebox error", "fix juicebox issue",
  "juicebox not working", "debug juicebox".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Juicebox Common Errors

## Overview

Diagnose and resolve the most frequent Juicebox PeopleGPT API errors. Covers authentication failures, rate limiting, malformed search queries, missing profiles, and server-side outages. Each error includes the raw response shape, root causes, diagnostic curl commands, and a production error-handling wrapper.

## Prerequisites

- Juicebox API credentials (`JUICEBOX_USERNAME` and `JUICEBOX_API_TOKEN` environment variables)
- `curl` available for diagnostic commands
- Node.js 18+ with `fetch` or a compatible HTTP client
- Access to Juicebox status page at `https://status.juicebox.ai`

## Instructions

### Step 1: Parse Error Responses

Every Juicebox API error returns a consistent JSON envelope. Build a typed parser first so downstream code can pattern-match on structured data instead of string-matching.

```typescript
// types/juicebox-errors.ts
export interface JuiceboxErrorResponse {
  error: {
    code: string;
    message: string;
    details?: Record<string, unknown>;
    request_id: string;
  };
}

export type JuiceboxErrorCode =
  | "INVALID_TOKEN"
  | "TOKEN_EXPIRED"
  | "RATE_LIMITED"
  | "INVALID_SEARCH_PARAMS"
  | "PROFILE_NOT_FOUND"
  | "ENRICHMENT_FAILED"
  | "INTERNAL_ERROR"
  | "SERVICE_UNAVAILABLE";

export function parseErrorResponse(
  status: number,
  body: unknown
): { code: JuiceboxErrorCode; message: string; requestId: string } {
  const err = (body as JuiceboxErrorResponse).error;
  return {
    code: err.code as JuiceboxErrorCode,
    message: err.message,
    requestId: err.request_id,
  };
}
```

### Step 2: Diagnose Authentication Errors (401)

A 401 means the `Authorization: token {username}:{api_token}` header is missing, malformed, or the token has been revoked.

```bash
# Verify credentials are set
echo "Username: ${JUICEBOX_USERNAME:-(not set)}"
echo "Token: ${JUICEBOX_API_TOKEN:+(set)}"

# Test auth against the search endpoint
curl -s -o /dev/null -w "%{http_code}" \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  "https://api.juicebox.ai/api/v1/search?q=test&limit=1"

# Full response for debugging
curl -s -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  "https://api.juicebox.ai/api/v1/search?q=test&limit=1" | jq .
```

Common causes:
- Missing colon separator between username and token
- Trailing whitespace in `.env` values
- Token regenerated in dashboard but not updated locally
- Using `Bearer` scheme instead of `token` scheme

### Step 3: Handle Rate Limits (429)

When the API returns 429, the response includes `Retry-After` (seconds) and rate limit headers.

```typescript
// lib/rate-limit-handler.ts
export interface RateLimitInfo {
  limit: number;
  remaining: number;
  resetAt: Date;
  retryAfterSeconds: number;
}

export function extractRateLimitInfo(headers: Headers): RateLimitInfo {
  return {
    limit: parseInt(headers.get("X-RateLimit-Limit") ?? "0", 10),
    remaining: parseInt(headers.get("X-RateLimit-Remaining") ?? "0", 10),
    resetAt: new Date(
      parseInt(headers.get("X-RateLimit-Reset") ?? "0", 10) * 1000
    ),
    retryAfterSeconds: parseInt(headers.get("Retry-After") ?? "0", 10),
  };
}

export async function waitForRateLimit(info: RateLimitInfo): Promise<void> {
  const waitMs = info.retryAfterSeconds > 0
    ? info.retryAfterSeconds * 1000
    : Math.max(0, info.resetAt.getTime() - Date.now());
  console.warn(`Rate limited. Waiting ${waitMs}ms (reset: ${info.resetAt.toISOString()})`);
  await new Promise((resolve) => setTimeout(resolve, waitMs));
}
```

Diagnostic check:

```bash
# Inspect rate limit headers on any request
curl -s -D - \
  -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  "https://api.juicebox.ai/api/v1/search?q=engineer&limit=1" \
  | grep -i "x-ratelimit\|retry-after"
```

### Step 4: Validate Search Parameters (400)

A 400 from `/api/v1/search` means the query or filter parameters are malformed. The `details` field pinpoints the issue.

```typescript
// lib/search-validator.ts
export interface SearchParams {
  q: string;
  limit?: number;
  offset?: number;
  location?: string;
  title?: string;
  company?: string;
  skills?: string[];
}

export function validateSearchParams(params: SearchParams): string[] {
  const errors: string[] = [];

  if (!params.q || params.q.trim().length === 0) {
    errors.push("Query string 'q' is required and cannot be empty");
  }

  if (params.limit !== undefined && (params.limit < 1 || params.limit > 100)) {
    errors.push("'limit' must be between 1 and 100");
  }

  if (params.offset !== undefined && params.offset < 0) {
    errors.push("'offset' must be >= 0");
  }

  // Check for unbalanced quotes or parentheses in query
  const quotes = (params.q.match(/"/g) ?? []).length;
  if (quotes % 2 !== 0) {
    errors.push("Query contains unbalanced double quotes");
  }

  return errors;
}
```

### Step 5: Handle Profile Not Found (404)

A 404 from `/api/v1/profiles/{id}` means the profile ID is invalid, the profile was removed, or a stale cache reference exists.

```typescript
// lib/profile-lookup.ts
export async function safeGetProfile(
  profileId: string,
  authHeader: string
): Promise<{ found: true; profile: Profile } | { found: false; reason: string }> {
  const res = await fetch(
    `https://api.juicebox.ai/api/v1/profiles/${encodeURIComponent(profileId)}`,
    { headers: { Authorization: authHeader } }
  );

  if (res.status === 404) {
    return {
      found: false,
      reason: `Profile '${profileId}' not found. It may have been removed or the ID is stale.`,
    };
  }

  if (!res.ok) {
    throw new Error(`Unexpected status ${res.status}: ${await res.text()}`);
  }

  return { found: true, profile: (await res.json()) as Profile };
}
```

### Step 6: Handle Server Errors (500/503)

Server errors are transient. Retry with exponential backoff and check the status page before opening a support ticket.

```bash
# Check Juicebox service status
curl -s "https://status.juicebox.ai/api/status" | jq '.status, .incidents[0]'

# Check API health endpoint
curl -s -o /dev/null -w "%{http_code}" "https://api.juicebox.ai/api/v1/health"
```

### Step 7: Comprehensive Error Handling Wrapper

Combine all error patterns into a single wrapper that handles every status code.

```typescript
// lib/juicebox-error-handler.ts
import { parseErrorResponse, JuiceboxErrorCode } from "../types/juicebox-errors";
import { extractRateLimitInfo, waitForRateLimit } from "./rate-limit-handler";

export class JuiceboxApiError extends Error {
  constructor(
    public readonly status: number,
    public readonly code: JuiceboxErrorCode,
    public readonly requestId: string,
    message: string
  ) {
    super(message);
    this.name = "JuiceboxApiError";
  }
}

export async function juiceboxFetch(
  url: string,
  options: RequestInit & { maxRetries?: number } = {}
): Promise<Response> {
  const { maxRetries = 3, ...fetchOpts } = options;
  const authHeader = `token ${process.env.JUICEBOX_USERNAME}:${process.env.JUICEBOX_API_TOKEN}`;

  for (let attempt = 0; attempt <= maxRetries; attempt++) {
    const res = await fetch(url, {
      ...fetchOpts,
      headers: {
        Authorization: authHeader,
        "Content-Type": "application/json",
        ...fetchOpts.headers,
      },
    });

    // Success
    if (res.ok) return res;

    // Rate limited — wait and retry
    if (res.status === 429) {
      const rateLimitInfo = extractRateLimitInfo(res.headers);
      if (attempt < maxRetries) {
        await waitForRateLimit(rateLimitInfo);
        continue;
      }
    }

    // Server error — retry with exponential backoff
    if (res.status >= 500 && attempt < maxRetries) {
      const delay = Math.min(1000 * Math.pow(2, attempt), 30000);
      const jitter = Math.random() * 500;
      await new Promise((r) => setTimeout(r, delay + jitter));
      continue;
    }

    // Client error or exhausted retries — throw structured error
    const body = await res.json().catch(() => ({
      error: { code: "UNKNOWN", message: res.statusText, request_id: "n/a" },
    }));
    const parsed = parseErrorResponse(res.status, body);
    throw new JuiceboxApiError(res.status, parsed.code, parsed.requestId, parsed.message);
  }

  throw new Error("Unreachable: exhausted retries without throwing");
}
```

## Output

- `types/juicebox-errors.ts` — Typed error response parser with exhaustive error codes
- `lib/rate-limit-handler.ts` — Rate limit header extractor and wait logic
- `lib/search-validator.ts` — Pre-flight search parameter validation
- `lib/profile-lookup.ts` — Safe profile fetch with 404 handling
- `lib/juicebox-error-handler.ts` — Production error wrapper with retry, backoff, and structured exceptions
- Diagnostic curl commands for auth, rate limits, and service health

## Error Handling

| HTTP Status | Error Code | Cause | Resolution |
|-------------|-----------|-------|------------|
| 401 | `INVALID_TOKEN` | Missing, malformed, or revoked `token user:key` header | Verify `JUICEBOX_USERNAME` and `JUICEBOX_API_TOKEN`; regenerate token in dashboard |
| 401 | `TOKEN_EXPIRED` | API token past expiry date | Regenerate token at `https://app.juicebox.ai/settings/api` |
| 429 | `RATE_LIMITED` | Exceeded per-minute or daily quota | Read `Retry-After` header; implement exponential backoff |
| 400 | `INVALID_SEARCH_PARAMS` | Bad query syntax, invalid field, out-of-range limit | Validate params client-side before sending; check `details` field |
| 404 | `PROFILE_NOT_FOUND` | Stale ID, removed profile, or typo | Verify profile ID format; invalidate cache; re-search |
| 500 | `INTERNAL_ERROR` | Server-side bug | Retry with backoff; include `request_id` in support ticket |
| 503 | `SERVICE_UNAVAILABLE` | Planned maintenance or overload | Check `https://status.juicebox.ai`; retry after status clears |

## Examples

### Diagnosing a 401 from the CLI

```bash
# Step 1: confirm env vars
env | grep JUICEBOX

# Step 2: make a minimal authenticated request
curl -v -H "Authorization: token ${JUICEBOX_USERNAME}:${JUICEBOX_API_TOKEN}" \
  "https://api.juicebox.ai/api/v1/search?q=CEO&limit=1" 2>&1 \
  | grep "< HTTP\|error"

# Step 3: if 401, regenerate token and re-export
export JUICEBOX_API_TOKEN="new-token-from-dashboard"
```

### Using the Error Wrapper in Application Code

```typescript
import { juiceboxFetch, JuiceboxApiError } from "./lib/juicebox-error-handler";

async function searchCandidates(query: string) {
  try {
    const res = await juiceboxFetch(
      `https://api.juicebox.ai/api/v1/search?q=${encodeURIComponent(query)}&limit=25`
    );
    return await res.json();
  } catch (err) {
    if (err instanceof JuiceboxApiError) {
      console.error(
        `[${err.code}] ${err.message} (request: ${err.requestId}, status: ${err.status})`
      );
      if (err.code === "INVALID_SEARCH_PARAMS") {
        // Surface validation error to the user
        return { profiles: [], error: err.message };
      }
    }
    throw err;
  }
}
```

### Batch Error Handling with Per-Item Recovery

```typescript
import { juiceboxFetch, JuiceboxApiError } from "./lib/juicebox-error-handler";

async function enrichBatch(profileIds: string[]) {
  const results: Array<{ id: string; profile?: Profile; error?: string }> = [];

  for (const id of profileIds) {
    try {
      const res = await juiceboxFetch(
        `https://api.juicebox.ai/api/v1/profiles/${id}`
      );
      results.push({ id, profile: await res.json() });
    } catch (err) {
      if (err instanceof JuiceboxApiError && err.status === 404) {
        results.push({ id, error: `Profile ${id} not found — skipping` });
        continue;
      }
      throw err; // Re-throw non-recoverable errors
    }
  }

  const succeeded = results.filter((r) => r.profile).length;
  console.log(`Enriched ${succeeded}/${profileIds.length} profiles`);
  return results;
}
```

## Resources

- [Juicebox API Documentation](https://juicebox.ai/docs/api)
- [Error Codes Reference](https://juicebox.ai/docs/errors)
- [Service Status Page](https://status.juicebox.ai)
- [Rate Limits Documentation](https://juicebox.ai/docs/rate-limits)

## Next Steps

After resolving errors, see `juicebox-debug-bundle` for collecting full diagnostic snapshots, or `juicebox-rate-limits` for advanced rate limiting strategies.
