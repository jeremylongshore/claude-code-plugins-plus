---
name: supabase-upgrade-migration
description: |
  Analyze, plan, and execute Supabase SDK and CLI upgrades with breaking change detection.
  Use when upgrading @supabase/supabase-js versions, migrating from v1 to v2,
  or detecting deprecations in your Supabase integration.
  Trigger with phrases like "upgrade supabase", "supabase breaking changes",
  "update supabase SDK", "supabase v2 migration", "supabase version".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Bash(supabase:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, supabase, migration, upgrade]

---
# Supabase Upgrade Migration

## Overview
Upgrade `@supabase/supabase-js` and the Supabase CLI safely with breaking change detection, automated code migration, and rollback planning. Covers the common v1-to-v2 migration path and minor version upgrades.

## Current State
!`npm list @supabase/supabase-js 2>/dev/null | grep supabase || echo 'not installed'`
!`supabase --version 2>/dev/null || echo 'CLI not installed'`

## Prerequisites
- Current Supabase SDK installed
- Git with clean working tree
- Test suite available

## Instructions

### Step 1: Audit Current Version and Usage

```bash
# Check current SDK version
npm list @supabase/supabase-js

# Check CLI version
supabase --version

# Find all Supabase imports in your codebase
grep -rn "from '@supabase/supabase-js'" --include="*.ts" --include="*.tsx" src/
grep -rn "from 'supabase'" --include="*.py" src/
```

### Step 2: Review Breaking Changes

**supabase-js v1 to v2 breaking changes:**

| v1 Pattern | v2 Pattern |
|-----------|-----------|
| `createClient(url, key)` | Same (no change) |
| `supabase.auth.session()` (sync) | `supabase.auth.getSession()` (async) |
| `supabase.auth.user()` (sync) | `supabase.auth.getUser()` (async) |
| `supabase.auth.signIn({ email, password })` | `supabase.auth.signInWithPassword({ email, password })` |
| `supabase.auth.signIn({ provider: 'google' })` | `supabase.auth.signInWithOAuth({ provider: 'google' })` |
| `supabase.auth.signIn({ email })` (magic link) | `supabase.auth.signInWithOtp({ email })` |
| `supabase.auth.api.resetPasswordForEmail(email)` | `supabase.auth.resetPasswordForEmail(email)` |
| `supabase.auth.onAuthStateChange(callback)` returns `{ data: subscription }` | Returns `{ data: { subscription } }` |
| `error.message` string parsing | `error.code` enum for reliable matching |
| `.single()` returns error on 0 rows | Same, use `.maybeSingle()` for optional |

### Step 3: Run the Upgrade

```bash
# Create a branch
git checkout -b upgrade-supabase-sdk

# Upgrade SDK
npm install @supabase/supabase-js@latest

# Upgrade CLI
npm install -g supabase@latest

# If using SSR helper:
npm install @supabase/ssr@latest

# Regenerate types (schema may have evolved)
supabase gen types typescript --linked > lib/database.types.ts
```

### Step 4: Apply Code Migrations

```typescript
// BEFORE (v1 auth patterns)
const session = supabase.auth.session()
const user = supabase.auth.user()
const { error } = await supabase.auth.signIn({ email, password })

// AFTER (v2 auth patterns)
const { data: { session } } = await supabase.auth.getSession()
const { data: { user } } = await supabase.auth.getUser()
const { error } = await supabase.auth.signInWithPassword({ email, password })

// BEFORE (v1 auth state listener)
const { data: subscription } = supabase.auth.onAuthStateChange(callback)
subscription.unsubscribe()

// AFTER (v2 auth state listener)
const { data: { subscription } } = supabase.auth.onAuthStateChange(callback)
subscription.unsubscribe()

// BEFORE (v1 error handling)
if (error.message.includes('not found')) { ... }

// AFTER (v2 error handling)
if (error.code === 'PGRST116') { ... }
```

### Step 5: Verify and Test

```bash
# Type check
npx tsc --noEmit

# Run tests
npm test

# Manual smoke test critical auth flows:
# - Sign up → confirm email → sign in
# - OAuth sign in → callback
# - Password reset flow
# - Session refresh across page navigations
```

### Step 6: Rollback Plan

```bash
# If upgrade causes issues:
git stash  # stash any uncommitted work
npm install @supabase/supabase-js@<previous-version>

# Or revert the branch
git checkout main
```

## Output
- SDK upgraded to latest version
- Breaking changes identified and fixed
- Type checking passes with new types
- Test suite green
- Rollback procedure documented

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `Property 'session' does not exist` | v1 sync methods removed in v2 | Use async `getSession()` |
| `Property 'signIn' does not exist` | Renamed in v2 | Use `signInWithPassword` / `signInWithOAuth` / `signInWithOtp` |
| Type errors after `gen types` | Schema changed | Update code to match new types |
| `supabase.auth.api` undefined | `.api` removed in v2 | Methods moved to `supabase.auth.*` directly |

## Resources
- [supabase-js v2 Migration Guide](https://supabase.com/blog/supabase-js-v2)
- [supabase-js Releases](https://github.com/supabase/supabase-js/releases)
- [Supabase CLI Releases](https://github.com/supabase/cli/releases)

## Next Steps
For CI integration with the new SDK, see `supabase-ci-integration`.
