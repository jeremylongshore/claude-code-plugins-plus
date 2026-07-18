---
name: groq-local-dev-loop
description: 'Configure Groq local development with hot reload, mocking, and testing.

  Use when setting up a Groq development environment, configuring mocked vs live
  test workflows, or establishing a fast iteration cycle with Groq.

  Trigger with phrases like "groq dev setup", "groq local development",

  "groq dev environment", "develop with groq".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- testing
- workflow
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Local Dev Loop

## Overview

Set up a fast, reproducible local development workflow for Groq. Groq's sub-second response times make it uniquely suited for tight dev loops -- you get LLM responses fast enough to iterate without context-switching. This skill scaffolds a project, a memoized client, model constants, and a two-tier test strategy (mocked unit tests + opt-in live integration tests). The lean skeleton lives here; the full code lives in [references/implementation.md](references/implementation.md) and [references/examples.md](references/examples.md).

## Prerequisites

- `groq-sdk` installed (`npm install groq-sdk`)
- `GROQ_API_KEY` set (free tier is fine for development)
- Node.js 18+ with tsx for TypeScript execution
- vitest for testing

## Authentication

The `groq-sdk` client reads `GROQ_API_KEY` from the environment automatically —
`new Groq()` and `getGroqClient()` both pick it up. Get a key at
[console.groq.com/keys](https://console.groq.com/keys), store it in a
git-ignored `.env.local`, and commit only `.env.example` as a template. Never
hardcode the key or commit `.env.local`.

## Instructions

Follow these seven steps in order. Steps 1-2 lay out the project; steps 3-4
centralize the client and model IDs; steps 5-6 establish the test tiers; step 7
templates the environment. Full code for each is in the reference files.

1. **Project structure** — create `src/groq/{client,models,completions}.ts`, `tests/`, and `.env.local` / `.env.example`.
2. **Package setup** — wire `dev` (tsx watch), `test` / `test:watch` (vitest), and `test:integration` scripts.
3. **Singleton client** — a lazily-memoized `getGroqClient()` that fails fast when `GROQ_API_KEY` is missing and a `resetClient()` for tests.
4. **Model constants** — a `MODELS` map with `DEV_MODEL` defaulting to `llama-3.1-8b-instant` to conserve dev quota.
5. **Unit tests with mocking** — `vi.mock("groq-sdk")` so unit tests run sub-second with zero API calls.
6. **Integration tests** — guard live-API tests behind `GROQ_INTEGRATION=1` with `describe.skipIf` so the default run stays offline.
7. **Environment template** — commit `.env.example`, git-ignore `.env.local`.

```typescript
// src/groq/client.ts -- lazily-memoized singleton
import Groq from "groq-sdk";

let _client: Groq | null = null;

export function getGroqClient(): Groq {
  if (!_client) {
    if (!process.env.GROQ_API_KEY) {
      throw new Error("GROQ_API_KEY not set. Copy .env.example to .env.local");
    }
    _client = new Groq({ apiKey: process.env.GROQ_API_KEY, maxRetries: 2, timeout: 30_000 });
  }
  return _client;
}
export function resetClient(): void { _client = null; }
```

See [references/implementation.md](references/implementation.md) for the full
project scaffold, package.json, model constants, and `.env.example`, and
[references/examples.md](references/examples.md) for the complete unit and
integration test files.

## Output

Applying the workflow produces:

- A scaffolded project with `src/groq/{client,models,completions}.ts` and a `tests/` directory.
- A **memoized `getGroqClient()`** that shares one configured client and throws an actionable error when `GROQ_API_KEY` is unset.
- A `MODELS` map + `DEV_MODEL` constant so dev runs on the cheap 8B model.
- A **two-tier test suite**: mocked unit tests (`npm run test:watch`, no API calls) and opt-in live tests (`npm run test:integration`, gated on `GROQ_INTEGRATION=1`).
- A `.env.example` template committed for the team, with real secrets in a git-ignored `.env.local`.

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `GROQ_API_KEY not set` | Missing .env.local | Copy from .env.example |
| Test timeout | Live API call in unit test | Mock groq-sdk in unit tests |
| `429 rate_limit_exceeded` | Free tier RPM hit | Wait 60s or use `test:watch` with longer intervals |
| Port already in use | Another tsx watch running | Kill process or change port |

## Dev Tips

- Use `llama-3.1-8b-instant` during development (lowest quota usage, fastest).
- Set `temperature: 0` for deterministic outputs during debugging.
- Set `max_tokens` conservatively to avoid burning through free tier.
- Groq free tier: 30 RPM for 70B and 8B models -- plan your dev loops accordingly.

## Examples

Run the hot-reload app and the mocked unit-test watcher side by side, then
exercise the live API only when you opt in:

```bash
npm run dev                # tsx watch src/index.ts (hot reload)
npm run test:watch         # vitest --watch (mocked, no API calls)
npm run test:integration   # GROQ_INTEGRATION=1 vitest (live API)
```

For the complete mocked unit test (`vi.mock("groq-sdk")`) and the
`GROQ_INTEGRATION`-gated live integration test, see
[references/examples.md](references/examples.md).

## Resources

- [references/implementation.md](references/implementation.md) — full project scaffold, client, model constants, and env template.
- [references/examples.md](references/examples.md) — complete unit and integration test files.
- [groq-sdk npm](https://www.npmjs.com/package/groq-sdk)
- [Vitest Documentation](https://vitest.dev/)
- [tsx Documentation](https://github.com/privatenumber/tsx)
- For production-ready code patterns, see the `groq-sdk-patterns` skill.
