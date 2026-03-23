---
name: supabase-policy-guardrails
description: |
  Enforce organizational governance for Supabase projects: shared RLS policy
  library with reusable templates, table and column naming conventions,
  migration review process with CI checks, cost alert thresholds,
  and security audit scripts scanning for common misconfigurations.
  Use when establishing Supabase standards across teams, creating RLS
  policy templates, setting up migration review workflows, or auditing
  existing projects for security and cost issues.
  Trigger with phrases like "supabase governance", "supabase policy library",
  "supabase naming convention", "supabase migration review",
  "supabase cost alert", "supabase security audit", "supabase RLS template".
allowed-tools: Read, Write, Edit, Bash(supabase:*), Bash(psql:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, governance, security, rls, naming-conventions, cost-management]
---

# Supabase Policy Guardrails

## Overview

Organizational governance for Supabase at scale: a **shared RLS policy library** (reusable templates for common access patterns), **naming conventions** (tables, columns, functions, policies), **migration review process** (CI checks ensuring RLS, preventing destructive operations, enforcing naming), **cost alert configuration** (billing thresholds and usage monitoring), and **security audit scripts** (scanning for exposed keys, missing RLS, overly permissive policies). All patterns use real `createClient` from `@supabase/supabase-js` and Supabase CLI commands.

## Prerequisites

- Supabase project with `supabase` CLI installed and linked
- `@supabase/supabase-js` v2+ installed
- CI/CD pipeline (GitHub Actions recommended)
- Database access via `psql` or Supabase SQL Editor
- Pro plan recommended for cost alerts and usage API

## Step 1 — Shared RLS Policy Library and Naming Conventions

### RLS Policy Templates

Create reusable RLS policy templates that teams apply to new tables. This prevents each developer from writing ad-hoc policies and ensures consistent access control.

```sql
-- supabase/migrations/00000000000000_rls_policy_library.sql
-- Shared RLS policy library — apply these templates to new tables

-- ============================================================
-- Template 1: Owner-only access (user owns the row)
-- Usage: tables with a user_id column (todos, profiles, settings)
-- ============================================================
CREATE OR REPLACE FUNCTION public.rls_owner_only(table_name text, user_column text DEFAULT 'user_id')
RETURNS void AS $$
BEGIN
  EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);

  EXECUTE format(
    'CREATE POLICY "owner_select" ON public.%I FOR SELECT USING (%I = auth.uid())',
    table_name, user_column
  );
  EXECUTE format(
    'CREATE POLICY "owner_insert" ON public.%I FOR INSERT WITH CHECK (%I = auth.uid())',
    table_name, user_column
  );
  EXECUTE format(
    'CREATE POLICY "owner_update" ON public.%I FOR UPDATE USING (%I = auth.uid())',
    table_name, user_column
  );
  EXECUTE format(
    'CREATE POLICY "owner_delete" ON public.%I FOR DELETE USING (%I = auth.uid())',
    table_name, user_column
  );
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Template 2: Organization-scoped access (user is member of org)
-- Usage: tables with org_id referencing org_members
-- ============================================================
CREATE OR REPLACE FUNCTION public.rls_org_scoped(
  table_name text,
  org_column text DEFAULT 'org_id',
  allow_delete boolean DEFAULT false
)
RETURNS void AS $$
BEGIN
  EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);

  EXECUTE format(
    'CREATE POLICY "org_select" ON public.%I FOR SELECT USING (
      %I IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
    )', table_name, org_column
  );
  EXECUTE format(
    'CREATE POLICY "org_insert" ON public.%I FOR INSERT WITH CHECK (
      %I IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid())
    )', table_name, org_column
  );
  EXECUTE format(
    'CREATE POLICY "org_update" ON public.%I FOR UPDATE USING (
      %I IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid() AND role IN (''admin'', ''editor''))
    )', table_name, org_column
  );

  IF allow_delete THEN
    EXECUTE format(
      'CREATE POLICY "org_delete" ON public.%I FOR DELETE USING (
        %I IN (SELECT org_id FROM public.org_members WHERE user_id = auth.uid() AND role = ''admin'')
      )', table_name, org_column
    );
  END IF;
END;
$$ LANGUAGE plpgsql;

-- ============================================================
-- Template 3: Public read, authenticated write
-- Usage: blog posts, product listings, public content
-- ============================================================
CREATE OR REPLACE FUNCTION public.rls_public_read_auth_write(
  table_name text,
  owner_column text DEFAULT 'created_by'
)
RETURNS void AS $$
BEGIN
  EXECUTE format('ALTER TABLE public.%I ENABLE ROW LEVEL SECURITY', table_name);

  EXECUTE format(
    'CREATE POLICY "public_select" ON public.%I FOR SELECT USING (true)',
    table_name
  );
  EXECUTE format(
    'CREATE POLICY "auth_insert" ON public.%I FOR INSERT WITH CHECK (auth.uid() IS NOT NULL)',
    table_name
  );
  EXECUTE format(
    'CREATE POLICY "owner_update" ON public.%I FOR UPDATE USING (%I = auth.uid())',
    table_name, owner_column
  );
  EXECUTE format(
    'CREATE POLICY "owner_delete" ON public.%I FOR DELETE USING (%I = auth.uid())',
    table_name, owner_column
  );
END;
$$ LANGUAGE plpgsql;

-- Apply templates to tables:
-- SELECT public.rls_owner_only('todos');
-- SELECT public.rls_org_scoped('projects', 'org_id', true);
-- SELECT public.rls_public_read_auth_write('blog_posts', 'author_id');
```

