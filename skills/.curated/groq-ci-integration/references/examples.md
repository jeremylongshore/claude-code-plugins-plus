# Groq CI Integration — Example Test Suite

The full integration test suite exercised by the CI workflow. It is gated
behind the `GROQ_INTEGRATION` environment variable so the same file is a no-op
in unit-test runs (no key, no network) and a live check when CI sets the flag.

## Step 3: Integration Test Suite

```typescript
// tests/groq.integration.ts
import { describe, it, expect } from "vitest";
import Groq from "groq-sdk";

const shouldRun = !!process.env.GROQ_INTEGRATION;

describe.skipIf(!shouldRun)("Groq API Integration", () => {
  const groq = new Groq();

  it("lists available models", async () => {
    const models = await groq.models.list();
    expect(models.data.length).toBeGreaterThan(0);

    const ids = models.data.map((m) => m.id);
    expect(ids).toContain("llama-3.1-8b-instant");
    expect(ids).toContain("llama-3.3-70b-versatile");
  }, 10_000);

  it("completes a chat request with 8B model", async () => {
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Reply with exactly one word: PONG" }],
      temperature: 0,
      max_tokens: 10,
    });

    expect(result.choices[0].message.content).toContain("PONG");
    expect(result.usage?.total_tokens).toBeGreaterThan(0);
  }, 10_000);

  it("streams a response", async () => {
    const stream = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [{ role: "user", content: "Count from 1 to 5." }],
      stream: true,
      max_tokens: 50,
    });

    let content = "";
    for await (const chunk of stream) {
      content += chunk.choices[0]?.delta?.content || "";
    }

    expect(content).toContain("1");
    expect(content).toContain("5");
  }, 10_000);

  it("returns JSON mode output", async () => {
    const result = await groq.chat.completions.create({
      model: "llama-3.1-8b-instant",
      messages: [
        { role: "system", content: "Respond with JSON: {\"status\": \"ok\"}" },
        { role: "user", content: "Health check" },
      ],
      response_format: { type: "json_object" },
      temperature: 0,
      max_tokens: 50,
    });

    const parsed = JSON.parse(result.choices[0].message.content!);
    expect(parsed).toHaveProperty("status");
  }, 10_000);
});
```

## Reading the CI output

Once the workflow runs, each job reports independently in the GitHub Actions
checks panel:

- **unit-tests** — always runs, on PRs and pushes; green means mocked logic
  passed and coverage was collected. No Groq key involved.
- **integration-tests** — runs on push to `main` only; the `--reporter=verbose`
  flag prints one line per live assertion (models list, chat, stream, JSON
  mode) so a failure names the exact capability that regressed.
- **model-check** — prints the `=== Models in our code ===` vs `=== Available
  on Groq ===` diff and exits non-zero listing any model ID your source
  references that Groq no longer serves.
