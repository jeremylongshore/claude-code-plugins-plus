---
name: customerio-upgrade-migration
description: |
  Plan and execute Customer.io SDK upgrades and migrations.
  Use when upgrading customerio-node versions, migrating from
  legacy APIs, or updating to new SDK patterns.
  Trigger: "upgrade customer.io", "customer.io migration",
  "update customer.io sdk", "customer.io breaking changes".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, migration, upgrade]

---
# Customer.io Upgrade & Migration

## Current State
!`npm list customerio-node 2>/dev/null | grep customerio || echo 'customerio-node: not installed'`
!`npm view customerio-node version 2>/dev/null || echo 'Cannot check latest version'`

## Overview

Plan and execute `customerio-node` SDK upgrades safely: assess current version, review breaking changes, apply code migrations, and validate with staged rollout.

## Prerequisites

- Current SDK version identified (`npm list customerio-node`)
- Test environment available
- Version control for rollback

## Major Version Migration Reference

### Legacy `CustomerIO` to Modern `TrackClient` + `APIClient`

Older versions of `customerio-node` used a single `CustomerIO` class. Modern versions split into `TrackClient` (tracking) and `APIClient` (transactional/broadcasts).

```typescript
// BEFORE — Legacy pattern (customerio-node < 2.x)
const CustomerIO = require("customerio-node");
const cio = new CustomerIO(siteId, apiKey);
cio.identify("user-1", { email: "user@example.com" });
cio.track("user-1", { name: "event_name" });

// AFTER — Modern pattern (customerio-node >= 2.x)
import { TrackClient, APIClient, RegionUS } from "customerio-node";

const cio = new TrackClient(siteId, apiKey, { region: RegionUS });
await cio.identify("user-1", { email: "user@example.com" });
await cio.track("user-1", { name: "event_name", data: {} });

const api = new APIClient(appApiKey, { region: RegionUS });
await api.sendEmail(request);
```

**Key changes:**
- `TrackClient` replaces `CustomerIO` for identify/track
- `APIClient` is new — handles transactional + broadcasts
- Region is now explicit (`RegionUS` or `RegionEU`)
- Methods return Promises (must `await`)
- Event tracking uses `{ name, data }` object instead of positional args

## Instructions

### Step 1: Assess Current Version

```typescript
// scripts/cio-version-check.ts
import { readFileSync, existsSync } from "fs";

function assessVersion() {
  // Check installed version
  const lockPath = "package-lock.json";
  if (existsSync(lockPath)) {
    const lock = JSON.parse(readFileSync(lockPath, "utf-8"));
    const installed =
      lock.packages?.["node_modules/customerio-node"]?.version ??
      lock.dependencies?.["customerio-node"]?.version ??
      "not found in lockfile";
    console.log(`Installed: customerio-node@${installed}`);
  }

  // Check package.json declared version
  const pkg = JSON.parse(readFileSync("package.json", "utf-8"));
  const declared = pkg.dependencies?.["customerio-node"] ?? "not declared";
  console.log(`Declared: ${declared}`);

  // Search for usage patterns
  console.log("\nUsage pattern check:");
  console.log("- Look for 'new CustomerIO(' → legacy pattern, needs migration");
  console.log("- Look for 'new TrackClient(' → modern pattern");
  console.log("- Look for 'RegionUS/RegionEU' → region-aware (good)");
}

assessVersion();
```

### Step 2: Review Breaking Changes

```typescript
// Common breaking changes between major versions:

// v1.x → v2.x:
// - CustomerIO class → TrackClient + APIClient
// - Callbacks → Promises (async/await)
// - Region parameter added (defaults to US)
// - SendEmailRequest constructor changed

// v2.x → v3.x:
// - Import path may change
// - TypeScript types improved
// - Error object structure may change

// Always check the official changelog:
// https://github.com/customerio/customerio-node/blob/main/CHANGELOG.md
```

### Step 3: Create Migration Wrapper

