# Implementation Reference — podium-rag-context-bridge

Vector-store schema, store-adapter portability, embedder + reranker swaps, ingest hook for `podium-conversation-history-export`, and the language-portability layer for Node.js / TypeScript.

## pgvector reference schema

The reference implementation. Apply once per Podium org's database.

```sql
-- Required: enable the pgvector extension. Run as a database superuser.
CREATE EXTENSION IF NOT EXISTS vector;

-- One row per chunk of past Podium conversation. Chunk size is configurable in ingest
-- (typical: 300-500 tokens) so several can fit inside max_tokens_historical (1500).
CREATE TABLE podium_conversations (
    id           TEXT        PRIMARY KEY,                -- chunk id from the export skill
    contact_uid  TEXT        NOT NULL,
    conversation_uid TEXT,
    location_uid TEXT,
    channel      TEXT        NOT NULL,                   -- 'call', 'webchat', 'sms', 'review'
    content      TEXT        NOT NULL,                   -- redacted-at-ingest content
    content_raw_redacted_count INTEGER DEFAULT 0,        -- how many PII matches ingest already replaced
    occurred_at  TIMESTAMPTZ NOT NULL,
    ingested_at  TIMESTAMPTZ NOT NULL DEFAULT now(),
    embedding    vector(1024)  NOT NULL                  -- 1024 = bge-large-en-v1.5; change for other models
);

-- Per-contact filter is the hot path; index it.
CREATE INDEX podium_conversations_contact_idx ON podium_conversations (contact_uid);

-- ANN index. HNSW is the production default; cosine distance to match bge embeddings.
CREATE INDEX podium_conversations_embedding_idx
    ON podium_conversations
    USING hnsw (embedding vector_cosine_ops)
    WITH (m = 16, ef_construction = 64);

-- Optional: recency-aware retrieval. Bias newer chunks higher when the agent loop cares about recency.
CREATE INDEX podium_conversations_occurred_at_idx ON podium_conversations (occurred_at DESC);
```

To resize the vector column for a different embedder (e.g., `text-embedding-3-small` = 1536):

```sql
-- Drop the ANN index first; recreate after re-embedding.
DROP INDEX podium_conversations_embedding_idx;
ALTER TABLE podium_conversations ALTER COLUMN embedding TYPE vector(1536);
-- Re-embed every row before recreating the index.
CREATE INDEX podium_conversations_embedding_idx ON podium_conversations
    USING hnsw (embedding vector_cosine_ops);
```

## Vector-store adapter contract

The `VectorStore` Protocol is intentionally small — one method.

```python
from typing import Protocol

class VectorStore(Protocol):
    async def query(self, embedding: list[float], top_k: int,
                    filter: dict | None = None) -> list[dict]: ...
```

Returned rows MUST include: `id`, `content`, `channel`, `occurred_at`, `score` (cosine ∈ [0, 1]). The bridge attaches `rerank_score` later. `contact_uid` is required when the filter is passed.

### Pinecone adapter (sketch — not shipped runnable)

```python
import pinecone

class PineconeStore:
    def __init__(self, index_name: str, namespace: str):
        self.index = pinecone.Index(index_name)
        self.namespace = namespace

    async def query(self, embedding: list[float], top_k: int,
                    filter: dict | None = None) -> list[dict]:
        flt = {"contact_uid": {"$eq": filter["contact_uid"]}} if filter and "contact_uid" in filter else None
        # Pinecone client is sync; wrap in asyncio.to_thread in production.
        res = self.index.query(
            vector=embedding, top_k=top_k, namespace=self.namespace,
            filter=flt, include_metadata=True,
        )
        return [
            {"id": m.id, "content": m.metadata["content"], "channel": m.metadata["channel"],
             "occurred_at": m.metadata["occurred_at"], "contact_uid": m.metadata["contact_uid"],
             "score": float(m.score)}
            for m in res.matches
        ]
```

Pinecone uses dot-product or cosine depending on index config; pick cosine to match bge.

### Weaviate adapter (sketch — not shipped runnable)

