---
name: groq-ci-integration
description: 'Configure Groq CI/CD integration with GitHub Actions, testing, and model
  validation.

  Use when setting up automated testing, configuring CI pipelines,

  or integrating Groq tests into your build process.

  Trigger with phrases like "groq CI", "groq GitHub Actions",

  "groq automated tests", "CI groq".

  '
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- testing
- ci-cd
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq CI Integration

## Overview

Set up CI/CD pipelines for Groq integrations with unit tests (mocked), integration tests (live API), and model deprecation checks. Groq's fast inference makes live integration tests practical in CI -- a completion round-trip takes < 500ms.

## Prerequisites

- GitHub repository with Actions enabled
- Groq API key stored as GitHub secret
- vitest or jest for testing

## Instructions

The integration has four moving parts. Read this section for the high-level
flow, then drill into the reference files for the full copy-paste blocks — the
complete workflows and configuration live in
[references/implementation.md](references/implementation.md) and the full test
suite in [references/examples.md](references/examples.md).

### Step 1: GitHub Actions workflow

Write `.github/workflows/groq-tests.yml` with three jobs: `unit-tests` (mocked
`groq-sdk`, runs on every PR, no key), `integration-tests` (live API,
push-to-`main` only, guarded by `if: github.event_name != 'pull_request'`), and
a weekly `model-check` cron that diffs the model IDs the code references against
Groq's live model list. The job skeleton:

```yaml
# .github/workflows/groq-tests.yml — see references/implementation.md for full file
on:
  push: { branches: [main] }
  pull_request: { branches: [main] }
  schedule:
    - cron: "0 6 * * 1"  # Weekly model deprecation check
jobs:
  unit-tests:        # mocked groq-sdk, no API key
  integration-tests: # live API, push-to-main only
  model-check:       # curl /v1/models, flag deprecated IDs
```

### Step 2: Configure secrets

Store a CI-scoped key with `gh secret set GROQ_API_KEY --body
"gsk_your_ci_key_here"`. Keep it separate from the production key so it rotates
and tracks CI usage independently.

### Step 3: Integration test suite

Add `tests/groq.integration.ts` gated on a `GROQ_INTEGRATION` env var (so the
file is a no-op without a key). It asserts model listing, chat completion,
streaming, and JSON mode. Full file:
[references/examples.md](references/examples.md).

### Step 4: Release workflow

Gate `npm publish` behind a live production Groq round-trip so a broken key or
deprecated model blocks the release. Full `release.yml`:
[references/implementation.md](references/implementation.md).

**CI best practices:** mock `groq-sdk` in unit tests, run integration tests
only on `main` push (saves quota), prefer `llama-3.1-8b-instant` (cheapest,
fastest) with low `max_tokens` (5-50), add `timeout-minutes: 2`, and schedule
the weekly deprecation check.

## Output

Applying this skill produces the following files in the target repository:

| File | Purpose |
|------|---------|
| `.github/workflows/groq-tests.yml` | Unit + integration + weekly model-check jobs |
| `.github/workflows/release.yml` | Tag-triggered release gated on a live Groq check |
| `tests/groq.integration.ts` | `GROQ_INTEGRATION`-gated live API test suite |
| `GROQ_API_KEY` GitHub secret | CI-scoped key set via `gh secret set` |

At runtime the workflow reports three independent checks in the GitHub Actions
panel — `unit-tests` (green without any key), `integration-tests` (verbose
per-assertion output on push to `main`), and `model-check` (a code-vs-Groq
model diff that exits non-zero on any deprecated model ID).

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found | `GROQ_API_KEY` not configured | `gh secret set GROQ_API_KEY` |
| Integration test timeout | Network issue or rate limit | Increase timeout, add retry |
| Model check fails | Model deprecated | Update model ID in source code |
| Flaky tests | Rate limiting in CI | Add backoff, run integration tests less often |

## Examples

**Set the CI secret and scaffold the workflow.** Store a dedicated CI key, then
drop in the workflow from the reference file:

```bash
gh secret set GROQ_API_KEY --body "gsk_your_ci_key_here"
# copy .github/workflows/groq-tests.yml from references/implementation.md
```

**Run the integration suite locally before pushing.** The suite is inert
without the flag, so opt in explicitly:

```bash
GROQ_INTEGRATION=1 npx vitest tests/groq.integration.ts --reporter=verbose
```

Full walkthroughs: [references/implementation.md](references/implementation.md)
(workflows, secrets, release gate) and
[references/examples.md](references/examples.md) (complete integration test
suite + how to read the CI output).

## Resources

- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [Groq API Reference](https://console.groq.com/docs/api-reference)
- [Groq Model Deprecations](https://console.groq.com/docs/deprecations)

## Next Steps

For deployment patterns — provisioning production keys, environment promotion,
and rollback on a failed Groq health check — see the `groq-deploy-integration`
skill, which picks up where this CI gate leaves off.
