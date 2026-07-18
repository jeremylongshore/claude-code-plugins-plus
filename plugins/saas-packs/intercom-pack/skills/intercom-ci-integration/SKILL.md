---
name: intercom-ci-integration
description: 'Configure CI/CD pipelines for Intercom integrations with GitHub Actions.

  Use when setting up automated testing, configuring CI with Intercom secrets,

  or integrating Intercom API tests into your build process.

  Trigger with phrases like "intercom CI", "intercom GitHub Actions",

  "intercom automated tests", "CI intercom", "intercom pipeline".

  '
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- support
- messaging
- intercom
compatibility: Designed for Claude Code
---
# Intercom CI Integration

## Overview

Set up CI/CD pipelines for Intercom integrations with GitHub Actions: unit
tests with a mocked SDK (fast, token-free, run on every PR), integration tests
against a dev workspace (gated to `main` pushes), webhook signature tests, and
encrypted secret management. This SKILL.md carries the workflow at a high level;
the full copy-ready workflow, secret setup, and complete test suites live in
`references/` for progressive disclosure.

## Prerequisites

- GitHub repository with Actions enabled
- Intercom dev workspace access token (separate from production)
- npm/pnpm project with `intercom-client` installed

## Authentication

CI authenticates to Intercom with a **dev workspace** access token, never a
production one. Store it as an encrypted GitHub Actions secret
(`INTERCOM_DEV_TOKEN`) and expose it to the integration job as the
`INTERCOM_ACCESS_TOKEN` environment variable. The Intercom SDK and the
`/me` connectivity check both send it as a bearer token in the
`Authorization: Bearer` header. The unit-test job never receives a token —
its SDK is fully mocked. Webhook verification uses a separate
`INTERCOM_WEBHOOK_SECRET` HMAC secret.

## Instructions

Read your existing `package.json` to confirm the `test`, `typecheck`, and
`test:integration` scripts exist, then work through these steps. Write each
file to the path shown; the deep reference files hold the full contents.

### Step 1: GitHub Actions workflow

Write `.github/workflows/intercom-ci.yml` with two jobs — `unit-tests` (every
push and PR) and `integration-tests` (gated to `main` pushes). The integration
job first probes `https://api.intercom.io/me` and fails fast on a non-200:

```yaml
      - name: Verify Intercom connectivity
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
            https://api.intercom.io/me)
          if [ "$STATUS" != "200" ]; then exit 1; fi
```

Full workflow YAML: [references/workflow.md](references/workflow.md).

### Step 2: Configure secrets

Store the dev token (and, if you verify webhooks, the signing secret) with the
`gh` CLI, then confirm with `gh secret list`:

```bash
gh secret set INTERCOM_DEV_TOKEN --body "dG9rOmRldl90b2tlbl9oZXJl"
gh secret list
```

Details and the webhook secret: [references/workflow.md](references/workflow.md).

### Step 3: Unit tests with a mocked SDK

Write `tests/unit/intercom-service.test.ts`, mocking the entire
`intercom-client` module so unit tests are deterministic and need no token.
Cover the happy path plus SDK errors such as a 409 duplicate-contact conflict.
Full mocked suite: [references/testing.md](references/testing.md).

### Step 4: Integration tests against the dev workspace

Write `tests/integration/contacts.integration.test.ts` using
`describe.skipIf(!token)` so the suite self-skips without a token, and track
every created contact for cleanup in `afterAll`. Full suite:
[references/testing.md](references/testing.md).

### Step 5: Webhook signature test

Verify inbound webhook signatures with a constant-time comparison
(`crypto.timingSafeEqual`). No network needed. Full test:
[references/testing.md](references/testing.md).

## Output

Applying this skill produces:

- `.github/workflows/intercom-ci.yml` — a two-job pipeline (unit + gated integration).
- `tests/unit/intercom-service.test.ts` — mocked-SDK unit tests.
- `tests/integration/contacts.integration.test.ts` — dev-workspace integration tests that self-skip without a token.
- A webhook signature verification test.
- Configured `INTERCOM_DEV_TOKEN` (and optional `INTERCOM_WEBHOOK_SECRET`) GitHub Actions secrets, confirmed via `gh secret list`.

On a green run, PRs pass unit tests token-free and `main` pushes additionally
run live integration tests and upload a coverage artifact.

## Error Handling

| CI Issue | Cause | Solution |
|----------|-------|----------|
| `INTERCOM_DEV_TOKEN` not found | Secret not configured | `gh secret set INTERCOM_DEV_TOKEN` |
| Integration tests timeout | Rate limited or slow API | Increase timeout, add delays |
| 401 in CI | Token expired or rotated | Update secret with new token |
| Flaky tests | Shared dev workspace state | Use unique names, clean up after |

## Examples

**Add Intercom CI to an existing repo.** Run `gh secret set INTERCOM_DEV_TOKEN`,
write the workflow from Step 1, and add the mocked unit suite from Step 3. PRs
now run unit tests with no token; the first `main` push runs the integration
job against the dev workspace.

**Verify webhook handling in CI.** Store `INTERCOM_WEBHOOK_SECRET`, add the
Step 5 signature test, and CI proves both valid-signature acceptance and
invalid-signature rejection with no network call.

Full worked code for every example — workflow, secrets, and all three test
suites — is in [references/workflow.md](references/workflow.md) and
[references/testing.md](references/testing.md).

## Resources

- [references/workflow.md](references/workflow.md) — full workflow YAML + secret setup
- [references/testing.md](references/testing.md) — complete unit, integration, and webhook test suites
- [GitHub Actions Docs](https://docs.github.com/en/actions)
- [GitHub Encrypted Secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Vitest](https://vitest.dev/)

## Next Steps

For deployment patterns once CI is green, see the `intercom-deploy-integration`
skill, which covers promoting a verified build from the dev workspace to
production with the same secret-management discipline.
