---
name: navan-data-handling
description: 'Extract and transform Navan booking and transaction data using pagination,
  filtering, and data pipeline connectors.

  Use when building data warehouses, analytics dashboards, or debugging data quality
  issues with Navan data.

  Trigger with "navan data handling", "navan data extraction", "navan pagination".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- navan
- travel
compatibility: Designed for Claude Code
---
# Navan Data Handling

## Overview

This skill covers data extraction and transformation patterns for Navan booking and transaction data. Navan exposes two primary data tables with different refresh behaviors: BOOKING (full re-import weekly, keyed by UUID) and TRANSACTION (incremental append-only). Data can be extracted via the direct REST API or through managed connectors — Fivetran, Airbyte (source-navan v0.0.42), and Estuary Flow. This skill provides pagination patterns, date-range filtering, UUID-based deduplication, and schema mapping for downstream analytics.

## Prerequisites

- Navan account with OAuth 2.0 API credentials (see `navan-install-auth`)
- For direct API: Node.js 18+ or Python 3.8+
- For Fivetran: Fivetran account with Navan connector
- For Airbyte: Airbyte instance (Cloud or OSS) with source-navan v0.0.42+
- Environment variables: `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, `NAVAN_BASE_URL`

## Instructions

### Step 1: Direct API — Paginated Booking Extraction

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

// Paginate through all bookings using page + size params
async function extractAllBookings(startDate: string, endDate: string) {
  const allBookings: any[] = [];
  let page = 0;
  const size = 50;

  while (true) {
    const res = await fetch(
      `${process.env.NAVAN_BASE_URL}/v1/bookings` +
      `?createdFrom=${startDate}&createdTo=${endDate}` +
      `&page=${page}&size=${size}`,
      { headers }
    );

    if (res.status === 429) {
      // Rate limited — exponential backoff
      const retryAfter = parseInt(res.headers.get('Retry-After') ?? '5');
      await new Promise(r => setTimeout(r, retryAfter * 1000));
      continue;
    }

    const { data } = await res.json();
    if (!data || !data.length) break;

    allBookings.push(...data);
    if (data.length < size) break; // last page
    page++;
    console.log(`Fetched ${allBookings.length} bookings...`);
  }
  return allBookings;
}

const bookings = await extractAllBookings('2026-01-01', '2026-03-31');
console.log(`Total bookings extracted: ${bookings.length}`);
```

### Step 2: UUID-Based Deduplication

```typescript
// BOOKING table re-imports weekly — same UUID may appear in multiple extractions
function deduplicateByUUID(records: any[]): any[] {
  const seen = new Map<string, any>();
  for (const record of records) {
    const existing = seen.get(record.uuid);
    if (!existing || record.updated_at > existing.updated_at) {
      seen.set(record.uuid, record);  // keep newest version
    }
  }
  return Array.from(seen.values());
}

const deduplicated = deduplicateByUUID(trips);
console.log(`After dedup: ${deduplicated.length} unique trips (was ${trips.length})`);
```

### Step 3: Date-Range Filtering and Chunking

```typescript
// Split large date ranges into chunks to avoid timeouts
function* dateChunks(start: string, end: string, daysPerChunk: number) {
  const startDate = new Date(start);
  const endDate = new Date(end);

  while (startDate < endDate) {
    const chunkEnd = new Date(startDate);
    chunkEnd.setDate(chunkEnd.getDate() + daysPerChunk);
    if (chunkEnd > endDate) chunkEnd.setTime(endDate.getTime());

    yield {
      start: startDate.toISOString().split('T')[0],
      end: chunkEnd.toISOString().split('T')[0],
    };
    startDate.setDate(startDate.getDate() + daysPerChunk + 1);
  }
}

// Extract in 30-day chunks
for (const chunk of dateChunks('2025-01-01', '2026-03-31', 30)) {
  const chunkBookings = await extractAllBookings(chunk.start, chunk.end);
  console.log(`${chunk.start} to ${chunk.end}: ${chunkBookings.length} bookings`);
}
```

### Step 4: Fivetran Connector Setup

Configure Fivetran for automated data extraction:

1. In Fivetran dashboard, add a new connector and search for "Navan"
2. Enter your OAuth credentials (client_id, client_secret)
3. Select destination warehouse (Snowflake, BigQuery, Redshift)
4. Configure sync frequency (recommended: daily for BOOKING, hourly for TRANSACTION)
5. Map schema: Fivetran creates `navan.booking` and `navan.transaction` tables

