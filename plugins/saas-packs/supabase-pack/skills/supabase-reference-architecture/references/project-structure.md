# Project Structure — Monorepo Layout

## Recommended Directory Layout

```
my-platform/
├── packages/
│   └── supabase/                    # Shared Supabase package
│       ├── supabase/
│       │   ├── config.toml          # Supabase CLI config
│       │   ├── migrations/          # Version-controlled SQL migrations
│       │   │   ├── 20260101000000_create_tenants.sql
│       │   │   ├── 20260102000000_create_profiles.sql
│       │   │   └── 20260103000000_create_audit_log.sql
│       │   ├── seed.sql             # Development seed data
│       │   └── functions/           # Edge Functions (Deno runtime)
│       │       ├── process-order/index.ts
│       │       └── send-notification/index.ts
│       ├── src/
│       │   ├── client.ts            # Client singleton (anon key)
│       │   ├── admin.ts             # Admin client (service_role, server only)
│       │   ├── database.types.ts    # Auto-generated from `supabase gen types`
│       │   └── errors.ts            # Custom error classes
│       ├── package.json
│       └── tsconfig.json
├── apps/
│   ├── web/                         # Next.js / SvelteKit frontend
│   ├── admin/                       # Internal admin dashboard
│   └── worker/                      # Background job runner
├── pnpm-workspace.yaml
└── turbo.json
```

## Migration Management

Keep migrations in version control. Every schema change is a new migration file.

```bash
# Generate a new migration after making changes in the dashboard
supabase db diff --use-migra -f add_orders_table

# Apply migrations locally
supabase db reset

# Push migrations to production
supabase db push

# Regenerate TypeScript types after any schema change
supabase gen types typescript --local > packages/supabase/src/database.types.ts
```

Add a `turbo.json` pipeline so type generation runs after migrations:

```json
{
  "pipeline": {
    "@my-platform/supabase#gen-types": {
      "outputs": ["src/database.types.ts"],
      "cache": false
    },
    "build": {
      "dependsOn": ["@my-platform/supabase#gen-types"]
    }
  }
}
```

## Microservices with Separate Supabase Projects

For large organizations, each service owns its own Supabase project. Cross-service reads use the `service_role` key (bypasses RLS).

```typescript
// services/billing/src/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { BillingDB } from './database.types'

export const billingDb = createClient<BillingDB>(
  process.env.BILLING_SUPABASE_URL!,
  process.env.BILLING_SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

// Cross-project access: read user profiles from the main project
import type { MainDB } from '@my-platform/supabase'

const mainDb = createClient<MainDB>(
  process.env.MAIN_SUPABASE_URL!,
  process.env.MAIN_SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)

export async function getUserProfile(userId: string) {
  const { data, error } = await mainDb
    .from('profiles')
    .select('id, email, display_name, avatar_url')
    .eq('id', userId)
    .single()

  if (error) throw new Error(`Cross-project profile lookup failed: ${error.message}`)
  return data
}
```

Cross-project access rules:
- Always use `service_role` key (it bypasses RLS)
- Never expose `service_role` keys to client-side code
- Limit cross-project calls to read-only where possible
- Consider caching cross-project lookups to reduce latency
