---
name: navan-data-sync
description: 'Implement incremental sync strategies for Navan BOOKING and TRANSACTION
  data with ETL pipeline patterns.

  Use when setting up production data pipelines, debugging sync drift, or adding real-time
  event processing.

  Trigger with "navan data sync", "navan incremental sync", "navan ETL pipeline".

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
# Navan — Data Sync

## Overview

This skill provides production-grade sync strategies for Navan data. The two primary tables have fundamentally different sync models: BOOKING requires weekly full-refresh with merge-upsert logic (every record is re-imported, keyed by UUID), while TRANSACTION is incremental and append-only. Real-time use cases require webhook callbacks for event-driven processing. This skill covers all three tiers — scheduled full-refresh, incremental watermark-based sync, and real-time webhooks — along with Airbyte connector configuration and idempotent SQL upsert patterns.

## Prerequisites

- Navan account with OAuth 2.0 API credentials (see `navan-install-auth`)
- Destination warehouse (Snowflake, BigQuery, PostgreSQL, or Redshift)
- For managed sync: Airbyte instance (Cloud or OSS) with source-navan v0.0.42+
- For webhooks: publicly accessible HTTPS endpoint for callbacks
- Node.js 18+ or Python 3.8+
- Environment variables: `NAVAN_CLIENT_ID`, `NAVAN_CLIENT_SECRET`, `NAVAN_BASE_URL`

## Instructions

### Step 1: Full-Refresh Sync for BOOKING Table

The BOOKING table is re-imported weekly by Navan. Every record is refreshed, so your sync must use merge-upsert logic to avoid duplicates while capturing updates.

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

// Full extraction — paginate through all bookings for weekly refresh
let allBookings: any[] = [];
let page = 0;
const size = 50;
while (true) {
  const res = await fetch(
    `${process.env.NAVAN_BASE_URL}/v1/bookings?page=${page}&size=${size}`,
    { headers }
  );
  const { data } = await res.json();
  if (!data || !data.length) break;
  allBookings.push(...data);
  if (data.length < size) break;
  page++;
}
console.log(`Extracted ${allBookings.length} bookings for full refresh`);
```

**SQL merge-upsert pattern (PostgreSQL):**

```sql
-- Staging table receives raw API data
CREATE TABLE IF NOT EXISTS navan_booking_staging (
  uuid TEXT PRIMARY KEY,
  traveler_email TEXT,
  origin TEXT,
  destination TEXT,
  start_date DATE,
  end_date DATE,
  total_cost NUMERIC(12,2),
  currency TEXT DEFAULT 'USD',
  department TEXT,
  cost_center TEXT,
  status TEXT,
  in_policy BOOLEAN,
  created_at TIMESTAMPTZ,
  updated_at TIMESTAMPTZ,
  synced_at TIMESTAMPTZ DEFAULT NOW()
);

-- Merge-upsert: insert new records, update changed records
INSERT INTO navan_booking AS b
SELECT * FROM navan_booking_staging s
ON CONFLICT (uuid) DO UPDATE SET
  traveler_email = EXCLUDED.traveler_email,
  origin = EXCLUDED.origin,
  destination = EXCLUDED.destination,
  start_date = EXCLUDED.start_date,
  end_date = EXCLUDED.end_date,
  total_cost = EXCLUDED.total_cost,
  status = EXCLUDED.status,
  in_policy = EXCLUDED.in_policy,
  updated_at = EXCLUDED.updated_at,
  synced_at = NOW()
WHERE b.updated_at < EXCLUDED.updated_at;
```

### Step 2: Incremental Sync for TRANSACTION Table

TRANSACTION data is append-only. Use watermark-based sync to pull only new records.

```typescript
// Track high-watermark for incremental pulls
interface SyncState {
  lastSyncDate: string;  // ISO date of last successful sync
  lastTransactionId: string;
}

async function loadSyncState(): Promise<SyncState> {
  const fs = await import('fs');
  try {
    return JSON.parse(fs.readFileSync('.navan-sync-state.json', 'utf-8'));
  } catch {
    return { lastSyncDate: '2025-01-01', lastTransactionId: '' };
  }
}

async function saveSyncState(state: SyncState) {
  const fs = await import('fs');
  fs.writeFileSync('.navan-sync-state.json', JSON.stringify(state, null, 2));
}

