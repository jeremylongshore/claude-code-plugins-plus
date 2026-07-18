# Klaviyo CI Workflow — Full Reference

The complete GitHub Actions workflow that runs mocked unit tests on every PR and
gated integration tests against the real Klaviyo API on main-branch pushes.

## Full CI workflow

Create `.github/workflows/klaviyo-ci.yml`:

```yaml
name: Klaviyo Integration CI

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
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npx tsc --noEmit
      - run: npm test -- --coverage
      - name: Check Klaviyo SDK version
        run: npm list klaviyo-api

  integration-tests:
    runs-on: ubuntu-latest
    needs: unit-tests
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    env:
      KLAVIYO_PRIVATE_KEY: ${{ secrets.KLAVIYO_PRIVATE_KEY }}
      KLAVIYO_TEST: '1'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 5
      - name: Verify Klaviyo connectivity
        run: |
          curl -s -w "HTTP %{http_code}\n" -o /dev/null \
            -H "Authorization: Klaviyo-API-Key $KLAVIYO_PRIVATE_KEY" \
            -H "revision: 2024-10-15" \
            "https://a.klaviyo.com/api/accounts/"
```

## PR checks configuration

```yaml
# .github/branch-protection.yml (or set via GitHub UI)
# Required checks: unit-tests
# Integration tests: optional (only on main push)
```

The `unit-tests` job is safe to require on every PR because it is fully mocked and
needs no API key. The `integration-tests` job is gated behind
`github.event_name == 'push' && github.ref == 'refs/heads/main'` so real-API calls
never run on fork PRs (where secrets are unavailable) — keep it optional in branch
protection.
