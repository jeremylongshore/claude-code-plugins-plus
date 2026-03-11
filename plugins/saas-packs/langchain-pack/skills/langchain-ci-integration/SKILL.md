---
name: langchain-ci-integration
description: |
  Configure LangChain CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating LangChain tests into your build process.
  Trigger with phrases like "langchain CI", "langchain GitHub Actions",
  "langchain automated tests", "CI langchain", "langchain pipeline".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# LangChain CI Integration

## Overview
Integrate LangChain chain and agent testing into CI/CD pipelines. Covers chain unit tests with mocked LLMs, RAG pipeline validation, agent tool testing, and integration tests with real LLM calls gated behind environment flags.

## Prerequisites
- LangChain installed (`langchain`, `langchain-openai`)
- GitHub Actions configured
- pytest for Python or Vitest for TypeScript
- LLM API keys stored as GitHub secrets

## Instructions

### Step 1: CI Workflow with Mocked and Live Tests
```yaml
# .github/workflows/langchain-tests.yml
name: LangChain Tests

on:
  pull_request:
    paths:
      - 'src/chains/**'
      - 'src/agents/**'
      - 'src/tools/**'
      - 'tests/**'

jobs:
  unit-tests:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run unit tests (no API calls)
        run: pytest tests/unit/ -v --tb=short

  integration-tests:
    runs-on: ubuntu-latest
    if: github.event.pull_request.draft == false
    steps:
      - uses: actions/checkout@v4
      - uses: actions/setup-python@v5
        with: { python-version: '3.11' }
      - run: pip install -r requirements.txt -r requirements-dev.txt

      - name: Run integration tests (with LLM calls)
        env:
          OPENAI_API_KEY: ${{ secrets.OPENAI_API_KEY }}
          LANGCHAIN_TRACING_V2: "true"
          LANGCHAIN_API_KEY: ${{ secrets.LANGCHAIN_API_KEY }}
        run: pytest tests/integration/ -v --tb=short -m "not slow"
```

### Step 2: Chain Unit Tests with Mocked LLM
```python
# tests/unit/test_chains.py
import pytest
from unittest.mock import AsyncMock, patch
from langchain_core.messages import AIMessage

from src.chains.summarize import create_summarize_chain

@pytest.fixture
def mock_llm():
    mock = AsyncMock()
    mock.ainvoke.return_value = AIMessage(content="This is a summary of the document.")
    return mock

def test_summarize_chain_output_format(mock_llm):
    """Test chain produces expected output structure."""
    chain = create_summarize_chain(llm=mock_llm)
    result = chain.invoke({"document": "Long document text here..."})

    assert "summary" in result
    assert len(result["summary"]) > 0

def test_summarize_chain_handles_empty_input(mock_llm):
    """Test chain handles edge cases."""
    chain = create_summarize_chain(llm=mock_llm)

    with pytest.raises(ValueError, match="Document cannot be empty"):
        chain.invoke({"document": ""})

@patch("src.chains.summarize.ChatOpenAI")
def test_chain_uses_correct_model(mock_chat):
    """Test chain configures model correctly."""
    mock_chat.return_value = AsyncMock()
    chain = create_summarize_chain(model_name="gpt-4o-mini")

    mock_chat.assert_called_once_with(model="gpt-4o-mini", temperature=0)
```

### Step 3: RAG Pipeline Validation
```python
# tests/integration/test_rag_pipeline.py
import pytest
from langchain_openai import OpenAIEmbeddings
from langchain_community.vectorstores import FAISS

from src.chains.rag import create_rag_chain

@pytest.fixture(scope="session")
def vector_store():
    """Create test vector store with known documents."""
    embeddings = OpenAIEmbeddings(model="text-embedding-3-small")
    texts = [
        "Python was created by Guido van Rossum in 1991.",
        "TypeScript was developed by Microsoft and released in 2012.",
        "Rust was first released in 2010 by Mozilla.",
    ]
    return FAISS.from_texts(texts, embeddings)

@pytest.mark.integration
def test_rag_retrieval_relevance(vector_store):
    """Test RAG pipeline retrieves relevant documents."""
    chain = create_rag_chain(vector_store)
    result = chain.invoke({"question": "Who created Python?"})

    assert "guido" in result["answer"].lower()
    assert len(result["source_documents"]) > 0

@pytest.mark.integration
def test_rag_no_hallucination(vector_store):
    """Test RAG doesn't hallucinate when answer not in context."""
    chain = create_rag_chain(vector_store)
    result = chain.invoke({"question": "What is the capital of France?"})

    # Should indicate it doesn't know from the context
    assert any(phrase in result["answer"].lower()
               for phrase in ["don't have", "not in", "cannot find", "no information"])
```

### Step 4: Agent Tool Testing
```python
# tests/unit/test_tools.py
import pytest
from src.tools.calculator import calculator_tool
from src.tools.search import search_tool

def test_calculator_tool():
    """Test calculator tool produces correct results."""
    result = calculator_tool.invoke({"expression": "2 + 2"})
    assert result == "4"

def test_calculator_tool_handles_invalid_input():
    """Test tool handles bad input gracefully."""
    result = calculator_tool.invoke({"expression": "not math"})
    assert "error" in result.lower()

@pytest.mark.integration
def test_search_tool_returns_results():
    """Test search tool (requires API key)."""
    result = search_tool.invoke({"query": "LangChain framework"})
    assert len(result) > 0
```

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Unit tests call real API | Mock not applied | Use `@patch` or dependency injection |
| Integration test fails | Missing API key | Gate behind `if` condition and secrets |
| Flaky RAG tests | Embedding variability | Use deterministic test data, pin embeddings |
| Agent test timeout | Tool execution slow | Set timeout on agent, mock external tools |

## Examples

### Quick Chain Smoke Test
```python
# Minimal test that chain constructs correctly
def test_chain_builds():
    from src.chains.summarize import create_summarize_chain
    chain = create_summarize_chain()
    assert chain is not None
    assert hasattr(chain, 'invoke')
```

## Resources
- [LangChain Testing Guide](https://python.langchain.com/docs/contributing/testing)
- [LangSmith Tracing](https://docs.smith.langchain.com/)
- [LangChain CI Examples](https://github.com/langchain-ai/langchain/tree/master/.github)
