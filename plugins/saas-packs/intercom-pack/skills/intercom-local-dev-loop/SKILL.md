---
name: intercom-local-dev-loop
description: |
  Configure Intercom local development with testing, mocking, and hot reload.
  Use when setting up a development environment, writing tests against the
  Intercom API, or establishing a fast iteration cycle.
  Trigger with phrases like "intercom dev setup", "intercom local development",
  "intercom dev environment", "develop with intercom", "test intercom locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(npx:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, support, messaging, intercom]
compatible-with: claude-code
---

# Intercom Local Dev Loop

## Overview

Set up a fast local development workflow for Intercom integrations with proper test isolation, mocking strategies, and webhook tunneling.

## Prerequisites

- Completed `intercom-install-auth` setup
- Node.js 18+ with npm/pnpm
- A test/development Intercom workspace (separate from production)

## Instructions

### Step 1: Project Structure

```
my-intercom-app/
├── src/
│   ├── intercom/
│   │   ├── client.ts       # Singleton client
│   │   ├── contacts.ts     # Contact operations
│   │   ├── conversations.ts # Conversation operations
│   │   └── types.ts        # Intercom type extensions
│   └── index.ts
├── tests/
│   ├── mocks/
│   │   └── intercom.ts     # Mock client factory
│   ├── contacts.test.ts
│   └── conversations.test.ts
├── .env.development        # Dev workspace token
├── .env.test               # Test config (mocked)
├── .env.example            # Template
└── package.json
```

### Step 2: Environment Configuration

```bash
# .env.example (commit this)
INTERCOM_ACCESS_TOKEN=
INTERCOM_WEBHOOK_SECRET=
NODE_ENV=development

# .env.development (git-ignored, real dev workspace token)
INTERCOM_ACCESS_TOKEN=dG9rOmRldl90b2tlbl9oZXJl
INTERCOM_WEBHOOK_SECRET=your-webhook-secret
NODE_ENV=development
```

### Step 3: Client Singleton with Environment Awareness

```typescript
// src/intercom/client.ts
import { IntercomClient } from "intercom-client";

let instance: IntercomClient | null = null;

export function getClient(): IntercomClient {
  if (!instance) {
    const token = process.env.INTERCOM_ACCESS_TOKEN;
    if (!token) {
      throw new Error(
        "INTERCOM_ACCESS_TOKEN not set. Copy .env.example to .env.development"
      );
    }
    instance = new IntercomClient({ token });
  }
  return instance;
}

// Reset for testing
export function resetClient(): void {
  instance = null;
}
```

### Step 4: Mock Client for Tests

```typescript
// tests/mocks/intercom.ts
import { vi } from "vitest";

export function createMockClient() {
  return {
    contacts: {
      create: vi.fn().mockResolvedValue({
        type: "contact",
        id: "mock-contact-id",
        role: "user",
        email: "test@example.com",
        name: "Test User",
        external_id: "ext-123",
        custom_attributes: {},
        created_at: 1711100000,
        updated_at: 1711100000,
      }),
      find: vi.fn().mockResolvedValue({
        type: "contact",
        id: "mock-contact-id",
        email: "test@example.com",
      }),
      search: vi.fn().mockResolvedValue({
        type: "list",
        data: [],
        total_count: 0,
        pages: { type: "pages", page: 1, per_page: 50, total_pages: 0 },
      }),
      list: vi.fn().mockResolvedValue({
        type: "list",
        data: [],
        total_count: 0,
        pages: { next: null },
      }),
      update: vi.fn(),
      delete: vi.fn(),
      tag: vi.fn(),
      untag: vi.fn(),
    },
    conversations: {
      create: vi.fn().mockResolvedValue({
        type: "conversation",
        id: "mock-convo-id",
        state: "open",
      }),
      find: vi.fn(),
      list: vi.fn().mockResolvedValue({
        type: "conversation.list",
        conversations: [],
        pages: { next: null },
      }),
      reply: vi.fn(),
      close: vi.fn(),
      assign: vi.fn(),
    },
    messages: {
      create: vi.fn().mockResolvedValue({
        type: "user_message",
        id: "mock-msg-id",
      }),
    },
    admins: {
      list: vi.fn().mockResolvedValue({
        type: "admin.list",
        admins: [{ id: "admin-1", name: "Test Admin", email: "admin@test.com" }],
      }),
    },
    tags: {
      create: vi.fn().mockResolvedValue({ type: "tag", id: "tag-1", name: "test" }),
      list: vi.fn().mockResolvedValue({ type: "list", data: [] }),
    },
  };
}
```

### Step 5: Write Tests

```typescript
// tests/contacts.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import { createMockClient } from "./mocks/intercom";

describe("Contact Operations", () => {
  let mockClient: ReturnType<typeof createMockClient>;

  beforeEach(() => {
    mockClient = createMockClient();
  });

  it("should create a user contact", async () => {
    const contact = await mockClient.contacts.create({
      role: "user",
      externalId: "user-123",
      email: "test@example.com",
    });

    expect(contact.id).toBe("mock-contact-id");
    expect(contact.role).toBe("user");
    expect(mockClient.contacts.create).toHaveBeenCalledWith({
      role: "user",
      externalId: "user-123",
      email: "test@example.com",
    });
  });

  it("should search contacts by email", async () => {
    await mockClient.contacts.search({
      query: { field: "email", operator: "=", value: "test@example.com" },
    });

    expect(mockClient.contacts.search).toHaveBeenCalledOnce();
  });
});
```

### Step 6: Webhook Testing with ngrok

```bash
# Install ngrok
npm install -g ngrok

# Start your local server
npm run dev  # Starts on port 3000

# Tunnel to expose locally
ngrok http 3000

# Use the HTTPS URL (e.g., https://abc123.ngrok.io) as your webhook URL
# in Intercom Developer Hub > Webhooks
```

### Step 7: Package Scripts

```json
{
  "scripts": {
    "dev": "tsx watch src/index.ts",
    "test": "vitest",
    "test:watch": "vitest --watch",
    "test:integration": "INTERCOM_ACCESS_TOKEN=$INTERCOM_DEV_TOKEN vitest --config vitest.integration.config.ts",
    "typecheck": "tsc --noEmit"
  }
}
```

## Integration Test Pattern

```typescript
// tests/integration/contacts.integration.test.ts
import { describe, it, expect } from "vitest";
import { IntercomClient } from "intercom-client";

const client = new IntercomClient({
  token: process.env.INTERCOM_ACCESS_TOKEN!,
});

describe.skipIf(!process.env.INTERCOM_ACCESS_TOKEN)("Contacts Integration", () => {
  it("should create and retrieve a contact", async () => {
    const created = await client.contacts.create({
      role: "lead",
      name: `Integration Test ${Date.now()}`,
    });

    expect(created.id).toBeDefined();

    // Clean up
    await client.contacts.delete({ contactId: created.id });
  });
});
```

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `INTERCOM_ACCESS_TOKEN not set` | Missing .env file | Copy `.env.example` to `.env.development` |
| Port 3000 in use | Another process | `lsof -i :3000` and kill, or change port |
| ngrok tunnel expired | Free tier 2h limit | Restart ngrok or use paid plan |
| Mock type mismatch | SDK updated | Regenerate mocks from SDK types |
| `rate_limit_exceeded` in dev | Dev workspace limits | Add delays between integration tests |

## Resources

- [intercom-client npm](https://www.npmjs.com/package/intercom-client)
- [Vitest Documentation](https://vitest.dev/)
- [ngrok](https://ngrok.com/)

## Next Steps

See `intercom-sdk-patterns` for production-ready code patterns.
