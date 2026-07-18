---
name: klaviyo-ci-integration
description: 'Configure CI/CD pipelines for Klaviyo integrations with GitHub Actions.

  Use when setting up automated testing, configuring CI secrets,

  or integrating Klaviyo SDK tests into your build pipeline.

  Trigger with phrases like "klaviyo CI", "klaviyo GitHub Actions",

  "klaviyo automated tests", "CI klaviyo", "klaviyo pipeline".

  '
allowed-tools: Read, Write, Edit, Bash(gh:*), Bash(npm:*)
version: 1.7.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- klaviyo
- email-marketing
- cdp
compatibility: Designed for Claude Code
---
# Klaviyo CI Integration

## Overview

Set up a GitHub Actions CI/CD pipeline for Klaviyo integrations: mocked unit tests
on every pull request, gated integration tests against the real Klaviyo API on
main-branch pushes, SDK-version verification, and an API connectivity smoke test.

The workflow follows the standard two-job split — a fast, key-free `unit-tests` job
safe to require on every PR, and an `integration-tests` job gated so real-API calls
never run on fork PRs where secrets are unavailable.

## Prerequisites

- GitHub repository with Actions enabled
- Klaviyo test API key (from a test/sandbox account)
- `klaviyo-api` SDK and Vitest configured in the repository

## Instructions

### Step 1: Configure GitHub secrets

Store the Klaviyo test credentials as encrypted repository secrets:

```bash
gh secret set KLAVIYO_PRIVATE_KEY --body "pk_test_***"
gh secret set KLAVIYO_WEBHOOK_SIGNING_SECRET --body "whsec_test_***"
```

### Step 2: Add the CI workflow

Create `.github/workflows/klaviyo-ci.yml` with two jobs. The essential skeleton:

```yaml
name: Klaviyo Integration CI
on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
jobs:
  unit-tests:        # mocked, runs on every PR, no API key
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: '20', cache: 'npm' }
      - run: npm ci
      - run: npm test -- --coverage
  integration-tests: # real API, gated to main-branch pushes only
    needs: unit-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    env:
      KLAVIYO_PRIVATE_KEY: ${{ secrets.KLAVIYO_PRIVATE_KEY }}
      KLAVIYO_TEST: '1'
    steps: [...]
```

The full workflow — including `tsc --noEmit`, `npm list klaviyo-api` version check,
the connectivity smoke test, and the branch-protection config — is in
[the CI workflow reference](references/ci-workflow.md).

### Step 3: Write the tests

Author two suites the workflow drives:

- **Unit tests** mock the `klaviyo-api` SDK (`vi.mock`) and run with no key.
- **Integration tests** hit the real API behind a `describe.skipIf` guard keyed on
  `KLAVIYO_TEST` + `KLAVIYO_PRIVATE_KEY`, so they skip cleanly when no key is present.

Full, runnable examples for both suites — event-tracking unit test and a
create-and-clean-up live profile test — are in
[the test examples reference](references/test-examples.md).

## Output

- Unit tests run on every PR (mocked, no API key needed)
- Integration tests run on main-branch pushes only (real API)
- SDK version verified in CI via `npm list klaviyo-api`
- API connectivity smoke test included in the integration job

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Secret not found in CI | Missing `gh secret set` | Add the secret via repository settings |
| Integration test 429 | Rate limited in CI | Add delays between tests, use a dedicated test key |
| Auth failures in CI | Wrong secret name | Verify the secret name matches the workflow env var |
| Test timeout | Slow Klaviyo response | Increase `timeout-minutes` on the job step |

## Examples

**Set up CI on a fresh repository.** Store the test credentials, drop in the
workflow, then let the pipeline gate itself:

```bash
gh secret set KLAVIYO_PRIVATE_KEY --body "pk_test_***"
# add .github/workflows/klaviyo-ci.yml (see Step 2 skeleton + full reference)
git add .github/workflows/klaviyo-ci.yml && git commit -m "ci: add Klaviyo pipeline"
git push   # opens a PR → unit-tests run mocked; integration-tests stay gated to main
```

**Run the gated integration suite locally** before pushing to main:

```bash
export KLAVIYO_TEST=1
export KLAVIYO_PRIVATE_KEY="pk_test_***"
npm run test:integration   # skipIf guard now active → live API exercised
```

Both example flows are expanded — full workflow YAML in
[references/ci-workflow.md](references/ci-workflow.md) and the complete unit +
integration suites in [references/test-examples.md](references/test-examples.md).

## Resources

- [GitHub Actions documentation](https://docs.github.com/en/actions)
- [GitHub encrypted secrets](https://docs.github.com/en/actions/security-guides/encrypted-secrets)
- [Full CI workflow reference](references/ci-workflow.md)
- [Test examples reference](references/test-examples.md)

## Next Steps

For deployment patterns that build on this pipeline, see the
`klaviyo-deploy-integration` skill in this pack.
