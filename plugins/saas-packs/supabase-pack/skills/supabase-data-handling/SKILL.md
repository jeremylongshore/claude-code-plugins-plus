---
name: supabase-data-handling
description: |
  Implement GDPR/CCPA compliance with Supabase: RLS for data isolation, user deletion
  via auth.admin.deleteUser(), data export via SQL, PII column management,
  backup/restore workflows, and retention policies.
  Use when handling sensitive data, implementing right-to-deletion, configuring data retention,
  or auditing PII in Supabase database columns.
  Trigger: "supabase GDPR", "supabase data handling", "supabase PII", "supabase compliance",
  "supabase data retention", "supabase delete user", "supabase data export".
allowed-tools: Read, Write, Edit, Bash(npx supabase:*), Bash(supabase:*), Bash(psql:*), Grep, Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, gdpr, ccpa, compliance, data-handling, privacy]
---

# Supabase Data Handling

## Overview

GDPR and CCPA compliance with Supabase requires a layered approach: Row Level Security (RLS) for tenant data isolation, `supabase.auth.admin.deleteUser()` for right-to-deletion requests, SQL-based data exports for subject access requests, PII detection across database columns, automated retention policies using `pg_cron`, and point-in-time recovery for backup/restore. This skill implements every compliance requirement using real Supabase SDK methods and PostgreSQL features.

**When to use:** Implementing GDPR right-to-deletion, responding to data subject access requests (DSARs), auditing PII in your database, configuring automated data retention, setting up tenant isolation with RLS, or planning backup/restore procedures.

## Prerequisites

- `@supabase/supabase-js` v2+ with service role key for admin operations
- Supabase project on Pro plan (for `pg_cron` and point-in-time recovery)
- Understanding of GDPR Articles 15-17 (access, rectification, erasure)
- Database access via SQL Editor or `psql` for schema changes

## Instructions

### Step 1: RLS for Data Isolation and PII Column Management

Configure Row Level Security to ensure users can only access their own data, and identify which columns contain PII.

**Tenant isolation with RLS:**

```sql
-- Enable RLS on all tables containing user data
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.orders ENABLE ROW LEVEL SECURITY;
ALTER TABLE public.documents ENABLE ROW LEVEL SECURITY;

-- Users can only read their own profile
CREATE POLICY "users_read_own_profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);

-- Users can update their own profile
CREATE POLICY "users_update_own_profile" ON public.profiles
  FOR UPDATE USING (auth.uid() = id)
  WITH CHECK (auth.uid() = id);

-- Users can only see their own orders
CREATE POLICY "users_read_own_orders" ON public.orders
  FOR SELECT USING (auth.uid() = user_id);

-- Organization-scoped isolation (multi-tenant)
CREATE POLICY "org_members_read_documents" ON public.documents
  FOR SELECT USING (
    org_id IN (
      SELECT org_id FROM public.org_members
      WHERE user_id = auth.uid()
    )
  );
```

**PII column audit — identify sensitive data across your schema:**

```sql
-- Find columns likely containing PII based on naming patterns
SELECT table_schema, table_name, column_name, data_type
FROM information_schema.columns
WHERE table_schema = 'public'
  AND (
    column_name ILIKE '%email%'
    OR column_name ILIKE '%phone%'
    OR column_name ILIKE '%name%'
    OR column_name ILIKE '%address%'
    OR column_name ILIKE '%ssn%'
    OR column_name ILIKE '%birth%'
    OR column_name ILIKE '%ip%'
    OR column_name ILIKE '%location%'
  )
ORDER BY table_name, column_name;

-- Add comments to mark PII columns for documentation
COMMENT ON COLUMN public.profiles.email IS 'PII: email address — GDPR Art. 4(1)';
COMMENT ON COLUMN public.profiles.full_name IS 'PII: personal name — GDPR Art. 4(1)';
COMMENT ON COLUMN public.profiles.phone IS 'PII: phone number — GDPR Art. 4(1)';

-- Create a PII registry view
CREATE OR REPLACE VIEW pii_registry AS
SELECT c.table_name, c.column_name, c.data_type,
       pg_catalog.col_description(
         (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass,
         c.ordinal_position
       ) AS pii_classification
FROM information_schema.columns c
WHERE c.table_schema = 'public'
  AND pg_catalog.col_description(
    (quote_ident(c.table_schema) || '.' || quote_ident(c.table_name))::regclass,
    c.ordinal_position
  ) LIKE 'PII:%';
```

