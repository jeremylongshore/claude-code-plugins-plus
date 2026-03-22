---
name: supabase-migration-deep-dive
description: |
  Execute major migrations to/from Supabase: strangler fig pattern, data migration,
  dual-write strategies, and zero-downtime schema changes.
  Use when migrating from Firebase/MongoDB/raw Postgres to Supabase,
  performing major schema refactors, or re-platforming to Supabase.
  Trigger with phrases like "migrate to supabase", "supabase migration",
  "switch to supabase", "supabase replatform", "firebase to supabase".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(supabase:*), Bash(node:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, migration, replatform]

---
# Supabase Migration Deep Dive

## Overview
Safely migrate to Supabase from another platform (Firebase, MongoDB, raw Postgres, other BaaS) using the strangler fig pattern, data migration scripts, and zero-downtime schema evolution.

## Current State
!`npm list @supabase/supabase-js 2>/dev/null | grep supabase || echo 'not installed'`
!`supabase --version 2>/dev/null || echo 'CLI not installed'`

## Prerequisites
- Source system documented (schema, data volume, auth provider)
- Supabase project created
- Feature flag infrastructure for traffic routing

## Instructions

### Step 1: Assess Source System

```typescript
// scripts/migration-assessment.ts
interface MigrationAssessment {
  source: string
  tables: { name: string; rowCount: number; sizeMB: number }[]
  authProvider: string
  userCount: number
  features: string[]
  blockers: string[]
}

// Document what needs to migrate:
const assessment: MigrationAssessment = {
  source: 'Firebase Firestore',
  tables: [
    { name: 'users', rowCount: 50000, sizeMB: 12 },
    { name: 'orders', rowCount: 200000, sizeMB: 45 },
    { name: 'products', rowCount: 5000, sizeMB: 2 },
  ],
  authProvider: 'Firebase Auth',
  userCount: 50000,
  features: ['Realtime subscriptions', 'File storage', 'Auth with Google/GitHub'],
  blockers: ['Nested document structure needs flattening', 'Firebase Auth UIDs differ from Supabase'],
}
```

### Step 2: Create the Supabase Schema

```sql
-- Map source schema to Supabase tables
-- Firebase collections → Postgres tables
-- Nested documents → foreign key relationships

create table public.users (
  id uuid default gen_random_uuid() primary key,
  firebase_uid text unique,  -- keep for migration mapping
  email text unique not null,
  display_name text,
  avatar_url text,
  created_at timestamptz default now()
);

create table public.orders (
  id uuid default gen_random_uuid() primary key,
  firebase_id text unique,  -- keep for migration mapping
  user_id uuid references public.users(id),
  total numeric(10,2) not null,
  status text default 'pending',
  items jsonb not null default '[]',
  created_at timestamptz default now()
);

-- Enable RLS on all tables
alter table public.users enable row level security;
alter table public.orders enable row level security;
```

### Step 3: Data Migration Script

```typescript
// scripts/migrate-data.ts
import { createClient } from '@supabase/supabase-js'
import admin from 'firebase-admin'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

const firebase = admin.initializeApp(/* config */)
const db = admin.firestore()

async function migrateUsers() {
  const snapshot = await db.collection('users').get()
  const batch: any[] = []

  for (const doc of snapshot.docs) {
    const data = doc.data()
    batch.push({
      firebase_uid: doc.id,
      email: data.email,
      display_name: data.displayName,
      avatar_url: data.photoURL,
      created_at: data.createdAt?.toDate()?.toISOString() ?? new Date().toISOString(),
    })

    // Batch insert every 500 rows
    if (batch.length >= 500) {
      const { error } = await supabase.from('users').upsert(batch, { onConflict: 'firebase_uid' })
      if (error) console.error('Batch error:', error.message)
      else console.log(`Migrated ${batch.length} users`)
      batch.length = 0
    }
  }

  // Insert remaining
  if (batch.length > 0) {
    await supabase.from('users').upsert(batch, { onConflict: 'firebase_uid' })
    console.log(`Migrated ${batch.length} remaining users`)
  }
}

async function migrateOrders() {
  const snapshot = await db.collection('orders').get()
  const batch: any[] = []

  for (const doc of snapshot.docs) {
    const data = doc.data()

    // Map Firebase UID to Supabase user UUID
    const { data: user } = await supabase
      .from('users')
      .select('id')
      .eq('firebase_uid', data.userId)
      .single()

    batch.push({
      firebase_id: doc.id,
      user_id: user?.id,
      total: data.total,
      status: data.status,
      items: data.items,  // Firestore array → JSONB
      created_at: data.createdAt?.toDate()?.toISOString(),
    })

    if (batch.length >= 500) {
      await supabase.from('orders').upsert(batch, { onConflict: 'firebase_id' })
      console.log(`Migrated ${batch.length} orders`)
      batch.length = 0
    }
  }

  if (batch.length > 0) {
    await supabase.from('orders').upsert(batch, { onConflict: 'firebase_id' })
  }
}

// Run migration
await migrateUsers()
await migrateOrders()
```

