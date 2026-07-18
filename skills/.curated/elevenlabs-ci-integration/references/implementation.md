# ElevenLabs CI Integration — Full Workflow Reference

This reference carries the complete GitHub Actions workflow and repository
secret configuration. SKILL.md summarizes the two-tier strategy; this file is
the copy-paste source for the pipeline itself.

## Step 1: GitHub Actions Workflow

```yaml
# .github/workflows/elevenlabs-tests.yml
name: ElevenLabs Tests

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

jobs:
  # Tier 1: Always runs — no API key needed, no quota cost
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
        env:
          # Mock mode — no real API calls
          ELEVENLABS_API_KEY: "sk_test_mock_key_for_ci"

  # Tier 2: Only on main or manual trigger — uses real API
  integration-tests:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main' || github.event_name == 'workflow_dispatch'
    needs: unit-tests
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci

      # Check quota before running integration tests
      - name: Check ElevenLabs quota
        env:
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
        run: |
          REMAINING=$(curl -s https://api.elevenlabs.io/v1/user \
            -H "xi-api-key: ${ELEVENLABS_API_KEY}" | \
            jq '.subscription | (.character_limit - .character_count)')
          echo "Characters remaining: $REMAINING"
          if [ "$REMAINING" -lt 5000 ]; then
            echo "::warning::Low ElevenLabs quota ($REMAINING chars). Skipping integration tests."
            echo "SKIP_INTEGRATION=true" >> $GITHUB_ENV
          fi

      - name: Run integration tests
        if: env.SKIP_INTEGRATION != 'true'
        env:
          ELEVENLABS_API_KEY: ${{ secrets.ELEVENLABS_API_KEY }}
          ELEVENLABS_INTEGRATION: "1"
        run: npm run test:integration
```

## Step 2: Configure Repository Secrets

```bash
# Store API key as GitHub secret (use a test/dev key, NOT production)
gh secret set ELEVENLABS_API_KEY --body "sk_your_test_key_here"

# Optional: webhook secret for webhook tests
gh secret set ELEVENLABS_WEBHOOK_SECRET --body "whsec_your_secret_here"
```
