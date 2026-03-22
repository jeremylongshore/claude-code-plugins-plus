---
name: palantir-ci-integration
description: |
  Configure CI/CD pipelines for Palantir Foundry integrations with GitHub Actions.
  Use when setting up automated testing, running transforms validation,
  or integrating Foundry SDK tests into your build process.
  Trigger with phrases like "palantir CI", "foundry GitHub Actions",
  "palantir automated tests", "CI foundry".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, ci-cd, github-actions]
compatible-with: claude-code, codex, openclaw
---

# Palantir CI Integration

## Overview
Set up GitHub Actions CI pipelines for Foundry integrations. Covers running transform unit tests with PySpark, SDK integration tests with mocked APIs, and linting Foundry-specific patterns.

## Prerequisites
- GitHub repository with Foundry integration code
- `foundry-platform-sdk` in requirements
- pytest test suite

## Instructions

### Step 1: GitHub Actions Workflow
```yaml
# .github/workflows/foundry-ci.yml
name: Foundry CI
on:
  push:
    branches: [main]
  pull_request:

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"
          cache: pip

      - name: Set up Java (for PySpark)
        uses: actions/setup-java@v4
        with:
          distribution: temurin
          java-version: "11"

      - name: Install dependencies
        run: pip install -r requirements.txt

      - name: Run unit tests
        run: pytest tests/ -v --tb=short --junitxml=test-results.xml

      - name: Upload test results
        if: always()
        uses: actions/upload-artifact@v4
        with:
          name: test-results
          path: test-results.xml

  lint:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install ruff
      - run: ruff check src/ tests/

  integration:
    runs-on: ubuntu-latest
    if: github.event_name == 'push' && github.ref == 'refs/heads/main'
    needs: [test, lint]
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with:
          python-version: "3.11"
      - run: pip install -r requirements.txt
      - name: Run integration smoke test
        env:
          FOUNDRY_HOSTNAME: ${{ secrets.FOUNDRY_HOSTNAME }}
          FOUNDRY_CLIENT_ID: ${{ secrets.FOUNDRY_CLIENT_ID }}
          FOUNDRY_CLIENT_SECRET: ${{ secrets.FOUNDRY_CLIENT_SECRET }}
        run: python scripts/smoke_test.py
```

### Step 2: Secret Configuration
```bash
# Add secrets to GitHub repository
gh secret set FOUNDRY_HOSTNAME --body "mycompany.palantirfoundry.com"
gh secret set FOUNDRY_CLIENT_ID --body "your-client-id"
gh secret set FOUNDRY_CLIENT_SECRET --body "your-client-secret"
```

### Step 3: Custom Linting Rules for Foundry
```python
# scripts/lint_foundry.py — catch common Foundry mistakes
import ast, sys

class FoundryLinter(ast.NodeVisitor):
    def visit_Str(self, node):
        # Flag hardcoded Foundry hostnames
        if "palantirfoundry.com" in node.s:
            print(f"  Line {node.lineno}: Hardcoded Foundry hostname — use env var")
        # Flag hardcoded RIDs
        if node.s.startswith("ri.foundry.main"):
            print(f"  Line {node.lineno}: Hardcoded RID — use config/env var")

for path in sys.argv[1:]:
    tree = ast.parse(open(path).read())
    FoundryLinter().visit(tree)
```

## Output
- GitHub Actions workflow with unit tests, linting, and integration tests
- PySpark tests running in CI with JDK setup
- Secrets configured securely in GitHub
- Custom linting for Foundry-specific patterns

## Error Handling
| CI Issue | Cause | Fix |
|----------|-------|-----|
| PySpark tests fail | No JDK | Add `setup-java` step |
| Integration test 401 | Bad secrets | Re-set `gh secret set` |
| Slow tests | Full Spark startup | Use `local[1]` master |
| Import errors | Missing deps | Pin all deps in requirements.txt |

## Resources
- [GitHub Actions](https://docs.github.com/en/actions)
- [PySpark Testing](https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html)

## Next Steps
For deployment pipelines, see `palantir-deploy-integration`.