### Step 4: Auth Migration

```typescript
// Migrate Firebase Auth users to Supabase Auth
import admin from 'firebase-admin'
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false }
})

async function migrateAuthUsers() {
  let nextPageToken: string | undefined

  do {
    const result = await admin.auth().listUsers(1000, nextPageToken)

    for (const user of result.users) {
      const { data, error } = await supabase.auth.admin.createUser({
        email: user.email!,
        email_confirm: true,
        user_metadata: {
          display_name: user.displayName,
          firebase_uid: user.uid,
        },
        // Users will need to reset password after migration
      })

      if (error && !error.message.includes('already been registered')) {
        console.error(`Failed to migrate ${user.email}:`, error.message)
      }
    }

    nextPageToken = result.pageToken
  } while (nextPageToken)

  console.log('Auth migration complete. Users will need to reset passwords.')
}
```

### Step 5: Strangler Fig — Dual-Write Adapter

```typescript
// services/data-adapter.ts
// Route traffic between old and new systems via feature flag

interface DataAdapter {
  getOrders(userId: string): Promise<Order[]>
  createOrder(order: OrderInput): Promise<Order>
}

class FirebaseAdapter implements DataAdapter {
  async getOrders(userId: string) { /* Firebase implementation */ }
  async createOrder(order: OrderInput) { /* Firebase implementation */ }
}

class SupabaseAdapter implements DataAdapter {
  async getOrders(userId: string) {
    const { data } = await supabase.from('orders')
      .select('*').eq('user_id', userId)
    return data ?? []
  }
  async createOrder(order: OrderInput) {
    const { data } = await supabase.from('orders')
      .insert(order).select().single()
    return data
  }
}

// Feature flag controls which adapter is used
export function getDataAdapter(): DataAdapter {
  return process.env.USE_SUPABASE === 'true'
    ? new SupabaseAdapter()
    : new FirebaseAdapter()
}
```

### Step 6: Verification and Cutover

```typescript
// scripts/verify-migration.ts
async function verifyMigration() {
  // Compare row counts
  const firebaseCount = await getFirebaseCount('orders')
  const { count } = await supabase.from('orders').select('*', { count: 'exact', head: true })

  console.log(`Firebase: ${firebaseCount} orders, Supabase: ${count} orders`)
  console.assert(firebaseCount === count, 'Row count mismatch!')

  // Spot-check random records
  const sampleIds = await getRandomFirebaseIds('orders', 10)
  for (const fbId of sampleIds) {
    const fbRecord = await getFirebaseRecord('orders', fbId)
    const { data: sbRecord } = await supabase.from('orders')
      .select('*').eq('firebase_id', fbId).single()

    console.assert(fbRecord.total === sbRecord?.total, `Total mismatch for ${fbId}`)
  }

  console.log('Migration verification complete')
}
```

## Output
- Migration assessment documenting source system and blockers
- Supabase schema with mapping columns for source IDs
- Data migration scripts with batch upsert and progress logging
- Auth user migration with password reset flow
- Strangler fig adapter for gradual traffic shifting
- Verification script comparing source and destination

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `23505: unique violation` during migration | Duplicate records | Use `.upsert()` with `onConflict` |
| Auth user `already registered` | Re-running migration | Skip existing users; use idempotent upsert |
| Row count mismatch | Incomplete migration batch | Check batch error logs; re-run failed batches |
| Foreign key violation | Migrating child rows before parents | Migrate in dependency order (users before orders) |

## Resources
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Supabase Auth Admin API](https://supabase.com/docs/reference/javascript/auth-admin-createuser)
- [Firebase to Supabase](https://supabase.com/docs/guides/resources/migrating-to-supabase)

## Next Steps
For advanced troubleshooting, see `supabase-advanced-troubleshooting`.
