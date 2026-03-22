---
name: fathom-ci-integration
description: |
  Test Fathom integrations in CI/CD pipelines.
  Trigger with phrases like "fathom CI", "fathom github actions", "test fathom pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, meeting-intelligence, ai-notes, fathom]
compatible-with: claude-code
---

# Fathom CI Integration

```yaml
name: Fathom Integration Tests
on:
  push:
    paths: ["src/fathom/**"]
jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: "3.11" }
      - run: pip install -r requirements.txt
      - run: pytest tests/ -v -k "not integration"
      - name: API connectivity check
        if: github.ref == 'refs/heads/main'
        env:
          FATHOM_API_KEY: ${{ secrets.FATHOM_API_KEY }}
        run: |
          python -c "
          from fathom_client import FathomClient
          client = FathomClient()
          meetings = client.list_meetings(limit=1)
          print(f'API connected: {len(meetings)} meetings')
          "
```

## Next Steps

For deployment, see `fathom-deploy-integration`.