**PII detection from the SDK:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Scan a table for PII patterns in text columns
async function scanTableForPII(tableName: string, sampleSize = 100) {
  const PII_PATTERNS = [
    { type: 'email', regex: /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g },
    { type: 'phone', regex: /\b\d{3}[-.]?\d{3}[-.]?\d{4}\b/g },
    { type: 'ssn', regex: /\b\d{3}-\d{2}-\d{4}\b/g },
    { type: 'ip_address', regex: /\b\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}\b/g },
  ];

  const { data, error } = await supabase
    .from(tableName)
    .select('*')
    .limit(sampleSize);

  if (error) throw error;

  const findings: { column: string; type: string; count: number }[] = [];

  for (const row of data ?? []) {
    for (const [column, value] of Object.entries(row)) {
      if (typeof value !== 'string') continue;
      for (const pattern of PII_PATTERNS) {
        const matches = value.match(pattern.regex);
        if (matches) {
          findings.push({ column, type: pattern.type, count: matches.length });
        }
      }
    }
  }

  return findings;
}
```

### Step 2: User Deletion and Data Export

Implement GDPR Article 17 (right to erasure) with `auth.admin.deleteUser()` and Article 15 (right of access) with SQL-based data export.

**Right to deletion — complete user erasure:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

interface DeletionResult {
  userId: string;
  tablesProcessed: string[];
  storageFilesDeleted: number;
  authDeleted: boolean;
  auditLogId: string;
  completedAt: string;
}

async function deleteUserData(userId: string): Promise<DeletionResult> {
  const tablesProcessed: string[] = [];
  let storageFilesDeleted = 0;

  // 1. Delete user data from application tables (cascade order)
  const tablesToPurge = ['comments', 'orders', 'documents', 'profiles'];

  for (const table of tablesToPurge) {
    const { error } = await supabase
      .from(table)
      .delete()
      .eq('user_id', userId);

    if (error && !error.message.includes('does not exist')) {
      console.error(`Failed to delete from ${table}:`, error.message);
    } else {
      tablesProcessed.push(table);
    }
  }

  // 2. Delete user files from storage
  const { data: buckets } = await supabase.storage.listBuckets();
  for (const bucket of buckets ?? []) {
    const { data: files } = await supabase.storage
      .from(bucket.name)
      .list(`users/${userId}`);

    if (files && files.length > 0) {
      const paths = files.map((f) => `users/${userId}/${f.name}`);
      const { error } = await supabase.storage
        .from(bucket.name)
        .remove(paths);

      if (!error) storageFilesDeleted += paths.length;
    }
  }

  // 3. Delete the auth user (removes from auth.users)
  const { error: authError } = await supabase.auth.admin.deleteUser(userId);
  const authDeleted = !authError;

  if (authError) {
    console.error('Auth deletion failed:', authError.message);
  }

  // 4. Create audit log entry (required — must survive deletion)
  const { data: auditEntry } = await supabase
    .from('gdpr_audit_log')
    .insert({
      action: 'USER_DELETION',
      subject_id: userId,
      tables_purged: tablesProcessed,
      storage_files_deleted: storageFilesDeleted,
      auth_deleted: authDeleted,
      performed_by: 'system',
      legal_basis: 'GDPR Article 17 — Right to Erasure',
    })
    .select('id')
    .single();

  return {
    userId,
    tablesProcessed,
    storageFilesDeleted,
    authDeleted,
    auditLogId: auditEntry?.id ?? 'unknown',
    completedAt: new Date().toISOString(),
  };
}

// GDPR audit log table (create this migration)
// CREATE TABLE gdpr_audit_log (
//   id uuid DEFAULT gen_random_uuid() PRIMARY KEY,
//   action text NOT NULL,
//   subject_id uuid NOT NULL,
//   tables_purged text[] DEFAULT '{}',
//   storage_files_deleted int DEFAULT 0,
//   auth_deleted boolean DEFAULT false,
//   performed_by text NOT NULL,
//   legal_basis text,
//   created_at timestamptz DEFAULT now()
// );
// -- Audit logs must NEVER be deleted (compliance requirement)
// ALTER TABLE gdpr_audit_log ENABLE ROW LEVEL SECURITY;
// CREATE POLICY "admin_only" ON gdpr_audit_log FOR ALL USING (false);
```

**Data subject access request (DSAR) — export all user data:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

interface DataExport {
  exportedAt: string;
  subjectId: string;
  legalBasis: string;
  data: Record<string, unknown[]>;
  storageFiles: string[];
}

