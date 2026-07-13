# CI Policy Pipeline

GitHub Actions workflow that enforces token scanning, GDPR webhook configuration, and API version stability on every push and PR.

```yaml
# .github/workflows/shopify-policy.yml
name: Shopify Policy

on: [push, pull_request]

jobs:
  policy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Scan for hardcoded Shopify tokens
        run: |
          if grep -rE "shpat_[a-f0-9]{32}|shpss_[a-f0-9]{32}" \
            --include="*.ts" --include="*.tsx" --include="*.js" \
            app/ src/ ; then
            echo "::error::Hardcoded Shopify tokens found!"
            exit 1
          fi

      - name: Check GDPR webhooks configured
        run: |
          for topic in "customers/data_request" "customers/redact" "shop/redact"; do
            if ! grep -q "$topic" shopify.app.toml; then
              echo "::error::Missing mandatory GDPR webhook: $topic"
              exit 1
            fi
          done
          echo "All GDPR webhooks configured"

      - name: Validate API version
        run: |
          VERSION=$(grep 'api_version' shopify.app.toml | head -1 | grep -oP '\d{4}-\d{2}')
          if [ "$VERSION" = "unstable" ]; then
            echo "::error::Cannot use unstable API version"
            exit 1
          fi
          echo "API version: $VERSION"
```
