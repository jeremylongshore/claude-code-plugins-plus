---
name: navan-local-dev-loop
description: 'Set up a local development environment for Navan API integrations with
  token caching and request logging.

  Use when starting a new Navan project or debugging API issues locally.

  Trigger with "navan local dev", "navan dev setup", "navan local dev loop", "navan
  dev environment".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Local Dev Loop

## Overview

Configure a local development environment for Navan API integrations with token caching, request logging, and mock fixtures. Navan has **no sandbox** — all API calls hit production, making a structured local setup essential.

**Purpose:** Establish a safe local dev workflow that minimizes production API calls during iteration.

## Prerequisites

- Completed `navan-install-auth` with working OAuth 2.0 credentials
- Node.js 18+ with `tsx` for TypeScript execution
- `.env` file with `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, `NAVAN_BASE_URL`

## Instructions

### Step 1: Project Structure

Set up a clean project layout that separates concerns:

```
my-navan-integration/
├── .env                    # Credentials (NEVER commit)
├── .env.example            # Template for teammates
├── .gitignore              # Must include .env, .token-cache, logs/
├── src/
│   ├── navan-client.ts     # API wrapper (from navan-sdk-patterns)
│   ├── navan-types.ts      # Response interfaces
│   └── index.ts            # Entry point
├── tests/
│   ├── fixtures/           # Recorded API responses for offline dev
│   │   ├── bookings.json
│   │   └── users.json
│   └── navan-client.test.ts
├── logs/                   # Request/response logs (gitignored)
├── .token-cache            # Cached OAuth token (gitignored)
├── package.json
└── tsconfig.json
```

### Step 2: Environment Configuration

Create `.env.example` as a safe template and enforce `.gitignore`:

```bash
# .env.example — commit this file, NOT .env
NAVAN_CLIENT_ID="your-client-id"
NAVAN_CLIENT_SECRET="your-client-secret"
NAVAN_BASE_URL="https://api.navan.com"
NAVAN_LOG_REQUESTS="true"
NAVAN_USE_FIXTURES="false"
```

```bash
# .gitignore additions for Navan projects
echo ".env" >> .gitignore
echo ".token-cache" >> .gitignore
echo "logs/" >> .gitignore
```

### Step 3: Token Cache Implementation

Persist tokens to disk to avoid hitting `/ta-auth/oauth/token` on every script run:

```typescript
// src/token-cache.ts
import { readFileSync, writeFileSync, existsSync } from 'fs';

interface CachedToken {
  access_token: string;
  expires_at: number; // Unix timestamp in ms
}

const CACHE_FILE = '.token-cache';

export function getCachedToken(): string | null {
  if (!existsSync(CACHE_FILE)) return null;
  try {
    const cached: CachedToken = JSON.parse(readFileSync(CACHE_FILE, 'utf-8'));
    if (Date.now() < cached.expires_at - 60_000) {
      return cached.access_token;
    }
  } catch { /* corrupt cache, re-auth */ }
  return null;
}

export function setCachedToken(token: string, expiresIn: number): void {
  const cached: CachedToken = {
    access_token: token,
    expires_at: Date.now() + expiresIn * 1000,
  };
  writeFileSync(CACHE_FILE, JSON.stringify(cached), { mode: 0o600 });
}
```

Integrate with authentication:

```typescript
import { getCachedToken, setCachedToken } from './token-cache';

async function getNavanToken(): Promise<string> {
  const cached = getCachedToken();
  if (cached) return cached;

  const response = await fetch(`${process.env.NAVAN_BASE_URL}/ta-auth/oauth/token`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
    body: new URLSearchParams({
      grant_type: 'client_credentials',
      client_id: process.env.NAVAN_CLIENT_ID!,
      client_secret: process.env.NAVAN_CLIENT_SECRET!,
    }),
  });
  if (!response.ok) throw new Error(`Auth failed: ${response.status}`);

  const data = await response.json();
  setCachedToken(data.access_token, data.expires_in);
  return data.access_token;
}
```

### Step 4: Request Logger

Log all API requests and responses for debugging without exposing secrets:

```typescript
// src/request-logger.ts
import { appendFileSync, mkdirSync, existsSync } from 'fs';

const LOG_DIR = 'logs';
const LOG_FILE = `${LOG_DIR}/navan-api.log`;

