---
name: elevenlabs-local-dev-loop
description: |
  Use when setting up a local ElevenLabs dev environment for a TTS/voice
  project and you need SDK mocking, hot reload, quota-aware iteration, and
  audio-output testing that does not burn character quota during development.
  Trigger with "elevenlabs dev setup", "elevenlabs local development",
  "elevenlabs dev environment", "develop with elevenlabs", "test elevenlabs
  locally".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pnpm:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- tts
- testing
compatibility: Designed for Claude Code
---
# ElevenLabs Local Dev Loop

## Overview

Set up a fast, cost-effective local development workflow for ElevenLabs audio
projects. The loop centers on three moves — mock the SDK so unit tests never
burn character quota, gate real API calls behind an explicit
`ELEVENLABS_INTEGRATION=1` flag, and select a cheaper model in dev while keeping
the high-quality model for production — with `tsx watch` hot reload and a quota
checker to round out the cycle.

Follow the high-level flow below to scaffold the project, then drill into
[references/implementation.md](references/implementation.md) for the full code
of every step and [references/examples.md](references/examples.md) for worked
end-to-end runs.

## Prerequisites

Before starting, confirm your environment is ready:

- The `elevenlabs-install-auth` setup is complete, so the SDK
  (`@elevenlabs/elevenlabs-js`) is installed and `ELEVENLABS_API_KEY` is
  available in `.env.local`.
- Node.js 18+ with `npm` or `pnpm`.
- `vitest` installed as the test runner (recommended) — it powers the mock
  layer and the integration-test guard.

## Instructions

Work through the six steps in order. Each is summarized here; the full code for
every step lives in [references/implementation.md](references/implementation.md).

1. **Project structure** — lay out `src/elevenlabs/` (client, config, tts),
   `tests/__mocks__/` and `tests/fixtures/sample.mp3`, a git-ignored `output/`,
   and `.env.local` / `.env.example`. Full tree in the reference.
2. **Environment configuration** — write an environment-aware `config.ts` that
   picks the model and output format by `NODE_ENV`. This is the essential
   skeleton:

   ```typescript
   // src/elevenlabs/config.ts
   export function loadConfig() {
     const env = process.env.NODE_ENV || "development";
     return {
       apiKey: process.env.ELEVENLABS_API_KEY || "",
       // cheaper/faster in dev, best quality in prod
       modelId: env === "production"
         ? "eleven_multilingual_v2"   // 1.0 credits/char
         : "eleven_flash_v2_5",       // 0.5 credits/char, ~75ms
       defaultVoiceId: process.env.ELEVENLABS_VOICE_ID || "21m00Tcm4TlvDq8ikWAM",
       outputFormat: "mp3_22050_32",  // smaller files for dev
     };
   }
   ```

3. **Mock the SDK** — write `tests/__mocks__/elevenlabs.ts` that returns the
   `sample.mp3` fixture from `textToSpeech.convert`/`stream` and stubs
   `voices.getAll` and `user.get`, so unit tests cost nothing.
4. **Development scripts** — add `dev` (`tsx watch`), `test`, `test:watch`,
   `test:integration`, `generate`, and `quota` scripts to `package.json`.
5. **Quota-aware development** — add `src/check-quota.ts` that reads
   `user.subscription` and exits non-zero when fewer than 1000 characters
   remain, so a low balance fails fast.
6. **Integration test guard** — write `tests/tts.test.ts` where the real-API
   test is `it.skipIf(!useRealApi)` and only runs under
   `ELEVENLABS_INTEGRATION=1`; the mocked test always runs.

See [references/implementation.md](references/implementation.md) for the
complete, copy-pasteable code for each step.

## Output

- Working development environment with hot reload via `tsx watch`
- Mock layer that avoids API calls and character charges during dev
- Quota checker to prevent surprise billing
- Integration test guard pattern (`ELEVENLABS_INTEGRATION=1`)
- Environment-aware model selection (cheap in dev, quality in prod)

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| `MODULE_NOT_FOUND` | SDK not installed | `npm install @elevenlabs/elevenlabs-js` |
| Mock returns undefined | Mock not wired | Check vi.mock path matches import |
| Integration test fails | No API key | Set `ELEVENLABS_API_KEY` in `.env.local` |
| Quota exceeded in dev | Running real API calls | Use mock layer; run `npm run quota` first |

## Examples

Four worked runs of the loop — full walkthroughs in
[references/examples.md](references/examples.md):

- **Zero-cost unit tests** — `npm run test` drives the service through the mock
  client, passes offline, and never touches the API or your quota.
- **Quota preflight** — `npm run quota` prints `Characters: 500 / 10,000 (5.0%
  used)` and exits `1` when fewer than 1000 characters remain, blocking a paid
  run before it starts.
- **Opt-in integration run** — `npm run test:integration` sets
  `ELEVENLABS_INTEGRATION=1`, flipping the `it.skipIf(!useRealApi)` test on so
  the real API is hit only when you ask for it.
- **Hot-reload iteration** — `npm run dev` (`tsx watch`) restarts on save; with
  the dev model (`eleven_flash_v2_5`) and mocks, each loop stays fast and free.

## Resources

- [ElevenLabs JS SDK](https://github.com/elevenlabs/elevenlabs-js)
- [Vitest Mocking](https://vitest.dev/guide/mocking.html)
- [tsx (TypeScript Execute)](https://github.com/privatenumber/tsx)

## Next Steps

Once the dev loop is running, move on to production-ready code: see the
`elevenlabs-sdk-patterns` skill for streaming, retries, and voice-management
patterns you can layer on top of this environment.