### Naming Conventions

```sql
-- supabase/migrations/00000000000001_naming_convention_check.sql
-- Validation function that checks naming conventions at migration time

CREATE OR REPLACE FUNCTION public.validate_naming_conventions()
RETURNS TABLE(issue text, object_name text, suggestion text) AS $$
BEGIN
  -- Tables must be snake_case, plural
  RETURN QUERY
  SELECT
    'Table name should be plural snake_case'::text,
    t.tablename::text,
    regexp_replace(t.tablename, '([A-Z])', '_\1', 'g')::text
  FROM pg_tables t
  WHERE t.schemaname = 'public'
  AND (
    t.tablename ~ '[A-Z]'           -- contains uppercase
    OR t.tablename ~ '-'             -- contains hyphens
    OR t.tablename !~ 's$'           -- not plural (heuristic)
  )
  AND t.tablename NOT LIKE '\_%';   -- skip internal tables

  -- Columns must be snake_case
  RETURN QUERY
  SELECT
    'Column name should be snake_case'::text,
    (c.table_name || '.' || c.column_name)::text,
    regexp_replace(c.column_name, '([A-Z])', '_\1', 'g')::text
  FROM information_schema.columns c
  WHERE c.table_schema = 'public'
  AND (c.column_name ~ '[A-Z]' OR c.column_name ~ '-');

  -- Foreign key columns should end with _id
  RETURN QUERY
  SELECT
    'Foreign key column should end with _id'::text,
    (tc.table_name || '.' || kcu.column_name)::text,
    (kcu.column_name || '_id')::text
  FROM information_schema.table_constraints tc
  JOIN information_schema.key_column_usage kcu
    ON tc.constraint_name = kcu.constraint_name
  WHERE tc.constraint_type = 'FOREIGN KEY'
  AND tc.table_schema = 'public'
  AND kcu.column_name NOT LIKE '%_id';

  -- Boolean columns should start with is_ or has_
  RETURN QUERY
  SELECT
    'Boolean column should start with is_ or has_'::text,
    (c.table_name || '.' || c.column_name)::text,
    ('is_' || c.column_name)::text
  FROM information_schema.columns c
  WHERE c.table_schema = 'public'
  AND c.data_type = 'boolean'
  AND c.column_name NOT LIKE 'is_%'
  AND c.column_name NOT LIKE 'has_%';
END;
$$ LANGUAGE plpgsql;

-- Run: SELECT * FROM public.validate_naming_conventions();
```

### Naming Convention Reference

