# GitHub Actions Workflow & Secret Management

Full reference for the CI workflow file and Intercom secret configuration. The
skeleton in SKILL.md is the minimum; this is the complete, copy-ready version.

## GitHub Actions Workflow

Write this to `.github/workflows/intercom-ci.yml`. It runs unit tests (mocked
SDK) on every push and pull request, and gates the live integration job to
`main` pushes only so pull requests never touch the shared dev workspace.

```yaml
# .github/workflows/intercom-ci.yml
name: Intercom Integration CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run typecheck
      - run: npm test -- --coverage
      - uses: actions/upload-artifact@v4
        with:
          name: coverage
          path: coverage/

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      INTERCOM_ACCESS_TOKEN: ${{ secrets.INTERCOM_DEV_TOKEN }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Verify Intercom connectivity
        run: |
          STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
            -H "Authorization: Bearer $INTERCOM_ACCESS_TOKEN" \
            https://api.intercom.io/me)
          if [ "$STATUS" != "200" ]; then
            echo "Intercom auth failed: $STATUS"
            exit 1
          fi
      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5
```

## Configure Secrets

Store the Intercom dev workspace token as an encrypted GitHub Actions secret.
Never use a production token in CI — a leaked or misused CI token must not be
able to mutate live customer data.

```bash
# Store dev workspace token (never production!)
gh secret set INTERCOM_DEV_TOKEN --body "dG9rOmRldl90b2tlbl9oZXJl"

# If using webhooks in CI, store the signing secret
gh secret set INTERCOM_WEBHOOK_SECRET --body "your-webhook-secret"

# Verify secrets are set
gh secret list
```

The workflow reads `INTERCOM_DEV_TOKEN` into the `INTERCOM_ACCESS_TOKEN`
environment variable only for the `integration-tests` job. The unit-test job
never sees a token because its SDK is fully mocked.