```typescript
// lib/customerio-migration.ts
// Adapter that supports both old and new patterns during migration

import { TrackClient, APIClient, RegionUS } from "customerio-node";

export class CioMigrationClient {
  private trackClient: TrackClient;
  private apiClient: APIClient | null;

  constructor(config: {
    siteId: string;
    trackApiKey: string;
    appApiKey?: string;
    region?: "us" | "eu";
  }) {
    const region = config.region === "eu"
      ? (await import("customerio-node")).RegionEU
      : RegionUS;

    this.trackClient = new TrackClient(config.siteId, config.trackApiKey, {
      region,
    });

    this.apiClient = config.appApiKey
      ? new APIClient(config.appApiKey, { region })
      : null;
  }

  // Legacy-compatible identify (accepts both old and new signatures)
  async identify(userId: string, attrs: Record<string, any>): Promise<void> {
    // Ensure timestamps are in seconds, not milliseconds
    if (attrs.created_at && attrs.created_at > 1e12) {
      attrs.created_at = Math.floor(attrs.created_at / 1000);
    }
    await this.trackClient.identify(userId, attrs);
  }

  // Legacy-compatible track (normalizes data format)
  async track(
    userId: string,
    eventOrOpts: string | { name: string; data?: Record<string, any> },
    data?: Record<string, any>
  ): Promise<void> {
    if (typeof eventOrOpts === "string") {
      // Legacy: track("user", "event_name", { key: "value" })
      await this.trackClient.track(userId, {
        name: eventOrOpts,
        data: data ?? {},
      });
    } else {
      // Modern: track("user", { name: "event_name", data: {} })
      await this.trackClient.track(userId, eventOrOpts);
    }
  }

  get app(): APIClient {
    if (!this.apiClient) {
      throw new Error("App API key not configured");
    }
    return this.apiClient;
  }
}
```

### Step 4: Update and Test

```bash
# Update to latest version
npm install customerio-node@latest

# Run your test suite
npm test

# Run integration tests against dev workspace
npx dotenv -e .env.development -- npx vitest run tests/customerio
```

### Step 5: Migration Test Suite

```typescript
// tests/cio-migration.test.ts
import { describe, it, expect } from "vitest";
import { TrackClient, APIClient, RegionUS } from "customerio-node";

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

describe("Post-migration validation", () => {
  const testId = `migration-test-${Date.now()}`;

  it("identify works with new client", async () => {
    await expect(
      cio.identify(testId, {
        email: `${testId}@test.example.com`,
        created_at: Math.floor(Date.now() / 1000),
      })
    ).resolves.not.toThrow();
  });

  it("track works with object format", async () => {
    await expect(
      cio.track(testId, { name: "migration_test", data: { version: "new" } })
    ).resolves.not.toThrow();
  });

  it("suppress and destroy work", async () => {
    await cio.suppress(testId);
    await expect(cio.destroy(testId)).resolves.not.toThrow();
  });
});
```

### Step 6: Staged Rollout with Feature Flag

```typescript
// Use feature flag to gradually migrate traffic
import { createHash } from "crypto";

function useNewSdk(userId: string, rolloutPercent: number): boolean {
  const hash = createHash("md5").update(`cio-migration-${userId}`).digest("hex");
  return parseInt(hash.substring(0, 8), 16) % 100 < rolloutPercent;
}

// In your application code:
if (useNewSdk(userId, 10)) {
  // New SDK path
  await newClient.identify(userId, attrs);
} else {
  // Legacy SDK path (until migration complete)
  await legacyClient.identify(userId, attrs);
}
```

## Migration Checklist

- [ ] Current version documented
- [ ] Target version identified
- [ ] Breaking changes reviewed (CHANGELOG.md)
- [ ] Code changes implemented (TrackClient, region, async/await)
- [ ] Unit tests passing
- [ ] Integration tests passing against dev workspace
- [ ] Staging deployment successful
- [ ] Feature flag for staged rollout ready
- [ ] Rollback plan documented (pin old version in package.json)
- [ ] Team notified of migration timeline

## Error Handling

| Issue | Solution |
|-------|----------|
| `TrackClient is not a constructor` | Old import style — use `import { TrackClient } from "customerio-node"` |
| `region is not defined` | Import `RegionUS` or `RegionEU` from `customerio-node` |
| Methods not returning Promises | Upgrade to latest — old versions used callbacks |
| `TypeError: cio.track is not a function` | Using `APIClient` instead of `TrackClient` for tracking |

## Resources

- [customerio-node CHANGELOG](https://github.com/customerio/customerio-node/blob/main/CHANGELOG.md)
- [customerio-node Releases](https://github.com/customerio/customerio-node/releases)
- [npm customerio-node](https://www.npmjs.com/package/customerio-node)

## Next Steps

After successful migration, proceed to `customerio-ci-integration` for CI/CD setup.
