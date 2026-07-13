# CI/CD Integration Patterns

Real workflow configurations for running cross-browser tests in CI/CD pipelines with BrowserStack, Sauce Labs, LambdaTest, and Kobiton.

---

## GitHub Actions

### Playwright (Local Browsers)

```yaml
name: Cross-Browser Tests
on: [push, pull_request]

jobs:
  browser-compat:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci
      - run: npx playwright install --with-deps chromium firefox webkit
      - run: npx playwright test --project=chromium --project=firefox --project=webkit
      - uses: actions/upload-artifact@v4
        if: failure()
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 7
```

### BrowserStack

```yaml
name: BrowserStack Cross-Browser
on: [push, pull_request]

jobs:
  browserstack:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci

      - name: Start BrowserStack Local
        uses: browserstack/github-actions/setup-local@master
        with:
          local-testing: start
          local-identifier: ci-${{ github.run_id }}

      - name: Run tests on BrowserStack
        env:
          BROWSERSTACK_USERNAME: ${{ secrets.BROWSERSTACK_USERNAME }}
          BROWSERSTACK_ACCESS_KEY: ${{ secrets.BROWSERSTACK_ACCESS_KEY }}
          BROWSERSTACK_LOCAL_IDENTIFIER: ci-${{ github.run_id }}
        run: npx playwright test --config=playwright.browserstack.config.ts

      - name: Stop BrowserStack Local
        uses: browserstack/github-actions/setup-local@master
        with:
          local-testing: stop
```

### Sauce Labs

```yaml
name: Sauce Labs Cross-Browser
on: [push, pull_request]

jobs:
  saucelabs:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci

      - name: Start Sauce Connect
        uses: saucelabs/sauce-connect-action@v2
        with:
          username: ${{ secrets.SAUCE_USERNAME }}
          accessKey: ${{ secrets.SAUCE_ACCESS_KEY }}
          tunnelName: ci-${{ github.run_id }}

      - name: Run tests on Sauce Labs
        env:
          SAUCE_USERNAME: ${{ secrets.SAUCE_USERNAME }}
          SAUCE_ACCESS_KEY: ${{ secrets.SAUCE_ACCESS_KEY }}
          SAUCE_TUNNEL_NAME: ci-${{ github.run_id }}
        run: npx playwright test --config=playwright.saucelabs.config.ts
```

### LambdaTest

```yaml
name: LambdaTest Cross-Browser
on: [push, pull_request]

jobs:
  lambdatest:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci

      - name: Start LambdaTest Tunnel
        uses: LambdaTest/tunnel-action@v2
        with:
          user: ${{ secrets.LT_USERNAME }}
          accessKey: ${{ secrets.LT_ACCESS_KEY }}
          tunnelName: ci-${{ github.run_id }}

      - name: Run tests on LambdaTest
        env:
          LT_USERNAME: ${{ secrets.LT_USERNAME }}
          LT_ACCESS_KEY: ${{ secrets.LT_ACCESS_KEY }}
          LT_TUNNEL_NAME: ci-${{ github.run_id }}
        run: npx playwright test --config=playwright.lambdatest.config.ts
```

### Kobiton

```yaml
name: Kobiton Real-Device Tests
on: [push, pull_request]

jobs:
  kobiton:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: 20
      - run: npm ci

      - name: Check device availability
        env:
          KOBITON_USERNAME: ${{ secrets.KOBITON_USERNAME }}
          KOBITON_API_KEY: ${{ secrets.KOBITON_API_KEY }}
        run: |
          curl -s -u "$KOBITON_USERNAME:$KOBITON_API_KEY" \
            "https://api.kobiton.com/v1/devices?isOnline=true&platformName=iOS" \
            | jq '.devices | length' | xargs -I{} echo "Available iOS devices: {}"

      - name: Run Appium tests on Kobiton
        env:
          KOBITON_USERNAME: ${{ secrets.KOBITON_USERNAME }}
          KOBITON_API_KEY: ${{ secrets.KOBITON_API_KEY }}
        run: npx wdio run wdio.kobiton.conf.ts

      - name: Fetch session results
        if: always()
        env:
          KOBITON_USERNAME: ${{ secrets.KOBITON_USERNAME }}
          KOBITON_API_KEY: ${{ secrets.KOBITON_API_KEY }}
        run: |
          # Fetch latest sessions for this build
          curl -s -u "$KOBITON_USERNAME:$KOBITON_API_KEY" \
            "https://api.kobiton.com/v1/sessions?page=1&size=10" \
            | jq '.data[] | {id, state, deviceName: .device.deviceName, duration}'
```

---

## CircleCI

### Multi-Provider Parallel Workflow

