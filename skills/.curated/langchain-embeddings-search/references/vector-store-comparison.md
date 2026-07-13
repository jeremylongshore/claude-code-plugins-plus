# Vector Store Comparison

Feature-by-feature comparison of the four vector stores most commonly wired
through LangChain 1.0. Use this to pick a backend, and before any migration,
to anticipate the score-semantics flip (P12).

## Matrix

| Feature | FAISS | Chroma | PGVector | Pinecone |
|---|---|---|---|---|
| Hosted | No (in-process) | No (local file or server) | Self-hosted Postgres | Fully managed |
| Score metric (default) | L2 distance | Cosine similarity | Cosine distance | Cosine similarity |
| Score direction | Lower = better | Higher = better | Lower = better | Higher = better |
| Max practical scale | ~5M vectors / GB RAM | ~1M per node | ~10M with indexing | Billions |
| Latency (p95, 1M vectors) | 2-8 ms | 8-15 ms | 15-30 ms | 40-80 ms |
| Filtering (metadata WHERE) | Manual post-filter | Native `where` | SQL | Native `filter` |
| Namespaces / tenants | Manual (one store per tenant) | Collection per tenant | Schema or column | Native namespaces |
| Persistence | `save_local` / `load_local` | Built-in | Postgres | Managed |
| Updates (delete / upsert) | Rebuild index | Native | SQL | Native |
| Backup / recovery | File copy | File copy | pg_dump | Provider handles |
| Cost | Free (compute only) | Free (compute only) | Postgres cost | Per-pod $$$ |

## When each wins

- **FAISS** — local dev, reproducible tests, offline deployments, single-process
  services, < 1M vectors, you own the embedding pipeline
- **Chroma** — small multi-user local, persistent volume, native filtering,
  < 1M vectors
- **PGVector** — you already run Postgres, need transactional guarantees
  alongside vectors, want SQL filtering, < 10M vectors with ivfflat / hnsw
- **Pinecone** — > 10M vectors, multi-tenant SaaS, no ops budget, need the
  hosted redundancy

## Score-semantics crib sheet (P12)

Migration direction: two gotchas occur — the direction flip, and the range shift.

| From | To | Direction change | Range shift |
|---|---|---|---|
| FAISS (L2) | Pinecone (cosine) | Flip (lower→higher better) | Unbounded → [0, 1] (mostly [0.5, 1]) |
| FAISS (L2) | PGVector (cosine distance) | No flip (both lower=better) | Unbounded → [0, 2] |
| Chroma (cosine sim) | Pinecone (cosine sim) | No flip | Same range |
| PGVector (cosine dist) | Pinecone (cosine sim) | Flip | [0,2] → [0,1] |

Always migrate through the normalizer in the SKILL.md Step 3. Re-tune any
threshold filter on a golden eval set post-migration — thresholds calibrated
on L2 distances will definitely not hold on cosine.

## Migration checklist

1. Re-embed: if you changed embedding model alongside the store, re-embed
   everything against the new model. Document re-embed cost (usually
   `$0.00002 / 1K tokens` for OpenAI small, `$0.00013 / 1K tokens` for large).
2. Dim assertion: `assert len(embeddings.embed_query("test")) == expected_dim`
   at startup in both old and new code paths during migration.
3. Dual-write: for a period, write to both stores; read from the old one.
4. Shadow-read: query both, compare top-K overlap. Target: 80%+ overlap on a
   golden query set before cutover.
5. Cutover: flip read path. Keep the old store writable for rollback for 24h.
6. Retire: delete the old store after success is confirmed.

## Filtering metadata

FAISS does not support native WHERE — post-filter Python-side. Everything else
has native filtering; always prefer it over post-filter for multi-tenant
isolation (P33).

```python
# Pinecone native filter — server-side, cheap
store.similarity_search("query", k=5, filter={"tenant_id": "acme"})

# FAISS — you must do it in Python after retrieval. Over-fetch k, then filter.
results = store.similarity_search("query", k=50)
filtered = [d for d in results if d.metadata.get("tenant_id") == "acme"][:5]
```

FAISS post-filter hurts at scale; if your app has tenant filtering at the
hottest read path, switch to Pinecone / PGVector / Chroma earlier than you
think.

## When to use none of these

For < 50K documents, a SQL `SELECT ... ORDER BY embedding <-> $1 LIMIT k` on
PGVector with no index is fine. Adding a specialized vector store is premature
optimization below that scale.

For > 1B vectors or very high QPS, a specialized cluster (Weaviate, Qdrant
Cloud, Vespa) usually outperforms Pinecone on cost. LangChain has integrations
for all three.