async function exportUserData(userId: string): Promise<DataExport> {
  const exportData: Record<string, unknown[]> = {};

  // Export from each table containing user data
  const tables = ['profiles', 'orders', 'documents', 'comments'];

  for (const table of tables) {
    const { data, error } = await supabase
      .from(table)
      .select('*')
      .eq('user_id', userId);

    if (!error && data) {
      exportData[table] = data;
    }
  }

  // List user files in storage
  const storageFiles: string[] = [];
  const { data: buckets } = await supabase.storage.listBuckets();
  for (const bucket of buckets ?? []) {
    const { data: files } = await supabase.storage
      .from(bucket.name)
      .list(`users/${userId}`);

    for (const file of files ?? []) {
      storageFiles.push(`${bucket.name}/users/${userId}/${file.name}`);
    }
  }

  // Log the export for compliance
  await supabase.from('gdpr_audit_log').insert({
    action: 'DATA_EXPORT',
    subject_id: userId,
    performed_by: 'system',
    legal_basis: 'GDPR Article 15 — Right of Access',
  });

  return {
    exportedAt: new Date().toISOString(),
    subjectId: userId,
    legalBasis: 'GDPR Article 15 — Right of Access',
    data: exportData,
    storageFiles,
  };
}
```

### Step 3: Retention Policies and Backup/Restore

Automate data retention with `pg_cron` scheduled jobs and configure backup/restore using Supabase's point-in-time recovery.

**Automated retention policies with pg_cron:**

```sql
-- Enable pg_cron extension (Supabase Pro plan)
CREATE EXTENSION IF NOT EXISTS pg_cron;

-- Retention policy: delete API logs older than 30 days
SELECT cron.schedule(
  'cleanup-api-logs',
  '0 3 * * *',  -- Run at 3 AM UTC daily
  $$DELETE FROM public.api_logs
    WHERE created_at < now() - interval '30 days'$$
);

-- Retention policy: delete error logs older than 90 days
SELECT cron.schedule(
  'cleanup-error-logs',
  '0 4 * * *',  -- Run at 4 AM UTC daily
  $$DELETE FROM public.error_logs
    WHERE created_at < now() - interval '90 days'$$
);

-- Retention policy: anonymize inactive user profiles after 2 years
SELECT cron.schedule(
  'anonymize-inactive-users',
  '0 5 * * 0',  -- Run weekly on Sunday at 5 AM UTC
  $$UPDATE public.profiles
    SET email = 'anonymized-' || id || '@deleted.local',
        full_name = 'Deleted User',
        phone = NULL,
        avatar_url = NULL,
        anonymized_at = now()
    WHERE last_active_at < now() - interval '2 years'
      AND anonymized_at IS NULL$$
);

-- View scheduled jobs
SELECT jobid, schedule, command, nodename
FROM cron.job
ORDER BY jobid;

-- Monitor job execution history
SELECT jobid, start_time, end_time, status, return_message
FROM cron.job_run_details
ORDER BY start_time DESC
LIMIT 20;
```

**Retention tracking from the SDK:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(
  process.env.NEXT_PUBLIC_SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
);

// Get retention policy status
async function getRetentionStatus() {
  const policies = [
    { table: 'api_logs', retentionDays: 30 },
    { table: 'error_logs', retentionDays: 90 },
    { table: 'audit_logs', retentionDays: null },  // Never delete
  ];

  for (const policy of policies) {
    const { count } = await supabase
      .from(policy.table)
      .select('*', { count: 'exact', head: true });

    let expiredCount = 0;
    if (policy.retentionDays) {
      const cutoff = new Date();
      cutoff.setDate(cutoff.getDate() - policy.retentionDays);

      const { count: expired } = await supabase
        .from(policy.table)
        .select('*', { count: 'exact', head: true })
        .lt('created_at', cutoff.toISOString());

      expiredCount = expired ?? 0;
    }

    console.log(`${policy.table}: ${count} total, ${expiredCount} expired, retention=${policy.retentionDays ?? 'forever'}`);
  }
}
```

**Backup and restore:**

