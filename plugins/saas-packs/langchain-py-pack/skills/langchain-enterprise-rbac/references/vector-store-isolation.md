# Vector-store Isolation Primitives

Each vector store offers a different isolation primitive. Pick one by scale and by the audit posture your security team requires.

## Comparison

| Store | Isolation primitive | p50 query latency | Max practical tenants | Audit posture |
|---|---|---|---|---|
| **Pinecone** | Namespace per tenant | ~40ms (shared index) | 100,000+ per index | Namespace is the isolation boundary; log both namespace and metadata for defense in depth |
| **PGVector** | Row-level security on `tenant_id` | ~20ms (HNSW) | Millions of rows, 1000s of tenants | Strongest — RLS enforced by Postgres server, not app code |
| **Chroma** | Collection per tenant | ~30ms | ~1,000 before metadata overhead | App-layer boundary; no server-side enforcement |
| **FAISS** | In-process index per tenant | ~5ms (in-memory) | 10-50 | No multi-process story; not suitable for SaaS |

Pinecone handles the highest scale. PGVector is the strongest when your security team needs isolation to be enforced at the database server. Chroma is appropriate for small B2B SaaS (≤1,000 tenants). FAISS is a development tool — document it so future engineers do not adopt it for production.

## Pinecone — namespace per tenant

```python
from langchain_pinecone import PineconeVectorStore

# Write path — always include namespace.
store = PineconeVectorStore(
    index_name="rag",
    namespace=tenant_id,          # REQUIRED — never omit
    embedding=emb,
)
store.add_texts(
    ["document content"],
    ids=[f"{tenant_id}-doc-1"],    # prefix IDs with tenant for leak forensics
    metadatas=[{"tenant_id": tenant_id}],  # defense in depth
)

# Read path — namespace + metadata filter together.
retriever = store.as_retriever(
    search_kwargs={
        "k": 4,
        "filter": {"tenant_id": tenant_id},  # redundant with namespace; belt-and-braces
    },
)
```

Why the redundant metadata filter: if a write path ever forgets to set `namespace` (the default is `""`, which silently succeeds), the misfiled vectors sit in the default namespace where every tenant's query with the metadata filter will exclude them. Without the filter, a query with `namespace=""` would pull them.

**Namespace lifecycle:** Pinecone namespaces are created on first write; no explicit provisioning step. Deletion: `store.delete(delete_all=True)` removes all vectors in the namespace. For tenant offboarding, this is the cleanup call.

## PGVector — row-level security

PGVector with RLS is the strongest isolation primitive because the database server enforces it. Even if application code has a bug, the server refuses to return rows from other tenants.

### Schema and RLS policy

```sql
-- Table — add tenant_id column.
CREATE TABLE documents (
  id TEXT PRIMARY KEY,
  tenant_id TEXT NOT NULL,
  content TEXT NOT NULL,
  embedding VECTOR(1536) NOT NULL,
  metadata JSONB,
  created_at TIMESTAMPTZ NOT NULL DEFAULT now()
);

CREATE INDEX documents_embedding_hnsw
  ON documents USING hnsw (embedding vector_cosine_ops);

CREATE INDEX documents_tenant_id ON documents (tenant_id);

-- Enable RLS.
ALTER TABLE documents ENABLE ROW LEVEL SECURITY;

-- Policy — reads and writes only for the current session's tenant.
CREATE POLICY tenant_isolation ON documents
  USING (tenant_id = current_setting('app.tenant_id', true))
  WITH CHECK (tenant_id = current_setting('app.tenant_id', true));

-- Grant to the app role — RLS still applies.
GRANT SELECT, INSERT, UPDATE, DELETE ON documents TO langchain_app;
```

### Setting the session variable per transaction

```python
from sqlalchemy import text

def run_with_tenant(tenant_id: str, work):
    with engine.begin() as conn:
        # SET LOCAL is transaction-scoped — auto-reset on commit/rollback.
        conn.execute(text("SET LOCAL app.tenant_id = :tid"), {"tid": tenant_id})
        return work(conn)
```

The `SET LOCAL` form is critical. `SET` without `LOCAL` persists for the whole session, which means connection pooling will bleed tenants into each other. Always `SET LOCAL`.

### Testing RLS enforcement

```python
def test_rls_blocks_cross_tenant_read():
    with engine.begin() as conn:
        conn.execute(text("SET LOCAL app.tenant_id = 'initech'"))
        rows = conn.execute(text(
            "SELECT id FROM documents WHERE content LIKE '%Acme%'"
        )).all()
    # Even though Acme documents exist, RLS filters them out.
    assert rows == []

def test_rls_blocks_write_to_other_tenant():
    with pytest.raises(Exception, match="violates row-level security"):
        with engine.begin() as conn:
            conn.execute(text("SET LOCAL app.tenant_id = 'initech'"))
            conn.execute(text(
                "INSERT INTO documents (id, tenant_id, content, embedding) "
                "VALUES ('x', 'acme', 'stolen', '[0,0,0,...]'::vector)"
            ))
```

A malicious or buggy write attempting to impersonate another tenant is blocked by the `WITH CHECK` clause.

## Chroma — collection per tenant

```python
import chromadb
from langchain_chroma import Chroma

client = chromadb.PersistentClient(path="/var/chroma")

def chroma_for(tenant_id: str) -> Chroma:
    # get_or_create is idempotent — safe per-request.
    collection = client.get_or_create_collection(name=f"rag-{tenant_id}")
    return Chroma(
        client=client,
        collection_name=collection.name,
        embedding_function=emb,
    )
```

Pros: simple mental model (one collection = one tenant), no shared index to reason about.

Cons: collection creation is synchronous and adds ~100ms on first write per tenant; metadata overhead grows with collection count; at ~1,000 collections query planning slows.

**Offboarding:** `client.delete_collection(name=f"rag-{tenant_id}")` — synchronous and final.

## FAISS — not recommended for multi-tenant

FAISS is in-process. Each worker loads its own index from disk. Implications:

- No shared memory across processes — 10 workers × 500MB index = 5GB RAM
- Cold start on every deploy
- No transactional isolation — a write during read is undefined
- Tenant offboarding requires deleting a file on disk, then signaling every worker to reload

Use FAISS for local development and single-tenant on-prem deployments. For multi-tenant SaaS, use one of the three above.

## Cross-cutting concerns

### Backups and retention

Pinecone, PGVector, and Chroma back up per-tenant differently:

- **Pinecone** — collections (backups) are index-scoped; you cannot back up a single tenant, only the whole index
- **PGVector** — standard Postgres backup (`pg_dump`) captures all tenants; for per-tenant export use `COPY ... WHERE tenant_id = $1`
- **Chroma** — one collection per tenant means per-tenant backup is `client.get_collection(name=...).get(include=["documents", "metadatas", "embeddings"])`

### Index growth pressure

At scale you will want to shard further — e.g. one Pinecone index per tier (enterprise customers in their own dedicated index). Design the retriever factory to accept an `(index_name, namespace)` pair so sharding doesn't require a rewrite.

### Migration between stores

When migrating FAISS → Pinecone or Chroma → PGVector, run the [regression tests](multi-tenant-regression-tests.md) against both stores in parallel for at least one full week. Diff the retrieved doc IDs per tenant per query; investigate any delta before cutting over.

## Related

- [Retriever-per-request](retriever-per-request.md) — factory implementations for all four stores
- [Multi-tenant regression tests](multi-tenant-regression-tests.md) — RLS integration test included
- [Audit-log schema](audit-log-schema.md) — `retrieval_ids` field enables cross-tenant leak detection queries
