# Apify CI/CD Workflows — Full Reference

Complete GitHub Actions workflow definitions for Apify Actor development. These
are the full versions of the workflows summarized in `SKILL.md`. Copy the block
you need into the named path.

## Test Workflow

Create `.github/workflows/apify-test.yml`:

```yaml
name: Apify Tests

on:
  pull_request:
    branches: [main]
  push:
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
      - run: npm run build
      - run: npm test -- --coverage

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event_name == 'push'  # Only on merge to main
    env:
      APIFY_TOKEN: ${{ secrets.APIFY_TOKEN_TEST }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci

      - name: Verify Apify connection
        run: |
          curl -sf -H "Authorization: Bearer $APIFY_TOKEN" \
            https://api.apify.com/v2/users/me | jq '.data.username'

      - name: Run integration tests
        run: npm run test:integration
        timeout-minutes: 10
```

## Deploy Workflow

Create `.github/workflows/apify-deploy.yml`:

```yaml
name: Deploy Actor

on:
  push:
    branches: [main]
    paths:
      - 'src/**'
      - 'package.json'
      - 'package-lock.json'
      - '.actor/**'

  workflow_dispatch:  # Manual trigger

jobs:
  deploy:
    runs-on: ubuntu-latest
    env:
      APIFY_TOKEN: ${{ secrets.APIFY_TOKEN_PROD }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'

      - run: npm ci
      - run: npm run build
      - run: npm test

      - name: Install Apify CLI
        run: npm install -g apify-cli

      - name: Login to Apify
        run: apify login --token $APIFY_TOKEN

      - name: Push Actor to Apify
        run: apify push

      - name: Verify deployment
        run: |
          # Get latest build status
          ACTOR_ID=$(jq -r '.name' .actor/actor.json)
          echo "Deployed Actor: $ACTOR_ID"

          # Run a smoke test with minimal input
          apify actors call $ACTOR_ID \
            --input='{"startUrls":[{"url":"https://example.com"}],"maxItems":1}' \
            --timeout=120

      - name: Notify on failure
        if: failure()
        run: |
          echo "::error::Actor deployment failed! Check build logs."
```

## Actor Build Verification in CI

```yaml
# .github/workflows/verify-build.yml
name: Verify Actor Build

on:
  pull_request:
    paths: ['src/**', '.actor/**', 'Dockerfile']

jobs:
  docker-build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Build Actor Docker image
        run: |
          docker build -t actor-test -f .actor/Dockerfile .

      - name: Verify entry point
        run: |
          # Check that the built image can at least start
          docker run --rm actor-test node -e "
            const { Actor } = require('apify');
            console.log('Actor module loaded successfully');
          "
```

## CI Configuration for apify-client Apps

For applications that call Actors (not Actor development):

```yaml
# .github/workflows/test.yml
name: Test Apify Integration

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm test
        env:
          # Unit tests should mock apify-client
          # Only set token for integration test job
          APIFY_TOKEN: ''

  integration:
    needs: test
    if: github.ref == 'refs/heads/main'
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: '20'
          cache: 'npm'
      - run: npm ci
      - run: npm run test:integration
        env:
          APIFY_TOKEN: ${{ secrets.APIFY_TOKEN }}
```

## Branch Protection Rules

```bash
# Require CI to pass before merging
gh api repos/{owner}/{repo}/branches/main/protection -X PUT \
  --input - <<EOF
{
  "required_status_checks": {
    "strict": true,
    "contexts": ["unit-tests", "docker-build"]
  },
  "enforce_admins": true,
  "required_pull_request_reviews": null
}
EOF
```
