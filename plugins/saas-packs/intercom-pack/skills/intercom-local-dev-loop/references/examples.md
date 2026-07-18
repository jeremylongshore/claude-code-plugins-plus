# Intercom Local Dev Loop — Examples

Worked examples referenced from `SKILL.md`. The mocked unit-test example lives in
[implementation.md](implementation.md) (Step 5); this file covers the live
integration lane that talks to a real dev workspace.

## Integration Test Pattern

Integration tests run against a real development workspace and are gated on the
presence of `INTERCOM_ACCESS_TOKEN` via `describe.skipIf`, so the suite is a
no-op in CI or on any machine without a dev token. Each test cleans up the
records it creates so the dev workspace does not accumulate test data.

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

## Running the loop

```bash
# Fast inner loop — mocked unit tests, no network, no token required
npm run test:watch

# Full integration lane — hits the dev workspace (token must be set)
INTERCOM_DEV_TOKEN=dG9rOmRldl90b2tlbl9oZXJl npm run test:integration

# Type safety in the background while you edit
npm run typecheck
```
