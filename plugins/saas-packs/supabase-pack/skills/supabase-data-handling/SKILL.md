---
name: supabase-data-handling
description: |
  Implement GDPR/CCPA compliance with Supabase: RLS for data isolation, user
  deletion via auth.admin.deleteUser(), data export via SQL, PII column
  management, backup/restore workflows, and retention policies.
  Use when handling sensitive data, implementing right-to-deletion, configuring
  data retention, or auditing PII in Supabase database columns.
  Trigger with: "supabase GDPR", "supabase data handling", "supabase PII",
  "supabase compliance", "supabase data retention", "supabase delete user",
  "supabase data export".
allowed-tools: Read, Write, Edit, Bash(npx supabase:*), Bash(supabase:*), Bash(psql:*),
  Grep, Glob
version: 1.53.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- supabase
- gdpr
- ccpa
- compliance
- data-handling
- privacy
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Supabase Data Handling

## Overview

GDPR and CCPA compliance with Supabase uses a layered approach: Row Level Security (RLS) for tenant data isolation, `supabase.auth.admin.deleteUser()` for right-to-deletion, SQL-based exports for subject access requests, PII detection across columns, automated retention with `pg_cron`, and point-in-time recovery for backup/restore. Every requirement maps to a real Supabase SDK method or PostgreSQL feature.

**When to use:** Implement GDPR right-to-deletion, respond to data subject access requests (DSARs), audit PII in the database, configure automated retention, set up tenant isolation with RLS, or plan backup/restore procedures.

## Prerequisites

- `@supabase/supabase-js` v2+ with service role key for admin operations
- Supabase project on Pro plan (for `pg_cron` and point-in-time recovery)
- Understanding of GDPR Articles 15-17 (access, rectification, erasure)
- Database access via SQL Editor or `psql` for schema changes

## Instructions

### Step 1: RLS for Data Isolation and PII Column Management

Enable RLS on every table holding user data, then classify PII columns so later deletion and export steps know what to touch. The RLS skeleton is one `USING (auth.uid() = ...)` policy per access pattern:

```sql
ALTER TABLE public.profiles ENABLE ROW LEVEL SECURITY;

CREATE POLICY "users_read_own_profile" ON public.profiles
  FOR SELECT USING (auth.uid() = id);
```

Pair the policies with a PII audit — an `information_schema.columns` scan by naming pattern, `COMMENT ON COLUMN` tags, a `pii_registry` view, and an SDK-side regex scanner for emails, phones, SSNs, and IPs.

See [RLS and PII reference](references/rls-and-pii.md) for the full multi-tenant policy set, the PII audit SQL, the `pii_registry` view, and the `scanTableForPII()` SDK scanner.

### Step 2: User Deletion and Data Export

Implement GDPR Article 17 (erasure) and Article 15 (access). Deletion runs in cascade order — application tables, then storage files, then the auth user, then an immutable audit-log entry that must survive the erasure:

```typescript
// Cascade order matters: children before parents, auth user last
const tablesToPurge = ['comments', 'orders', 'documents', 'profiles'];
// ...delete rows, remove storage files, then:
await supabase.auth.admin.deleteUser(userId);
await supabase.from('gdpr_audit_log').insert({ action: 'USER_DELETION', subject_id: userId });
```

Export is the inverse: read every user-scoped table plus storage listings into one JSON payload and log a `DATA_EXPORT` audit row.

See [deletion and export reference](references/deletion-and-export.md) for the full `deleteUserData()` pipeline (with the `gdpr_audit_log` migration and locked-down RLS policy) and the `exportUserData()` DSAR builder.

### Step 3: Retention Policies and Backup/Restore

See [retention policies and backup/restore](references/retention-and-backup.md) for `pg_cron` automated retention schedules (30/90/730-day tiers), SDK-based retention monitoring, `pg_dump`/`pg_restore` commands, and point-in-time recovery configuration.

## Output

Completing this skill produces:

- **RLS tenant isolation** — row-level policies ensuring users access only their own data
- **PII column registry** — documented and classified PII columns across all tables
- **PII scanner** — SDK-based pattern detection for emails, phones, SSNs, and IPs in text columns
- **User deletion pipeline** — complete `auth.admin.deleteUser()` flow with cascade table deletion, storage cleanup, and audit logging
- **Data export** — DSAR-compliant export of all user data from tables and storage
- **GDPR audit log** — immutable log of all deletion and export operations with legal basis
- **Automated retention** — `pg_cron` jobs for 30/90/730-day retention tiers
- **Backup/restore** — `pg_dump`/`pg_restore` commands and PITR configuration

## Error Handling

| Error | Cause | Solution |
| ------- | ------- | ---------- |
| `auth.admin.deleteUser()` returns 404 | User already deleted or wrong ID | Check `auth.users` table; may have been deleted by another process |
| `violates foreign key constraint` during deletion | Child rows reference user | Delete in cascade order (comments → orders → profiles) or use `ON DELETE CASCADE` |
| `permission denied for function cron.schedule` | `pg_cron` not enabled or wrong plan | Enable `pg_cron` extension; requires Supabase Pro plan |
| `pg_dump: connection refused` | Using wrong port or pooler URL | Use direct connection (port 5432), not pooler (port 6543) for `pg_dump` |
| `RLS policy blocks admin operations` | Service role key not used | Use `createClient` with `SUPABASE_SERVICE_ROLE_KEY` to bypass RLS |
| Audit log entries missing | Table has RLS blocking inserts | Use `SECURITY DEFINER` function or service role for audit writes |
| Retention job not running | `pg_cron` job disabled or errored | Check `cron.job_run_details` for error messages |

## Examples

Each example uses the functions defined in the reference files above. See [deletion and export reference](references/deletion-and-export.md) for `deleteUserData()`.

**Example 1 — Handle a GDPR deletion request:**

```typescript
// Wraps deleteUserData() behind an API endpoint; GDPR requires completion within 30 days
async function handleDeletionRequest(userId: string) {
  const result = await deleteUserData(userId);
  return { status: 'completed', auditId: result.auditLogId };
}
```

**Example 2 — Quick PII audit:**

```sql
-- Count rows with email-like patterns in unexpected columns
SELECT 'profiles' AS table_name, 'bio' AS column_name, count(*) AS rows_with_email
FROM public.profiles
WHERE bio ~ '[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}';
```

**Example 3 — Verify retention job execution:**

```typescript
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
- [CCPA Compliance Guide](https://oag.ca.gov/privacy/ccpa)

## Next Steps

- For enterprise role-based access control, see `supabase-enterprise-rbac`
- For security hardening and API key scoping, see `supabase-security-basics`
- For observability and audit trail monitoring, see `supabase-observability`
