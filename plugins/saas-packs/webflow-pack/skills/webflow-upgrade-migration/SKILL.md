---
name: webflow-upgrade-migration
description: |
  Analyze, plan, and execute Webflow SDK upgrades (webflow-api v1 to v3) with
  breaking change detection, API v1-to-v2 migration, and deprecation handling.
  Trigger with phrases like "upgrade webflow", "webflow migration",
  "webflow breaking changes", "update webflow SDK", "webflow v1 to v2".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, design, no-code, webflow]
compatible-with: claude-code
---

# Webflow Upgrade & Migration

## Overview

Guide for upgrading the `webflow-api` SDK and migrating from Webflow Data API v1
to v2. Covers breaking changes, endpoint mapping, import updates, and rollback.

## Prerequisites

- Current `webflow-api` SDK installed
- Git for version control (create upgrade branch)
- Test suite available
- Staging environment for validation

## Instructions

### Step 1: Assess Current Version

```bash
# Check installed version
npm list webflow-api

# Check latest available
npm view webflow-api version

# View changelog
npm view webflow-api --json | jq '.versions[-5:]'
```

### Step 2: SDK Version History

| SDK Version | API Version | Node.js | Key Changes |
|-------------|-------------|---------|-------------|
| 3.x | Data API v2 | 18+ | Current. `WebflowClient`, auto-retry, bulk ops |
| 2.x | Data API v1/v2 | 16+ | Transitional. Mixed v1/v2 endpoints |
| 1.x | Data API v1 | 14+ | Legacy. `Webflow` class, no types |

**v1 endpoints deprecation: late 2026.** Migrate before then.

### Step 3: API v1 to v2 Migration Map

#### Base URL Change

```
v1: https://api.webflow.com
v2: https://api.webflow.com/v2
```

#### Authentication Change

```typescript
// v1 (old) — API key
import Webflow from "webflow-api";
const webflow = new Webflow({ token: "your-api-key" });

// v2 (current) — Access token
import { WebflowClient } from "webflow-api";
const webflow = new WebflowClient({ accessToken: "your-access-token" });
```

#### Endpoint Migration Map

| Operation | v1 Endpoint | v2 Endpoint |
|-----------|-------------|-------------|
| List sites | `GET /sites` | `GET /v2/sites` |
| Get site | `GET /sites/{site_id}` | `GET /v2/sites/{site_id}` |
| Publish site | `POST /sites/{site_id}/publish` | `POST /v2/sites/{site_id}/publish` |
| List collections | `GET /sites/{site_id}/collections` | `GET /v2/sites/{site_id}/collections` |
| List items | `GET /collections/{id}/items` | `GET /v2/collections/{id}/items` |
| Create item | `POST /collections/{id}/items` | `POST /v2/collections/{id}/items` |
| Update item | `PUT /collections/{id}/items/{item_id}` | `PATCH /v2/collections/{id}/items/{item_id}` |
| List products | `GET /sites/{site_id}/products` | `GET /v2/sites/{site_id}/products` |
| List orders | `GET /sites/{site_id}/orders` | `GET /v2/sites/{site_id}/orders` |

**Key v2 differences:**
- Update uses `PATCH` (not `PUT`) — partial updates only
- Items created as drafts by default (`isDraft: true`)
- Bulk endpoints added (create/update/delete up to 100 items)
- Live (published) items have separate endpoints (`/items/live`)
- Scopes required (e.g., `cms:read`, `cms:write`)

### Step 4: SDK Method Migration

```typescript
// ===== v1 SDK (old) =====
const webflow = new Webflow({ token: "xxx" });

// List sites
const sites = await webflow.sites();

// List collections
const collections = await webflow.collections({ siteId: "site-123" });

// Get items
const items = await webflow.items({ collectionId: "col-456" });

// Create item
const item = await webflow.createItem({
  collectionId: "col-456",
  fields: { name: "Test", slug: "test", _archived: false, _draft: false },
});

// Update item (full replace)
await webflow.updateItem({
  collectionId: "col-456",
  itemId: "item-789",
  fields: { name: "Updated", slug: "test" },
});
```

```typescript
// ===== v2 SDK (current) =====
const webflow = new WebflowClient({ accessToken: "xxx" });

// List sites
const { sites } = await webflow.sites.list();

// List collections
const { collections } = await webflow.collections.list("site-123");

// Get items (staged)
const { items } = await webflow.collections.items.listItems("col-456");

// Get items (live/published)
const { items: live } = await webflow.collections.items.listItemsLive("col-456");

// Create item (draft by default)
const item = await webflow.collections.items.createItem("col-456", {
  fieldData: { name: "Test", slug: "test" },
  isDraft: false,
});

// Update item (partial update via PATCH)
await webflow.collections.items.updateItem("col-456", "item-789", {
  fieldData: { name: "Updated" }, // Only changed fields
});

// NEW: Bulk create (up to 100)
await webflow.collections.items.createItemsBulk("col-456", {
  items: [{ fieldData: { name: "Item 1", slug: "item-1" } }],
});

// NEW: Publish items
await webflow.collections.items.publishItem("col-456", {
  itemIds: ["item-789"],
});
```

### Step 5: Execute Upgrade

```bash
# Create upgrade branch
git checkout -b upgrade/webflow-api-v3

# Install latest
npm install webflow-api@latest

# Run tests to find breaking changes
npm test 2>&1 | tee upgrade-test-results.txt

# Fix breaking changes (common patterns above)
# ...

# Verify in staging
npm run test:integration

# Commit and PR
git add -A
git commit -m "upgrade: webflow-api to v3 (Data API v2)"
```

### Step 6: Rollback if Needed

```bash
# Rollback to previous version
npm install webflow-api@2.x.x --save-exact

# Or revert the upgrade branch
git revert HEAD
```

## Breaking Change Checklist

- [ ] Import changed: `Webflow` class to `WebflowClient` named export
- [ ] Auth changed: `token` to `accessToken`
- [ ] Method calls changed: `webflow.sites()` to `webflow.sites.list()`
- [ ] Field data wrapped in `fieldData` object
- [ ] Update method changed from `PUT` to `PATCH` (partial)
- [ ] Item status: `_draft`/`_archived` to `isDraft`/`isArchived`
- [ ] Response shape: items now under `.items` property with `.pagination`
- [ ] Scopes required for all operations

## Output

- Updated SDK to latest version
- All v1 endpoints migrated to v2
- Breaking changes fixed
- Tests passing on staging
- Rollback procedure documented

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `TypeError: Webflow is not a constructor` | Using v1 import with v3 SDK | Change to `import { WebflowClient }` |
| `400 Bad Request` on create | Fields not in `fieldData` wrapper | Wrap fields: `{ fieldData: { ... } }` |
| `405 Method Not Allowed` | Using `PUT` instead of `PATCH` | Update to `PATCH` for item updates |
| Missing items in response | Not checking `.items` property | Destructure: `const { items } = await ...` |

## Resources

- [Migration Guide](https://developers.webflow.com/data/docs/migrating-to-v2)
- [SDK Releases](https://github.com/webflow/js-webflow-api/releases)
- [v2 API Reference](https://developers.webflow.com/data/reference/rest-introduction)
- [v1 Deprecation Timeline](https://developers.webflow.com/data/changelog/webflow-api-changed-endpoints)

## Next Steps

For CI integration during upgrades, see `webflow-ci-integration`.
