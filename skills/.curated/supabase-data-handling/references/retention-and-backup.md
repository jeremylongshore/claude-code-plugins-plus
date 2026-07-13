# Retention Policies and Backup/Restore

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
- GDPR Developer Guide
- [CCPA Compliance Guide](https://oag.ca.gov/privacy/ccpa)

## Next Steps

- For enterprise role-based access control, see `supabase-enterprise-rbac`
- For security hardening and API key scoping, see `supabase-security-basics`
- For observability and audit trail monitoring, see `supabase-observability`
