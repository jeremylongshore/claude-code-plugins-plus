# RLS for Data Isolation and PII Column Management

Configure Row Level Security so users can only access their own data, and identify which columns contain PII.

## Tenant isolation with RLS

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

## PII column audit — identify sensitive data across your schema

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

## PII detection from the SDK

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

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
