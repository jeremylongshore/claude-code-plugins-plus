# Groq Local Dev Loop — Testing Examples

The two-tier test strategy: fast mocked unit tests that run on every save with
zero API calls, and opt-in integration tests that hit the live API only when
`GROQ_INTEGRATION=1` is set (CI or manual verification).

## Unit Tests with Mocking

Mock the entire `groq-sdk` module so unit tests never touch the network. This
keeps `vitest --watch` sub-second and free of quota usage.

```typescript
// tests/groq.test.ts
import { describe, it, expect, vi, beforeEach } from "vitest";
import Groq from "groq-sdk";

// Mock the entire groq-sdk module
vi.mock("groq-sdk", () => {
  const mockCreate = vi.fn().mockResolvedValue({
    choices: [{ message: { content: "mocked response" }, finish_reason: "stop" }],
    usage: { prompt_tokens: 10, completion_tokens: 5, total_tokens: 15 },
    model: "llama-3.1-8b-instant",
  });

  return {
    default: vi.fn(() => ({
      chat: { completions: { create: mockCreate } },
      models: { list: vi.fn().mockResolvedValue({ data: [] }) },
    })),
  };
});

describe("Groq Completions", () => {
  it("should create a chat completion", async () => {
    const groq = new Groq();
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "test" }],
    });

    expect(result.choices[0].message.content).toBe("mocked response");
    expect(result.usage.total_tokens).toBe(15);
  });
});
```

## Integration Tests (Live API)

Guard live tests behind `GROQ_INTEGRATION` so they only run when you explicitly
opt in. `describe.skipIf` skips the whole block otherwise, keeping the default
`vitest` run offline and deterministic.

```typescript
// tests/groq.integration.ts
import { describe, it, expect } from "vitest";
import Groq from "groq-sdk";

const shouldRun = !!process.env.GROQ_INTEGRATION;

describe.skipIf(!shouldRun)("Groq Integration", () => {
  const groq = new Groq();

  it("should list available models", async () => {
    const models = await groq.models.list();
    expect(models.data.length).toBeGreaterThan(0);
    const ids = models.data.map((m) => m.id);
    expect(ids).toContain("llama-3.1-8b-instant");
  }, 10_000);

  it("should complete a chat request", async () => {
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Reply with exactly: PONG" }],
      temperature: 0,
      max_tokens: 10,
    });
    expect(result.choices[0].message.content).toContain("PONG");
  }, 10_000);
});
```

## Running the Loop

```bash
# Terminal 1: hot-reload the app on every save
npm run dev            # tsx watch src/index.ts

# Terminal 2: re-run mocked unit tests on every save (no API calls)
npm run test:watch     # vitest --watch

# On demand / in CI: exercise the live API
npm run test:integration   # GROQ_INTEGRATION=1 vitest tests/groq.integration.ts
```
