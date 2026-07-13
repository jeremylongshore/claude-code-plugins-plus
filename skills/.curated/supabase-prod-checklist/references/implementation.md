# Implementation Guide

## Pre-Deployment Configuration

### Step 1: Environment Variable Setup

```bash
# Required environment variables for production
NEXT_PUBLIC_SUPABASE_URL=https://your-project.supabase.co
NEXT_PUBLIC_SUPABASE_ANON_KEY=eyJ...   # Safe for client-side
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_SERVICE_ROLE_KEY=eyJ...        # Server-side ONLY
DATABASE_URL=postgresql://postgres.[REF]:[PASSWORD]@aws-0-us-east-1.pooler.supabase.com:6543/postgres  # Pooled
```

- [ ] Production API keys stored in deployment platform secrets (Vercel, Netlify, etc.)
- [ ] Environment variables set in deployment platform (not in `.env` files committed to git)
- [ ] API key scopes are minimal (least privilege)
- [ ] `.env` and `.env.local` in `.gitignore`

### Step 2: Code Quality Verification

```bash
# Verify no hardcoded credentials
grep -r "eyJ" src/ --include="*.ts" --include="*.tsx" --include="*.js"
# Should return zero results

# Verify service_role key not in client bundle
grep -r "service_role\|SERVICE_ROLE" src/ --include="*.ts" --include="*.tsx"
# Should only appear in server-side files (app/api/, lib/supabase/server.ts)

# Run test suite
npm test
npm run typecheck
npm run lint
```

- [ ] All tests passing
- [ ] No hardcoded credentials in source code
- [ ] Error handling covers Supabase error types (see errors.md)
- [ ] Retry logic with exponential backoff for transient failures
- [ ] Logging is production-appropriate (no PII, no secrets)

### Step 3: Database Configuration

```sql
-- Set statement timeout for authenticated role (prevent runaway queries)
ALTER ROLE authenticated SET statement_timeout = '10s';

-- Enable required extensions
CREATE EXTENSION IF NOT EXISTS pg_stat_statements;  -- Query monitoring
CREATE EXTENSION IF NOT EXISTS pgcrypto;             -- Encryption functions
CREATE EXTENSION IF NOT EXISTS pg_trgm;              -- Text search (if needed)

-- Verify RLS on all public tables (must return zero rows)
SELECT schemaname, tablename, rowsecurity
FROM pg_tables
WHERE schemaname = 'public' AND rowsecurity = false;
```

### Step 4: Infrastructure Setup

- [ ] Health check endpoint deployed (see examples.md)
- [ ] Monitoring/alerting configured (error rates, latency, pool usage)
- [ ] Custom domain configured and DNS verified
- [ ] Network restrictions applied (IP allowlist)
- [ ] SSL enforcement enabled

### Step 5: Migration Verification

```bash
# Verify migrations are clean
npx supabase db reset           # Reset local DB and replay all migrations
npx supabase migration list     # Compare local vs remote migration history
npx supabase db diff --use-migra # Check for schema drift

# Apply to production
npx supabase db push
```

- [ ] All schema changes captured in `supabase/migrations/`
- [ ] Migrations replay cleanly on a fresh database
- [ ] No schema drift between local and remote
- [ ] Rollback migration prepared for risky changes

### Step 6: Deploy with Verification

```bash
# Pre-flight checks
curl -sf https://status.supabase.com/api/v2/status.json | jq '.status'
npx supabase db ping --linked

# Deploy application
# (Platform-specific: Vercel, Netlify, etc.)

# Post-deploy verification
curl -sf https://your-app.com/api/health | jq '.'
# Expected: { "status": "healthy", "latency_ms": <50, ... }
```

### Step 7: Post-Launch Monitoring (First 24 Hours)

| Check | Frequency | Where |
|-------|-----------|-------|
| Health check response | Every 5 min | Uptime monitor (UptimeRobot, Better Stack) |
| API error rate | Hourly | Dashboard > Logs > API |
| Query performance | Every 4 hours | Dashboard > Database > Performance |
| Connection pool usage | Every 2 hours | Dashboard > Database > Connections |
| Auth success rate | Every 4 hours | Dashboard > Auth > Logs |
| Storage bandwidth | Daily | Dashboard > Storage |

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
