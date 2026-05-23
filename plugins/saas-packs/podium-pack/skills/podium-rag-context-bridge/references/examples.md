# Examples — podium-rag-context-bridge

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Minimal: build a bundle for one transcript chunk (Python, async)

```python
# env: PODIUM_CLIENT_ID, PODIUM_CLIENT_SECRET, PODIUM_REFRESH_TOKEN_FILE, PODIUM_PGVECTOR_DSN
import asyncio, os, json
from pathlib import Path
from podium_auth import PodiumAuth
from podium_rag_bridge import (
    build_context, PgvectorStore, BgeEmbedder, BgeReranker,
)

async def main():
    record = json.loads(Path(os.environ["PODIUM_REFRESH_TOKEN_FILE"]).read_text())
    auth = PodiumAuth(
        client_id=os.environ["PODIUM_CLIENT_ID"],
        client_secret=os.environ["PODIUM_CLIENT_SECRET"],
        refresh_token=record["refresh_token"],
    )
    embedder = BgeEmbedder()
    store = PgvectorStore(dsn=os.environ["PODIUM_PGVECTOR_DSN"])
    reranker = BgeReranker()

    bundle = await build_context(
        transcript_chunk="I had a question about my last order",
        contact_uid="ctc_abc123",
        auth=auth, embedder=embedder, vector_store=store, reranker=reranker,
        timeout_ms=800,
    )
    print(json.dumps(bundle, indent=2))

asyncio.run(main())
```

## 2. Wire the bridge into an agent loop

```python
# A single agent-turn handler. Called for each transcript chunk the pipeline emits.
async def on_transcript_chunk(chunk: str, contact_uid: str, conv_uid: str) -> str:
    bundle = await build_context(
        transcript_chunk=chunk,
        contact_uid=contact_uid,
        auth=AUTH, embedder=EMB, vector_store=STORE, reranker=RR,
        timeout_ms=800,
    )

    prompt = format_llm_prompt(
        system="You are a helpful agent for an SMB.",
        live_contact=bundle["contact"],
        historical=bundle["historical_excerpts"],
        current_turn=chunk,
        partial=bundle["meta"]["partial"],
    )
    return await llm.complete(prompt)
```

The agent never reaches into the vector store directly. The bridge is the single seam between retrieval and the LLM.

## 3. Bootstrap the vector-store table from the export skill

```bash
# Once per Podium org. The export skill (podium-conversation-history-export) emits
# JSONL chunks; this script embeds and upserts them.

python3 -c '
import json, os, sys
from podium_rag_bridge import BgeEmbedder, PgvectorStore
import asyncio, psycopg

async def ingest():
    emb = BgeEmbedder()
    dsn = os.environ["PODIUM_PGVECTOR_DSN"]
    async with await psycopg.AsyncConnection.connect(dsn) as conn:
        for line in sys.stdin:
            row = json.loads(line)
            vec = await emb.embed(row["content"])
            await conn.execute(
                "INSERT INTO podium_conversations (id, contact_uid, content, channel, occurred_at, embedding) "
                "VALUES (%s, %s, %s, %s, %s, %s::vector) ON CONFLICT (id) DO UPDATE "
                "SET content = EXCLUDED.content, embedding = EXCLUDED.embedding",
                (row["id"], row["contact_uid"], row["content"], row["channel"], row["occurred_at"], vec),
            )
        await conn.commit()

asyncio.run(ingest())
' < podium-export.jsonl
```

This is the one-time bootstrap. Incremental ingest is a webhook handler that does the same per new conversation event.

## 4. Raw vector query (no live merge, no redaction)

```bash
# Debug-only. Bypasses everything except retrieval + rerank.
# Useful for inspecting why the bridge ranked things the way it did.
python3 scripts/vector_query.py \
  --query "did they ask about refund policy" \
  --contact-uid "ctc_abc123" \
  --pgvector-dsn "{your-pgvector-dsn}" \
  --pool-k 20 \
  --final-k 5
```

Output:

```json
[
  {"id": "...", "content": "Our refund policy is 30 days...", "channel": "webchat",
   "cosine_score": 0.78, "rerank_score": 0.94, "occurred_at": "2026-04-12T..."},
  ...
]
```

## 5. Build the LLM prompt from a bundle (CLI)

