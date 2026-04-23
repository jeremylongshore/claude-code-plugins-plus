# Dependency Rules

The architecture is only useful if the layer graph is actually enforced. `import-linter` is a Python static analyzer that reads `pyproject.toml` and fails CI when imports cross forbidden edges. Run it on every PR.

## The Layer Graph

```
app          (FastAPI routes — HTTP boundary)
 │
 ▼
services     (chain/graph definitions)
 │
 ▼
adapters     (LLM factory, retriever factory, vendor SDKs)
 │
 ├──▶ config   (Pydantic Settings)
 │
 └──▶ domain  (pure Pydantic models, enums, typed state)
```

Rules:

1. Each layer may import the layer below it, or any layer lower.
2. No layer may import a layer above it.
3. No vendor SDK (`langchain_anthropic`, `langchain_openai`, `langchain_pinecone`, etc.) may be imported outside `adapters/`.
4. `domain/` imports nothing outside `pydantic` and the standard library. No I/O. No LangChain.
5. `config/` imports nothing from `domain`, `adapters`, `services`, or `app`.

## `import-linter` Configuration

Full config in `pyproject.toml`:

```toml
[tool.importlinter]
root_package = "my_service"

# Contract 1: strict layering
[[tool.importlinter.contracts]]
name = "Layered architecture"
type = "layers"
layers = [
    "my_service.app",
    "my_service.services",
    "my_service.adapters",
    "my_service.config",
    "my_service.domain",
]

# Contract 2: services do not import vendor SDKs directly
[[tool.importlinter.contracts]]
name = "Services go through adapters for vendors"
type = "forbidden"
source_modules = ["my_service.services"]
forbidden_modules = [
    "langchain_anthropic",
    "langchain_openai",
    "langchain_google_genai",
    "langchain_pinecone",
    "langchain_community.vectorstores",
]

# Contract 3: domain stays pure
[[tool.importlinter.contracts]]
name = "Domain has no external deps"
type = "forbidden"
source_modules = ["my_service.domain"]
forbidden_modules = [
    "langchain_core",
    "langgraph",
    "fastapi",
    "sqlalchemy",
]
ignore_imports = [
    # Allow Pydantic and typing
]

# Contract 4: app layer only imports services, not adapters
[[tool.importlinter.contracts]]
name = "Routes don't reach into adapters"
type = "forbidden"
source_modules = ["my_service.app.routes"]
forbidden_modules = [
    "my_service.adapters",
    "langchain_core",
]
```

## Run in CI

`.github/workflows/ci.yml`:

```yaml
- name: Install import-linter
  run: pip install "import-linter>=2.0"

- name: Enforce layer graph
  run: lint-imports --config pyproject.toml
```

Expected output on a clean repo:

```
$ lint-imports
=================
Import Linter
=================

Using config file: pyproject.toml

Contracts
---------
Analyzed 47 files, 123 dependencies.
-----------------------------------

Layered architecture KEPT
Services go through adapters for vendors KEPT
Domain has no external deps KEPT
Routes don't reach into adapters KEPT

Contracts: 4 kept, 0 broken.
```

Expected output when a PR violates the graph:

```
Services go through adapters for vendors BROKEN

my_service.services.support.chain is not allowed to import langchain_anthropic:
-   my_service.services.support.chain -> langchain_anthropic (l. 3)
```

## Testing Injection Boundaries

The layer graph defines **where** fakes plug in. For each adapter:

| Adapter | Fake injection pattern |
|---------|------------------------|
| `llm_factory.chat_model` | `monkeypatch.setattr` in unit tests; real client in integration |
| `retriever_factory.retriever_for` | Hand-built `FakeRetriever` from `langchain_core.retrievers`; real Pinecone in integration |
| `tool_factory.tools_for` | List of `@tool`-decorated test fns; real integrations in integration |
| `checkpointer.checkpointer_for` | `MemorySaver()` regardless of env; Postgres fixtures in integration |
| `history.history_for` | `InMemoryChatMessageHistory()` regardless of env |

Unit test example for tenant isolation (the P33 test):

```python
# tests/unit/test_retriever_factory.py
def test_tenants_do_not_share_namespace():
    r1 = retriever_for(tenant_id="acme")
    r2 = retriever_for(tenant_id="zeta")
    # Different namespaces on the underlying store
    assert r1.vectorstore._index_name == r2.vectorstore._index_name  # same index
    assert r1.vectorstore._namespace == "tenant:acme"
    assert r2.vectorstore._namespace == "tenant:zeta"
    assert r1.vectorstore._namespace != r2.vectorstore._namespace
```

A regression that binds `tenant_id` at import time fails this test because both retrievers would share the pre-bound namespace.

## What This Buys You

- A PR that adds `from langchain_anthropic import ChatAnthropic` to a route fails CI, not production
- A service module importing a vendor SDK fails CI, not production
- A domain model growing an `sqlalchemy` dep fails CI before the coupling rots everything
- Refactoring is safe: if the dependency direction is preserved, behavior is preserved
