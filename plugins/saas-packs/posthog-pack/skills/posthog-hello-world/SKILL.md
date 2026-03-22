---
name: posthog-hello-world
description: |
  Create a minimal working PostHog example with event capture, identify, and feature flags.
  Use when starting a new PostHog integration, testing your setup,
  or learning basic posthog-js and posthog-node patterns.
  Trigger: "posthog hello world", "posthog example", "posthog quick start",
  "simple posthog code", "first posthog event".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, posthog, api, testing]
---

# PostHog Hello World

## Overview

Minimal working examples demonstrating the three core PostHog operations: capturing events, identifying users, and evaluating feature flags. Covers both browser (`posthog-js`) and server (`posthog-node`) SDKs.

## Prerequisites

- Completed `posthog-install-auth` setup
- Project API key (`phc_...`) configured
- `posthog-js` and/or `posthog-node` installed

## Instructions

### Step 1: Capture Your First Event (Node.js)

```typescript
// hello-posthog.ts
import { PostHog } from 'posthog-node';

const posthog = new PostHog(process.env.NEXT_PUBLIC_POSTHOG_KEY!, {
  host: 'https://us.i.posthog.com',
});

async function main() {
  // 1. Capture a custom event
  posthog.capture({
    distinctId: 'user-123',
    event: 'hello_posthog',
    properties: {
      greeting: 'Hello from posthog-node!',
      source: 'hello-world-skill',
      timestamp: new Date().toISOString(),
    },
  });
  console.log('Event captured: hello_posthog');

  // 2. Identify a user with properties
  posthog.identify({
    distinctId: 'user-123',
    properties: {
      email: 'dev@example.com',
      name: 'Dev User',
      plan: 'free',
    },
  });
  console.log('User identified: user-123');

  // 3. Check a feature flag
  const flagValue = await posthog.getFeatureFlag('my-feature-flag', 'user-123');
  console.log(`Feature flag "my-feature-flag": ${flagValue}`);

  // 4. Flush and shutdown (required in scripts/serverless)
  await posthog.shutdown();
  console.log('Done — check app.posthog.com Activity tab');
}

main().catch(console.error);
```

### Step 2: Browser Hello World (posthog-js)

```typescript
// In a React component or vanilla JS
import posthog from 'posthog-js';

// Initialize (call once at app startup)
posthog.init('phc_your_project_key', {
  api_host: 'https://us.i.posthog.com',
  loaded: () => console.log('PostHog loaded'),
});

// Capture a custom event
posthog.capture('button_clicked', {
  button_name: 'signup',
  page: window.location.pathname,
});

// Identify the user after login
posthog.identify('user-123', {
  email: 'user@example.com',
  plan: 'pro',
});

// Check a feature flag
if (posthog.isFeatureEnabled('new-checkout')) {
  console.log('New checkout flow is enabled');
}

// Associate user with a company (group analytics)
posthog.group('company', 'company-456', {
  name: 'Acme Corp',
  plan: 'enterprise',
});
```

### Step 3: Python Hello World

```python
import posthog

posthog.project_api_key = 'phc_your_project_key'
posthog.host = 'https://us.i.posthog.com'

# Capture event
posthog.capture('user-123', 'hello_posthog', {
    'greeting': 'Hello from Python!',
})

# Identify user
posthog.identify('user-123', {
    'email': 'dev@example.com',
    'plan': 'free',
})

# Feature flag
is_enabled = posthog.feature_enabled('my-flag', 'user-123')
print(f'Flag enabled: {is_enabled}')
```

### Step 4: Raw HTTP API (No SDK)

```bash
set -euo pipefail
# Capture event via POST to /capture/
curl -X POST 'https://us.i.posthog.com/capture/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "phc_your_project_key",
    "event": "hello_posthog",
    "distinct_id": "user-123",
    "properties": {
      "greeting": "Hello from curl!"
    }
  }'

# Batch capture multiple events
curl -X POST 'https://us.i.posthog.com/batch/' \
  -H 'Content-Type: application/json' \
  -d '{
    "api_key": "phc_your_project_key",
    "batch": [
      {"event": "page_viewed", "distinct_id": "user-123", "properties": {"page": "/home"}},
      {"event": "button_clicked", "distinct_id": "user-123", "properties": {"button": "cta"}}
    ]
  }'
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Events not in dashboard | Not flushed | Call `await posthog.shutdown()` or `posthog.flush()` |
| `posthog.init` silently fails | Wrong API host | Use `us.i.posthog.com` (not `app.posthog.com`) |
| Feature flag returns `undefined` | Flag not created yet | Create flag in PostHog dashboard first |
| `identify` not linking | Different `distinct_id` | Frontend and backend must use the same `distinct_id` |
| Python events missing | No flush before exit | `posthog.shutdown()` or `posthog.flush()` at end |

## Output

- Working event capture in PostHog Activity tab
- User identified with properties in Persons view
- Feature flag evaluation result logged
- Console output confirming each operation

## Resources

- [PostHog Getting Started](https://posthog.com/docs/getting-started/install)
- [Capture Events](https://posthog.com/docs/product-analytics/capture-events)
- [posthog-node Reference](https://posthog.com/docs/libraries/node)
- [Capture API Endpoint](https://posthog.com/docs/api/capture)

## Next Steps

Proceed to `posthog-local-dev-loop` for development workflow setup.
