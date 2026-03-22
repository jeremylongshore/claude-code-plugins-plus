---
name: customerio-local-dev-loop
description: |
  Configure Customer.io local development workflow.
  Use when setting up local testing, dev/staging isolation,
  or mocking Customer.io for unit tests.
  Trigger: "customer.io local dev", "test customer.io locally",
  "customer.io dev environment", "customer.io sandbox", "mock customer.io".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Glob, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
tags: [saas, customer-io, testing, development, workflow]

---
# Customer.io Local Dev Loop

## Overview

Set up an efficient local development workflow for Customer.io: environment isolation via separate workspaces, a dry-run client for safe development, test mocks for unit tests, and prefixed events that never pollute production data.

## Prerequisites

- `customerio-node` installed
- Separate Customer.io workspace for development (recommended — free workspaces available)
- `dotenv` or similar for environment variable loading

## Instructions

### Step 1: Environment Configuration

```bash
# .env.development
CUSTOMERIO_SITE_ID=dev-site-id
CUSTOMERIO_TRACK_API_KEY=dev-track-key
CUSTOMERIO_APP_API_KEY=dev-app-key
CUSTOMERIO_REGION=us
CUSTOMERIO_DRY_RUN=false
CUSTOMERIO_EVENT_PREFIX=dev_

# .env.test
CUSTOMERIO_SITE_ID=not-needed
CUSTOMERIO_TRACK_API_KEY=not-needed
CUSTOMERIO_APP_API_KEY=not-needed
CUSTOMERIO_DRY_RUN=true
CUSTOMERIO_EVENT_PREFIX=test_
```

### Step 2: Environment-Aware Client

```typescript
// lib/customerio-dev.ts
import { TrackClient, APIClient, RegionUS, RegionEU } from "customerio-node";

interface CioConfig {
  siteId: string;
  trackApiKey: string;
  appApiKey: string;
  region: typeof RegionUS | typeof RegionEU;
  dryRun: boolean;
  eventPrefix: string;
}

function loadConfig(): CioConfig {
  return {
    siteId: process.env.CUSTOMERIO_SITE_ID ?? "",
    trackApiKey: process.env.CUSTOMERIO_TRACK_API_KEY ?? "",
    appApiKey: process.env.CUSTOMERIO_APP_API_KEY ?? "",
    region: process.env.CUSTOMERIO_REGION === "eu" ? RegionEU : RegionUS,
    dryRun: process.env.CUSTOMERIO_DRY_RUN === "true",
    eventPrefix: process.env.CUSTOMERIO_EVENT_PREFIX ?? "",
  };
}

export class DevTrackClient {
  private client: TrackClient | null = null;
  private config: CioConfig;
  private log: typeof console.log;

  constructor() {
    this.config = loadConfig();
    this.log = console.log.bind(console);
    if (!this.config.dryRun) {
      this.client = new TrackClient(
        this.config.siteId,
        this.config.trackApiKey,
        { region: this.config.region }
      );
    }
  }

  async identify(userId: string, attributes: Record<string, any>) {
    const prefixedId = `${this.config.eventPrefix}${userId}`;
    if (this.config.dryRun) {
      this.log("[DRY RUN] identify:", prefixedId, attributes);
      return;
    }
    return this.client!.identify(prefixedId, attributes);
  }

  async track(userId: string, eventName: string, data?: Record<string, any>) {
    const prefixedId = `${this.config.eventPrefix}${userId}`;
    const prefixedEvent = `${this.config.eventPrefix}${eventName}`;
    if (this.config.dryRun) {
      this.log("[DRY RUN] track:", prefixedId, prefixedEvent, data);
      return;
    }
    return this.client!.track(prefixedId, {
      name: prefixedEvent,
      data,
    });
  }

  async suppress(userId: string) {
    const prefixedId = `${this.config.eventPrefix}${userId}`;
    if (this.config.dryRun) {
      this.log("[DRY RUN] suppress:", prefixedId);
      return;
    }
    return this.client!.suppress(prefixedId);
  }
}
```

### Step 3: Test Mocks for Unit Tests

