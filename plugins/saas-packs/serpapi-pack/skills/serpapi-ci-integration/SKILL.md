---
name: serpapi-ci-integration
description: |
  Set up CI/CD for SerpApi integrations with fixture-based testing.
  Use when automating SerpApi tests without consuming credits,
  or validating search result parsing in CI.
  Trigger: "serpapi CI", "serpapi GitHub Actions", "serpapi automated tests".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, search, seo, serpapi]
compatible-with: claude-code
---

# SerpApi CI Integration

## Overview

CI for SerpApi should use fixture-based tests (no API credits consumed) for PRs, with optional live integration tests on main branch only.

## Instructions

### Step 1: GitHub Actions Workflow

```yaml
name: SerpApi Tests
on: [push, pull_request]

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install serpapi pytest
      - run: pytest tests/ -v  # Uses fixtures, no API key needed

  integration:
    runs-on: ubuntu-latest
    if: github.ref == 'refs/heads/main'
    env:
      SERPAPI_API_KEY: ${{ secrets.SERPAPI_API_KEY }}
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.12' }
      - run: pip install serpapi pytest
      - run: pytest tests/integration/ -v --timeout=30
```

### Step 2: Fixture-Based Unit Tests

```python
# tests/test_search_parser.py
import json, pytest

def load_fixture(name):
    with open(f"tests/fixtures/{name}.json") as f:
        return json.load(f)

def test_parse_organic_results():
    result = load_fixture("google_python_tutorial")
    assert "organic_results" in result
    assert len(result["organic_results"]) > 0
    assert result["organic_results"][0]["title"]

def test_parse_youtube_results():
    result = load_fixture("youtube_react_hooks")
    assert "video_results" in result
    assert result["video_results"][0]["length"]

def test_handle_no_results():
    result = load_fixture("google_no_results")
    assert result.get("organic_results", []) == []
```

### Step 3: Live Integration Test (Controlled)

```python
# tests/integration/test_serpapi_live.py
import serpapi, os, pytest

@pytest.fixture
def client():
    key = os.environ.get("SERPAPI_API_KEY")
    if not key:
        pytest.skip("SERPAPI_API_KEY not set")
    return serpapi.Client(api_key=key)

def test_account_has_credits(client):
    account = client.account()
    assert account["plan_searches_left"] > 0

def test_google_search_returns_results(client):
    result = client.search(engine="google", q="python", num=1)
    assert result["search_metadata"]["status"] == "Success"
    assert len(result["organic_results"]) > 0
```

## Error Handling

| CI Issue | Cause | Solution |
|----------|-------|----------|
| Fixture not found | Missing test data | Record fixtures with `record_fixture()` |
| Integration test uses credits | Tests on every PR | Only run on `main` branch |
| Flaky results | Search results change | Use fixtures for deterministic tests |

## Resources

- [SerpApi Playground](https://serpapi.com/playground)
- [pytest Docs](https://docs.pytest.org/)

## Next Steps

For deployment patterns, see `serpapi-deploy-integration`.
