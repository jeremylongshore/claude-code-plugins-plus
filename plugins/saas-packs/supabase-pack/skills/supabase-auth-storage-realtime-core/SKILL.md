---
name: supabase-auth-storage-realtime-core
description: |
  Execute Supabase secondary workflow: Auth + Storage + Realtime.
  Use when creating tables and indexes for a new feature,
  or altering columns without downtime.
  Trigger with phrases like "supabase auth storage realtime",
  "implement full stack features with supabase".
allowed-tools: Read, Write, Edit, Bash(npm:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, supabase]
---

# Supabase Auth + Storage + Realtime

## Overview
Implement the core Supabase trifecta: authentication, file storage,
and real-time subscriptions in a single cohesive setup.


## Prerequisites
- Completed `supabase-install-auth` setup
- Familiarity with `supabase-schema-from-requirements`
- Valid API credentials configured

## Instructions

### Step 1: Generate Migration File
```typescript
// migrations/001_create_events.sql
const migration = `
  CREATE TABLE events (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id UUID NOT NULL REFERENCES users(id),
    event_type VARCHAR(64) NOT NULL,
    payload JSONB DEFAULT '{}',
    created_at TIMESTAMPTZ DEFAULT NOW()
  );
  CREATE INDEX idx_events_user ON events(user_id);
  CREATE INDEX idx_events_type_date ON events(event_type, created_at);
`;

```

### Step 2: Apply Migration
```typescript
// Run migration with transaction safety
await client.query('BEGIN');
try {
  await client.query(migration);
  await client.query("INSERT INTO schema_migrations (version) VALUES ('001')");
  await client.query('COMMIT');
} catch (err) {
  await client.query('ROLLBACK');
  throw err;
}

```

### Step 3: Verify Schema
```typescript
const check = await client.query(`
  SELECT column_name, data_type
  FROM information_schema.columns
  WHERE table_name = 'events'
`);
console.log('Migration applied:', check.rows.length, 'columns');

```

## Output
- Completed Auth + Storage + Realtime execution

- Migration applied with schema changes verified
- Rollback available if issues detected

- Success confirmation or error details

## Error Handling
| Aspect | Schema from Requirements | Auth + Storage + Realtime |
|--------|------------|------------|
| Use Case | Starting a new project with defined data requirements | creating tables and indexes for a new feature |
| Complexity | Medium | High |
| Performance | Standard | Depends on table size (ALTER on large tables can lock) |

## Examples

### Complete Workflow
```typescript
// Safe migration with rollback
async function migrate(client, upSQL, downSQL) {
  await client.query('BEGIN');
  try {
    await client.query(upSQL);
    await client.query('COMMIT');
    console.log('Migration applied successfully');
  } catch (err) {
    await client.query('ROLLBACK');
    console.error('Migration failed, rolled back:', err.message);
  }
}

```

### Error Recovery
```typescript
try {
  await client.query(migrationSQL);
} catch (err) {
  if (err.code === '42P07') { // relation already exists
    console.log('Table already exists, skipping');
  } else if (err.code === '23505') { // unique violation
    console.log('Migration already applied');
  } else {
    throw err;
  }
}

```

## Resources
- [Supabase Documentation](https://supabase.com/docs)
- [Supabase API Reference](https://supabase.com/docs/api)

## Next Steps
For common errors, see `supabase-common-errors`.