```bash
# Run build_context first, save the bundle, then format the prompt.
python3 scripts/context_fetch.py \
  --transcript "I had a question about my last order" \
  --contact-uid "ctc_abc123" \
  --pgvector-dsn "{your-pgvector-dsn}" \
  --output json > bundle.json

python3 scripts/transcript_to_llm.py \
  --transcript "I had a question about my last order" \
  --bundle-file bundle.json \
  --system-prompt-file ./system.txt \
  --max-tokens 4000
```

Emits a structured prompt with explicit blocks: `SYSTEM`, `LIVE CONTACT (current truth)`, `HISTORICAL CONTEXT (with rerank scores)`, `TRANSCRIPT TURN`. The blocks help the LLM distinguish what it can rely on (live) vs what it should treat as hints (historical).

## 6. Score a single (query, candidate) pair

```bash
# Useful for building eval datasets: label a top-1 expected result by hand,
# then score the bridge's top-1 against it.
python3 scripts/relevance_score.py \
  --query "did they ask about refund policy" \
  --candidate "Our policy is 30-day refunds with receipt"
# 0.87

python3 scripts/relevance_score.py \
  --query "did they ask about refund policy" \
  --candidate "Have a great day, thanks for reaching out"
# 0.04
```

The reranker's score is what the bridge would have used for ranking. Useful in CI to assert top-1 precision against a labeled eval set.

## 7. Fault drill — vector store unreachable

```python
# Inject a connection error and verify the bundle still emits.
class BrokenStore:
    async def query(self, *a, **kw):
        raise ConnectionError("simulated outage")

bundle = await build_context(
    "I had a question about my last order",
    contact_uid="ctc_abc123",
    auth=AUTH, embedder=EMB, vector_store=BrokenStore(), reranker=RR,
    timeout_ms=800,
)
assert bundle["meta"]["partial"] is True
assert bundle["meta"]["had_vector_hits"] is False
assert bundle["meta"]["had_live_lookup"] is True
assert bundle["historical_excerpts"] == []
```

The bridge MUST still ship a bundle. Asserting on `meta` is how operational tests verify graceful degradation.

## 8. Fault drill — full timeout

```python
class SlowStore:
    async def query(self, *a, **kw):
        await asyncio.sleep(5)   # exceeds any reasonable timeout
        return []

bundle = await build_context(
    "...",
    contact_uid="ctc_abc123",
    auth=AUTH, embedder=EMB, vector_store=SlowStore(), reranker=RR,
    timeout_ms=200,  # aggressively short
)
assert bundle["meta"]["partial"] is True
assert bundle["meta"]["elapsed_ms"] < 300  # the deadline IS the contract
```

The bridge cannot block past the deadline. This is a hard property — tested in CI.

## 9. PII smoke test

```python
# Plant a credit-card-like string in a vector row, retrieve, verify it's redacted.
class CCStore:
    async def query(self, *a, **kw):
        return [{"id": "x", "content": "card on file is 4242424242424242", "channel": "webchat",
                 "occurred_at": "2026-05-01T00:00:00Z", "score": 0.95}]

bundle = await build_context(
    "what card is on file",
    contact_uid="ctc_abc123",
    auth=AUTH, embedder=EMB, vector_store=CCStore(), reranker=NoopReranker(),
    timeout_ms=800,
)
assert "4242424242424242" not in bundle["historical_excerpts"][0]["content"]
assert "[REDACTED:CC]" in bundle["historical_excerpts"][0]["content"]
```

If this test ever fails, the redaction filter regressed. Ship the fix before the next deploy.

## 10. Eval set against labeled data

```bash
# eval.jsonl: each line is {"chunk": "...", "contact_uid": "...", "expected_top1_id": "..."}
python3 - <<'PY'
import asyncio, json
from podium_rag_bridge import build_context, BgeEmbedder, BgeReranker, PgvectorStore
from podium_auth import PodiumAuth

async def main():
    auth = PodiumAuth(...)
    emb, rr, store = BgeEmbedder(), BgeReranker(), PgvectorStore(dsn="...")
    correct = 0
    total = 0
    for line in open("eval.jsonl"):
        row = json.loads(line)
        bundle = await build_context(
            row["chunk"], row["contact_uid"],
            auth=auth, embedder=emb, vector_store=store, reranker=rr,
        )
        excerpts = bundle["historical_excerpts"]
        top1_id = excerpts[0]["id"] if excerpts else None
        if top1_id == row["expected_top1_id"]:
            correct += 1
        total += 1
    print(f"top-1 precision: {correct/total:.3f} ({correct}/{total})")
asyncio.run(main())
PY
```

Gate CI on `top-1 precision >= 0.80`. If reranking regresses (model swap, pool_k change), this catches it before production.
