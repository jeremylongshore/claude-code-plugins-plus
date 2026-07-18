---
name: elevenlabs-upgrade-migration
description: |
  Upgrade ElevenLabs SDK versions and migrate between API model generations.
  Use when upgrading the elevenlabs-js or elevenlabs Python SDK, migrating from
  v1 to v2 models, or handling deprecations across the JS package rename and
  model ID changes.
  Trigger with: "upgrade elevenlabs", "elevenlabs migration",
  "elevenlabs breaking changes", "update elevenlabs SDK",
  "migrate elevenlabs model", "eleven_v3 migration".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Bash(git:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- migration
- upgrade
compatibility: Designed for Claude Code
---
# ElevenLabs Upgrade & Migration

## Overview

Guide for upgrading the ElevenLabs SDK and migrating between model generations.
Covers the JS SDK package rename (community `elevenlabs` → official
`@elevenlabs/elevenlabs-js`), model ID changes across generations, voice-settings
evolution, and API endpoint stability.

Work the seven steps below at a high level from this file; drill into
[references/migration-guide.md](references/migration-guide.md) for the full command
set and per-step code, and [references/examples.md](references/examples.md) for three
end-to-end worked scenarios.

## Authentication

All API calls authenticate with an account API key passed as the `xi-api-key`
header. Store it in the `ELEVENLABS_API_KEY` environment variable — never inline a
key in source. The SDK clients read the same value (`process.env.ELEVENLABS_API_KEY`
in Node, `api_key=...` in Python).

## Prerequisites

- Current ElevenLabs SDK installed (Node or Python)
- `ELEVENLABS_API_KEY` exported in the environment
- Git for version control
- Test suite available
- Staging environment for validation

## Instructions

The migration is a seven-step, branch-isolated workflow. Read package manifests and
config with **Read**, apply import/model changes with **Edit**, add new config files
(e.g. `config/models.ts`) with **Write**, and run the npm/pip/git commands via
**Bash**. Full commands and code for each step are in
[references/migration-guide.md](references/migration-guide.md).

1. **Check current versions** — inspect installed Node/Python SDK versions and list
   the models your account can reach.
2. **JS SDK package migration** — uninstall the legacy community `elevenlabs`
   package, install `@elevenlabs/elevenlabs-js`, and update imports on an
   `upgrade/elevenlabs-sdk` branch.
3. **Model migration** — map deprecated model IDs to current generations using the
   migration table, and add a `selectModel()` helper that falls back off
   `eleven_v3` when WebSocket streaming is required.
4. **Voice settings migration** — verify `stability`, `similarity_boost`, `style`,
   and `speed` against each model's capabilities.
5. **API endpoint changes** — confirm the stable `/v1/` endpoints and adopt the
   enhanced `/v2/voices` search where useful.
6. **Python SDK upgrade** — upgrade, pin the version in `requirements.txt`, and move
   from the old module-level `generate`/`set_api_key` API to the client object.
7. **Validation** — run tests plus a TTS smoke test and a voice-list check.

The essential skeleton for the highest-leverage step (the JS package swap):

```bash
npm uninstall elevenlabs
npm install @elevenlabs/elevenlabs-js
git checkout -b upgrade/elevenlabs-sdk
```

```typescript
import { ElevenLabsClient } from "@elevenlabs/elevenlabs-js";
const client = new ElevenLabsClient({
  apiKey: process.env.ELEVENLABS_API_KEY,
  maxRetries: 3,
  timeoutInSeconds: 60,
});
```

### Model migration map

| Old Model | New Model | Migration Notes |
|-----------|-----------|-----------------|
| `eleven_monolingual_v1` | `eleven_multilingual_v2` | 29 languages; same voice IDs work |
| `eleven_multilingual_v1` | `eleven_multilingual_v2` | Better emotional range; same API |
| `eleven_english_v1` | `eleven_turbo_v2_5` | Lower latency; same voice_settings |
| `eleven_turbo_v2` | `eleven_flash_v2_5` | Same quality, lower latency (~75ms) |
| `eleven_multilingual_v2` | `eleven_v3` | Most expressive; 70+ languages; NO WebSocket support |

Full model-selection code, voice-settings and endpoint tables, the Python client
migration, and the rollback procedure live in
[references/migration-guide.md](references/migration-guide.md).

## Output

Working through this skill produces:

- An `upgrade/elevenlabs-sdk` branch with the package swap and updated imports.
- Updated dependency manifests — `package.json` on `@elevenlabs/elevenlabs-js`, or a
  pinned `elevenlabs==` line in `requirements.txt`.
- A model-selection helper (`config/models.ts`) mapping quality/balanced/speed
  preferences to current model IDs with a WebSocket-safe fallback.
- Validation evidence: a green test run, a `200` from the TTS smoke test, and a
  non-empty voice-list count.
- A rollback path (pinned previous version or `git revert`) if validation fails.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `Cannot find module` | Old package name | Update import to `@elevenlabs/elevenlabs-js` |
| `model_not_found` | Deprecated model ID | Map to current model (see table) |
| WebSocket fails after model change | `eleven_v3` doesn't support WS | Use `eleven_flash_v2_5` or `eleven_multilingual_v2` |
| Voice settings ignored | Wrong parameter names | Verify `stability`, `similarity_boost`, `style`, `speed` |

## Examples

Three complete, copy-pasteable walkthroughs are in
[references/examples.md](references/examples.md):

1. **Migrate a Node.js app off the legacy `elevenlabs` community package** —
   branch, swap the package, update the client, and validate with a smoke test.
2. **Migrate a deprecated model with a WebSocket-safe fallback** — move toward
   `eleven_v3` while keeping streaming working via automatic downgrade.
3. **Upgrade the Python SDK from a pre-client generation** — move to the client
   object and pin the version for reproducible builds.

Minimal first example (the package swap and smoke test):

```bash
git checkout -b upgrade/elevenlabs-sdk
npm uninstall elevenlabs && npm install @elevenlabs/elevenlabs-js
npm test
curl -s -o /dev/null -w "%{http_code}" \
  -X POST "https://api.elevenlabs.io/v1/text-to-speech/21m00Tcm4TlvDq8ikWAM" \
  -H "xi-api-key: ${ELEVENLABS_API_KEY}" \
  -H "Content-Type: application/json" \
  -d '{"text":"Upgrade test.","model_id":"eleven_flash_v2_5"}'
```

## Resources

- [Full migration guide (references/migration-guide.md)](references/migration-guide.md)
- [Worked examples (references/examples.md)](references/examples.md)
- [ElevenLabs JS SDK Releases](https://github.com/elevenlabs/elevenlabs-js/releases)
- [ElevenLabs Python SDK Changelog](https://pypi.org/project/elevenlabs/#history)
- [ElevenLabs Models](https://elevenlabs.io/docs/overview/models)
- [ElevenLabs Changelog](https://elevenlabs.io/docs/changelog)

## Next Steps

For CI integration during upgrades, see the `elevenlabs-ci-integration` skill, which
wires the smoke test and voice-list check into a pipeline gate so a bad SDK or model
bump fails the build before it ships.
