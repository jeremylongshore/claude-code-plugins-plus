---
name: intercom-ci-integration
description: |
  Configure CI/CD pipelines for Intercom integrations with GitHub Actions.
  Use when setting up automated testing, configuring CI with Intercom secrets,
  or integrating Intercom API tests into your build process.
  Trigger with phrases like "intercom CI", "intercom GitHub Actions",
  "intercom automated tests", "CI intercom", "intercom pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom CI Integration

## Overview

Set up CI/CD pipelines for Intercom integrations with GitHub Actions, including unit tests with mocked SDK, integration tests against a dev workspace, and secret management.

## Prerequisites

- GitHub repository with Actions enabled
- Intercom dev workspace access token (separate from production)
- npm/pnpm project with `intercom-client` installed

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/intercom-ci.yml
name: Intercom Integration CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run typecheck
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      INTERCOM_ACCESS_TOKEN: ${{ secrets.INTERCOM_DEV_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Verify Intercom connectivity
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
            https://api.intercom.io/me)
          if [ "$STATUS" != "200" ]; then
            echo "Intercom auth failed: $STATUS"
            exit 1
          fi
      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5
```

### Step 2: Configure Secrets

```bash
# Store dev workspace token (never production!)
gh secret set INTERCOM_DEV_TOKEN --body "dG9rOmRldl90b2tlbl9oZXJl"

# If using webhooks in CI, store the signing secret
gh secret set INTERCOM_WEBHOOK_SECRET --body "your-webhook-secret"

# Verify secrets are set
gh secret list
```

### Step 3: Unit Tests with Mocked SDK

```typescript
// tests/unit/intercom-service.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { IntercomError } from "intercom-client";

// Mock the entire module
vi.mock("intercom-client", () => ({
  IntercomClient: vi.fn().mockImplementation(() => mockClient),
  IntercomError: class extends Error {
    statusCode: number;
    constructor(message: string, statusCode: number) {
      super(message);
      this.statusCode = statusCode;
    }
  },
}));

const mockClient = {
  contacts: {
    create: vi.fn(),
    find: vi.fn(),
    search: vi.fn(),
    list: vi.fn(),
  },
  conversations: {
    create: vi.fn(),
    reply: vi.fn(),
    find: vi.fn(),
  },
  admins: {
    list: vi.fn().mockResolvedValue({
      admins: [{ id: "admin-1", name: "CI Admin" }],
    }),
  },
};

describe("Contact sync service", () => {
  beforeEach(() => vi.clearAllMocks());

  it("should create a contact with correct attributes", async () => {
    mockClient.contacts.create.mockResolvedValue({
      type: "contact",
      id: "test-id",
      role: "user",
      email: "test@example.com",
    });

    const result = await mockClient.contacts.create({
      role: "user",
      email: "test@example.com",
      externalId: "usr-1",
    });

    expect(result.id).toBe("test-id");
    expect(mockClient.contacts.create).toHaveBeenCalledWith({
      role: "user",
      email: "test@example.com",
      externalId: "usr-1",
    });
  });

  it("should handle 409 conflict on duplicate contact", async () => {
    mockClient.contacts.create.mockRejectedValue(
      new IntercomError("A contact matching those details already exists", 409)
    );

    await expect(
      mockClient.contacts.create({ role: "user", email: "dupe@example.com" })
    ).rejects.toThrow("already exists");
  });
});
```

### Step 4: Integration Tests (Against Dev Workspace)

```typescript
// tests/integration/contacts.integration.test.ts
import { describe, it, expect, afterAll } from "vitest";
import { IntercomClient } from "intercom-client";

const token = process.env.INTERCOM_ACCESS_TOKEN;
const client = token ? new IntercomClient({ token }) : null;

// Track created resources for cleanup
const createdContactIds: string[] = [];

afterAll(async () => {
  if (!client) return;
  for (const id of createdContactIds) {
    try { await client.contacts.delete({ contactId: id }); } catch {}
  }
});

describe.skipIf(!token)("Intercom API Integration", () => {
  it("should authenticate and list admins", async () => {
    const admins = await client!.admins.list();
    expect(admins.admins.length).toBeGreaterThan(0);
  });

  it("should create and retrieve a contact", async () => {
    const contact = await client!.contacts.create({
      role: "lead",
      name: `CI Test ${Date.now()}`,
    });

    createdContactIds.push(contact.id);
    expect(contact.role).toBe("lead");

    const found = await client!.contacts.find({ contactId: contact.id });
    expect(found.id).toBe(contact.id);
  });

  it("should search contacts", async () => {
    const results = await client!.contacts.search({
      query: { field: "role", operator: "=", value: "user" },
      pagination: { per_page: 5 },
    });

    expect(results.data).toBeDefined();
  });
});
```

### Step 5: Webhook Signature Test

```typescript
import { describe, it, expect } from "vitest";
import crypto from "crypto";

function verifySignature(payload: string, signature: string, secret: string): boolean {
  const expected = "sha1=" + crypto
    .createHmac("sha1", secret)
    .update(payload)
    .digest("hex");
  return crypto.timingSafeEqual(Buffer.from(signature), Buffer.from(expected));
}

describe("Webhook signature verification", () => {
  const secret = "test-webhook-secret";
  const payload = '{"type":"notification_event","topic":"conversation.user.created"}';

  it("should verify valid signature", () => {
    const signature = "sha1=" + crypto.createHmac("sha1", secret).update(payload).digest("hex");
    expect(verifySignature(payload, signature, secret)).toBe(true);
  });

  it("should reject invalid signature", () => {
    expect(verifySignature(payload, "sha1=invalid", secret)).toBe(false);
  });
});
```

## Error Handling

| CI Issue | Cause | Solution |
|----------|-------|----------|
| `INTERCOM_DEV_TOKEN` not found | Secret not configured | `gh secret set INTERCOM_DEV_TOKEN` |
| Integration tests timeout | Rate limited or slow API | Increase timeout, add delays |
| 401 in CI | Token expired or rotated | Update secret with new token |
| Flaky tests | Shared dev workspace state | Use unique names, clean up after |

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest](https://vitest.dev/)

## Next Steps

For deployment patterns, see `intercom-deploy-integration`.
