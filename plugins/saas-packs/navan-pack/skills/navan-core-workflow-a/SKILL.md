---
name: navan-core-workflow-a
description: 'Manage the complete Navan travel booking lifecycle via REST API.

  Use when building travel dashboards, automating trip reporting, or syncing booking
  data to internal systems.

  Trigger with "navan travel workflow", "navan booking management", "navan trip retrieval".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan — Travel Booking & Management

## Overview

This skill provides the complete travel booking workflow through the Navan REST API. Navan has no public SDK — all access is via raw HTTP calls using OAuth 2.0 bearer tokens. This skill covers trip retrieval for both user and admin scopes, itinerary PDF downloads, invoice access, and trip filtering by date range and status. Every booking is keyed by a UUID primary key that must be tracked for deduplication and updates.

## Prerequisites

- Navan account with API credentials (client_id + client_secret)
- Credentials created in Admin > Travel admin > Settings > Integrations > Navan API Credentials
- OAuth 2.0 token obtained via POST `/ta-auth/oauth/token` (see `navan-install-auth`)
- Node.js 18+ with `node-fetch` or Python 3.8+ with `requests`
- Environment variables: `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, `NAVAN_BASE_URL`
- `NAVAN_BASE_URL` should be set to `https://api.navan.com`

## Instructions

### Step 1: Authenticate and Obtain Bearer Token

```typescript
const tokenRes = await fetch(`${process.env.NAVAN_BASE_URL}/ta-auth/oauth/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: process.env.NAVAN_CLIENT_ID!,
    client_secret: process.env.NAVAN_CLIENT_SECRET!,
  }),
});
const { access_token } = await tokenRes.json();
const headers = { Authorization: `Bearer ${access_token}` };
```

### Step 2: Retrieve Bookings

```typescript
// GET /v1/bookings — returns booking records (paginated via page + size)
// Response: records in .data array, primary key uuid
const bookingsRes = await fetch(
  `${process.env.NAVAN_BASE_URL}/v1/bookings?page=0&size=50`,
  { headers }
);
const { data: bookings } = await bookingsRes.json();

bookings.forEach((booking: any) => {
  console.log(`UUID: ${booking.uuid}`);
  console.log(`  Route: ${booking.origin} -> ${booking.destination}`);
  console.log(`  Status: ${booking.status}`);
  console.log(`  Dates: ${booking.start_date} to ${booking.end_date}`);
});
```

### Step 3: Retrieve Bookings with Date Filtering

```typescript
// GET /v1/bookings with createdFrom/createdTo for incremental pulls
const filteredRes = await fetch(
  `${process.env.NAVAN_BASE_URL}/v1/bookings?createdFrom=2026-01-01&createdTo=2026-03-31&page=0&size=50`,
  { headers }
);
const { data: filteredBookings } = await filteredRes.json();
console.log(`Total bookings in range: ${filteredBookings.length}`);
```

### Step 4: Paginate Through All Bookings

```typescript
// Paginate using page + size query params (start from page 0, page_size 50)
async function getAllBookings(): Promise<any[]> {
  const allBookings: any[] = [];
  let page = 0;
  const size = 50;

  while (true) {
    const res = await fetch(
      `${process.env.NAVAN_BASE_URL}/v1/bookings?page=${page}&size=${size}`,
      { headers }
    );
    const { data } = await res.json();
    if (!data || data.length === 0) break;
    allBookings.push(...data);
    if (data.length < size) break; // last page
    page++;
  }
  return allBookings;
}

const allBookings = await getAllBookings();
console.log(`Total bookings: ${allBookings.length}`);
```

### Step 5: Token Refresh

```typescript
// Re-authenticate by requesting a new token (same client_credentials flow)
const refreshRes = await fetch(`${process.env.NAVAN_BASE_URL}/ta-auth/oauth/token`, {
  method: 'POST',
  headers: { 'Content-Type': 'application/x-www-form-urlencoded' },
  body: new URLSearchParams({
    grant_type: 'client_credentials',
    client_id: process.env.NAVAN_CLIENT_ID!,
    client_secret: process.env.NAVAN_CLIENT_SECRET!,
  }),
});
const refreshed = await refreshRes.json();
console.log('Token refreshed successfully');
```

## Output

Successful execution returns:
- Booking objects in `.data` array with UUID primary keys, origin/destination, dates, and status
- Paginated results using `page` + `size` query params
- Incremental filtering via `createdFrom` / `createdTo` params

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| Unauthorized | 401 | Expired or invalid bearer token | Re-authenticate via POST /ta-auth/oauth/token |
| Forbidden | 403 | Insufficient API scope | Verify credentials have correct permissions |
| Not Found | 404 | Invalid endpoint or UUID | Confirm endpoint path starts with /v1/ |
| Rate Limited | 429 | Too many requests | Implement exponential backoff (start at 1s) |
| Server Error | 500 | Navan platform issue | Retry with backoff; check Navan status page |

## Examples

**Python — Retrieve trips with date filtering:**

```python
import requests
import os

base_url = os.environ.get('NAVAN_BASE_URL', 'https://api.navan.com')

# Authenticate (form-encoded, not JSON)
auth = requests.post(f'{base_url}/ta-auth/oauth/token', data={
    'grant_type': 'client_credentials',
    'client_id': os.environ['NAVAN_CLIENT_ID'],
    'client_secret': os.environ['NAVAN_CLIENT_SECRET'],
})
token = auth.json()['access_token']
headers = {'Authorization': f'Bearer {token}'}

# Get bookings for Q1 (records in .data array)
resp = requests.get(
    f'{base_url}/v1/bookings',
    params={'createdFrom': '2026-01-01', 'createdTo': '2026-03-31', 'page': 0, 'size': 50},
    headers=headers,
).json()

for booking in resp['data']:
    print(f"{booking['uuid']}: {booking.get('origin')} -> {booking.get('destination')}")
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Official documentation and support articles
- [Booking Data Integration](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/booking-data-integration) — Booking data export configuration
- [Navan Integrations](https://navan.com/integrations) — Available third-party integrations

## Next Steps

After retrieving trip data, proceed to `navan-core-workflow-b` for expense management or `navan-data-handling` for bulk data extraction patterns.
