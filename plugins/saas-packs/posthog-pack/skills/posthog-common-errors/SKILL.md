---
name: posthog-common-errors
description: |
  Diagnose and fix common PostHog errors: events not appearing, flags returning
  undefined, 401/429 errors, SDK initialization failures, and identity issues.
  Trigger: "posthog error", "fix posthog", "posthog not working",
  "debug posthog", "posthog events missing", "posthog broken".
allowed-tools: Read, Grep, Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, debugging]
---

# PostHog Common Errors

## Overview

Diagnosis and solutions for the most common PostHog integration errors. Covers event capture failures, authentication issues, feature flag problems, identity fragmentation, and SDK initialization errors.

## Prerequisites

- PostHog SDK installed (`posthog-js` or `posthog-node`)
- Access to browser console or server logs
- PostHog project API key (`phc_...`) available

## Instructions

### Error 1: Events Not Appearing in Dashboard

**Symptoms:** `posthog.capture()` calls execute without error but events never show in PostHog Activity tab.

**Diagnoses and fixes:**

```typescript
// Problem A: Not flushing in serverless/scripts
// posthog-node queues events — they're lost if process exits before flush
const posthog = new PostHog('phc_...');
posthog.capture({ distinctId: 'user-1', event: 'test' });
// FIX: Always flush before exit
await posthog.shutdown(); // or await posthog.flush()

// Problem B: Wrong API host
posthog.init('phc_...', {
  api_host: 'https://app.posthog.com', // WRONG — this is the UI
});
// FIX: Use the ingest endpoint
posthog.init('phc_...', {
  api_host: 'https://us.i.posthog.com', // CORRECT for US Cloud
  // api_host: 'https://eu.i.posthog.com', // For EU Cloud
});

// Problem C: Ad blocker blocking posthog-js requests
// FIX: Set up a reverse proxy (see posthog-sdk-patterns)
// next.config.js rewrites: /ingest/* → us.i.posthog.com/*
// Then: posthog.init('phc_...', { api_host: '/ingest' });
```

### Error 2: Feature Flag Returns `undefined` or Wrong Value

```typescript
// Problem: Checking flag before flags are loaded
const value = posthog.isFeatureEnabled('my-flag'); // undefined — flags not ready

// FIX: Wait for flags to load
posthog.onFeatureFlags(() => {
  const value = posthog.isFeatureEnabled('my-flag'); // Now has correct value
});

// Problem (server): No personalApiKey — falls back to remote evaluation
const ph = new PostHog('phc_...'); // Missing personalApiKey
const flag = await ph.getFeatureFlag('my-flag', 'user-1'); // Slow, may fail

// FIX: Add personalApiKey for local evaluation
const ph = new PostHog('phc_...', {
  personalApiKey: process.env.POSTHOG_PERSONAL_API_KEY, // phx_...
});
// Now evaluates locally — faster and more reliable
```

### Error 3: 401 Unauthorized on API Calls

```bash
set -euo pipefail
# Symptom: 401 when calling admin endpoints
curl "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/feature_flags/" \
  -H "Authorization: Bearer phc_wrong_key_type"
# Returns: {"detail": "Authentication credentials were not provided."}

# FIX: Use Personal API Key (phx_...) for admin endpoints, not project key (phc_...)
curl "https://app.posthog.com/api/projects/$POSTHOG_PROJECT_ID/feature_flags/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY"  # Must be phx_...

# Check which key type you have:
echo "$POSTHOG_PERSONAL_API_KEY" | head -c 4
# phx_ = Personal API Key (correct for admin API)
# phc_ = Project API Key (only for event capture)
```

### Error 4: 429 Rate Limited

