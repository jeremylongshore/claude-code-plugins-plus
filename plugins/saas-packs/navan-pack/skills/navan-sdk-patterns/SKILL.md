---
name: navan-sdk-patterns
description: 'Build a typed API wrapper around Navan REST endpoints since no official
  SDK exists.

  Use when you need production-grade API access with auto token refresh, retry logic,
  and typed responses.

  Trigger with "navan sdk patterns", "navan api wrapper", "navan client class", "navan
  typed client".

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
# Navan SDK Patterns

## Overview

Build a typed API wrapper around Navan REST endpoints since no official SDK exists (`@navan/sdk` is not a real package). These patterns provide automatic token lifecycle management, typed responses, retry middleware, and centralized error handling.

**Purpose:** Create a reusable NavanAPI class encapsulating authentication, request handling, and error recovery.

## Prerequisites

- Completed `navan-install-auth` with working OAuth 2.0 credentials
- TypeScript 5+ project with `dotenv` installed
- Familiarity with the Navan endpoints from `navan-hello-world`

## Instructions

### Step 1: Define Response Interfaces

Type the known API response shapes so every call returns structured data:

```typescript
// navan-types.ts
export interface NavanTrip {
  uuid: string;
  traveler_name: string;
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string;
  booking_status: string;
  booking_type: 'flight' | 'hotel' | 'car';
}

export interface NavanUser {
  id: string;
  email: string;
  first_name: string;
  last_name: string;
  department: string;
  role: string;
}

export interface NavanApiError {
  status: number;
  message: string;
  endpoint: string;
  timestamp: string;
}
```

### Step 2: Build the NavanAPI Wrapper Class

Create a singleton client with automatic token management:

```typescript
// navan-client.ts
import 'dotenv/config';
import type { NavanTrip, NavanUser, NavanApiError } from './navan-types';

export class NavanAPI {
  private baseUrl: string;
  private clientId: string;
  private clientSecret: string;
  private accessToken: string | null = null;
  private tokenExpiry: number = 0;

  constructor() {
    this.baseUrl = process.env.NAVAN_BASE_URL ?? 'https://api.navan.com';
    this.clientId = process.env.NAVAN_CLIENT_ID ?? '';
    this.clientSecret = process.env.NAVAN_CLIENT_SECRET ?? '';
    if (!this.clientId || !this.clientSecret) {
      throw new Error('NAVAN_CLIENT_ID and NAVAN_CLIENT_SECRET must be set');
    }
  }

  /** Acquire or refresh the OAuth 2.0 bearer token */
  private async authenticate(): Promise<string> {
    if (this.accessToken && Date.now() < this.tokenExpiry) {
      return this.accessToken;
    }

    const response = await fetch(`${this.baseUrl}/ta-auth/oauth/token`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
      body: new URLSearchParams({
        grant_type: 'client_credentials',
        client_id: this.clientId,
        client_secret: this.clientSecret,
      }),
    });

    if (!response.ok) {
      throw this.toApiError(response.status, 'Authentication failed', '/ta-auth/oauth/token');
    }

    const data = await response.json();
    this.accessToken = data.access_token;
    // Buffer 60 seconds before actual expiry
    this.tokenExpiry = Date.now() + (data.expires_in - 60) * 1000;
    return this.accessToken!;
  }

  /** Core request method with auth, retries, and error handling */
  private async request<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
    const token = await this.authenticate();
    const url = `${this.baseUrl}${endpoint}`;

    for (let attempt = 0; attempt < 3; attempt++) {
      const response = await fetch(url, {
        ...options,
        headers: {
          Authorization: `Bearer ${token}`,
          'Content-Type': 'application/json',
          ...options.headers,
        },
      });

      if (response.ok) return response.json() as Promise<T>;

      // Retry on 429 (rate limit) and 503 (maintenance)
      if ((response.status === 429 || response.status === 503) && attempt < 2) {
        const delay = Math.pow(2, attempt + 1) * 1000; // 2s, 4s
        await new Promise((r) => setTimeout(r, delay));
        continue;
      }

      // Re-auth on 401 (expired token)
      if (response.status === 401 && attempt < 2) {
        this.accessToken = null;
        this.tokenExpiry = 0;
        continue;
      }

      throw this.toApiError(response.status, await response.text(), endpoint);
    }

    throw this.toApiError(0, 'Max retries exceeded', endpoint);
  }

  private toApiError(status: number, message: string, endpoint: string): NavanApiError {
    return { status, message, endpoint, timestamp: new Date().toISOString() };
  }

  // --- Public API methods ---

  async getBookings(page = 0, size = 50): Promise<NavanTrip[]> {
    const data = await this.request<{ data: NavanTrip[] }>(`/v1/bookings?page=${page}&size=${size}`);
    return data.data ?? [];
  }

  async getUsers(): Promise<NavanUser[]> {
    const data = await this.request<{ data: NavanUser[] }>('/v1/users');
    return data.data ?? [];
  }
}
```

