---
title: "Python Class Identity Mismatch: The CI Bug That Broke 9 PRs"
description: "How a subtle Python import path difference caused isinstance() to fail on perfectly valid objects, and the systematic approach to diagnose and fix it."
date: "2025-12-12"
tags: ["python", "ci-cd", "debugging", "testing", "devops", "adk", "google-cloud"]
featured: false
---
## The Problem: CI Failing Everywhere

Picture this: You have 9 open pull requests, all failing CI with the same cryptic error. The test assertions show objects that *look* correct but fail `isinstance()` checks.

```python
AssertionError: PipelineResult(...) is not an instance of <class 'agents.shared_contracts.PipelineResult'>
```

The object has every field. The data is correct. But Python says it's not the right type.

## Root Cause: Class Identity Mismatch

Python determines class identity by the module path where the class was defined. When you import the same class via different paths:

```python
# In orchestrator.py
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_contracts import PipelineResult  # Module: shared_contracts

# In test_swe_pipeline.py
from agents.shared_contracts import PipelineResult  # Module: agents.shared_contracts
```

These create **two different class objects** in Python's memory. Even though they have identical code, `isinstance()` sees them as different types.

## The Systematic Diagnosis

### Step 1: Reproduce Locally

```bash
source .venv/bin/activate
pytest tests/test_swe_pipeline.py -v
```

The tests failed with the same error as CI.

### Step 2: Trace the Import Paths

Looking at the error message closely:

- Expected: `<class 'agents.shared_contracts.PipelineResult'>`
- Got: `PipelineResult(...)` (from a different module path)

This pointed to import path inconsistency.

### Step 3: Audit All Imports

Found the orchestrator using `sys.path` manipulation:

```python
# BAD: Relative path manipulation
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_contracts import PipelineResult
```

While tests used absolute imports:

```python
# GOOD: Absolute import path
from agents.shared_contracts import PipelineResult
```

## The Fix

Standardize all imports to use absolute paths:

```python
# BEFORE (broken)
sys.path.insert(0, str(Path(__file__).parent.parent))
from shared_contracts import PipelineResult
from utils.logging import get_logger

# AFTER (working)
_agents_dir = str(Path(__file__).parent.parent.parent)
if _agents_dir not in sys.path:
    sys.path.insert(0, _agents_dir)

from agents.shared_contracts import PipelineResult
from agents.utils.logging import get_logger
```

## Additional Fixes Required

The import fix revealed cascading issues:

1. **Module exports mismatch** - `iam_issue/__init__.py` was exporting `create_agent` but the actual function was `get_agent`

2. **Test function signatures** - Tests calling `iam_fix_plan_create()` without the required `max_fixes` parameter

3. **CI workflow paths** - The CI was linting `my_agent/` which didn't exist (should be `agents/`)

## Results

After the fixes:

- ✅ 197 unit tests passing
- ✅ All ARV department checks green
- ✅ CI pipeline fully operational
- ✅ All 9 PRs now pass CI

## Key Takeaways

### 1. Be Ruthless About Import Consistency

Pick ONE import style for your project and enforce it everywhere:

- Either always use absolute imports (`from mypackage.module import Class`)
- Or always use relative imports (`from .module import Class`)

Never mix `sys.path` manipulation with standard imports.

### 2. The Fix is Often Embarrassingly Simple

What looked like a complex type system bug was just inconsistent import paths. The actual code change was minimal once diagnosed.

### 3. CI Failures Are Your Friend

9 failing PRs forced me to fix a latent bug that would have caused production issues. The CI was doing its job.

### 4. Check ARV Scripts Too

The ARV (Agent Readiness Verification) check was also looking for the old import pattern. Updated it to accept both patterns:

```python
has_logging_import = (
    "from utils.logging import" in content or
    "from agents.utils.logging import" in content
)
```

## Architecture Context

This fix was part of the Bob's Brain v1.0.0 release - a production-grade ADK agent department with:

- 10 agents (1 orchestrator + 1 foreman + 8 specialists)
- 233+ documents following the 6767 filing system
- 197 tests with full coverage
- 8 Hard Mode rules (R1-R8) enforced via CI/CD

The class identity issue was blocking the final release PR.

## Code References

- Orchestrator fix: `agents/iam_senior_adk_devops_lead/orchestrator.py`
- Test fix: `tests/test_swe_pipeline.py`
- ARV check: `scripts/check_arv_minimum.py`
- CI workflow: `.github/workflows/ci.yml`

*When isinstance() lies to you, check your import paths first.*
