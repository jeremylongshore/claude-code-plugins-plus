---
name: langchain-local-dev-loop
description: |
  Configure LangChain local development workflow with hot reload and testing.
  Use when setting up development environment, configuring test fixtures,
  or establishing a rapid iteration workflow for LangChain apps.
  Trigger with phrases like "langchain dev setup", "langchain local development",
  "langchain testing", "langchain development workflow".
allowed-tools: Read, Write, Edit, Bash(pytest:*), Bash(python:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# LangChain Local Dev Loop

## Overview
Configure a rapid local development workflow for LangChain applications with testing, debugging, and hot reload capabilities.

## Prerequisites
- Completed `langchain-install-auth` setup
- Python 3.9+ with virtual environment
- pytest and related testing tools
- IDE with Python support (VS Code recommended)

## Instructions

### Step 1: Set Up Project Structure
```
my-langchain-app/
├── src/
│   ├── __init__.py
│   ├── chains/
│   │   └── __init__.py
│   ├── agents/
│   │   └── __init__.py
│   └── prompts/
│       └── __init__.py
├── tests/
│   ├── __init__.py
│   ├── conftest.py
│   └── test_chains.py
├── .env
├── .env.example
├── pyproject.toml
└── README.md
```

### Step 2: Configure Testing
```python
# tests/conftest.py
import pytest
from unittest.mock import MagicMock
from langchain_core.messages import AIMessage

@pytest.fixture
def mock_llm():
    """Mock LLM for unit tests without API calls."""
    mock = MagicMock()
    mock.invoke.return_value = AIMessage(content="Mocked response")
    return mock

@pytest.fixture
def sample_prompt():
    """Sample prompt for testing."""
    from langchain_core.prompts import ChatPromptTemplate
    return ChatPromptTemplate.from_template("Test: {input}")
```

### Step 3: Create Test File
```python
# tests/test_chains.py
def test_chain_construction(mock_llm, sample_prompt):
    """Test that chain can be constructed."""
    from langchain_core.output_parsers import StrOutputParser

    chain = sample_prompt | mock_llm | StrOutputParser()
    assert chain is not None

def test_chain_invoke(mock_llm, sample_prompt):
    """Test chain invocation with mock."""
    from langchain_core.output_parsers import StrOutputParser

    chain = sample_prompt | mock_llm | StrOutputParser()
    result = chain.invoke({"input": "test"})
    assert result == "Mocked response"
```

### Step 4: Set Up Development Tools
```toml
# pyproject.toml
[project]
name = "my-langchain-app"
version = "0.1.0"
requires-python = ">=3.9"
dependencies = [
    "langchain>=0.3.0",
    "langchain-openai>=0.2.0",
    "python-dotenv>=1.0.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0.0",
    "pytest-asyncio>=0.23.0",
    "pytest-cov>=4.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]

[tool.pytest.ini_options]
asyncio_mode = "auto"
testpaths = ["tests"]

[tool.ruff]
line-length = 100
```

## Output
- Organized project structure with separation of concerns
- pytest configuration with fixtures for mocking LLMs
- Development dependencies configured
- Ready for rapid iteration

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| Import Error | Missing package | Install with `pip install -e ".[dev]"` |
| Fixture Not Found | conftest.py issue | Ensure conftest.py is in tests/ directory |
| Async Test Error | Missing marker | Add `@pytest.mark.asyncio` decorator |
| Env Var Missing | .env not loaded | Use `python-dotenv` and load_dotenv() |

## Examples

### Running Tests
```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=src --cov-report=html

# Run specific test
pytest tests/test_chains.py::test_chain_invoke -v

# Watch mode (requires pytest-watch)
ptw
```

### Integration Test Example
```python
# tests/test_integration.py
import pytest
from dotenv import load_dotenv

load_dotenv()

@pytest.mark.integration
def test_real_llm_call():
    """Integration test with real LLM (requires API key)."""
    from langchain_openai import ChatOpenAI

    llm = ChatOpenAI(model="gpt-4o-mini", temperature=0)
    response = llm.invoke("Say 'test passed'")
    assert "test" in response.content.lower()
```

## Resources
- [pytest Documentation](https://docs.pytest.org/)
- [LangChain Testing Guide](https://python.langchain.com/docs/contributing/testing)
- [python-dotenv](https://pypi.org/project/python-dotenv/)

## Next Steps
Proceed to `langchain-sdk-patterns` for production-ready code patterns.