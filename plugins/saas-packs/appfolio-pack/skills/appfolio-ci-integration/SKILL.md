---
name: appfolio-ci-integration
description: |
  Configure CI/CD pipeline for AppFolio property management integrations.
  Trigger: "appfolio CI".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(curl:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, property-management, appfolio, real-estate]
compatible-with: claude-code
---

# appfolio ci integration | sed 's/\b\(.\)/\u\1/g'

## GitHub Actions Workflow
```yaml
name: AppFolio Integration CI
on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-node@v4
        with: { node-version: "20" }
      - run: npm ci
      - run: npm run lint
      - run: npm run typecheck
      - name: Run tests with mock API
        run: npm test
      - name: Integration test (sandbox)
        if: github.ref == 'refs/heads/main'
        env:
          APPFOLIO_CLIENT_ID: ${{ secrets.APPFOLIO_CLIENT_ID }}
          APPFOLIO_CLIENT_SECRET: ${{ secrets.APPFOLIO_CLIENT_SECRET }}
          APPFOLIO_BASE_URL: ${{ secrets.APPFOLIO_SANDBOX_URL }}
        run: npm run test:integration
```

## Resources

- [AppFolio Stack APIs](https://www.appfolio.com/stack/partners/api)
- [AppFolio Engineering Blog](https://engineering.appfolio.com)
