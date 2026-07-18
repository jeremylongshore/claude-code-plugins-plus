# Groq CI Integration — Full Implementation

Complete, copy-paste-ready CI/CD workflows and configuration for Groq
integrations. Each block below is production-tested and referenced as a lean
skeleton from the parent `SKILL.md`.

## Step 1: GitHub Actions Workflow

The full workflow runs three jobs: mocked unit tests (no key), live
integration tests (push-to-main only), and a weekly model-deprecation check.

```yaml
# .github/workflows/groq-tests.yml
name: Groq Integration Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]
  schedule:
    - cron: "0 6 * * 1"  # Weekly model deprecation check

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
      - run: npm test -- --coverage
        # Unit tests use mocked groq-sdk -- no API key needed

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name != 'pull_request'  # Only on push to main
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run Groq integration tests
        run: GROQ_INTEGRATION=1 npx vitest tests/groq.integration.ts --reporter=verbose
        timeout-minutes: 2

  model-check:
    runs-on: ubuntu-latest
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - name: Check for deprecated models
        run: |
          set -euo pipefail
          # Get current models from Groq API
          MODELS=$(curl -sf https://api.groq.com/openai/v1/models \
            -H "Authorization: Bearer $GROQ_API_KEY" | jq -r '.data[].id')

          # Check our code references valid models
          USED=$(grep -roh "model.*['\"].*['\"]" src/ --include="*.ts" | \
            grep -oP "(?<=['\"])[\w./-]+(?=['\"])" | sort -u)

          echo "=== Models in our code ==="
          echo "$USED"
          echo ""
          echo "=== Available on Groq ==="
          echo "$MODELS"

          # Flag any model in our code that's not in the API response
          MISSING=""
          while IFS= read -r model; do
            if ! echo "$MODELS" | grep -qF "$model"; then
              MISSING="$MISSING\n  - $model"
            fi
          done <<< "$USED"

          if [ -n "$MISSING" ]; then
            echo "WARNING: These models in code are not available on Groq:$MISSING"
            exit 1
          fi
          echo "All models valid."
```

## Step 2: Configure Secrets

```bash
# Store Groq API key as GitHub secret
gh secret set GROQ_API_KEY --body "gsk_your_ci_key_here"

# Use a separate key for CI (easier to rotate, track usage)
```

## Step 4: Release Workflow

Gate `npm publish` behind a real production Groq round-trip so a broken key or
deprecated model blocks the release rather than shipping.

```yaml
# .github/workflows/release.yml
on:
  push:
    tags: ["v*"]

jobs:
  release:
    runs-on: ubuntu-latest
    env:
      GROQ_API_KEY: ${{ secrets.GROQ_API_KEY_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm test
      - name: Verify Groq API in production
        run: GROQ_INTEGRATION=1 npx vitest tests/groq.integration.ts
      - run: npm run build
      - run: npm publish
        env:
          NODE_AUTH_TOKEN: ${{ secrets.NPM_TOKEN }}
```

## CI Best Practices

- Mock `groq-sdk` in unit tests (no API key needed, no network)
- Run integration tests only on `main` push (not PRs -- saves quota)
- Use `llama-3.1-8b-instant` for CI tests (cheapest, fastest)
- Set `max_tokens` low (5-50) in CI to minimize token usage
- Add `timeout-minutes: 2` to prevent hung jobs
- Schedule weekly model deprecation checks