export function logRequest(method: string, url: string, status: number, durationMs: number, body?: string): void {
  if (process.env.NAVAN_LOG_REQUESTS !== 'true') return;
  if (!existsSync(LOG_DIR)) mkdirSync(LOG_DIR, { recursive: true });

  const entry = {
    timestamp: new Date().toISOString(),
    method,
    url: url.replace(/client_secret=[^&"]+/g, 'client_secret=***'),
    status,
    duration_ms: durationMs,
    response_preview: body ? body.substring(0, 200) : undefined,
  };
  appendFileSync(LOG_FILE, JSON.stringify(entry) + '\n');
}

// Usage in API wrapper
const start = Date.now();
const response = await fetch(url, options);
const body = await response.text();
logRequest('GET', url, response.status, Date.now() - start, body);
```

### Step 5: Mock Fixtures for Offline Development

Record real API responses and replay them during development:

```typescript
// tests/fixtures/bookings.json
{
  "data": [
    {
      "uuid": "trip-001-abc-def",
      "traveler_name": "Jane Smith",
      "origin": "SFO",
      "destination": "JFK",
      "departure_date": "2026-04-01",
      "return_date": "2026-04-05",
      "booking_status": "confirmed",
      "booking_type": "flight"
    }
  ]
}
```

Use fixtures when `NAVAN_USE_FIXTURES` is set:

```typescript
// src/fixture-loader.ts
import { readFileSync } from 'fs';
import { join } from 'path';

const FIXTURE_DIR = join(__dirname, '..', 'tests', 'fixtures');

export function loadFixture<T>(endpoint: string): T | null {
  if (process.env.NAVAN_USE_FIXTURES !== 'true') return null;
  const filename = endpoint.replace(/^\//, '').replace(/\//g, '_') + '.json';
  try {
    return JSON.parse(readFileSync(join(FIXTURE_DIR, filename), 'utf-8'));
  } catch {
    return null;
  }
}

// In the API wrapper, check fixtures first
async function request<T>(endpoint: string): Promise<T> {
  const fixture = loadFixture<T>(endpoint);
  if (fixture) return fixture;
  // ... real API call
}
```

### Step 6: Dev Scripts

Configure `package.json` for a fast iteration loop:

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "dev:offline": "NAVAN_USE_FIXTURES=true tsx watch src/index.ts",
    "test": "vitest",
    "test:live": "NAVAN_USE_FIXTURES=false vitest",
    "record": "NAVAN_LOG_REQUESTS=true tsx src/record-fixtures.ts",
    "logs": "tail -f logs/navan-api.log | python3 -m json.tool"
  }
}
```

### Step 7: Recording Fixtures from Production

Create a one-time script to capture real responses for offline use:

```typescript
// src/record-fixtures.ts
import { writeFileSync, mkdirSync } from 'fs';

const FIXTURE_DIR = 'tests/fixtures';
mkdirSync(FIXTURE_DIR, { recursive: true });

const token = await getNavanToken();
const endpoints = ['/v1/bookings?page=0&size=50', '/v1/users'];

for (const endpoint of endpoints) {
  const response = await fetch(`${process.env.NAVAN_BASE_URL}${endpoint}`, {
    headers: { Authorization: `Bearer ${token}` },
  });
  if (response.ok) {
    const data = await response.json();
    const filename = endpoint.replace(/^\//, '') + '.json';
    writeFileSync(`${FIXTURE_DIR}/${filename}`, JSON.stringify(data, null, 2));
    console.log(`Recorded ${endpoint} -> ${filename}`);
  } else {
    console.error(`Failed to record ${endpoint}: ${response.status}`);
  }
}
```

## Output

Successful setup produces:
- A project scaffold with proper secret isolation (.env, .gitignore)
- Token caching that avoids redundant auth calls to production
- Request/response logging for debugging with secret redaction
- Mock fixtures for offline development without production API calls
- Dev scripts for live, offline, and recording modes

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Unauthorized | 401 | Cached token expired | Delete `.token-cache` and re-authenticate |
| Forbidden | 403 | Credentials lack required scope | Regenerate credentials with proper permissions |
| Not found | 404 | Fixture file missing for endpoint | Record fixtures with `npm run record` |
| Rate limited | 429 | Too many dev iterations hitting production | Switch to `npm run dev:offline` |
| Server error | 500 | Navan service issue | Use fixtures; retry later |
| Maintenance | 503 | Navan downtime | Use `NAVAN_USE_FIXTURES=true` for offline mode |

## Examples

**Typical dev workflow:**

```bash
# 1. First time: record fixtures from production
npm run record

# 2. Daily development: use offline mode
npm run dev:offline

# 3. Integration testing: hit production
npm run test:live

# 4. Debug a failure: check logs
npm run logs
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — primary documentation hub
- [Navan TMC API Docs](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/navan-tmc-api-integration-documentation) — API reference
- [Navan Booking Data](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/booking-data-integration) — booking data export docs
- [Navan Security](https://navan.com/security) — compliance certifications

## Next Steps

With your local dev environment running, see `navan-sdk-patterns` for production-grade wrapper patterns, or `navan-common-errors` when you encounter API failures during development.
