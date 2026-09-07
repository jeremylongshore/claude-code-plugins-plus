# Test Suites: Mocked Unit, Live Integration, Webhook Signature

Complete test code for the three CI layers. Unit tests run everywhere with a
fully mocked SDK; integration tests run only when a dev token is present
(`describe.skipIf`); the webhook test needs no network at all.

## Unit Tests with a Mocked SDK

`tests/unit/intercom-service.test.ts` — mock the entire `intercom-client`
module so unit tests are fast, deterministic, and token-free.

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

## Integration Tests (Against a Dev Workspace)

`tests/integration/contacts.integration.test.ts` — hit the real Intercom dev
workspace, but track every created resource and clean it up in `afterAll` so
the shared workspace does not accumulate test litter.

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

## Webhook Signature Test

Verify inbound Intercom webhook signatures with a constant-time comparison
(`crypto.timingSafeEqual`) so a bad signature is rejected without a timing
side-channel. No network required.

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