```python
import weaviate

class WeaviateStore:
    def __init__(self, url: str, class_name: str = "PodiumConversation"):
        self.client = weaviate.Client(url)
        self.cls = class_name

    async def query(self, embedding: list[float], top_k: int,
                    filter: dict | None = None) -> list[dict]:
        q = self.client.query.get(self.cls, ["id", "content", "channel", "occurredAt", "contactUid"]) \
                .with_near_vector({"vector": embedding}) \
                .with_limit(top_k) \
                .with_additional(["distance"])
        if filter and "contact_uid" in filter:
            q = q.with_where({"path": ["contactUid"], "operator": "Equal", "valueString": filter["contact_uid"]})
        res = q.do()
        return [
            {"id": o["id"], "content": o["content"], "channel": o["channel"],
             "occurred_at": o["occurredAt"], "contact_uid": o["contactUid"],
             "score": 1.0 - float(o["_additional"]["distance"])}   # Weaviate returns distance; invert
            for o in res["data"]["Get"][self.cls]
        ]
```

## Embedder adapter contract

```python
class Embedder(Protocol):
    async def embed(self, text: str) -> list[float]: ...
```

### BGE default (local, free)

```python
from sentence_transformers import SentenceTransformer
import asyncio

class BgeEmbedder:
    def __init__(self, model: str = "BAAI/bge-large-en-v1.5"):
        self._model = SentenceTransformer(model)

    async def embed(self, text: str) -> list[float]:
        # sentence-transformers is sync; offload to a thread to keep the event loop free.
        vec = await asyncio.to_thread(self._model.encode, text, normalize_embeddings=True)
        return vec.tolist()
```

### OpenAI hosted (per-call cost, lower local memory)

```python
import os
from openai import AsyncOpenAI

class OpenAIEmbedder:
    def __init__(self, model: str = "text-embedding-3-small"):
        # API key MUST come from the secret store, never hardcoded.
        # Use {your-openai-key} as the placeholder in skill docs.
        self.client = AsyncOpenAI(api_key=os.environ["OPENAI_API_KEY"])
        self.model = model

    async def embed(self, text: str) -> list[float]:
        r = await self.client.embeddings.create(model=self.model, input=text)
        return r.data[0].embedding
```

Match `embedder.dimension` in `config/settings.yaml` to the model: 1024 for bge-large, 1536 for `text-embedding-3-small`, 3072 for `text-embedding-3-large`.

## Reranker adapter contract

```python
class Reranker(Protocol):
    async def score(self, query: str, candidates: list[str]) -> list[float]: ...
```

### BGE reranker default (local, free)

```python
from sentence_transformers import CrossEncoder
import asyncio

class BgeReranker:
    def __init__(self, model: str = "BAAI/bge-reranker-base"):
        self._model = CrossEncoder(model)

    async def score(self, query: str, candidates: list[str]) -> list[float]:
        pairs = [(query, c) for c in candidates]
        scores = await asyncio.to_thread(self._model.predict, pairs)
        return scores.tolist()
```

### LLM-as-reranker (slower, sometimes higher precision)

```python
import json, httpx, os

class LLMReranker:
    """Use a small LLM to score (query, candidate) on relevance.

    Adds 100-400ms per call relative to the BGE cross-encoder. Use only when
    domain-specific phrasing in candidates rewards a more capable model.
    """
    def __init__(self, model: str = "claude-haiku"):
        self.model = model

    async def score(self, query: str, candidates: list[str]) -> list[float]:
        prompt = (
            f"For the query: {query!r}\n"
            "Rate each candidate's relevance from 0.0 to 1.0. Return JSON array.\n\n"
            + "\n".join(f"{i}: {c!r}" for i, c in enumerate(candidates))
        )
        # NOTE: hosted-LLM keys MUST come from the secret store at request time.
        # Placeholder in skill docs: {your-anthropic-key}
        async with httpx.AsyncClient(timeout=4) as c:
            r = await c.post(
                "https://api.anthropic.com/v1/messages",
                headers={"x-api-key": os.environ["ANTHROPIC_API_KEY"]},
                json={"model": self.model, "max_tokens": 256,
                      "messages": [{"role": "user", "content": prompt}]},
            )
        body = r.json()
        return json.loads(body["content"][0]["text"])
```

### No-op reranker

```python
class NoopReranker:
    """Pass raw cosine through as rerank_score. Degraded relevance, zero latency cost."""
    async def score(self, query: str, candidates: list[str]) -> list[float]:
        return [0.0] * len(candidates)   # caller falls back to cosine_score ordering
```

## Ingest hook for `podium-conversation-history-export`

The export skill emits JSONL. Each line is one conversation chunk. The bridge does NOT consume JSONL at retrieval time — it consumes the pgvector table. The hook below is the boundary:

