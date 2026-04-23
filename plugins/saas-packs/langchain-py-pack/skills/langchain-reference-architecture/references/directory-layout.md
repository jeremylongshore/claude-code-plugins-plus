# Directory Layout

The target tree for a LangChain 1.0 / LangGraph 1.0 service. Five layers, strict downward dependency, tests mirror the production tree.

## Full Tree

```
my_service/
├── src/
│   └── my_service/
│       ├── __init__.py
│       │
│       ├── app/                              # Layer 1 — HTTP boundary
│       │   ├── __init__.py
│       │   ├── main.py                       # FastAPI() instance, lifespan, routers
│       │   ├── deps.py                       # FastAPI Depends() providers
│       │   ├── middleware.py                 # HTTP middleware (auth, request_id)
│       │   └── routes/
│       │       ├── __init__.py
│       │       ├── health.py                 # GET /healthz, /readyz
│       │       ├── support.py                # POST /support
│       │       └── triage.py                 # POST /triage
│       │
│       ├── services/                         # Layer 2 — chains and graphs
│       │   ├── __init__.py                   # imports each service to register it
│       │   ├── registry.py                   # @register / get(name, tenant=...)
│       │   ├── support/
│       │   │   ├── __init__.py
│       │   │   ├── chain.py                  # LCEL pipeline
│       │   │   └── graph.py                  # LangGraph StateGraph
│       │   └── triage/
│       │       ├── __init__.py
│       │       └── chain.py
│       │
│       ├── adapters/                         # Layer 3 — vendor integrations
│       │   ├── __init__.py
│       │   ├── llm_factory.py                # chat_model(provider, **kw)
│       │   ├── retriever_factory.py          # retriever_for(tenant_id=...)
│       │   ├── tool_factory.py               # tools_for(tenant_id=...)
│       │   ├── checkpointer.py               # checkpointer_for(env=...)
│       │   ├── history.py                    # history_for(session_id, tenant_id)
│       │   ├── middleware.py                 # LangChain middleware stack
│       │   └── telemetry.py                  # LangSmith / OTEL bootstrap
│       │
│       ├── config/                           # Layer 4 — configuration
│       │   ├── __init__.py
│       │   └── settings.py                   # Pydantic Settings class
│       │
│       └── domain/                           # Layer 5 — pure models
│           ├── __init__.py
│           ├── state.py                      # LangGraph TypedDict state
│           ├── models.py                     # request/response Pydantic models
│           └── enums.py
│
├── tests/
│   ├── unit/
│   │   ├── test_support_chain.py             # injects FakeListChatModel
│   │   └── test_retriever_factory.py         # asserts tenant isolation
│   ├── integration/
│   │   ├── test_postgres_checkpointer.py     # ephemeral PG
│   │   └── test_pinecone_namespace.py        # sandbox namespace
│   └── contract/
│       └── test_tool_schemas.py              # snapshots bind_tools JSON
│
├── .env.example                              # template; never commit real .env
├── pyproject.toml                            # [tool.importlinter] contracts here
├── README.md
└── Dockerfile
```

## File-Naming Conventions

| Pattern | Meaning | Example |
|---------|---------|---------|
| `*_factory.py` | Adapter that constructs a vendor-bound object per request or per env | `retriever_factory.py` |
| `*/chain.py` | LCEL (`Runnable`) composition | `services/support/chain.py` |
| `*/graph.py` | LangGraph `StateGraph` | `services/support/graph.py` |
| `registry.py` | Name → builder lookup inside a layer | `services/registry.py` |
| `settings.py` | Exactly one Pydantic `BaseSettings` subclass | `config/settings.py` |
| `state.py` | TypedDict or Pydantic model for LangGraph state | `domain/state.py` |
| `deps.py` | FastAPI `Depends()` providers only | `app/deps.py` |

## Where Each SKILL Component Lives

| Component from SKILL.md Step | File |
|------------------------------|------|
| LLM factory (Step 2) | `adapters/llm_factory.py` |
| Chain/graph registry (Step 3) | `services/registry.py` |
| Retriever factory (Step 4) | `adapters/retriever_factory.py` |
| Tool factory (Step 4) | `adapters/tool_factory.py` |
| Pydantic `Settings` (Step 5) | `config/settings.py` |
| Middleware stack (Step 6) | `adapters/middleware.py` |
| Checkpointer selection (Step 7) | `adapters/checkpointer.py` |
| Chat history selection (Step 7) | `adapters/history.py` |
| Fakes and injection points (Step 8) | `tests/unit/conftest.py` |
| `import-linter` contracts (Step 9) | `pyproject.toml` |

## Depth Discipline

Typical production depth is 5 layers from route to domain model:

```
app.routes.support.run
  -> services.registry.get
    -> services.support.chain.build_support_agent
      -> adapters.llm_factory.chat_model
        -> langchain_anthropic.ChatAnthropic  # only here
```

If a stack trace shows a 7th frame inside `langchain_*` called from inside `app/`, the layer boundary was violated. Import-linter (Step 9 in SKILL.md) catches this at PR time, not at incident time.