```yaml
version: 2.1

orbs:
  browser-testing: circleci/browser-tools@1.4

jobs:
  playwright-local:
    docker:
      - image: mcr.microsoft.com/playwright:v1.45.0
    steps:
      - checkout
      - run: npm ci
      - run: npx playwright test
      - store_artifacts:
          path: playwright-report

  browserstack-cloud:
    docker:
      - image: cimg/node:20.0
    steps:
      - checkout
      - run: npm ci
      - run:
          name: Run on BrowserStack
          command: npx playwright test --config=playwright.browserstack.config.ts
          environment:
            BROWSERSTACK_USERNAME: << pipeline.parameters.bs-user >>
            BROWSERSTACK_ACCESS_KEY: << pipeline.parameters.bs-key >>

  kobiton-mobile:
    docker:
      - image: cimg/node:20.0
    steps:
      - checkout
      - run: npm ci
      - run:
          name: Run on Kobiton real devices
          command: npx wdio run wdio.kobiton.conf.ts
          environment:
            KOBITON_USERNAME: << pipeline.parameters.kobiton-user >>
            KOBITON_API_KEY: << pipeline.parameters.kobiton-key >>

workflows:
  cross-browser:
    jobs:
      - playwright-local
      - browserstack-cloud:
          requires: [playwright-local]  # gate cloud tests behind local pass
      - kobiton-mobile:
          requires: [playwright-local]
```

---

## Secrets Management

### GitHub Actions Secrets

```bash
# Set secrets via gh CLI
gh secret set BROWSERSTACK_USERNAME --body "your_username"
gh secret set BROWSERSTACK_ACCESS_KEY --body "your_key"
gh secret set SAUCE_USERNAME --body "your_username"
gh secret set SAUCE_ACCESS_KEY --body "your_key"
gh secret set LT_USERNAME --body "your_username"
gh secret set LT_ACCESS_KEY --body "your_key"
gh secret set KOBITON_USERNAME --body "your_username"
gh secret set KOBITON_API_KEY --body "your_key"
```

### Environment Variable Pattern

All provider configs should read credentials from environment variables, never from config files checked into source control:

```typescript
// wdio.kobiton.conf.ts
export const config = {
  user: process.env.KOBITON_USERNAME,
  key: process.env.KOBITON_API_KEY,
  hostname: 'api.kobiton.com',
  // ...
};

if (!config.user || !config.key) {
  throw new Error('KOBITON_USERNAME and KOBITON_API_KEY must be set');
}
```

---

## Parallel Execution Strategy

### Fan-Out Pattern

Run local tests first as a gate, then fan out to cloud providers in parallel:

```
Local Playwright (fast, ~2 min)
    ├── BrowserStack (desktop matrix)
    ├── Sauce Labs (enterprise matrix)
    ├── LambdaTest (extended matrix)
    └── Kobiton (real mobile devices)
```

This saves cloud provider minutes by catching obvious failures locally first.

### Result Aggregation

After all providers complete, aggregate into a single report:

```bash
#!/bin/bash
# aggregate-results.sh

echo "## Cross-Browser Test Results" > report.md
echo "" >> report.md
echo "| Provider | Passed | Failed | Duration |" >> report.md
echo "|----------|--------|--------|----------|" >> report.md

# Parse each provider's output and append
for provider in playwright browserstack saucelabs lambdatest kobiton; do
  if [ -f "results/${provider}.json" ]; then
    passed=$(jq '.passed' "results/${provider}.json")
    failed=$(jq '.failed' "results/${provider}.json")
    duration=$(jq -r '.duration' "results/${provider}.json")
    echo "| ${provider} | ${passed} | ${failed} | ${duration} |" >> report.md
  fi
done
```

---

## Failure Handling

### Retry Strategy

Cloud tests can be flaky due to device availability, network latency, or provider infrastructure. Configure retries:

```typescript
// playwright.browserstack.config.ts
export default defineConfig({
  retries: 2,              // retry failed tests up to 2 times
  timeout: 60_000,         // 60s per test (cloud is slower than local)
  expect: { timeout: 15_000 }, // 15s for assertions (real devices are slower)
});
```

### Kobiton Device Fallback

If a specific device is unavailable, fall back to a compatible alternative:

```json
{
  "kobiton:options": {
    "deviceGroup": "KOBITON",
    "deviceName": "*iPhone*",
    "platformVersion": ">=16"
  }
}
```

Using wildcards and version ranges lets Kobiton match any available device that fits the criteria, avoiding "device not found" failures in CI.

### Notifications

Post results to Slack or GitHub PR comments:

```yaml
      - name: Post results to PR
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v7
        with:
          script: |
            const fs = require('fs');
            const report = fs.readFileSync('report.md', 'utf8');
            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: report
            });
```
