---
name: hubspot-upgrade-migration
description: |
  Upgrade @hubspot/api-client SDK versions and migrate between API versions.
  Use when upgrading the HubSpot Node.js SDK, migrating from v1/v2 to v3 APIs,
  or handling breaking changes in the HubSpot API client.
  Trigger with phrases like "upgrade hubspot", "hubspot SDK update",
  "hubspot breaking changes", "migrate hubspot API version", "hubspot v3 migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, crm, marketing, hubspot]
compatible-with: claude-code
---

# HubSpot Upgrade & Migration

## Overview

Guide for upgrading `@hubspot/api-client` SDK versions and migrating from legacy HubSpot APIs to the current CRM v3 API.

## Prerequisites

- Current `@hubspot/api-client` installed
- Git for version control
- Test suite available
- Staging environment for validation

## Instructions

### Step 1: Check Current Version and Available Updates

```bash
# Current version
npm list @hubspot/api-client

# Latest available
npm view @hubspot/api-client version

# See changelog
npm view @hubspot/api-client versions --json | tail -10
```

### Step 2: Review Breaking Changes

Key breaking changes in `@hubspot/api-client`:

| Version | Breaking Change | Migration |
|---------|----------------|-----------|
| v11 -> v12 | Association APIs moved to v4 namespace | `client.crm.associations.v4.basicApi` |
| v10 -> v11 | Batch API input format changed | Wrap inputs in `{ inputs: [...] }` |
| v9 -> v10 | `apiKey` auth removed (API keys deprecated) | Use `accessToken` only |
| v8 -> v9 | TypeScript strict types on all methods | Update type imports |

### Step 3: Create Upgrade Branch and Update

```bash
git checkout -b chore/upgrade-hubspot-api-client
npm install @hubspot/api-client@latest
npm test
```

### Step 4: Common Migration Patterns

#### API Key to Access Token (v9 -> v10+)

```typescript
// BEFORE (deprecated -- API keys removed in v10)
const client = new hubspot.Client({ apiKey: 'your-api-key' });

// AFTER (use private app access token)
const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
});
```

#### Associations v3 to v4 (v11 -> v12+)

```typescript
// BEFORE (v3 associations)
await client.crm.contacts.associationsApi.create(
  contactId, 'companies', companyId, 'contact_to_company'
);

// AFTER (v4 associations)
await client.crm.associations.v4.basicApi.create(
  'contacts', contactId, 'companies', companyId,
  [{ associationCategory: 'HUBSPOT_DEFINED', associationTypeId: 1 }]
);
```

#### Legacy Contact API to CRM v3

```typescript
// BEFORE (legacy /contacts/v1/)
const response = await fetch(
  `https://api.hubapi.com/contacts/v1/contact/email/${email}/profile`,
  { headers: { Authorization: `Bearer ${token}` } }
);

// AFTER (CRM v3 search)
const result = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [{
    filters: [{ propertyName: 'email', operator: 'EQ', value: email }],
  }],
  properties: ['firstname', 'lastname', 'email'],
  limit: 1,
  after: 0,
  sorts: [],
});
const contact = result.results[0];
```

#### Legacy Deals API to CRM v3

```typescript
// BEFORE (legacy /deals/v1/)
const response = await fetch(
  `https://api.hubapi.com/deals/v1/deal/${dealId}`,
  { headers: { Authorization: `Bearer ${token}` } }
);

// AFTER (CRM v3)
const deal = await client.crm.deals.basicApi.getById(
  dealId,
  ['dealname', 'amount', 'dealstage', 'pipeline', 'closedate']
);
```

### Step 5: Validate and Deploy

```bash
# Run full test suite
npm test

# Run integration tests against test account
HUBSPOT_TEST=true npm run test:integration

# If tests pass, merge
git add package.json package-lock.json src/
git commit -m "chore: upgrade @hubspot/api-client to vX.Y.Z"
```

## Output

- Updated SDK version in package.json
- Migrated breaking changes (auth, associations, types)
- All tests passing
- Documented rollback procedure

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `apiKey is not a valid option` | SDK v10+ removed API keys | Switch to `accessToken` |
| `associationsApi is not a function` | Associations moved to v4 | Use `associations.v4.basicApi` |
| Type errors after upgrade | Stricter TypeScript types | Update imports from `lib/codegen/crm/` |
| `Cannot find module` | SDK restructured exports | Check the npm package README for new imports |

## Examples

### Rollback Procedure

```bash
# If upgrade causes issues
npm install @hubspot/api-client@PREVIOUS_VERSION --save-exact
npm test
git commit -am "revert: rollback @hubspot/api-client to vPREVIOUS"
```

### Check for Deprecated API Usage

```bash
# Search for legacy API endpoints in codebase
grep -rn "contacts/v1\|deals/v1\|companies/v2\|engagements/v1" src/
grep -rn "apiKey:" src/  # deprecated auth method
grep -rn "associationsApi\." src/  # may need v4 migration
```

## Resources

- [@hubspot/api-client Changelog](https://github.com/HubSpot/hubspot-api-nodejs/blob/master/CHANGELOG.md)
- [HubSpot API Changelog](https://developers.hubspot.com/changelog)
- [CRM v3 Migration Guide](https://developers.hubspot.com/docs/guides/crm/understanding-the-crm)

## Next Steps

For CI integration during upgrades, see `hubspot-ci-integration`.
