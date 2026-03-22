---
name: supabase-install-auth
description: |
  Install and configure Supabase SDK, CLI, and project authentication.
  Use when setting up a new Supabase project, installing @supabase/supabase-js,
  configuring environment variables, or initializing the Supabase CLI.
  Trigger with phrases like "install supabase", "setup supabase",
  "supabase auth", "configure supabase", "supabase init".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(pnpm:*), Bash(supabase:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, setup, authentication]

---
# Supabase Install & Auth

## Overview
Set up the Supabase JavaScript SDK (`@supabase/supabase-js`), the Supabase CLI, and configure project credentials. This skill handles the full installation path from package install through verified connectivity.

## Prerequisites
- Node.js 18+ (or Deno / Bun)
- Package manager (npm, pnpm, or yarn)
- A Supabase project created at https://supabase.com/dashboard

## Instructions

### Step 1: Install the SDK

```bash
# Install the JavaScript SDK
npm install @supabase/supabase-js

# For SSR frameworks (Next.js, SvelteKit, Nuxt), also install:
npm install @supabase/ssr
```

### Step 2: Install the Supabase CLI

```bash
# Via npm (recommended)
npm install -g supabase

# Via Homebrew (macOS/Linux)
brew install supabase/tap/supabase

# Verify installation
supabase --version
```

### Step 3: Configure Environment Variables

Create a `.env` or `.env.local` file with your project credentials from the Supabase Dashboard (Settings > API):

```bash
# .env.local
SUPABASE_URL=https://<project-ref>.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIs...  # safe for client-side
SUPABASE_SERVICE_ROLE_KEY=eyJhbGciOiJIUzI1...  # server-side ONLY, never expose to browser
```

Add to `.gitignore`:
```
.env
.env.local
.env.*.local
```

### Step 4: Initialize the Client

```typescript
// lib/supabase.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'  // generated types

const supabaseUrl = process.env.SUPABASE_URL!
const supabaseAnonKey = process.env.SUPABASE_ANON_KEY!

export const supabase = createClient<Database>(supabaseUrl, supabaseAnonKey)
```

For server-side operations (API routes, Edge Functions):

```typescript
// lib/supabase-admin.ts
import { createClient } from '@supabase/supabase-js'
import type { Database } from './database.types'

export const supabaseAdmin = createClient<Database>(
  process.env.SUPABASE_URL!,
  process.env.SUPABASE_SERVICE_ROLE_KEY!,
  { auth: { autoRefreshToken: false, persistSession: false } }
)
```

### Step 5: Generate TypeScript Types

```bash
# Login to Supabase CLI
supabase login

# Link to your project
supabase link --project-ref <your-project-ref>

# Generate types from your database schema
supabase gen types typescript --linked > lib/database.types.ts
```

### Step 6: Verify Connection

```typescript
async function verifyConnection() {
  const { data, error } = await supabase.from('_test').select('*').limit(1)
  if (error && error.code !== 'PGRST116') {
    // PGRST116 = table not found, which is fine for verification
    console.error('Connection failed:', error.message)
    return false
  }
  console.log('Supabase connection verified')
  return true
}
```

### Step 7: Initialize Local Development

```bash
# Initialize Supabase in your project directory
supabase init

# Start local Supabase stack (Postgres, Auth, Storage, Edge Functions)
supabase start

# Local URLs will be printed:
# API URL: http://127.0.0.1:54321
# Studio:  http://127.0.0.1:54323
# Anon key: eyJ...
```

## Output
- `@supabase/supabase-js` installed in node_modules
- Supabase CLI available globally
- `.env.local` with project URL and keys
- `lib/supabase.ts` client singleton (anon key)
- `lib/supabase-admin.ts` admin client (service role key)
- `lib/database.types.ts` generated TypeScript types
- Verified connectivity to your Supabase project

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `FetchError: request failed` | Wrong SUPABASE_URL | Verify URL in Dashboard > Settings > API |
| `Invalid API key` | Wrong or expired key | Copy fresh key from Dashboard > Settings > API |
| `PGRST301: JWSError` | Malformed JWT in key | Ensure no trailing whitespace in env var |
| `supabase: command not found` | CLI not installed | Run `npm install -g supabase` |
| `Cannot find module '@supabase/supabase-js'` | SDK not installed | Run `npm install @supabase/supabase-js` |
| `Error: supabase start` fails | Docker not running | Start Docker Desktop, then retry |

## Security Notes

- The **anon key** is safe to expose in client-side code. It respects Row Level Security policies.
- The **service role key** bypasses RLS entirely. Use only on the server. Never bundle into client code.
- Always add `.env*` files to `.gitignore` before your first commit.

## Resources
- [Supabase JS Reference](https://supabase.com/docs/reference/javascript/initializing)
- [Supabase CLI Reference](https://supabase.com/docs/reference/cli/introduction)
- [Generating TypeScript Types](https://supabase.com/docs/guides/api/rest/generating-types)
- [Supabase Dashboard](https://supabase.com/dashboard)

## Next Steps
After successful setup, proceed to `supabase-hello-world` for your first database query.
