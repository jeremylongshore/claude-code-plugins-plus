---
name: hex-ci-integration
description: |
  Configure Hex CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Hex tests into your build process.
  Trigger with phrases like "hex CI", "hex GitHub Actions",
  "hex automated tests", "CI hex".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, hex, data, analytics]
compatible-with: claude-code
---

# Hex CI Integration

## Instructions

### GitHub Actions — Trigger Hex on Deploy

```yaml
name: Deploy & Refresh Data
on:
  push:
    branches: [main]

jobs:
  refresh-hex:
    runs-on: ubuntu-latest
    steps:
      - name: Trigger Hex project refresh
        env:
          HEX_API_TOKEN: ${{ secrets.HEX_API_TOKEN }}
        run: |
          curl -X POST \
            -H "Authorization: Bearer $HEX_API_TOKEN" \
            -H "Content-Type: application/json" \
            -d '{"inputParams": {"triggered_by": "ci"}, "updateCacheResult": true}' \
            https://app.hex.tech/api/v1/project/${{ vars.HEX_PROJECT_ID }}/run
```

```bash
gh secret set HEX_API_TOKEN --body "hex_token_..."
gh variable set HEX_PROJECT_ID --body "project-id"
```

## Resources

- [GitHub Actions](https://docs.github.com/en/actions)
- [Hex API](https://learn.hex.tech/docs/api/api-reference)