```bash
# Point-in-time recovery (PITR) — available on Pro plan
# Configured in Supabase Dashboard → Database → Backups

# Manual backup via pg_dump (for migration or offline backup)
pg_dump "postgres://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres" \
  --format=custom \
  --no-owner \
  --no-privileges \
  --file=backup-$(date +%Y%m%d).dump

# Restore to a different project (e.g., staging)
pg_restore \
  --dbname="postgres://postgres.<staging-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres" \
  --no-owner \
  --no-privileges \
  --clean \
  backup-20260322.dump

# Export specific tables as CSV for DSAR compliance
psql "postgres://postgres.<project-ref>:<password>@aws-0-<region>.pooler.supabase.com:5432/postgres" \
  -c "\COPY (SELECT * FROM profiles WHERE id = 'user-uuid') TO 'user-export.csv' CSV HEADER"
```

## Output

After completing this skill, you will have:

- **RLS tenant isolation** — row-level security policies ensuring users only access their own data
- **PII column registry** — documented and classified PII columns across all tables
- **PII scanner** — SDK-based pattern detection for emails, phones, SSNs, and IPs in text columns
- **User deletion pipeline** — complete `auth.admin.deleteUser()` flow with cascade table deletion, storage cleanup, and audit logging
- **Data export** — DSAR-compliant export of all user data from tables and storage
- **GDPR audit log** — immutable log of all deletion and export operations with legal basis
- **Automated retention** — `pg_cron` jobs for 30/90/730-day retention tiers
- **Backup/restore** — `pg_dump`/`pg_restore` commands and PITR configuration

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `auth.admin.deleteUser()` returns 404 | User already deleted or wrong ID | Check `auth.users` table; may have been deleted by another process |
| `violates foreign key constraint` during deletion | Child rows reference user | Delete in cascade order (comments → orders → profiles) or use `ON DELETE CASCADE` |
| `permission denied for function cron.schedule` | `pg_cron` not enabled or wrong plan | Enable `pg_cron` extension; requires Supabase Pro plan |
| `pg_dump: connection refused` | Using wrong port or pooler URL | Use direct connection (port 5432), not pooler (port 6543) for `pg_dump` |
| `RLS policy blocks admin operations` | Service role key not used | Use `createClient` with `SUPABASE_SERVICE_ROLE_KEY` to bypass RLS |
| Audit log entries missing | Table has RLS blocking inserts | Use `SECURITY DEFINER` function or service role for audit writes |
| Retention job not running | `pg_cron` job disabled or errored | Check `cron.job_run_details` for error messages |

## Examples

**Example 1 — Handle a GDPR deletion request:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

// API endpoint for GDPR deletion
async function handleDeletionRequest(userId: string) {
  // Verify the request is legitimate (e.g., authenticated user or admin)
  const result = await deleteUserData(userId);

  console.log(`User ${userId} deleted:`, {
    tables: result.tablesProcessed.join(', '),
    files: result.storageFilesDeleted,
    auth: result.authDeleted,
    auditId: result.auditLogId,
  });

  // GDPR requires completion within 30 days
  return { status: 'completed', auditId: result.auditLogId };
}
```

**Example 2 — Quick PII audit:**

```sql
-- Count rows with email-like patterns in unexpected columns
SELECT 'profiles' AS table_name, 'bio' AS column_name,
       count(*) AS rows_with_email
FROM public.profiles
WHERE bio ~ '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}'
UNION ALL
SELECT 'orders', 'notes',
       count(*)
FROM public.orders
WHERE notes ~ '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}';
```

**Example 3 — Verify retention job execution:**

```typescript
import { createClient } from '@supabase/supabase-js';

const supabase = createClient(url, serviceRoleKey, {
  auth: { autoRefreshToken: false, persistSession: false },
});

async function checkRetentionJobs() {
  const { data, error } = await supabase.rpc('get_cron_status');
  if (error) throw error;

  for (const job of data ?? []) {
    console.log(`Job "${job.jobname}": last_run=${job.last_run}, status=${job.status}`);
  }
}
```

## Resources

- [Row Level Security — Supabase Docs](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Auth Admin deleteUser — Supabase Docs](https://supabase.com/docs/reference/javascript/auth-admin-deleteuser)
- [Database Backups — Supabase Docs](https://supabase.com/docs/guides/platform/backups)
- [pg_cron Extension — Supabase Docs](https://supabase.com/docs/guides/database/extensions/pg_cron)
- [GDPR Developer Guide](https://gdpr.eu/developers/)
- [CCPA Compliance Guide](https://oag.ca.gov/privacy/ccpa)

## Next Steps

- For enterprise role-based access control, see `supabase-enterprise-rbac`
- For security hardening and API key scoping, see `supabase-security-basics`
- For observability and audit trail monitoring, see `supabase-observability`
