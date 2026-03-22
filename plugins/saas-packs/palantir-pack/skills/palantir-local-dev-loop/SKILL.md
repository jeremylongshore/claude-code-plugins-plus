---
name: palantir-local-dev-loop
description: |
  Configure Palantir Foundry local development with Python transforms and testing.
  Use when setting up a development environment, running transforms locally,
  or establishing a fast iteration cycle with Foundry.
  Trigger with phrases like "palantir dev setup", "palantir local development",
  "foundry local dev", "develop with palantir".
allowed-tools: Read, Write, Edit, Bash(pip:*), Bash(npm:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, development, testing]
compatible-with: claude-code, codex, openclaw
---

# Palantir Local Dev Loop

## Overview
Set up local development for Palantir Foundry integrations. Covers running transforms locally against sample data, mocking the Foundry API for fast iteration, and testing with pytest before pushing to Foundry.

## Prerequisites
- Completed `palantir-install-auth` setup
- Python 3.9+ with pip
- A Foundry Code Repository cloned locally (or a standalone project)

## Instructions

### Step 1: Project Structure
```
my-foundry-project/
├── src/myproject/
│   ├── __init__.py
│   ├── pipeline.py          # @transform functions
│   └── utils.py             # Shared logic
├── tests/
│   ├── conftest.py           # Fixtures with sample DataFrames
│   ├── test_pipeline.py      # Transform unit tests
│   └── sample_data/          # CSV/Parquet test fixtures
├── .env                      # FOUNDRY_HOSTNAME, FOUNDRY_TOKEN
├── requirements.txt          # foundry-platform-sdk, pytest, pyspark
└── pyproject.toml
```

### Step 2: Install Local Dependencies
```bash
set -euo pipefail
pip install foundry-platform-sdk pyspark pytest pandas
python -c "import foundry; import pyspark; print('Dependencies ready')"
```

### Step 3: Test Transforms Locally with PySpark
```python
# tests/conftest.py
import pytest
from pyspark.sql import SparkSession

@pytest.fixture(scope="session")
def spark():
    return SparkSession.builder.master("local[2]").appName("test").getOrCreate()

@pytest.fixture
def sample_orders(spark):
    data = [
        ("ORD-001", "alice@company.com", "2026-03-01", 99.99),
        ("ORD-002", "bob@test.com", "2026-03-02", 49.99),      # test email
        (None, "carol@company.com", "2026-03-03", 149.99),       # null ID
    ]
    return spark.createDataFrame(data, ["order_id", "email", "order_date_str", "total"])
```

```python
# tests/test_pipeline.py
from myproject.pipeline import clean_orders

def test_clean_orders_removes_nulls_and_test_emails(sample_orders):
    result = clean_orders(sample_orders)
    assert result.count() == 1  # Only alice remains
    assert result.columns == ["order_id", "email", "order_date", "total_cents"]
    row = result.first()
    assert row.total_cents == 9999  # 99.99 * 100
```

### Step 4: Mock Foundry API for Integration Tests
```python
# tests/test_api.py
import pytest
from unittest.mock import MagicMock, patch

def test_list_ontology_objects():
    mock_client = MagicMock()
    mock_client.ontologies.OntologyObject.list.return_value.data = [
        MagicMock(properties={"fullName": "Alice", "department": "Engineering"}),
    ]

    result = mock_client.ontologies.OntologyObject.list(
        ontology="test", object_type="Employee", page_size=10
    )
    assert len(result.data) == 1
    assert result.data[0].properties["fullName"] == "Alice"
```

### Step 5: Run Tests
```bash
set -euo pipefail
pytest tests/ -v --tb=short
# Expected: all tests pass against local Spark + mocked API
```

### Step 6: Live API Smoke Test (Optional)
```python
# scripts/smoke_test.py — runs against real Foundry (needs credentials)
import os, foundry, sys

client = foundry.FoundryClient(
    auth=foundry.UserTokenAuth(
        hostname=os.environ["FOUNDRY_HOSTNAME"],
        token=os.environ["FOUNDRY_TOKEN"],
    ),
    hostname=os.environ["FOUNDRY_HOSTNAME"],
)

try:
    ontologies = list(client.ontologies.Ontology.list())
    print(f"Smoke test passed: {len(ontologies)} ontologies accessible")
except foundry.ApiError as e:
    print(f"Smoke test failed: {e.status_code} {e.message}", file=sys.stderr)
    sys.exit(1)
```

## Output
- Local PySpark environment for testing transforms without Foundry
- Mocked Foundry API client for integration tests
- pytest suite validating pipeline logic
- Optional live smoke test for credential verification

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `Java not found` (PySpark) | JDK not installed | Install JDK 11+: `apt install openjdk-11-jdk` |
| `ModuleNotFoundError: pyspark` | Missing dependency | `pip install pyspark` |
| Import error on transform functions | Circular imports | Keep transforms in separate modules |
| Spark `AnalysisException` | Column name mismatch | Print `df.columns` in test to debug |

## Examples

### Watch Mode with pytest-watch
```bash
pip install pytest-watch
ptw tests/ -- -v --tb=short
# Re-runs tests on every file save
```

## Resources
- [Foundry Local Development](https://www.palantir.com/docs/foundry/transforms-python/local-development)
- [Code Examples](https://www.palantir.com/docs/foundry/code-examples/foundry-apis-local-environment)
- [PySpark Testing](https://spark.apache.org/docs/latest/api/python/getting_started/testing_pyspark.html)

## Next Steps
- Apply SDK patterns: `palantir-sdk-patterns`
- Build data pipelines: `palantir-core-workflow-a`
