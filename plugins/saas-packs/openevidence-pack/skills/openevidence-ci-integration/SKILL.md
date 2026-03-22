---
name: openevidence-ci-integration
description: |
  Ci Integration for OpenEvidence.
  Trigger: "openevidence ci integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, openevidence, healthcare]
compatible-with: claude-code
---

# OpenEvidence CI Integration

## GitHub Actions
```yaml
name: OpenEvidence Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
```

## Resources
- [OpenEvidence Docs](https://www.openevidence.com)

## Next Steps
See `openevidence-deploy-integration`.