| Object | Convention | Example |
|--------|-----------|---------|
| Tables | Plural snake_case | `user_profiles`, `order_items` |
| Columns | snake_case | `created_at`, `full_name` |
| Foreign keys | `{referenced_table_singular}_id` | `user_id`, `order_id` |
| Booleans | `is_` or `has_` prefix | `is_active`, `has_verified_email` |
| Timestamps | `_at` suffix | `created_at`, `updated_at`, `deleted_at` |
| RLS policies | `{scope}_{operation}` | `owner_select`, `org_insert` |
| Functions | `verb_noun` | `create_user`, `get_dashboard_metrics` |
| Indexes | `idx_{table}_{columns}` | `idx_orders_user_id_created_at` |
| Migrations | `{timestamp}_{verb}_{description}` | `20250322000000_create_orders_table.sql` |

## Step 2 — Migration Review Process with CI Checks

### GitHub Actions Migration Guardrails

```yaml
# .github/workflows/supabase-guardrails.yml
name: Supabase Migration Guardrails

on:
  pull_request:
    paths:
      - 'supabase/migrations/**'

jobs:
  migration-review:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: supabase/setup-cli@v1

      - name: Start local Supabase
        run: supabase start

      - name: Apply migrations
        run: supabase db reset

      - name: Check RLS enabled on all public tables
        run: |
          MISSING_RLS=$(supabase db query "
            SELECT tablename FROM pg_tables
            WHERE schemaname = 'public'
            AND rowsecurity = false
            AND tablename NOT LIKE '\_%'
            AND tablename NOT IN ('schema_migrations')
          " --output csv | tail -n +2)

          if [ -n "$MISSING_RLS" ]; then
            echo "::error::Tables missing RLS: $MISSING_RLS"
            echo "Fix: ALTER TABLE public.<table> ENABLE ROW LEVEL SECURITY;"
            exit 1
          fi
          echo "All public tables have RLS enabled"

      - name: Check migration naming convention
        run: |
          for file in supabase/migrations/*.sql; do
            basename=$(basename "$file")
            if ! echo "$basename" | grep -qE '^[0-9]{14}_(create|alter|drop|add|remove|update|fix|seed|enable|disable)_[a-z_]+\.sql$'; then
              echo "::error::Migration '$basename' violates naming convention"
              echo "Expected: <14-digit-timestamp>_<verb>_<description>.sql"
              exit 1
            fi
          done
          echo "Migration naming convention check passed"

      - name: Block unannotated destructive operations
        run: |
          for file in supabase/migrations/*.sql; do
            if grep -qiE 'DROP TABLE|DROP COLUMN|TRUNCATE|DELETE FROM.*WHERE\s+(1=1|true)' "$file"; then
              if ! grep -qi '-- APPROVED-DESTRUCTIVE:' "$file"; then
                echo "::error::Destructive operation in $file without approval annotation"
                echo "Add '-- APPROVED-DESTRUCTIVE: <reason>' to acknowledge"
                exit 1
              fi
            fi
          done
          echo "Destructive operation check passed"

      - name: Validate naming conventions
        run: |
          ISSUES=$(supabase db query "SELECT * FROM public.validate_naming_conventions()" --output csv | tail -n +2)
          if [ -n "$ISSUES" ]; then
            echo "::warning::Naming convention issues found:"
            echo "$ISSUES"
          fi

      - name: Check foreign key indexes
        run: |
          MISSING_INDEXES=$(supabase db query "
            SELECT
              tc.table_name,
              kcu.column_name
            FROM information_schema.table_constraints tc
            JOIN information_schema.key_column_usage kcu
              ON tc.constraint_name = kcu.constraint_name
            LEFT JOIN pg_indexes pi
              ON pi.tablename = tc.table_name
              AND pi.indexdef LIKE '%' || kcu.column_name || '%'
            WHERE tc.constraint_type = 'FOREIGN KEY'
            AND tc.table_schema = 'public'
            AND pi.indexname IS NULL
          " --output csv | tail -n +2)

          if [ -n "$MISSING_INDEXES" ]; then
            echo "::warning::Foreign key columns missing indexes: $MISSING_INDEXES"
          fi

      - name: Stop Supabase
        if: always()
        run: supabase stop
```

### Pre-Commit Hook for Secrets and SQL Lint

