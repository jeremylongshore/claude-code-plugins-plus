# Klaviyo Local Dev Loop — Full Implementation

Detailed, copy-paste-ready setup for the Klaviyo local development workflow. The
SKILL.md gives the high-level flow; this file carries the complete file layout,
environment configuration, package scripts, and the SDK client singleton.

## Step 1: Project Structure

```
my-klaviyo-project/
├── src/
│   ├── klaviyo/
│   │   ├── client.ts          # ApiKeySession + API class singletons
│   │   ├── profiles.ts        # Profile operations
│   │   ├── events.ts          # Event tracking
│   │   └── lists.ts           # List management
│   └── index.ts
├── tests/
│   ├── unit/
│   │   └── profiles.test.ts   # Mocked SDK tests
│   └── integration/
│       └── klaviyo.test.ts    # Live API tests (CI only)
├── .env.local                 # Local secrets (git-ignored)
├── .env.example               # Template for team
├── .env.test                  # Test environment (sandbox key)
└── package.json
```

## Step 2: Environment Configuration

```bash
# .env.example (commit this)
KLAVIYO_PRIVATE_KEY=pk_your_test_key_here
KLAVIYO_PUBLIC_KEY=YourPublicKey
NODE_ENV=development

# .env.local (git-ignored, actual secrets)
KLAVIYO_PRIVATE_KEY=pk_********************************
```

```json
// package.json scripts
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "KLAVIYO_TEST=1 vitest --config vitest.integration.config.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

## Step 3: SDK Client Singleton

```typescript
// src/klaviyo/client.ts
import {
  ApiKeySession,
  ProfilesApi,
  EventsApi,
  ListsApi,
  SegmentsApi,
  CampaignsApi,
  MetricsApi,
} from 'klaviyo-api';

let session: ApiKeySession | null = null;

function getSession(): ApiKeySession {
  if (!session) {
    const key = process.env.KLAVIYO_PRIVATE_KEY;
    if (!key) throw new Error('KLAVIYO_PRIVATE_KEY not set');
    session = new ApiKeySession(key);
  }
  return session;
}

// Lazy singletons -- only instantiate what you use
export const profiles = () => new ProfilesApi(getSession());
export const events = () => new EventsApi(getSession());
export const lists = () => new ListsApi(getSession());
export const segments = () => new SegmentsApi(getSession());
export const campaigns = () => new CampaignsApi(getSession());
export const metrics = () => new MetricsApi(getSession());
```

## Step 6: Hot Reload Development

```bash
# Start dev server with file watching
npm run dev

# In another terminal, run tests on change
npm run test:watch
```

The unit- and integration-test files referenced above (Steps 4 and 5) live in
[examples.md](examples.md).
