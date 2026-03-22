---
name: navan-ci-integration
description: |
  Ci Integration for Navan.
  Trigger: "navan ci integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, navan, travel]
compatible-with: claude-code
---

# Navan CI Integration

## GitHub Actions
```yaml
name: Navan Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
```

## Resources
- [Navan Docs](https://app.navan.com/app/helpcenter)

## Next Steps
See `navan-deploy-integration`.