```bash
#!/bin/bash
# scripts/supabase-pre-commit.sh
set -euo pipefail

echo "Running Supabase pre-commit checks..."

STAGED_FILES=$(git diff --cached --name-only --diff-filter=ACM)

# Check 1: No hardcoded Supabase keys (JWT format)
if echo "$STAGED_FILES" | grep -v '.env' | grep -v 'pnpm-lock' | \
   xargs grep -lE 'eyJ[A-Za-z0-9_-]{50,}\.' 2>/dev/null; then
  echo "ERROR: Possible Supabase API key in staged files"
  echo "Use environment variables instead"
  exit 1
fi

# Check 2: No connection strings
if echo "$STAGED_FILES" | xargs grep -lE 'postgres://postgres\.[a-z]+:' 2>/dev/null; then
  echo "ERROR: Supabase connection string in staged files"
  exit 1
fi

# Check 3: Migration files have RLS (new tables)
for file in $(echo "$STAGED_FILES" | grep 'supabase/migrations/.*\.sql$' || true); do
  if grep -qi 'CREATE TABLE public\.' "$file"; then
    if ! grep -qi 'ENABLE ROW LEVEL SECURITY' "$file"; then
      echo "ERROR: $file creates a table without enabling RLS"
      echo "Add: ALTER TABLE public.<table> ENABLE ROW LEVEL SECURITY;"
      exit 1
    fi
  fi
done

echo "Supabase pre-commit checks passed"
```

```bash
# Install with Husky
npx husky add .husky/pre-commit 'bash scripts/supabase-pre-commit.sh'
```

## Step 3 — Cost Alerts and Security Audit Scripts

### Cost Alert Configuration

```typescript
// scripts/supabase-cost-monitor.ts
import { createClient } from '@supabase/supabase-js'

// Use the Supabase Management API for cost monitoring
const SUPABASE_ACCESS_TOKEN = process.env.SUPABASE_ACCESS_TOKEN!
const PROJECT_REF = process.env.SUPABASE_PROJECT_REF!

interface UsageMetrics {
  database_size_gb: number
  storage_size_gb: number
  bandwidth_gb: number
  edge_function_invocations: number
  monthly_active_users: number
}

// Cost thresholds — adjust per your budget
const THRESHOLDS = {
  database_size_gb: 8,          // Pro includes 8 GB
  storage_size_gb: 100,         // Pro includes 100 GB
  bandwidth_gb: 250,            // Pro includes 250 GB
  edge_function_invocations: 2_000_000,  // Pro includes 2M
  monthly_active_users: 100_000,          // Pro limit
}

async function checkCostAlerts() {
  // Fetch current usage via Supabase Management API
  const response = await fetch(
    `https://api.supabase.com/v1/projects/${PROJECT_REF}/usage`,
    {
      headers: { Authorization: `Bearer ${SUPABASE_ACCESS_TOKEN}` },
    }
  )

  if (!response.ok) {
    console.error('Failed to fetch usage:', response.statusText)
    return
  }

  const usage: UsageMetrics = await response.json()

  const alerts: string[] = []

  for (const [metric, threshold] of Object.entries(THRESHOLDS)) {
    const current = usage[metric as keyof UsageMetrics] as number
    const percent = (current / threshold) * 100

    if (percent >= 90) {
      alerts.push(`CRITICAL: ${metric} at ${percent.toFixed(1)}% (${current}/${threshold})`)
    } else if (percent >= 75) {
      alerts.push(`WARNING: ${metric} at ${percent.toFixed(1)}% (${current}/${threshold})`)
    }
  }

  if (alerts.length > 0) {
    console.warn('Cost alerts:\n' + alerts.join('\n'))
    // Send to Slack, PagerDuty, email, etc.
    await sendCostAlert(alerts)
  } else {
    console.log('All usage metrics within budget')
  }
}

async function sendCostAlert(alerts: string[]) {
  // Example: Slack webhook
  const webhookUrl = process.env.SLACK_WEBHOOK_URL
  if (!webhookUrl) return

  await fetch(webhookUrl, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({
      text: `*Supabase Cost Alert* (${PROJECT_REF})\n${alerts.join('\n')}`,
    }),
  })
}
```

### Security Audit Script

```typescript
// scripts/supabase-security-audit.ts
import { createClient } from '@supabase/supabase-js'

