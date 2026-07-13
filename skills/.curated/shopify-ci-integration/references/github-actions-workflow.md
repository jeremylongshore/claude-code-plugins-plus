Complete GitHub Actions workflow for Shopify app CI/CD with lint, test, API version check, and deployment.

```yaml
# .github/workflows/shopify-ci.yml
name: Shopify App CI

on:
  push:
    branches: [main]
  pull_request:
    branches: [main]

env:
  SHOPIFY_API_VERSION: "2025-04"  # Update quarterly — see shopify.dev/docs/api/usage/versioning

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - run: npm test -- --coverage
        env:
          SHOPIFY_API_KEY: ${{ secrets.SHOPIFY_API_KEY }}
          SHOPIFY_API_SECRET: ${{ secrets.SHOPIFY_API_SECRET }}

  integration-test:
    runs-on: ubuntu-latest
    needs: lint-and-test
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
          cache: "npm"
      - run: npm ci
      - name: Run Shopify integration tests
        run: npm run test:integration
        env:
          SHOPIFY_STORE: ${{ secrets.SHOPIFY_TEST_STORE }}
          SHOPIFY_ACCESS_TOKEN: ${{ secrets.SHOPIFY_TEST_TOKEN }}
          SHOPIFY_API_KEY: ${{ secrets.SHOPIFY_API_KEY }}
          SHOPIFY_API_SECRET: ${{ secrets.SHOPIFY_API_SECRET }}

  api-version-check:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - name: Check for deprecated API version
        run: |
          # Ensure we're not using an expired API version
          VERSION=$(grep -r "apiVersion" src/ --include="*.ts" -h | head -1 | grep -oP '\d{4}-\d{2}')
          echo "Using API version: $VERSION"

          # Check if version is still supported
          SUPPORTED=$(curl -sf -H "X-Shopify-Access-Token: ${{ secrets.SHOPIFY_TEST_TOKEN }}" \
            "https://${{ secrets.SHOPIFY_TEST_STORE }}/admin/api/versions.json" \
            | jq -r ".supported_versions[] | select(.handle == \"$VERSION\") | .supported")

          if [ "$SUPPORTED" != "true" ]; then
            echo "::warning::API version $VERSION is no longer supported!"
            exit 1
          fi

  deploy:
    runs-on: ubuntu-latest
    needs: [lint-and-test, integration-test]
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with:
          node-version: "20"
      - run: npm ci
      - run: npm run build
      - name: Deploy with Shopify CLI
        run: npx shopify app deploy --force
        env:
          SHOPIFY_CLI_PARTNERS_TOKEN: ${{ secrets.SHOPIFY_PARTNERS_TOKEN }}
```