```typescript
// Symptom: HTTP 429 on analytics endpoints
// PostHog rate limits: 240 req/min and 1200 req/hour for analytics endpoints
// Feature flag local eval: 600 req/min

// FIX: Implement backoff with Retry-After header
async function postHogRequest(url: string, options: RequestInit) {
  const response = await fetch(url, options);

  if (response.status === 429) {
    const retryAfter = parseInt(response.headers.get('Retry-After') || '60');
    console.warn(`PostHog rate limited. Retrying in ${retryAfter}s`);
    await new Promise(r => setTimeout(r, retryAfter * 1000));
    return postHogRequest(url, options); // Retry
  }

  return response;
}

// FIX: Cache insight results instead of polling
let cachedInsights: any = null;
let cacheExpiry = 0;

async function getInsights() {
  if (cachedInsights && Date.now() < cacheExpiry) return cachedInsights;

  const res = await postHogRequest(
    `https://app.posthog.com/api/projects/${PROJECT_ID}/insights/trend/`,
    { headers: { Authorization: `Bearer ${PERSONAL_KEY}` } }
  );
  cachedInsights = await res.json();
  cacheExpiry = Date.now() + 300000; // Cache 5 minutes
  return cachedInsights;
}
```

### Error 5: Identity Fragmentation (Duplicate Users)

```typescript
// Problem: Same user appears as multiple persons in PostHog
// Cause: Different distinct_id on frontend vs backend

// Frontend captures with anonymous ID: "anon-abc123"
posthog.capture('page_viewed'); // distinct_id = "anon-abc123"

// Backend captures with user ID: "user-456"
serverPosthog.capture({
  distinctId: 'user-456', // Different from frontend!
  event: 'api_called',
});

// FIX: Call identify on frontend to merge anonymous → known
posthog.identify('user-456'); // Merges anon-abc123 → user-456

// FIX: Use same distinct_id on server as frontend
serverPosthog.capture({
  distinctId: 'user-456', // Same as what frontend uses after identify
  event: 'api_called',
});
```

### Error 6: posthog-js Not Loading or Initializing

```typescript
// Problem: posthog.capture is not a function
// Cause: SDK not initialized or called server-side

// FIX: Guard all browser calls
if (typeof window !== 'undefined') {
  posthog.init('phc_...', { api_host: 'https://us.i.posthog.com' });
}

// FIX: Check if initialized before capturing
if (typeof posthog.capture === 'function') {
  posthog.capture('my_event');
}

// Problem: CSP (Content Security Policy) blocking PostHog
// FIX: Add PostHog domains to your CSP header
// connect-src: https://us.i.posthog.com https://us-assets.i.posthog.com
```

### Quick Diagnostic Commands

```bash
set -euo pipefail
# 1. Check PostHog API reachability
curl -s -o /dev/null -w "HTTP %{http_code}\n" https://us.i.posthog.com/healthz

# 2. Verify project API key works (send test event)
curl -s -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d "{\"api_key\":\"$NEXT_PUBLIC_POSTHOG_KEY\",\"event\":\"diagnostic_test\",\"distinct_id\":\"debug\"}" | jq .

# 3. Verify personal API key works
curl -s "https://app.posthog.com/api/projects/" \
  -H "Authorization: Bearer $POSTHOG_PERSONAL_API_KEY" | jq '.[0].name'

# 4. Check installed SDK versions
npm list posthog-js posthog-node 2>/dev/null || echo "No PostHog SDK found"

# 5. Check environment variables
env | grep -i posthog | sed 's/=.*/=***/'
```

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| Events missing | N/A | Not flushed | `await posthog.shutdown()` |
| Auth failed | 401 | Wrong key type | Use `phx_` for admin, `phc_` for capture |
| Rate limited | 429 | Too many API calls | Backoff, cache results |
| Flag undefined | N/A | Flags not loaded | Use `onFeatureFlags` callback |
| CSP blocked | N/A | Missing CSP entry | Add `us.i.posthog.com` to connect-src |
| Duplicate users | N/A | Identity mismatch | Call `posthog.identify()` consistently |

## Output

- Root cause identified for PostHog integration errors
- Fix applied with verification steps
- Diagnostic output confirming resolution

## Resources

- [PostHog Troubleshooting](https://posthog.com/docs/feature-flags/common-questions)
- [PostHog Status Page](https://status.posthog.com)
- [PostHog API Overview](https://posthog.com/docs/api)

## Next Steps

For comprehensive debugging, see `posthog-debug-bundle`.
