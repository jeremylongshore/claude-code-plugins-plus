---
name: elevenlabs-ci-integration
description: |
  Configure CI/CD pipelines for ElevenLabs with mocked unit tests and gated
  integration tests.
  Use when setting up GitHub Actions for TTS projects, configuring CI test
  strategies, or automating ElevenLabs integration validation without burning
  character quota on every PR.
  Trigger with "elevenlabs CI", "elevenlabs GitHub Actions",
  "elevenlabs automated tests", "CI elevenlabs", "elevenlabs pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- voice
- ai
- elevenlabs
- ci
- github-actions
compatibility: Designed for Claude Code
---
# ElevenLabs CI Integration

## Overview

Set up CI/CD pipelines that test ElevenLabs integrations without burning
character quota on every PR. Uses a two-tier strategy: **mocked unit tests** on
every push (no API key, zero quota), and **gated integration tests** that hit
the real API only on `main` or a manual dispatch, behind a quota guard.

The full workflow YAML and secret setup live in
[references/implementation.md](references/implementation.md); the complete test
code lives in [references/examples.md](references/examples.md). This file walks
the strategy end to end, then drills into either reference for copy-paste source.

## Prerequisites

- GitHub repository with Actions enabled
- ElevenLabs API key for integration tests (use a test/dev key, not production)
- npm/pnpm project with vitest configured

## Instructions

### Step 1: Add the two-tier workflow

Create `.github/workflows/elevenlabs-tests.yml` with two jobs. `unit-tests`
runs on every push/PR with a mock key. `integration-tests` runs only on `main`
or `workflow_dispatch`, `needs: unit-tests`, and checks remaining quota before
spending any:

```yaml
jobs:
  unit-tests:                       # every push/PR — mock key, 0 quota
    runs-on: ubuntu-latest
    steps: [checkout, setup-node, npm ci, npm test -- --coverage]
    # env: ELEVENLABS_API_KEY: "sk_test_mock_key_for_ci"

  integration-tests:                # main / manual only — real key
    if: github.ref == 'refs/heads/main' || github.event_name == 'workflow_dispatch'
    needs: unit-tests
    # 1) GET /v1/user → skip if remaining characters < 5000
    # 2) npm run test:integration behind that guard
```

Copy the complete, runnable workflow from
[references/implementation.md](references/implementation.md).

### Step 2: Store the API key as a repository secret

```bash
gh secret set ELEVENLABS_API_KEY --body "sk_your_test_key_here"
# optional, for webhook tests:
gh secret set ELEVENLABS_WEBHOOK_SECRET --body "whsec_your_secret_here"
```

### Step 3: Write mocked unit tests

Mock the entire SDK so unit tests never call the API or spend quota. Minimal
skeleton:

```typescript
vi.mock("@elevenlabs/elevenlabs-js", () => ({
  ElevenLabsClient: vi.fn().mockImplementation(() => ({
    textToSpeech: { convert: vi.fn().mockResolvedValue(/* mock MP3 stream */) },
    voices: { getAll: vi.fn().mockResolvedValue({ voices: [/* Rachel */] }) },
  })),
}));
```

Full mock (streaming, voices, user/subscription) and assertions:
[references/examples.md](references/examples.md).

### Step 4: Write gated integration tests

Skip integration tests unless `ELEVENLABS_INTEGRATION` is set, and keep them
cheap — Flash model, short text, low bitrate:

```typescript
const SKIP = !process.env.ELEVENLABS_INTEGRATION;
describe.skipIf(SKIP)("ElevenLabs Integration", () => { /* smoke tests */ });
```

Full smoke suite: [references/examples.md](references/examples.md).

### Step 5: Wire the package scripts

Add `test`, `test:integration`, and `test:ci` scripts so CI and local runs
share one entry point. See
[references/examples.md](references/examples.md).

## Output

Once configured, the pipeline produces:

- `.github/workflows/elevenlabs-tests.yml` — two-tier CI pipeline
- `ELEVENLABS_API_KEY` (and optional webhook secret) stored in GitHub secrets
- `tests/unit/` mocked tests that run on every push at **0 character cost**
- `tests/integration/` smoke tests gated to `main`/manual behind a quota guard
- npm scripts (`test`, `test:integration`, `test:ci`) shared by CI and local

### CI Strategy Summary

| Tier | When | API Key | Quota Cost | Coverage |
|------|------|---------|------------|----------|
| Unit tests | Every push/PR | Mock key | 0 characters | SDK integration patterns |
| Integration | Main + manual | Real test key | ~50 chars | End-to-end TTS verification |
| Quota check | Before integration | Real test key | 0 (GET only) | Prevents surprise billing |

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in CI | Missing repository secret | `gh secret set ELEVENLABS_API_KEY` |
| Integration tests timeout | Slow TTS generation | Increase test timeout to 30s; use Flash model |
| Quota depleted in CI | Too many integration runs | Use quota guard; limit to main branch only |
| Mock drift | SDK API changed | Update mocks when upgrading SDK |

## Examples

**Run only the cheap tier locally** (no API key, no quota):

```bash
npm test -- --coverage
```

**Trigger the gated integration tier by hand** (from the Actions tab or CLI):

```bash
gh workflow run elevenlabs-tests.yml
```

**Run integration tests locally against a real test key:**

```bash
ELEVENLABS_INTEGRATION=1 npm run test:integration
```

Full worked examples — complete SDK mock, gated smoke suite, and package
scripts — are in [references/examples.md](references/examples.md).

## Resources

- [references/implementation.md](references/implementation.md) — complete workflow YAML + secret setup
- [references/examples.md](references/examples.md) — complete unit, integration, and package-script code
- [GitHub Actions Secrets](https://docs.github.com/en/actions/security-guides/using-secrets-in-github-actions)
- [ElevenLabs JS SDK](https://github.com/elevenlabs/elevenlabs-js)

## Next Steps

For deployment patterns, see the `elevenlabs-deploy-integration` skill, which
covers promoting validated TTS builds through staging and production.
