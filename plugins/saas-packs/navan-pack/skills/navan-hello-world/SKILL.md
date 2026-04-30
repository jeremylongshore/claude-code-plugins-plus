---
name: navan-hello-world
description: 'Make your first Navan API call to retrieve trip and user data.

  Use when verifying a new Navan integration works end-to-end after auth setup.

  Trigger with "navan hello world", "navan example", "test navan api", "first navan
  call".

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
# Navan Hello World

## Overview

Execute a first API call against the Navan REST API to retrieve trip data. All examples use raw REST calls — Navan has **no public SDK**.

**Purpose:** Confirm end-to-end integration by retrieving real trip data and parsing `uuid` primary keys.

## Prerequisites

- Completed `navan-install-auth` with working OAuth 2.0 credentials
- `.env` file with `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, and `NAVAN_BASE_URL`
- Node.js 18+ (for TypeScript) or Python 3.8+ (for Python)
- At least one trip or user in your Navan organization

## Instructions

### Step 1: Acquire a Bearer Token

Reuse the token exchange from `navan-install-auth`:

```typescript
import 'dotenv/config';

async function getNavanToken(): Promise<string> {
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
  return data.access_token;
}
```

### Step 2: Retrieve Bookings (TypeScript)

Call `GET /v1/bookings` to fetch booking records (paginated with `page` + `size`):

```typescript
interface NavanBooking {
  uuid: string;           // Primary key for all booking records
  traveler_name: string;
  origin: string;
  destination: string;
  departure_date: string;
  return_date: string;
  booking_status: string;
  booking_type: string;   // "flight", "hotel", "car"
}

async function getBookings(token: string): Promise<NavanBooking[]> {
  const response = await fetch(
    `${process.env.NAVAN_BASE_URL}/v1/bookings?page=0&size=50`,
    {
      headers: { Authorization: `Bearer ${token}` },
    }
  );

  if (!response.ok) {
    throw new Error(`GET /v1/bookings failed: ${response.status} ${response.statusText}`);
  }

  const { data } = await response.json(); // records in .data array
  return data ?? [];
}

// Execute
const token = await getNavanToken();
const bookings = await getBookings(token);
console.log(`Retrieved ${bookings.length} bookings:`);
bookings.forEach((b) =>
  console.log(`  [${b.uuid}] ${b.origin} -> ${b.destination} (${b.booking_status})`)
);
```

### Step 3: Retrieve Bookings (Python)

```python
import os
import requests
from dotenv import load_dotenv

load_dotenv()

def get_navan_token() -> str:
    resp = requests.post(
        f"{os.environ.get('NAVAN_BASE_URL', 'https://api.navan.com')}/ta-auth/oauth/token",
        data={
            "grant_type": "client_credentials",
            "client_id": os.environ["NAVAN_CLIENT_ID"],
            "client_secret": os.environ["NAVAN_CLIENT_SECRET"],
        },
    )
    resp.raise_for_status()
    return resp.json()["access_token"]

def get_bookings(token: str) -> list[dict]:
    base_url = os.environ.get('NAVAN_BASE_URL', 'https://api.navan.com')
    resp = requests.get(
        f"{base_url}/v1/bookings",
        params={"page": 0, "size": 50},
        headers={"Authorization": f"Bearer {token}"},
    )
    resp.raise_for_status()
    return resp.json()["data"]  # records in .data array

token = get_navan_token()
bookings = get_bookings(token)
print(f"Retrieved {len(bookings)} bookings:")
for b in bookings:
    print(f"  [{b['uuid']}] {b.get('origin')} -> {b.get('destination')}")
```

### Step 4: Paginate and Filter Bookings

Once the basic call works, use pagination and date filtering:

```typescript
// Paginate: page starts at 0, size controls page size
const page2 = await fetch(
  `${process.env.NAVAN_BASE_URL}/v1/bookings?page=1&size=50`,
  { headers: { Authorization: `Bearer ${token}` } }
);

// Filter by creation date range (incremental params)
const filtered = await fetch(
  `${process.env.NAVAN_BASE_URL}/v1/bookings?createdFrom=2026-01-01&createdTo=2026-03-31&page=0&size=50`,
  { headers: { Authorization: `Bearer ${token}` } }
);
```

### Step 5: Understand the Response Shape

Navan API responses use `uuid` as the primary key for booking records. Key fields to expect:

| Field | Type | Description |
|-------|------|-------------|
| `uuid` | string | Unique booking identifier (primary key) |
| `traveler_name` | string | Full name of the traveler |
| `booking_type` | string | "flight", "hotel", or "car" |
| `booking_status` | string | Current status of the booking |
| `origin` / `destination` | string | Airport codes or city names |

## Output

Successful completion produces:
- A working API call retrieving real booking data from the Navan organization
- Parsed response structure with records in `.data` array and `uuid` primary key
- Tested pagination (`page` + `size`) and date filtering (`createdFrom` / `createdTo`)

## Error Handling

| Error | Code | Cause | Solution |
|-------|------|-------|----------|
| Unauthorized | 401 | Expired or invalid OAuth token | Re-run token exchange; check credentials |
| Forbidden | 403 | Insufficient permissions or wrong tier | Verify admin role; contact Navan support |
| Not found | 404 | Invalid endpoint path | Check spelling; use exact paths from this guide |
| Rate limited | 429 | Too many requests | Wait and retry with exponential backoff |
| Server error | 500 | Navan service issue | Retry after 30s; check Navan status |
| Maintenance | 503 | Scheduled or unscheduled downtime | Wait and retry; check for maintenance windows |

## Examples

**Quick curl test from terminal:**

```bash
# Get token and fetch bookings in one pipeline
TOKEN=$(curl -s -X POST https://api.navan.com/ta-auth/oauth/token \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "grant_type=client_credentials&client_id=$NAVAN_CLIENT_ID&client_secret=$NAVAN_CLIENT_SECRET" \
  | python3 -c "import sys,json; print(json.load(sys.stdin)['access_token'])")

curl -s "https://api.navan.com/v1/bookings?page=0&size=5" \
  -H "Authorization: Bearer $TOKEN" | python3 -m json.tool
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — primary documentation hub
- [Booking Data Integration](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/booking-data-integration) — booking data export guide
- [Navan TMC API Docs](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/navan-tmc-api-integration-documentation) — API integration reference
- [Navan Security](https://navan.com/security) — compliance certifications (SOC 2, ISO 27001)

## Next Steps

Now that your first API call works, proceed to `navan-sdk-patterns` to build a typed wrapper class, or see `navan-local-dev-loop` for a structured development environment.