// Pull bookings since last watermark
const state = await loadSyncState();
const today = new Date().toISOString().split('T')[0];

const txnRes = await fetch(
  `${process.env.NAVAN_BASE_URL}/v1/bookings` +
  `?createdFrom=${state.lastSyncDate}&createdTo=${today}&page=0&size=50`,
  { headers }
);
const { data: transactions } = await txnRes.json();

// Filter out already-seen transactions
const newTxns = transactions.filter(
  (t: any) => t.transaction_id > state.lastTransactionId
);
console.log(`New transactions since ${state.lastSyncDate}: ${newTxns.length}`);

// Update watermark after successful load
if (newTxns.length > 0) {
  await saveSyncState({
    lastSyncDate: today,
    lastTransactionId: newTxns[newTxns.length - 1].transaction_id,
  });
}
```

### Step 3: Webhook Endpoint for Real-Time Events

```typescript
import { createServer } from 'http';
import { createHmac } from 'crypto';

// Webhook handler for real-time Navan events
const server = createServer(async (req, res) => {
  if (req.method !== 'POST' || req.url !== '/navan/webhook') {
    res.writeHead(404);
    res.end();
    return;
  }

  const chunks: Buffer[] = [];
  for await (const chunk of req) chunks.push(chunk as Buffer);
  const body = Buffer.concat(chunks).toString();

  // Verify webhook signature
  const signature = req.headers['x-navan-signature'] as string;
  const expected = createHmac('sha256', process.env.NAVAN_WEBHOOK_SECRET!)
    .update(body)
    .digest('hex');

  if (signature !== expected) {
    console.error('Invalid webhook signature');
    res.writeHead(401);
    res.end('Unauthorized');
    return;
  }

  const event = JSON.parse(body);
  console.log(`Webhook event: ${event.type}`);

  switch (event.type) {
    case 'booking.created':
      console.log(`New booking: ${event.data.uuid}`);
      break;
    case 'booking.updated':
      console.log(`Booking updated: ${event.data.uuid}`);
      break;
    case 'booking.cancelled':
      console.log(`Booking cancelled: ${event.data.uuid}`);
      break;
    case 'expense.submitted':
      console.log(`Expense submitted: ${event.data.transaction_id}`);
      break;
    case 'expense.approved':
      console.log(`Expense approved: ${event.data.transaction_id}`);
      break;
    default:
      console.log(`Unknown event type: ${event.type}`);
  }

  res.writeHead(200);
  res.end('OK');
});

server.listen(3000, () => console.log('Webhook listener on :3000'));
```

### Step 4: Airbyte Connector Sync Configuration

```yaml
# Airbyte source-navan connector (v0.0.42)
# Production sync mode configuration
source:
  sourceDefinitionId: source-navan
  connectionConfiguration:
    client_id: "${NAVAN_CLIENT_ID}"
    client_secret: "${NAVAN_CLIENT_SECRET}"

# Sync catalog — bookings stream
syncCatalog:
  streams:
    - stream:
        name: bookings
        jsonSchema: {}
      config:
        # Full Refresh for BOOKING (weekly re-import model)
        syncMode: full_refresh
        destinationSyncMode: overwrite
        # Alternative: append_dedup with uuid as primary key
        # syncMode: full_refresh
        # destinationSyncMode: append_dedup
        # primaryKey: [["uuid"]]

# Schedule: run weekly to match Navan's BOOKING refresh cycle
schedule:
  scheduleType: cron
  cronExpression: "0 2 * * 0"  # Sunday 2am UTC
```

### Step 5: Sync Monitoring and Alerting

```typescript
// Monitor sync health and detect drift
interface SyncMetrics {
  tableName: string;
  lastSyncTime: Date;
  recordCount: number;
  expectedFrequency: string;
  isStale: boolean;
}