```sql
-- Fivetran destination query: trip summary by department
SELECT
  department,
  COUNT(*) AS trip_count,
  SUM(total_cost) AS total_spend,
  AVG(total_cost) AS avg_trip_cost
FROM navan.booking
WHERE booking_date >= '2026-01-01'
GROUP BY department
ORDER BY total_spend DESC;
```

### Step 5: Airbyte Connector Configuration

```yaml
# Airbyte source-navan connector config (v0.0.42)
# Supports one stream: bookings
sourceDefinitionId: source-navan
connectionConfiguration:
  client_id: "${NAVAN_CLIENT_ID}"
  client_secret: "${NAVAN_CLIENT_SECRET}"
  # Available streams: bookings
  # Sync mode: full_refresh (BOOKING table is re-imported weekly)
```

Airbyte setup steps:
1. In Airbyte, add source > search "Navan"
2. Enter client_id and client_secret
3. Select "bookings" stream
4. Set sync mode to "Full Refresh | Overwrite" (matches Navan's weekly re-import)
5. Configure destination and schedule

### Step 6: Schema Mapping for Analytics

```typescript
// Map Navan API response fields to analytics schema
interface NormalizedBooking {
  booking_id: string;     // from uuid
  employee_email: string;
  department: string;
  cost_center: string;
  origin: string;
  destination: string;
  start_date: string;
  end_date: string;
  booking_type: string;   // flight, hotel, car
  total_cost: number;
  currency: string;
  policy_compliant: boolean;
  created_at: string;
  updated_at: string;
}

function normalizeBooking(raw: any): NormalizedBooking {
  return {
    booking_id: raw.uuid,
    employee_email: raw.traveler_email ?? raw.email,
    department: raw.department ?? 'Unknown',
    cost_center: raw.cost_center ?? '',
    origin: raw.origin,
    destination: raw.destination,
    start_date: raw.start_date,
    end_date: raw.end_date,
    booking_type: raw.type ?? 'flight',
    total_cost: parseFloat(raw.total_cost ?? raw.amount ?? '0'),
    currency: raw.currency ?? 'USD',
    policy_compliant: raw.in_policy ?? true,
    created_at: raw.created_at,
    updated_at: raw.updated_at,
  };
}
```

## Output

Successful execution produces:
- Paginated trip and transaction records extracted via REST API
- Deduplicated records keyed by UUID for the BOOKING table
- Configured Fivetran or Airbyte connectors for automated extraction
- Normalized schema mappings ready for warehouse loading

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| Unauthorized | 401 | Expired or invalid bearer token | Re-authenticate via POST /ta-auth/oauth/token |
| Forbidden | 403 | Insufficient API scope for admin endpoints | Verify admin-level credentials |
| Rate Limited | 429 | Too many API requests | Use exponential backoff; chunk date ranges |
| Timeout | 504 | Date range too large | Split into 30-day chunks |
| Empty Response | 200 | No data in date range | Verify date format (YYYY-MM-DD); widen range |
| Connector Auth Failed | N/A | Invalid credentials in Fivetran/Airbyte | Verify client_id and client_secret |

## Examples

**Python — Bulk extraction with retry logic:**

```python
import requests
import time
import os

base_url = os.environ.get('NAVAN_BASE_URL', 'https://api.navan.com')
auth = requests.post(f'{base_url}/ta-auth/oauth/token', data={
    'grant_type': 'client_credentials',
    'client_id': os.environ['NAVAN_CLIENT_ID'],
    'client_secret': os.environ['NAVAN_CLIENT_SECRET'],
})
headers = {'Authorization': f'Bearer {auth.json()["access_token"]}'}

def extract_with_retry(endpoint, params, max_retries=3):
    for attempt in range(max_retries):
        res = requests.get(f'{base_url}/{endpoint}', params=params, headers=headers)
        if res.status_code == 200:
            return res.json()
        elif res.status_code == 429:
            wait = int(res.headers.get('Retry-After', 2 ** attempt))
            print(f'Rate limited, waiting {wait}s...')
            time.sleep(wait)
        else:
            res.raise_for_status()
    raise Exception(f'Failed after {max_retries} retries')

# Records in .data array, paginated with page + size
resp = extract_with_retry('v1/bookings', {
    'createdFrom': '2026-01-01', 'createdTo': '2026-03-31', 'page': 0, 'size': 50
})
bookings = resp['data']
print(f'Extracted {len(bookings)} bookings')
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Official API documentation
- [Booking Data Integration](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/booking-data-integration) — Booking data export and connector setup
- [Navan Integrations](https://navan.com/integrations) — Fivetran, Airbyte, and Estuary connectors

## Next Steps

After setting up data extraction, proceed to `navan-data-sync` for incremental sync strategies or `navan-performance-tuning` for optimizing large data pulls.