### Step 3: Implement a Singleton Factory

Ensure one client instance per process to reuse the token:

```typescript
// navan-singleton.ts
import { NavanAPI } from './navan-client';

let instance: NavanAPI | null = null;

export function getNavanClient(): NavanAPI {
  if (!instance) instance = new NavanAPI();
  return instance;
}

// Usage
const navan = getNavanClient();
const bookings = await navan.getBookings();
const users = await navan.getUsers();
```

### Step 4: Add Error Handling Middleware

Wrap API calls with structured error handling for calling code:

```typescript
// navan-safe.ts
import type { NavanApiError } from './navan-types';

type Result<T> = { ok: true; data: T } | { ok: false; error: NavanApiError };

export async function safeCall<T>(fn: () => Promise<T>): Promise<Result<T>> {
  try {
    const data = await fn();
    return { ok: true, data };
  } catch (err) {
    const apiError = err as NavanApiError;
    console.error(`Navan API error [${apiError.status}] ${apiError.endpoint}: ${apiError.message}`);
    return { ok: false, error: apiError };
  }
}

// Usage
const result = await safeCall(() => navan.getUserTrips());
if (result.ok) {
  console.log(`Found ${result.data.length} trips`);
} else {
  console.error(`Failed: ${result.error.message}`);
}
```

### Step 5: Python Equivalent Pattern

```python
# navan_client.py
import os
import time
import requests
from dataclasses import dataclass
from dotenv import load_dotenv

load_dotenv()

@dataclass
class NavanAPIError(Exception):
    status: int
    message: str
    endpoint: str

class NavanAPI:
    def __init__(self):
        self.base_url = os.environ.get("NAVAN_BASE_URL", "https://api.navan.com")
        self.client_id = os.environ["NAVAN_CLIENT_ID"]
        self.client_secret = os.environ["NAVAN_CLIENT_SECRET"]
        self._token: str | None = None
        self._token_expiry: float = 0

    def _authenticate(self) -> str:
        if self._token and time.time() < self._token_expiry:
            return self._token
        resp = requests.post(f"{self.base_url}/ta-auth/oauth/token", data={
            "grant_type": "client_credentials",
            "client_id": self.client_id,
            "client_secret": self.client_secret,
        })
        resp.raise_for_status()
        data = resp.json()
        self._token = data["access_token"]
        self._token_expiry = time.time() + data.get("expires_in", 3600) - 60
        return self._token

    def _request(self, method: str, endpoint: str, **kwargs) -> dict:
        token = self._authenticate()
        for attempt in range(3):
            resp = requests.request(method, f"{self.base_url}{endpoint}",
                headers={"Authorization": f"Bearer {token}"}, **kwargs)
            if resp.ok:
                return resp.json()
            if resp.status_code in (429, 503) and attempt < 2:
                time.sleep(2 ** (attempt + 1))
                continue
            if resp.status_code == 401 and attempt < 2:
                self._token = None
                token = self._authenticate()
                continue
            raise NavanAPIError(resp.status_code, resp.text, endpoint)
        raise NavanAPIError(0, "Max retries exceeded", endpoint)

    def get_bookings(self, page: int = 0, size: int = 50) -> list[dict]:
        return self._request("GET", f"/v1/bookings?page={page}&size={size}").get("data", [])

    def get_users(self) -> list[dict]:
        return self._request("GET", "/v1/users").get("data", [])
```

## Output

Successful implementation produces:
- A typed `NavanAPI` class with automatic token refresh and retry logic
- Response interfaces for trips, users, and errors
- A singleton factory for client reuse across the application
- A `safeCall` wrapper for structured error handling in calling code

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Invalid credentials | 401 | Expired token or wrong secrets | Client auto-retries with fresh token; check .env |
| Forbidden | 403 | Insufficient permissions or wrong tier | Verify admin role; check Navan plan tier |
| Not found | 404 | Invalid endpoint path | Verify endpoint against known paths in this guide |
| Rate limited | 429 | Too many requests | Client auto-retries with exponential backoff |
| Server error | 500 | Navan service issue | Client auto-retries; escalate if persistent |
| Maintenance | 503 | Navan downtime | Client auto-retries; check for scheduled windows |

## Examples

**Fetch all bookings with error handling:**

```typescript
const navan = getNavanClient();
const result = await safeCall(() => navan.getBookings());
if (result.ok) {
  const flights = result.data.filter((t) => t.booking_type === 'flight');
  console.log(`${flights.length} flight bookings found`);
}
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — primary documentation hub
- [Navan TMC API Docs](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/navan-tmc-api-integration-documentation) — endpoint reference
- [Navan Integrations](https://navan.com/integrations) — integration partner ecosystem
- [Navan Security](https://navan.com/security) — SOC 2 Type II, ISO 27001, PCI DSS Level 1

## Next Steps

With your typed wrapper in place, see `navan-common-errors` for a comprehensive error reference, or `navan-local-dev-loop` to set up token caching and request logging for development.