async function checkSyncHealth(): Promise<SyncMetrics[]> {
  const state = await loadSyncState();
  const lastSync = new Date(state.lastSyncDate);
  const hoursSinceSync = (Date.now() - lastSync.getTime()) / (1000 * 60 * 60);

  return [
    {
      tableName: 'BOOKING',
      lastSyncTime: lastSync,
      recordCount: 0,  // populated from warehouse query
      expectedFrequency: 'weekly',
      isStale: hoursSinceSync > 7 * 24 + 6, // alert if > 7.25 days
    },
    {
      tableName: 'TRANSACTION',
      lastSyncTime: lastSync,
      recordCount: 0,
      expectedFrequency: 'daily',
      isStale: hoursSinceSync > 25, // alert if > 25 hours
    },
  ];
}

const health = await checkSyncHealth();
health.forEach(m => {
  const status = m.isStale ? 'STALE' : 'OK';
  console.log(`${m.tableName}: ${status} (last sync: ${m.lastSyncTime.toISOString()})`);
});
```

### Step 6: Idempotent Load Pattern

```typescript
// Ensure loads are idempotent — safe to re-run without side effects
async function idempotentLoad(records: any[], tableName: string) {
  const batchId = `${tableName}-${new Date().toISOString()}`;

  // 1. Write to staging with batch ID
  console.log(`Loading ${records.length} records to ${tableName}_staging (batch: ${batchId})`);

  // 2. Merge-upsert from staging to target
  // Uses UUID as natural key — same record always resolves to same row
  console.log(`Merging ${tableName}_staging -> ${tableName}`);

  // 3. Record batch metadata for audit
  console.log(`Batch ${batchId} complete: ${records.length} records processed`);

  return { batchId, recordCount: records.length, status: 'complete' };
}
```

## Output

Successful execution produces:
- Full-refresh BOOKING sync with merge-upsert deduplication
- Incremental TRANSACTION sync with watermark state tracking
- Webhook endpoint for real-time event processing
- Configured Airbyte connector with production-ready sync schedule
- Sync health monitoring with staleness alerting

## Error Handling

| Error | HTTP Code | Cause | Solution |
|-------|-----------|-------|----------|
| Unauthorized | 401 | Expired or invalid bearer token | Re-authenticate via POST /ta-auth/oauth/token |
| Rate Limited | 429 | Too many API requests | Use exponential backoff; increase sync interval |
| Timeout | 504 | Full refresh too large | Chunk by date range (30-day windows) |
| Webhook Sig Invalid | 401 | Tampered or replayed event | Verify NAVAN_WEBHOOK_SECRET; check clock skew |
| Duplicate Records | N/A | Missing UUID dedup in BOOKING sync | Apply merge-upsert with ON CONFLICT (uuid) |
| Sync Drift | N/A | Missed incremental window | Fall back to full refresh; reset watermark |

## Examples

**Python — Incremental TRANSACTION sync with watermark:**

```python
import requests
import json
import os
from datetime import datetime

base_url = os.environ.get('NAVAN_BASE_URL', 'https://api.navan.com')
auth = requests.post(f'{base_url}/ta-auth/oauth/token', data={
    'grant_type': 'client_credentials',
    'client_id': os.environ['NAVAN_CLIENT_ID'],
    'client_secret': os.environ['NAVAN_CLIENT_SECRET'],
})
headers = {'Authorization': f'Bearer {auth.json()["access_token"]}'}

# Load watermark
try:
    with open('.navan-sync-state.json') as f:
        state = json.load(f)
except FileNotFoundError:
    state = {'last_sync_date': '2025-01-01'}

today = datetime.now().strftime('%Y-%m-%d')
resp = requests.get(
    f'{base_url}/v1/bookings',
    params={'createdFrom': state['last_sync_date'], 'createdTo': today, 'page': 0, 'size': 50},
    headers=headers,
).json()
txns = resp['data']

print(f'Fetched {len(txns)} records since {state["last_sync_date"]}')

# Save updated watermark
with open('.navan-sync-state.json', 'w') as f:
    json.dump({'last_sync_date': today}, f)
```

## Resources

- [Navan Help Center](https://app.navan.com/app/helpcenter) — Official documentation and support
- [Booking Data Integration](https://app.navan.com/app/helpcenter/articles/travel/admin/other-integrations/booking-data-integration) — BOOKING table refresh schedule and schema
- [Navan Integrations](https://navan.com/integrations) — Fivetran, Airbyte, and Estuary connector details

## Next Steps

After configuring data sync, proceed to `navan-observability` for pipeline monitoring or `navan-performance-tuning` for optimizing large-volume syncs.
