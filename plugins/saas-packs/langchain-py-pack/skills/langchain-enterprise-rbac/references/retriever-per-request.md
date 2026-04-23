# Retriever-per-request Factory Pattern

The canonical fix for **P33** (per-tenant vector stores leak if retriever bound at process start). Every tenant-scoped retrieval path in LangChain 1.0 / LangGraph 1.0 should follow this pattern.

## Why not at import time

A module-scope `RETRIEVER = vectorstore.as_retriever(...)` captures whatever filter / namespace / collection is in scope when the module first loads. That value is **cached for the process lifetime**. The retriever has no awareness of `RunnableConfig.configurable["tenant_id"]` and no reason to re-read it — it is a plain object with pre-baked state.

Result: every tenant gets the same retrieval. The first tenant onboarded wins; everyone else leaks into their namespace. P33 is triggered by the pattern, not by any specific vector store, so it applies equally to Pinecone, Chroma, PGVector, and FAISS.

## The factory

```python
from typing import Callable
from langchain_core.retrievers import BaseRetriever
from langchain_core.runnables import RunnableConfig, RunnableLambda

def make_retriever_factory(
    build: Callable[[str], BaseRetriever],
) -> Callable[[RunnableConfig], BaseRetriever]:
    """Returns a function that builds a retriever per-request from config.

    The `build` argument is the store-specific constructor. Keep this
    factory generic so the caller chooses their store.
    """
    def factory(config: RunnableConfig) -> BaseRetriever:
        try:
            tenant_id = config["configurable"]["tenant_id"]
        except KeyError as exc:
            raise PermissionError("tenant_id missing from RunnableConfig") from exc
        if not tenant_id or not isinstance(tenant_id, str):
            raise PermissionError(f"invalid tenant_id: {tenant_id!r}")
        return build(tenant_id)
    return factory
```

`PermissionError` on missing tenant — never `KeyError`, never a silent default. A caller that forgets to pass `configurable` must fail loudly.

## Store-specific `build` functions

### Pinecone (namespace-per-tenant)

```python
from langchain_pinecone import PineconeVectorStore

def build_pinecone(tenant_id: str) -> BaseRetriever:
    store = PineconeVectorStore(
        index_name="rag",
        namespace=tenant_id,
        embedding=emb,
    )
    # Defense in depth — also filter on metadata in case namespace config
    # drifts or a write path forgot to set namespace.
    return store.as_retriever(
        search_kwargs={"k": 4, "filter": {"tenant_id": tenant_id}},
    )
```

### PGVector (row-level security)

```python
from sqlalchemy import text
from langchain_postgres import PGVector

def build_pgvector(tenant_id: str) -> BaseRetriever:
    store = PGVector(
        embeddings=emb,
        collection_name="rag",
        connection=engine,
    )
    # Set the tenant session variable per-transaction. The RLS policy on
    # the documents table reads it. If it's missing, RLS denies all rows.
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
    return store.as_retriever(search_kwargs={"k": 4})
```

See [Vector-store isolation](vector-store-isolation.md) for the RLS policy DDL.

### Chroma (collection-per-tenant)

```python
import chromadb
from langchain_chroma import Chroma

def build_chroma(tenant_id: str) -> BaseRetriever:
    client = chromadb.PersistentClient(path="/var/chroma")
    # get_or_create is idempotent; safe to call per-request.
    collection = client.get_or_create_collection(name=f"rag-{tenant_id}")
    store = Chroma(client=client, collection_name=collection.name, embedding_function=emb)
    return store.as_retriever(search_kwargs={"k": 4})
```

### FAISS (single-tenant only)

```python
# FAISS is in-process only. If you must use it multi-tenant, load a separate
# index file per tenant — but you pay the file-load cost on cold cache, and
# you cannot share memory across processes. Not recommended beyond ~50 tenants.
def build_faiss(tenant_id: str) -> BaseRetriever:
    path = f"/var/faiss/{tenant_id}.index"
    store = FAISS.load_local(path, emb, allow_dangerous_deserialization=False)
    return store.as_retriever(search_kwargs={"k": 4})
```

## Wiring the factory into a chain

```python
factory = make_retriever_factory(build_pinecone)

def retrieve(inputs: dict, config: RunnableConfig):
    return factory(config).invoke(inputs["query"])

chain = RunnableLambda(retrieve) | prompt | model

chain.invoke(
    {"query": "when was the contract signed?"},
    config={"configurable": {"tenant_id": "initech", "user_id": "u_42"}},
)
```

The retriever is rebuilt on every `invoke`. For high-QPS endpoints where the cost of rebuilding matters, cache the **client** (the Pinecone / Chroma / Postgres connection) but rebuild the per-tenant view each request — never cache the retriever itself.

## Lifecycle checklist

1. Retriever is constructed **inside** the request handler, not at module scope
2. Factory reads `tenant_id` from `RunnableConfig.configurable`, not from env / globals
3. Missing `tenant_id` raises `PermissionError`, not a `KeyError` or silent default
4. Vector-store client (connection pool, Pinecone client, Chroma client) is cached; the retriever view is not
5. Two-tenant regression test runs in CI and asserts non-overlap (see [Multi-tenant regression tests](multi-tenant-regression-tests.md))
6. On deploy, the first request for each tenant triggers a fresh build — no state carries over from a previous deploy

## Common anti-patterns

- `@lru_cache` on the factory — defeats the whole point, caches first tenant
- Default `tenant_id="public"` — silent escape hatch for forgotten configs
- Building the retriever in a FastAPI lifespan handler — runs once at startup, same as import
- Reading tenant from an env var instead of `RunnableConfig` — breaks when the process serves multiple tenants

## Related

- [Vector-store isolation](vector-store-isolation.md) — Pinecone / PGVector RLS / Chroma / FAISS detail
- [Multi-tenant regression tests](multi-tenant-regression-tests.md) — pytest fixtures that catch P33
- [Audit-log schema](audit-log-schema.md) — log every retrieval with tenant_id for forensics