```typescript
// __mocks__/customerio-node.ts (for vitest/jest auto-mocking)
import { vi } from "vitest";

export const TrackClient = vi.fn().mockImplementation(() => ({
  identify: vi.fn().mockResolvedValue(undefined),
  track: vi.fn().mockResolvedValue(undefined),
  trackAnonymous: vi.fn().mockResolvedValue(undefined),
  suppress: vi.fn().mockResolvedValue(undefined),
  destroy: vi.fn().mockResolvedValue(undefined),
  mergeCustomers: vi.fn().mockResolvedValue(undefined),
}));

export const APIClient = vi.fn().mockImplementation(() => ({
  sendEmail: vi.fn().mockResolvedValue({ delivery_id: "mock-delivery-123" }),
  sendPush: vi.fn().mockResolvedValue({ delivery_id: "mock-push-456" }),
  triggerBroadcast: vi.fn().mockResolvedValue(undefined),
}));

export const RegionUS = "us";
export const RegionEU = "eu";
export const SendEmailRequest = vi.fn().mockImplementation((data) => data);
export const SendPushRequest = vi.fn().mockImplementation((data) => data);
```

### Step 4: Integration Test with Real API

```typescript
// tests/customerio.integration.test.ts
import { describe, it, expect, afterAll } from "vitest";
import { TrackClient, RegionUS } from "customerio-node";

const TEST_PREFIX = `test_${Date.now()}_`;
const testUserIds: string[] = [];

const cio = new TrackClient(
  process.env.CUSTOMERIO_SITE_ID!,
  process.env.CUSTOMERIO_TRACK_API_KEY!,
  { region: RegionUS }
);

function testUserId(label: string): string {
  const id = `${TEST_PREFIX}${label}`;
  testUserIds.push(id);
  return id;
}

describe("Customer.io Integration", () => {
  afterAll(async () => {
    // Clean up all test users
    for (const id of testUserIds) {
      await cio.suppress(id).catch(() => {});
      await cio.destroy(id).catch(() => {});
    }
  });

  it("should identify a user", async () => {
    const id = testUserId("identify");
    await expect(
      cio.identify(id, { email: `${id}@test.example.com` })
    ).resolves.not.toThrow();
  });

  it("should track an event", async () => {
    const id = testUserId("track");
    await cio.identify(id, { email: `${id}@test.example.com` });
    await expect(
      cio.track(id, { name: "test_event", data: { step: 1 } })
    ).resolves.not.toThrow();
  });

  it("should reject invalid credentials", async () => {
    const badClient = new TrackClient("bad-id", "bad-key", {
      region: RegionUS,
    });
    await expect(
      badClient.identify("x", { email: "x@test.com" })
    ).rejects.toThrow();
  });
});
```

Run integration tests only against your dev workspace:

```bash
# Load dev env and run integration tests
npx dotenv -e .env.development -- npx vitest run tests/customerio.integration.test.ts
```

### Step 5: Dev Scripts

```json
// package.json scripts
{
  "scripts": {
    "cio:verify": "dotenv -e .env.development -- tsx scripts/verify-customerio.ts",
    "cio:test": "dotenv -e .env.development -- vitest run tests/customerio.integration.test.ts",
    "cio:test:dry": "CUSTOMERIO_DRY_RUN=true vitest run tests/customerio"
  }
}
```

## Workspace Isolation Strategy

| Environment | Workspace Name | Event Prefix | Dry Run |
|-------------|---------------|--------------|---------|
| Unit tests | (mocked) | `test_` | true |
| Integration tests | `myapp-dev` | `inttest_` | false |
| Staging | `myapp-staging` | (none) | false |
| Production | `myapp-prod` | (none) | false |

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Dev events in production | Wrong `.env` file loaded | Verify `NODE_ENV` and env file path |
| Mock not intercepting | Import order issue | Mock `customerio-node` before importing your client module |
| Test user pollution | No cleanup | Always suppress + destroy test users in `afterAll` |

## Resources

- [Customer.io Workspaces](https://docs.customer.io/accounts-and-workspaces/managing-credentials/)
- [customerio-node GitHub](https://github.com/customerio/customerio-node)

## Next Steps

After setting up local dev, proceed to `customerio-sdk-patterns` for production-ready patterns.
