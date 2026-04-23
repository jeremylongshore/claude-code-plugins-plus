# Fake Model Fixtures Reference

Deterministic, network-free stand-ins for chat models, completion LLMs,
embedders, retrievers, and agents. Copy-paste ready. Pinned to
`langchain-core 1.0.x`.

## The three stock fakes

| Class | Module | Emits |
|-------|--------|-------|
| `FakeListChatModel` | `langchain_core.language_models.fake` | `AIMessage(content=str)` cycled from `responses=[...]` |
| `FakeListLLM` | `langchain_core.language_models.fake` | `str` cycled from `responses=[...]` |
| `FakeStreamingListLLM` | `langchain_core.language_models.fake` | Streaming `str` chunks |

All three implement `Runnable` — they slot directly into LCEL `prompt | model`
chains without any adapter.

## Chat model fake with `response_metadata` (P43 fix)

The stock `FakeListChatModel` does **not** emit `response_metadata["token_usage"]`.
Downstream callbacks that log cost or enforce budgets crash with `KeyError`.
Subclass and synthesize the metadata instead of mocking the callback:

```python
# tests/fakes.py
from langchain_core.language_models.fake import FakeListChatModel
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.messages import AIMessage


class FakeChatWithUsage(FakeListChatModel):
    """FakeListChatModel that synthesizes response_metadata and usage_metadata
    so downstream callbacks reading token usage do not KeyError under test.

    Token counts are approximations: input=10, output=len(response.split()).
    Override in a subclass if your assertion surface is the exact count.
    """

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        response = self.responses[self.i % len(self.responses)]
        self.i += 1
        out_tokens = max(1, len(response.split()))
        message = AIMessage(
            content=response,
            response_metadata={
                "token_usage": {
                    "input_tokens": 10,
                    "output_tokens": out_tokens,
                    "total_tokens": 10 + out_tokens,
                },
                "model_name": "fake-chat",
                "finish_reason": "stop",
            },
            usage_metadata={
                "input_tokens": 10,
                "output_tokens": out_tokens,
                "total_tokens": 10 + out_tokens,
            },
        )
        return ChatResult(generations=[ChatGeneration(message=message)])
```

### When to use which

| Chain surface under test | Fake to use |
|--------------------------|-------------|
| Prompt → model → parser (output-only assertion) | `FakeListChatModel` |
| Prompt → model → callback that reads `response_metadata` | `FakeChatWithUsage` |
| Streaming endpoint, counting chunks | `FakeStreamingListLLM` (wrap as chat if needed) |
| Legacy `LLMChain` / completion-style | `FakeListLLM` |

## Agent fake — canned tool calls

`create_tool_calling_agent` expects the model to emit `tool_calls` on the
`AIMessage`. The stock fakes do not. Subclass to emit tool calls:

```python
from langchain_core.messages import AIMessage
from langchain_core.outputs import ChatGeneration, ChatResult
from langchain_core.language_models.fake import FakeListChatModel


class FakeAgentModel(FakeListChatModel):
    """Emits one tool call per `responses` entry when entry is a dict;
    plain strings are treated as final text responses."""

    def _generate(self, messages, stop=None, run_manager=None, **kwargs):
        item = self.responses[self.i % len(self.responses)]
        self.i += 1
        if isinstance(item, dict):
            # item = {"tool": "search", "args": {"q": "..."}}
            msg = AIMessage(
                content="",
                tool_calls=[{
                    "name": item["tool"],
                    "args": item["args"],
                    "id": f"call_{self.i}",
                }],
            )
        else:
            msg = AIMessage(content=item)
        return ChatResult(generations=[ChatGeneration(message=msg)])
```

Usage:

```python
fake = FakeAgentModel(responses=[
    {"tool": "search", "args": {"q": "weather"}},
    "The weather is 72°F.",
])
```

## Retriever fake

```python
from langchain_core.retrievers import BaseRetriever
from langchain_core.documents import Document
from typing import List


class FakeRetriever(BaseRetriever):
    docs: List[Document] = []

    def _get_relevant_documents(self, query, *, run_manager):
        return list(self.docs)


# In conftest.py:
import pytest

@pytest.fixture
def fake_retriever():
    return FakeRetriever(docs=[
        Document(page_content="doc 1 content", metadata={"source": "a.md"}),
        Document(page_content="doc 2 content", metadata={"source": "b.md"}),
    ])
```

## Embedder fake

```python
from langchain_core.embeddings import Embeddings
import hashlib


class FakeEmbeddings(Embeddings):
    """Stable, deterministic embeddings derived from a hash of the text.
    Same text → same vector every run. Not useful for similarity semantics;
    use only for plumbing tests."""

    def __init__(self, dims: int = 384):
        self.dims = dims

    def _vec(self, text: str):
        h = hashlib.sha256(text.encode()).digest()
        return [(h[i % len(h)] / 255.0) for i in range(self.dims)]

    def embed_documents(self, texts):
        return [self._vec(t) for t in texts]

    def embed_query(self, text):
        return self._vec(text)
```

## Per-test response override pattern

Fixtures return a fake with a default response list; tests override via
attribute assignment. This avoids re-building the chain per test:

```python
def test_short_answer(summarize_chain, fake_chat):
    fake_chat.responses = ["short"]
    assert summarize_chain.invoke({"text": "long"}).content == "short"

def test_long_answer(summarize_chain, fake_chat):
    fake_chat.responses = ["a much longer summary here"]
    assert "summary" in summarize_chain.invoke({"text": "long"}).content
```

## Reset between tests

`FakeListChatModel.i` is an instance counter — it survives across test
invocations on a session-scoped fixture. Either use function-scoped fixtures
(default) or reset explicitly:

```python
@pytest.fixture(autouse=True)
def _reset_fake(fake_chat):
    fake_chat.i = 0
    yield
```