const supabase = createClient(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

interface AuditFinding {
  severity: 'critical' | 'high' | 'medium' | 'low'
  category: string
  description: string
  remediation: string
}

export async function runSecurityAudit(): Promise<AuditFinding[]> {
  const findings: AuditFinding[] = []

  // Check 1: Tables without RLS
  const { data: noRls } = await supabase.rpc('run_sql', {
    sql: `
      SELECT tablename FROM pg_tables
      WHERE schemaname = 'public'
      AND rowsecurity = false
      AND tablename NOT LIKE '\\_%'
    `,
  })

  for (const row of noRls ?? []) {
    findings.push({
      severity: 'critical',
      category: 'RLS',
      description: `Table "${row.tablename}" has RLS disabled`,
      remediation: `ALTER TABLE public.${row.tablename} ENABLE ROW LEVEL SECURITY;`,
    })
  }

  // Check 2: Tables with RLS enabled but no policies
  const { data: noPolicies } = await supabase.rpc('run_sql', {
    sql: `
      SELECT t.tablename
      FROM pg_tables t
      LEFT JOIN pg_policies p ON p.tablename = t.tablename AND p.schemaname = t.schemaname
      WHERE t.schemaname = 'public'
      AND t.rowsecurity = true
      AND p.policyname IS NULL
    `,
  })

  for (const row of noPolicies ?? []) {
    findings.push({
      severity: 'high',
      category: 'RLS',
      description: `Table "${row.tablename}" has RLS enabled but no policies (blocks all access)`,
      remediation: 'Add appropriate RLS policies or this table is inaccessible via API',
    })
  }

  // Check 3: Overly permissive policies (USING (true) for non-public tables)
  const { data: permissive } = await supabase.rpc('run_sql', {
    sql: `
      SELECT tablename, policyname, qual
      FROM pg_policies
      WHERE schemaname = 'public'
      AND qual = 'true'
      AND cmd != 'SELECT'
    `,
  })

  for (const row of permissive ?? []) {
    findings.push({
      severity: 'high',
      category: 'RLS',
      description: `Policy "${row.policyname}" on "${row.tablename}" allows unrestricted writes (USING true)`,
      remediation: 'Restrict policy to owner or organization scope',
    })
  }

  // Check 4: Foreign key columns without indexes
  const { data: missingIdx } = await supabase.rpc('run_sql', {
    sql: `
      SELECT
        tc.table_name,
        kcu.column_name
      FROM information_schema.table_constraints tc
      JOIN information_schema.key_column_usage kcu
        ON tc.constraint_name = kcu.constraint_name
      LEFT JOIN pg_indexes pi
        ON pi.tablename = tc.table_name
        AND pi.indexdef LIKE '%' || kcu.column_name || '%'
      WHERE tc.constraint_type = 'FOREIGN KEY'
      AND tc.table_schema = 'public'
      AND pi.indexname IS NULL
    `,
  })

  for (const row of missingIdx ?? []) {
    findings.push({
      severity: 'medium',
      category: 'Performance',
      description: `Foreign key ${row.table_name}.${row.column_name} has no index`,
      remediation: `CREATE INDEX idx_${row.table_name}_${row.column_name} ON public.${row.table_name}(${row.column_name});`,
    })
  }

  // Check 5: Storage buckets without RLS
  const { data: buckets } = await supabase.storage.listBuckets()
  for (const bucket of buckets ?? []) {
    if (bucket.public) {
      findings.push({
        severity: 'low',
        category: 'Storage',
        description: `Bucket "${bucket.name}" is public — verify this is intentional`,
        remediation: 'Set bucket to private if it contains sensitive files',
      })
    }
  }

  return findings
}

// Run and display results
async function main() {
  const findings = await runSecurityAudit()

  const critical = findings.filter(f => f.severity === 'critical')
  const high = findings.filter(f => f.severity === 'high')

  console.log(`\nSecurity Audit Results:`)
  console.log(`  Critical: ${critical.length}`)
  console.log(`  High: ${high.length}`)
  console.log(`  Medium: ${findings.filter(f => f.severity === 'medium').length}`)
  console.log(`  Low: ${findings.filter(f => f.severity === 'low').length}`)

  for (const finding of findings) {
    console.log(`\n[${finding.severity.toUpperCase()}] ${finding.category}: ${finding.description}`)
    console.log(`  Fix: ${finding.remediation}`)
  }

  // Exit with error code if critical/high issues found
  if (critical.length > 0 || high.length > 0) {
    process.exit(1)
  }
}

main()
```

### Scheduled Audit via Edge Function

```typescript
// supabase/functions/security-audit/index.ts
import { createClient } from 'https://esm.sh/@supabase/supabase-js@2'

Deno.serve(async () => {
  const supabase = createClient(
    Deno.env.get('SUPABASE_URL')!,
    Deno.env.get('SUPABASE_SERVICE_ROLE_KEY')!
  )

  // Check tables without RLS
  const { data: noRls } = await supabase
    .from('pg_tables')
    .select('tablename')
    .eq('schemaname', 'public')
    .eq('rowsecurity', false)

  const issues = (noRls ?? []).map(t => t.tablename)

  if (issues.length > 0) {
    // Store audit result
    await supabase.from('audit_log').insert({
      event: 'security_audit',
      severity: 'critical',
      details: { tables_without_rls: issues },
    })
  }

  return new Response(JSON.stringify({
    status: issues.length === 0 ? 'pass' : 'fail',
    tables_without_rls: issues,
    checked_at: new Date().toISOString(),
  }))
})
```

## Output

- Shared RLS policy library with owner-only, org-scoped, and public-read templates
- Naming convention validation function checking tables, columns, FKs, and booleans
- CI pipeline enforcing RLS, naming, and destructive operation controls
- Pre-commit hook blocking hardcoded secrets and tables without RLS
- Cost monitoring script with configurable thresholds and Slack alerting
- Security audit script detecting missing RLS, permissive policies, and missing indexes
- Scheduled Edge Function for continuous security monitoring

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| CI RLS check fails on new table | Migration missing `ENABLE ROW LEVEL SECURITY` | Add `ALTER TABLE` after `CREATE TABLE` in same migration |
| Naming convention false positive | Table is intentionally singular (e.g., `config`) | Add to exclusion list in validation function |
| Cost alert not firing | Missing `SUPABASE_ACCESS_TOKEN` | Generate token at supabase.com/dashboard/account/tokens |
| Security audit times out | Too many tables to scan | Run audit on specific schemas or paginate results |
| Pre-commit blocks legitimate JWT in test | Test fixture contains JWT-like string | Add test file path to exclusion pattern |
| RLS template function not found | Migration not applied | Run `supabase db reset` or apply migration manually |

## Examples

### Apply RLS Template to a New Table

```sql
-- Create the table
CREATE TABLE public.tasks (
  id uuid PRIMARY KEY DEFAULT gen_random_uuid(),
  org_id uuid NOT NULL REFERENCES public.organizations(id),
  title text NOT NULL,
  is_complete boolean DEFAULT false,
  created_by uuid REFERENCES auth.users(id),
  created_at timestamptz DEFAULT now()
);

-- Apply org-scoped RLS template (with delete for admins)
SELECT public.rls_org_scoped('tasks', 'org_id', true);

-- Create index on foreign key
CREATE INDEX idx_tasks_org_id ON public.tasks(org_id);
```

### Run Security Audit Locally

```bash
npx tsx scripts/supabase-security-audit.ts
```

### Check Naming Conventions

```sql
SELECT * FROM public.validate_naming_conventions();
```

## Resources

- [Supabase Row Level Security](https://supabase.com/docs/guides/database/postgres/row-level-security)
- [Supabase CLI Migrations](https://supabase.com/docs/guides/cli/managing-environments)
- [Supabase Management API](https://supabase.com/docs/reference/api/introduction)
- [Supabase Pricing](https://supabase.com/pricing)
- [PostgreSQL Naming Conventions](https://www.postgresql.org/docs/current/sql-syntax-lexical.html#SQL-SYNTAX-IDENTIFIERS)

## Next Steps

For architecture patterns across different app types, see `supabase-architecture-variants`.