```python
import asyncio, json, os, sys, psycopg
from podium_rag_bridge import BgeEmbedder

async def ingest_chunk(conn, embedder, row: dict) -> None:
    vec = await embedder.embed(row["content"])
    await conn.execute(
        "INSERT INTO podium_conversations "
        "(id, contact_uid, conversation_uid, location_uid, channel, content, occurred_at, embedding) "
        "VALUES (%s, %s, %s, %s, %s, %s, %s, %s::vector) "
        "ON CONFLICT (id) DO UPDATE SET "
        "  content = EXCLUDED.content, "
        "  embedding = EXCLUDED.embedding, "
        "  ingested_at = now()",
        (row["id"], row["contact_uid"], row.get("conversation_uid"), row.get("location_uid"),
         row["channel"], row["content"], row["occurred_at"], vec),
    )

async def main():
    emb = BgeEmbedder()
    dsn = os.environ["PODIUM_PGVECTOR_DSN"]   # {your-pgvector-dsn} in docs
    async with await psycopg.AsyncConnection.connect(dsn) as conn:
        for line in sys.stdin:
            row = json.loads(line)
            await ingest_chunk(conn, emb, row)
        await conn.commit()

if __name__ == "__main__":
    asyncio.run(main())
```

The ingest path is responsible for PII redaction at write time. The bridge's redaction filter is defense-in-depth for misses.

## Node.js / TypeScript port (sketch)

The Python `build_context` translates to TypeScript with `Promise.allSettled` for parallel fan-out and `AbortController` for the hard deadline.

```typescript
interface ContextBundle {
  contact: Record<string, unknown>;
  historical_excerpts: Array<{
    content: string; channel: string; occurred_at: string; rerank_score: number;
  }>;
  token_count: number;
  meta: {
    elapsed_ms: number; timeout_ms: number; partial: boolean;
    had_vector_hits: boolean; had_live_lookup: boolean;
  };
}

async function buildContext(
  transcriptChunk: string, contactUid: string | null,
  auth: PodiumAuth, embedder: Embedder, store: VectorStore, reranker: Reranker,
  timeoutMs = 800,
): Promise<ContextBundle> {
  const started = Date.now();
  const controller = new AbortController();
  setTimeout(() => controller.abort(), timeoutMs);

  const withDeadline = async <T>(p: Promise<T>): Promise<T | null> => {
    try { return await Promise.race([p, new Promise<null>((_, rej) =>
      controller.signal.addEventListener("abort", () => rej(new Error("deadline"))))]); }
    catch { return null; }
  };

  const [vecHits, live] = await Promise.all([
    withDeadline(searchWithRerank(transcriptChunk, embedder, store, reranker, contactUid)),
    withDeadline(contactUid ? fetchLiveContact(auth, contactUid) : Promise.resolve(null)),
  ]);

  const bundle = mergeLiveOverVector(vecHits ?? [], live ?? { live_fields_available: false });
  redactBundle(bundle);
  enforceBudget(bundle, 1500);

  const elapsed = Date.now() - started;
  bundle.meta = {
    elapsed_ms: elapsed, timeout_ms: timeoutMs, partial: elapsed >= timeoutMs,
    had_vector_hits: !!(vecHits && vecHits.length),
    had_live_lookup: !!(live && (live as any).live_fields_available),
  };
  return bundle;
}
```

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_hard_deadline_returns_partial` | unit | Bundle emits with `meta.partial=true` when every surface times out |
| `test_live_wins_on_phone` | unit | Live `phone` overrides any vector hit's phone |
| `test_redaction_credit_card` | unit | Planted CC in corpus is redacted in emitted bundle |
| `test_budget_drop_lowest_rerank` | unit | Over-budget excerpts dropped in rerank-score order |
| `test_per_contact_filter_pushed_down` | unit | `WHERE contact_uid =` appears in the SQL for filtered queries |
| `test_coalescer_prepends_prev_tail` | unit | Embed query for chunk N contains tail of chunk N-1 |
| `test_rerank_top1_precision_on_eval_set` | integration | ≥0.80 on the labeled eval set |
| `test_vector_store_outage_emits_partial` | integration | Connection error → live-only bundle, no exception |
| `test_no_pii_in_emission_logs` | static | Grep audit of logs returns clean |
| `test_no_credential_leak_in_repo` | static | Grep against the canonical leak regex returns clean |
