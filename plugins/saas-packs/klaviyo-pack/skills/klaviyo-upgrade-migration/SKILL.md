---
name: klaviyo-upgrade-migration
description: |
  Upgrade Klaviyo SDK versions and migrate between API revisions.
  Use when upgrading the klaviyo-api package, migrating from v1/v2 legacy APIs
  to the current REST API, or handling breaking changes between revisions.
  Trigger with phrases like "upgrade klaviyo", "klaviyo migration",
  "klaviyo breaking changes", "update klaviyo SDK", "klaviyo API revision".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, klaviyo, email-marketing, cdp]
compatible-with: claude-code
---

# Klaviyo Upgrade & Migration

## Overview

Guide for upgrading the `klaviyo-api` SDK, migrating from legacy v1/v2 APIs, and handling breaking changes between Klaviyo API revisions.

## Prerequisites

- Current Klaviyo SDK installed
- Git for version control
- Test suite available

## Klaviyo API Revision Timeline

Each revision is supported for **2 years** after release. Connect to the latest every 12-18 months.

| Revision | Released | Deprecated | Key Changes |
|----------|----------|------------|-------------|
| `2024-10-15` | Oct 2024 | Oct 2026 | Reporting API, campaign message updates |
| `2024-07-15` | Jul 2024 | Jul 2026 | Custom objects, tracking settings |
| `2024-02-15` | Feb 2024 | Feb 2026 | Bulk operations, segments V2 |
| `2023-12-15` | Dec 2023 | Dec 2025 | Profile subscription changes |
| `2023-07-15` | Jul 2023 | Jul 2025 | Relationship endpoint restructuring |

## Instructions

### Step 1: Assess Current State

```bash
# Check current SDK version
npm list klaviyo-api
# e.g., klaviyo-api@15.0.0

# Check latest available
npm view klaviyo-api version
# e.g., 21.0.0

# See all available versions
npm view klaviyo-api versions --json | tail -10
```

### Step 2: Review Breaking Changes

```bash
# View changelog
# https://github.com/klaviyo/klaviyo-api-node/releases

# Find your usage patterns that may be affected
grep -rn "from 'klaviyo-api'" src/
grep -rn "ApiKeySession\|ProfilesApi\|EventsApi" src/
```

### Step 3: Common Migration Patterns

#### Legacy v1/v2 to Current API

```typescript
// BEFORE: Legacy v1/v2 endpoints (DEPRECATED)
// POST https://a.klaviyo.com/api/v2/list/LIST_ID/subscribe
// POST https://a.klaviyo.com/api/track

// AFTER: Current REST API (2024-10-15)
import { ApiKeySession, ProfilesApi, EventsApi, ProfileEnum } from 'klaviyo-api';

const session = new ApiKeySession(process.env.KLAVIYO_PRIVATE_KEY!);

// v2 Track → Create Event
const eventsApi = new EventsApi(session);
await eventsApi.createEvent({
  data: {
    type: 'event',
    attributes: {
      metric: { data: { type: 'metric', attributes: { name: 'Placed Order' } } },
      profile: { data: { type: 'profile', attributes: { email: 'user@example.com' } } },
      properties: { orderId: '123' },
      time: new Date().toISOString(),
      value: 99.99,
    },
  },
});

// v2 Identify → Create or Update Profile
const profilesApi = new ProfilesApi(session);
await profilesApi.createOrUpdateProfile({
  data: {
    type: ProfileEnum.Profile,
    attributes: {
      email: 'user@example.com',
      firstName: 'Jane',
      properties: { plan: 'pro' },
    },
  },
});
```

#### SDK Version Upgrade (e.g., v15 to v21)

```typescript
// BEFORE (older SDK versions): ConfigWrapper pattern
// import { ConfigWrapper, Profiles } from 'klaviyo-api';
// ConfigWrapper('pk_***');
// const profiles = await Profiles.getProfiles();

// AFTER (v21+): ApiKeySession pattern
import { ApiKeySession, ProfilesApi } from 'klaviyo-api';
const session = new ApiKeySession('pk_***');
const profilesApi = new ProfilesApi(session);
const profiles = await profilesApi.getProfiles();
```

#### Property Casing Changes

```typescript
// BEFORE: Some older versions used snake_case
// { first_name: 'Jane', phone_number: '+1555...' }

// AFTER: SDK v21+ uses camelCase everywhere
{ firstName: 'Jane', phoneNumber: '+15551234567' }
```

### Step 4: Upgrade Procedure

```bash
# 1. Create upgrade branch
git checkout -b upgrade/klaviyo-api-v21

# 2. Install new version
npm install klaviyo-api@21.0.0 --save-exact

# 3. Run TypeScript compiler to find breaking changes
npx tsc --noEmit 2>&1 | grep -i "klaviyo\|error TS"

# 4. Fix all type errors, then run tests
npm test

# 5. Run integration tests against staging
KLAVIYO_TEST=1 npm run test:integration

# 6. Commit and deploy to staging first
git add package.json package-lock.json src/
git commit -m "upgrade: klaviyo-api to v21.0.0"
```

### Step 5: Rollback Procedure

```bash
# If issues found after upgrade
npm install klaviyo-api@15.0.0 --save-exact
npm test
git add package.json package-lock.json
git commit -m "revert: rollback klaviyo-api to v15.0.0"
```

## Migration Checklist

- [ ] Backup current `package-lock.json`
- [ ] Read SDK changelog for target version
- [ ] Update `ApiKeySession` import (if changed)
- [ ] Fix property casing (camelCase in v21+)
- [ ] Update response access pattern (`response.body.data`)
- [ ] Verify all filter syntax still works
- [ ] Run full test suite
- [ ] Deploy to staging first
- [ ] Monitor error rates for 24 hours after production deploy

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `TypeError: ConfigWrapper is not a function` | Old SDK pattern | Switch to `ApiKeySession` pattern |
| `Property 'first_name' does not exist` | Casing change | Use `firstName` (camelCase) |
| `response.data is undefined` | Access pattern change | Use `response.body.data` |
| `revision not supported` | Deprecated revision | Update `revision` header value |

## Resources

- [API Versioning & Deprecation Policy](https://developers.klaviyo.com/en/docs/api_versioning_and_deprecation_policy)
- [v1/v2 Migration Guide](https://developers.klaviyo.com/en/v2024-10-15/docs/best_practices_v1v2_migration)
- [Relationship Migration](https://developers.klaviyo.com/en/v2024-10-15/docs/migrate_to_2023_07_15_relationships)
- [klaviyo-api-node Releases](https://github.com/klaviyo/klaviyo-api-node/releases)

## Next Steps

For CI integration during upgrades, see `klaviyo-ci-integration`.
