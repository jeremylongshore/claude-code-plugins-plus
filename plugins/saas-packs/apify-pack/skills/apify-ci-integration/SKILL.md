---
name: apify-ci-integration
description: |
  Configure CI/CD pipelines for Apify Actor builds and deployments.
  Use when automating Actor deployment via GitHub Actions, running
  integration tests against the live Apify API, or building CI/CD for
  scrapers that push to the Apify platform.
  Trigger with "apify CI", "apify GitHub Actions", "apify automated deploy",
  "CI apify", "apify pipeline", "auto deploy actor".
allowed-tools: Write, Bash(gh:*), Bash(npm:*)
version: 1.5.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- scraping
- automation
- apify
compatibility: Designed for Claude Code
---
# Apify CI Integration

## Overview

Automate Apify Actor builds, tests, and deployments using GitHub Actions —
test-on-PR, deploy-on-merge, live-API integration testing, and Docker build
verification. Three workflow files do the work (test, deploy, verify-build);
full copy-paste-ready definitions live in
[references/workflows.md](references/workflows.md).

## Prerequisites

- GitHub repository with Actions enabled
- Apify API token stored as a GitHub secret
- Actor code in the repository

## Authentication

CI authenticates to Apify with a personal API token, never a hard-coded
credential:

- Store the token as a GitHub Actions **secret** (`gh secret set APIFY_TOKEN`),
  and expose it to a job only via `env: APIFY_TOKEN: ${{ secrets.APIFY_TOKEN }}`.
- The Apify CLI reads it as `apify login --token $APIFY_TOKEN`; the REST API and
  `apify-client` read it from the `APIFY_TOKEN` environment variable.
- Use separate `APIFY_TOKEN_TEST` / `APIFY_TOKEN_PROD` secrets so integration
  runs never touch production data. Get tokens from Apify Console → Settings →
  Integrations.

## Instructions

### Step 1: Configure GitHub Secrets

```bash
# Store Apify token for CI
gh secret set APIFY_TOKEN --body "apify_api_YOUR_CI_TOKEN"

# Optional: separate tokens for test vs production
gh secret set APIFY_TOKEN_TEST --body "apify_api_test_token"
gh secret set APIFY_TOKEN_PROD --body "apify_api_prod_token"
```

### Step 2: Create the test workflow

Add `.github/workflows/apify-test.yml` with two jobs — `unit-tests` on every PR
and `integration-tests` gated to `push` (merge) events. The integration job
proves connectivity before running tests:

```yaml
      - name: Verify Apify connection
        run: |
          curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
            https://api.apify.com/v2/users/me | jq '.data.username'
```

Full two-job workflow: [references/workflows.md](references/workflows.md) (Test Workflow).

### Step 3: Create the deploy workflow

Add `.github/workflows/apify-deploy.yml` — triggered on merges that touch
`src/**`, `package.json`, or `.actor/**` (plus `workflow_dispatch`). It builds,
tests, installs the Apify CLI, `apify push`es, then runs a minimal smoke call to
confirm the new build actually starts. Full definition:
[references/workflows.md](references/workflows.md) (Deploy Workflow).

### Step 4: Write integration tests

Gate live-API tests on the token so they skip cleanly when it is absent:

```typescript
const SKIP_INTEGRATION = !process.env.APIFY_TOKEN;

describe.skipIf(SKIP_INTEGRATION)('Apify Integration', () => {
  it('should authenticate successfully', async () => {
    const user = await client.user().get();
    expect(user.username).toBeTruthy();
  });
});
```

The complete suite (auth, live Actor run, create/delete a named dataset with
cleanup) is in [references/integration-tests.md](references/integration-tests.md).

### Step 5: Verify the Actor build

Add a `verify-build.yml` that `docker build`s the Actor image and boots it once
to confirm the entry point loads. Optionally add branch-protection rules that
require the CI contexts before merge. Both blocks:
[references/workflows.md](references/workflows.md) (Actor Build Verification).

## Output

Applying this skill produces committed CI/CD infrastructure in the repository:

- `.github/workflows/apify-test.yml` — unit tests on every PR, integration tests
  on merge to `main`.
- `.github/workflows/apify-deploy.yml` — `apify push` + post-deploy smoke test on
  merge, plus manual `workflow_dispatch`.
- `.github/workflows/verify-build.yml` — Docker build + entry-point check on PRs.
- `tests/integration/apify.test.ts` — token-gated live-API integration suite.
- Configured GitHub secrets (`APIFY_TOKEN`, optional `_TEST` / `_PROD` variants)
  and, optionally, branch-protection requiring the CI checks to pass.

Once merged, every PR runs unit tests, every merge deploys and smoke-tests the
Actor, and a failed deploy surfaces a `::error::` annotation in the run log.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| `APIFY_TOKEN` not set | Secret not configured | `gh secret set APIFY_TOKEN` |
| Integration test timeout | Slow Actor run | Increase timeout, use smaller input |
| Docker build fails in CI | Local-only deps | Commit `package-lock.json` |
| `apify push` fails | Not logged in | Add `apify login --token` step |
| Flaky integration tests | External service issues | Add retries, use `test.retry(2)` |

## Examples

**Minimal test-on-PR gate** — the smallest useful setup is Step 1 (store the
secret) plus the `unit-tests` job from the test workflow. Every PR then runs
`npm ci && npm run build && npm test` before it can merge.

**Full deploy pipeline** — add the deploy workflow so a merge to `main` that
touches `src/**` builds, tests, runs `apify push`, then smoke-tests the new
build:

```yaml
      - name: Push Actor to Apify
        run: apify push

      - name: Verify deployment
        run: |
          ACTOR_ID=$(jq -r '.name' .actor/actor.json)
          apify actors call $ACTOR_ID \
            --input='{"startUrls":[{"url":"https://example.com"}],"maxItems":1}' \
            --timeout=120
```

**apify-client app (not Actor dev)** — for an app that *calls* Actors rather than
publishing one, mock `apify-client` in unit tests and gate a real-token
integration job to `main`. Full workflow:
[references/workflows.md](references/workflows.md) (CI Configuration for apify-client Apps).

See [references/workflows.md](references/workflows.md) for every full workflow
and [references/integration-tests.md](references/integration-tests.md) for the
complete integration suite.

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Apify CLI Reference](https://docs.apify.com/cli/docs/reference)
- [Actor Deployment](https://docs.apify.com/platform/actors/development/deployment)

## Next Steps

For runtime deployment patterns beyond CI wiring — release channels, versioned
Actor builds, and rollback — see the `apify-deploy-integration` skill in this
pack.
