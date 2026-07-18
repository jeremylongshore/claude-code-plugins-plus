---
name: groq-upgrade-migration
description: 'Upgrade groq-sdk versions and handle Groq model deprecations.

  Use when upgrading SDK versions, detecting deprecated models,

  or migrating to new Groq model IDs.

  Trigger with phrases like "upgrade groq", "groq migration",

  "groq breaking changes", "update groq SDK", "groq deprecated model".

  '
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(git:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- api
- migration
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Upgrade & Migration

## Current State

!`npm list groq-sdk 2>/dev/null | grep groq-sdk || echo 'groq-sdk not installed'`
!`pip show groq 2>/dev/null | grep -E "Name|Version" || echo 'groq not installed (python)'`

## Overview

Guide for upgrading the `groq-sdk` package and migrating away from deprecated
model IDs. It walks a safe upgrade path — branch, bump, scan for deprecated
model references, rewrite them, and verify against the live models endpoint
before merging.

## Prerequisites

- A Node project that depends on `groq-sdk` (or the Python `groq` package).
- `npm`, `git`, `curl`, and `jq` available on `PATH`.
- **Authentication:** `GROQ_API_KEY` exported in your shell (or CI secret
  store). The SDK constructor `new Groq()` reads it automatically; the live
  model check passes it as `Authorization: Bearer $GROQ_API_KEY`. Get a key at
  <https://console.groq.com/keys>. See
  the Authentication section of
  [references/implementation.md](references/implementation.md).

## Model Deprecation Timeline

Groq announces deprecations with advance notice. These models have been deprecated:

| Deprecated Model | Deprecation Date | Replacement |
|-----------------|-----------------|-------------|
| `mixtral-8x7b-32768` | 2025-03-05 | `llama-3.3-70b-versatile` or `llama-3.1-8b-instant` |
| `gemma2-9b-it` | 2025-08-08 | `llama-3.1-8b-instant` |
| `llama-3.1-70b-versatile` | 2024-12-06 | `llama-3.3-70b-versatile` |
| `llama-3.1-70b-specdec` | 2024-12-06 | `llama-3.3-70b-specdec` |
| `playai-tts` | 2025-12-23 | Orpheus TTS models |
| `playai-tts-arabic` | 2025-12-23 | Orpheus TTS models |
| `distil-whisper-large-v3-en` | — | `whisper-large-v3-turbo` |

## Current Model IDs (Use These)

| Model ID | Type | Context | Speed |
|----------|------|---------|-------|
| `llama-3.1-8b-instant` | Text | 128K | ~560 tok/s |
| `llama-3.3-70b-versatile` | Text | 128K | ~280 tok/s |
| `llama-3.3-70b-specdec` | Text | 128K | Faster |
| `meta-llama/llama-4-scout-17b-16e-instruct` | Vision+Text | 128K | ~460 tok/s |
| `meta-llama/llama-4-maverick-17b-128e-instruct` | Vision+Text | 128K | — |
| `whisper-large-v3` | Audio STT | — | 164x RT |
| `whisper-large-v3-turbo` | Audio STT | — | 216x RT |

Always verify against the live endpoint: `GET https://api.groq.com/openai/v1/models`.

## Instructions

Work through these six steps. Each has a copy-paste command block in
[references/implementation.md](references/implementation.md); the summary here is
enough to drive the workflow, then drill in for the exact commands.

1. **Check current version and models** — read the installed `groq-sdk` version,
   compare to `npm view groq-sdk version`, and `grep` your `src/` for every
   model string reference.
2. **Upgrade the SDK** — `git checkout -b chore/upgrade-groq-sdk`, then
   `npm install groq-sdk@latest`.
3. **Find and replace deprecated models** — use `Read`/`Edit` to fold the
   `MODEL_MIGRATIONS` resolver map (below) into your Groq client module, or
   `Write` a new `groq-migrations.ts` helper, so deprecated IDs are rewritten
   at runtime.
4. **Run the migration scanner** — the `grep` sweep in the reference flags
   deprecated model IDs, old `@groq/sdk` imports, and removed method calls.
5. **Validate and test** — `npm test`, then confirm current IDs against the live
   `/v1/models` endpoint and run the SDK integration smoke test.
6. **Roll back if needed** — pin the previous version with
   `npm install groq-sdk@0.11.0 --save-exact` and re-run tests.

The essential resolver skeleton (full version in the reference):

```typescript
const MODEL_MIGRATIONS: Record<string, string> = {
  "mixtral-8x7b-32768": "llama-3.3-70b-versatile",
  "gemma2-9b-it": "llama-3.1-8b-instant",
  "distil-whisper-large-v3-en": "whisper-large-v3-turbo",
  // ...full map in references/implementation.md
};

function resolveModel(model: string): string {
  if (model in MODEL_MIGRATIONS) {
    console.warn(`Model ${model} is deprecated. Using ${MODEL_MIGRATIONS[model]} instead.`);
    return MODEL_MIGRATIONS[model];
  }
  return model;
}
```

## Output

Running this workflow produces:

- A `chore/upgrade-groq-sdk` branch with `groq-sdk` bumped in `package.json` and
  the lockfile.
- A scanner report listing any remaining deprecated model IDs, stale
  `@groq/sdk` imports, or removed method calls — empty under every heading means
  the code is clean.
- Updated call sites (or a `resolveModel` wrapper) pointing at current model IDs.
- A green `npm test` run plus a live `/v1/models` listing confirming every model
  your code uses is still served.

## Error Handling

| Issue | Symptom | Solution |
|-------|---------|----------|
| Deprecated model | `400 model_not_found` or `400 model_decommissioned` | Replace with current model ID |
| Type errors after upgrade | TypeScript compilation fails | Check SDK changelog for type changes |
| Auth format change | `401` after upgrade | Verify constructor uses `apiKey`, not `key`, and `GROQ_API_KEY` is set |
| New required fields | `400` on previously working requests | Check API docs for parameter changes |

## Examples

Worked before/after migrations — replacing a decommissioned chat model, routing
every call through `resolveModel`, migrating a transcription model, and reading a
clean scanner run — are in
[references/examples.md](references/examples.md). Quick example: a call still
using `mixtral-8x7b-32768` swaps to `llama-3.3-70b-versatile` per the migration
map, clearing the `400 model_decommissioned` error.

## Resources

- [Full walkthrough (all commands)](references/implementation.md)
- [Worked examples](references/examples.md)
- [Groq Model Deprecations](https://console.groq.com/docs/deprecations)
- [Groq Changelog](https://console.groq.com/docs/changelog)
- [groq-sdk GitHub Releases](https://github.com/groq/groq-typescript/releases)
- [Groq Current Models](https://console.groq.com/docs/models)

For CI integration during upgrades, see the `groq-ci-integration` skill.
