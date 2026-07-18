# Intercom Local Dev Loop — Full Implementation Walkthrough

This is the complete, copy-paste-ready implementation referenced from `SKILL.md`.
Follow it top to bottom to stand up a fully isolated Intercom development loop.

## Step 1: Project Structure

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

## Step 2: Environment Configuration

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

## Step 3: Client Singleton with Environment Awareness

The singleton reads the access token from the environment. Authentication is a
single bearer token issued per workspace by `intercom-install-auth` — the client
never hardcodes it, so swapping the `.env.development` token is the only step
needed to point the loop at a different dev workspace.

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

## Step 4: Mock Client for Tests

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

## Step 5: Write Tests

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

## Step 6: Webhook Testing with ngrok

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

## Step 7: Package Scripts

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
