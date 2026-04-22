# LLM Factory Pattern

The `adapters/llm_factory.py` module is the single source of version-safe defaults. Every chain in `services/` depends on the `BaseChatModel` **protocol**, not on `ChatAnthropic` or `ChatOpenAI` directly.

## Why a Factory

Without one, `max_retries=6` (the `ChatOpenAI` default) leaks into four call sites. Timeouts are missing on three of the four because the author forgot. Swapping providers requires a grep-and-replace. Unit tests spin up real API clients.

With one:

- Safe defaults (`timeout=30`, `max_retries=2`) live in exactly one file
- Services take `BaseChatModel` as a constructor arg — test fakes and prod clients are interchangeable
- Adding a provider is one branch in one file

## Minimal Factory

```python
# src/my_service/adapters/llm_factory.py
from typing import Any
from langchain_core.language_models import BaseChatModel
from langchain_anthropic import ChatAnthropic
from langchain_openai import ChatOpenAI

_SAFE_DEFAULTS: dict[str, Any] = {
    "timeout": 30,         # seconds; default None hangs forever on provider stall
    "max_retries": 2,      # retries, not attempts — see pain catalog P30
}

_MODELS: dict[str, str] = {
    "anthropic": "claude-sonnet-4-6",
    "openai": "gpt-4o",
    "gemini": "gemini-2.5-pro",
}

def chat_model(provider: str, **overrides: Any) -> BaseChatModel:
    defaults = {**_SAFE_DEFAULTS, **overrides}  # caller's kwargs win
    model = defaults.pop("model", _MODELS.get(provider))
    if model is None:
        raise ValueError(f"No default model for provider {provider!r}")

    if provider == "anthropic":
        return ChatAnthropic(model=model, **defaults)
    if provider == "openai":
        return ChatOpenAI(model=model, **defaults)
    if provider == "gemini":
        from langchain_google_genai import ChatGoogleGenerativeAI
        return ChatGoogleGenerativeAI(model=model, **defaults)
    raise ValueError(f"Unknown provider: {provider!r}")
```

## Per-Provider Variants

Some providers need extra config that does not fit `_SAFE_DEFAULTS`:

```python
def _anthropic(**kw) -> BaseChatModel:
    return ChatAnthropic(
        model=kw.pop("model", "claude-sonnet-4-6"),
        default_headers={"anthropic-beta": "tools-2024-05-16"} if kw.pop("beta_tools", False) else None,
        **kw,
    )

def _openai(**kw) -> BaseChatModel:
    return ChatOpenAI(
        model=kw.pop("model", "gpt-4o"),
        # OpenAI-specific: response_format requires json_schema method
        **kw,
    )
```

The factory dispatcher calls `_anthropic` / `_openai` — services still only see `BaseChatModel`.

## Caching

For stateless chat models, caching the instance is safe and saves the per-request construction cost:

```python
from functools import lru_cache

@lru_cache(maxsize=16)  # keyed by provider + frozen kwargs
def _cached(provider: str, frozen: frozenset) -> BaseChatModel:
    return chat_model(provider, **dict(frozen))

def chat_model_cached(provider: str, **kw) -> BaseChatModel:
    return _cached(provider, frozenset(kw.items()))
```

Do **not** cache retrievers this way — they need per-tenant keys, which is why the retriever factory is separate (see SKILL.md Step 4 and P33).

## Service Consumption

Chains take `BaseChatModel`, never `ChatAnthropic`:

```python
# src/my_service/services/support/chain.py
from langchain_core.language_models import BaseChatModel
from langchain_core.prompts import ChatPromptTemplate

def build_support_agent_with_llm(llm: BaseChatModel):
    prompt = ChatPromptTemplate.from_messages([
        ("system", "You are a support agent."),
        ("human", "{input}"),
    ])
    return prompt | llm
```

Construction wiring:

```python
# src/my_service/services/support/chain.py (registration wrapper)
from my_service.adapters.llm_factory import chat_model
from my_service.services.registry import register

@register("support_agent")
def build(*, tenant_id: str):
    return build_support_agent_with_llm(chat_model("anthropic"))
```

## Test Injection

Unit tests bypass `chat_model` via `monkeypatch`:

```python
from langchain_core.language_models.fake_chat_models import FakeListChatModel

def test_agent_calls_llm_once(monkeypatch):
    fake = FakeListChatModel(responses=["ok"])
    monkeypatch.setattr(
        "my_service.services.support.chain.chat_model",
        lambda provider, **kw: fake,
    )
    # ... exercise chain, assert on fake.invocations ...
```

Because the service imports `chat_model` by name, not the concrete class, this one-line patch replaces the entire LLM boundary. No `responses`-mock HTTP matcher required.

## Relation to `langchain-model-inference`

This pattern's version-safe defaults (`timeout=30`, `max_retries=2`), the `BaseChatModel` protocol-first design, and the provider-dispatch factory come straight from the sibling skill `langchain-model-inference` Step 3. This skill's contribution is treating that factory as the **architectural seam** between layers — the single place vendor SDKs are imported.
