---
name: clari-ci-integration
description: |
  Integrate Clari export pipeline testing and validation into CI/CD.
  Use when adding automated tests for Clari integrations,
  validating export schemas in CI, or testing pipeline reliability.
  Trigger with phrases like "clari CI", "clari github actions",
  "clari automated tests", "test clari pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, revenue-intelligence, forecasting, clari]
compatible-with: claude-code
---

# Clari CI Integration

## Overview

Add Clari export validation to CI: test API connectivity, validate export schemas, and run pipeline integration tests.

## Instructions

### GitHub Actions Workflow

```yaml
name: Clari Pipeline Tests

on:
  push:
    paths: ["src/clari/**", "tests/clari/**"]
  schedule:
    - cron: "0 6 * * 1"  # Weekly Monday check

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - run: pip install -r requirements.txt

      - name: Unit tests (mock data)
        run: pytest tests/ -v -k "not integration"

      - name: Integration test (real API)
        if: github.ref == 'refs/heads/main'
        env:
          CLARI_API_KEY: ${{ secrets.CLARI_API_KEY }}
        run: |
          python -c "
          from clari_client import ClariClient
          client = ClariClient()
          forecasts = client.list_forecasts()
          assert len(forecasts) > 0, 'No forecasts found'
          print(f'Connected: {len(forecasts)} forecasts available')
          "

      - name: Schema validation
        env:
          CLARI_API_KEY: ${{ secrets.CLARI_API_KEY }}
        run: |
          python scripts/validate_schema.py
```

### Store Secrets

```bash
gh secret set CLARI_API_KEY --body "your-api-token"
```

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Next Steps

For deployment patterns, see `clari-deploy-integration`.
