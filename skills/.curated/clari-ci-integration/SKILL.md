---
name: clari-ci-integration
description: 'Integrate Clari export pipeline testing and validation into CI/CD.

  Use when adding automated tests for Clari integrations,

  validating export schemas in CI, or testing pipeline reliability.

  Trigger with phrases like "clari CI", "clari github actions",

  "clari automated tests", "test clari pipeline".

  '
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.6.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- revenue-intelligence
- forecasting
- clari
compatibility: Designed for Claude Code
---
# Clari CI Integration

## Overview

Add Clari export validation to CI: test API connectivity, validate export schemas, and run pipeline integration tests.

## Prerequisites

- Protected CI environment with scoped, masked secrets
- Mock fixtures for pull-request tests and an approved integration test account
- A repository environment gate for any production-targeted job
- Retention policy for generated logs and artifacts

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

## Error Handling

| Condition | Response |
|---|---|
| Unit fixture or schema test fails | Fail the run before any external request and attach a redacted report. |
| Integration account cannot authenticate | Stop retries, verify the secret reference and account scope, then notify its owner. |
| Export shape changes | Quarantine the release and require a reviewed schema migration. |
| Secret appears in logs or artifacts | Revoke it, purge according to policy, and investigate exposure. |

## Output

Publish a redacted run summary with fixture/integration status, schema version,
external job IDs, artifact retention location, and promotion decision. Secrets,
forecast payloads, and download URLs must remain masked and unavailable to
untrusted pull-request code.

## Examples

Run mock tests on every pull request, then run one read-only integration export
only from a protected branch using a scoped environment secret. Fail closed if
the schema changes or the credential is unavailable; a successful read does not
authorize a data load or production deployment.

## Resources

- [GitHub Actions Documentation](https://docs.github.com/en/actions)

## Next Steps

For deployment patterns, see `clari-deploy-integration`.
