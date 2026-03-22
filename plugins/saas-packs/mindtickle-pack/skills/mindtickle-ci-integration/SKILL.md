---
name: mindtickle-ci-integration
description: |
  Ci Integration for MindTickle.
  Trigger: "mindtickle ci integration".
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, mindtickle, sales]
compatible-with: claude-code
---

# MindTickle CI Integration

## GitHub Actions
```yaml
name: MindTickle Tests
on: [push, pull_request]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - run: npm ci && npm test
```

## Resources
- [MindTickle Docs](https://www.mindtickle.com/platform/integrations/)

## Next Steps
See `mindtickle-deploy-integration`.
