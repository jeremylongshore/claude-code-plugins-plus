# Implementation Reference — podium-conversation-history-export

Language-portability layer plus vector-store-specific wiring plus chunk-sizing math plus the two-pass design rationale.

## Node.js / TypeScript port

The Python pipeline translates to TypeScript with three changes: async generators become `AsyncIterable` with `Symbol.asyncIterator`, the gzip stream uses Node's `zlib.createGzip()` piped to a write stream, and SQLite watermark access uses `better-sqlite3`.

```typescript
import { promises as fs } from "fs";
import { createWriteStream } from "fs";
import { pipeline } from "stream/promises";
import { createGzip } from "zlib";
import Database from "better-sqlite3";

interface PageResponse<T> {
  data: T[];
  next_cursor: string | null;
}

interface ExportConfig {
  baseUrl: string;
  locationUid: string;
  pageSize: number;
  overlapMarginS: number;
  watermarkDb: string;
}

async function* crawlConversations(
  podiumGet: (path: string, params: Record<string, string>) => Promise<Response>,
  cfg: ExportConfig,
): AsyncIterable<any> {
  const seen = new Set<string>();
  let cursor: string | null = null;

  while (true) {
    const params: Record<string, string> = {
      location_uid: cfg.locationUid,
      sort: "created_at:asc",
      limit: String(cfg.pageSize),
    };
    if (cursor) params.cursor = cursor;

    const r = await podiumGet("/v4/conversations", params);
    if (!r.ok) throw new Error(`export ${r.status}: ${await r.text()}`);
    const body = (await r.json()) as PageResponse<any>;

    for (const row of body.data) {
      if (seen.has(row.id)) continue;
      seen.add(row.id);
      yield row;
    }

    await fs.writeFile(
      `./.cursor.conversations.json`,
      JSON.stringify({
        cursor: body.next_cursor,
        seen_ids: Array.from(seen).slice(-50_000),
      }),
    );
    cursor = body.next_cursor;
    if (!cursor) return;
  }
}

async function streamExport(rows: AsyncIterable<any>, outPath: string): Promise<number> {
  const gz = createGzip();
  const out = createWriteStream(outPath);
  let count = 0;

  const writer = (async function* () {
    for await (const row of rows) {
      yield Buffer.from(JSON.stringify(row) + "\n", "utf-8");
      count++;
    }
  })();

  await pipeline(writer, gz, out);
  return count;
}

function getWatermark(db: string, resource: string): number {
  const con = new Database(db);
  con.exec("CREATE TABLE IF NOT EXISTS cdc(resource TEXT PRIMARY KEY, watermark REAL, updated_at REAL)");
  const row = con.prepare("SELECT watermark FROM cdc WHERE resource = ?").get(resource) as any;
  con.close();
  return row?.watermark ?? 0;
}

function advanceWatermark(db: string, resource: string, ts: number): void {
  const con = new Database(db);
  con.prepare(
    "INSERT INTO cdc(resource, watermark, updated_at) VALUES(?, ?, ?) " +
    "ON CONFLICT(resource) DO UPDATE SET watermark = excluded.watermark, updated_at = excluded.updated_at",
  ).run(resource, ts, Date.now() / 1000);
  con.close();
}
```

## Vector-store-specific loaders

### pgvector (Postgres)

```python
import gzip, json, psycopg2
from openai import OpenAI

def load_to_pgvector(chunk_path: str, dsn: str, model: str = "text-embedding-3-small"):
    oa = OpenAI()
    con = psycopg2.connect(dsn)
    with con.cursor() as cur:
        cur.execute("""
            CREATE TABLE IF NOT EXISTS podium_chunks (
                chunk_id    TEXT PRIMARY KEY,
                source_id   TEXT NOT NULL,
                source_type TEXT NOT NULL,
                body        TEXT NOT NULL,
                embedding   VECTOR(1536) NOT NULL,
                created_at  TIMESTAMPTZ DEFAULT NOW()
            );
            CREATE INDEX IF NOT EXISTS podium_chunks_emb_idx ON podium_chunks
                USING hnsw (embedding vector_cosine_ops);
        """)
    con.commit()

    batch = []
    with gzip.open(chunk_path, "rt") as f:
        for line in f:
            chunk = json.loads(line)
            assert chunk.get("pii_redacted"), f"refusing un-redacted chunk: {chunk['chunk_id']}"
            batch.append(chunk)
            if len(batch) == 100:
                _flush_batch(oa, con, model, batch)
                batch.clear()
        if batch:
            _flush_batch(oa, con, model, batch)

def _flush_batch(oa, con, model, batch):
    embs = oa.embeddings.create(model=model, input=[c["body"] for c in batch])
    with con.cursor() as cur:
        cur.executemany(
            "INSERT INTO podium_chunks(chunk_id, source_id, source_type, body, embedding) "
            "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (chunk_id) DO NOTHING",
            [(c["chunk_id"], c["source_id"], c["source_type"], c["body"], emb.embedding)
             for c, emb in zip(batch, embs.data)],
        )
    con.commit()
```

### Qdrant

```python
import gzip, json
from qdrant_client import QdrantClient
from qdrant_client.models import PointStruct, Distance, VectorParams
from openai import OpenAI

def load_to_qdrant(chunk_path: str, qdrant_url: str, collection: str = "podium_chunks"):
    oa = OpenAI()
    client = QdrantClient(url=qdrant_url)
    try:
        client.create_collection(
            collection_name=collection,
            vectors_config=VectorParams(size=1536, distance=Distance.COSINE),
        )
    except Exception:
        pass  # already exists

    batch = []
    with gzip.open(chunk_path, "rt") as f:
        for line in f:
            chunk = json.loads(line)
            assert chunk.get("pii_redacted")
            batch.append(chunk)
            if len(batch) == 100:
                _upsert(client, collection, oa, batch)
                batch.clear()
        if batch:
            _upsert(client, collection, oa, batch)

def _upsert(client, collection, oa, batch):
    embs = oa.embeddings.create(model="text-embedding-3-small", input=[c["body"] for c in batch])
    client.upsert(
        collection_name=collection,
        points=[
            PointStruct(
                id=hash(c["chunk_id"]) & ((1<<63)-1),  # qdrant uses uint64 ids
                vector=emb.embedding,
                payload={
                    "chunk_id":    c["chunk_id"],
                    "source_id":   c["source_id"],
                    "source_type": c["source_type"],
                    "body":        c["body"],
                },
            )
            for c, emb in zip(batch, embs.data)
        ],
    )
```

### Weaviate

```python
import gzip, json, weaviate
from openai import OpenAI

def load_to_weaviate(chunk_path: str, weaviate_url: str, class_name: str = "PodiumChunk"):
    oa = OpenAI()
    client = weaviate.Client(weaviate_url)

    if not client.schema.exists(class_name):
        client.schema.create_class({
            "class": class_name,
            "vectorizer": "none",
            "properties": [
                {"name": "chunk_id",    "dataType": ["string"]},
                {"name": "source_id",   "dataType": ["string"]},
                {"name": "source_type", "dataType": ["string"]},
                {"name": "body",        "dataType": ["text"]},
            ],
        })

    with gzip.open(chunk_path, "rt") as f, client.batch as batch:
        for line in f:
            chunk = json.loads(line)
            assert chunk.get("pii_redacted")
            emb = oa.embeddings.create(model="text-embedding-3-small", input=chunk["body"]).data[0].embedding
            batch.add_data_object(
                data_object={
                    "chunk_id":    chunk["chunk_id"],
                    "source_id":   chunk["source_id"],
                    "source_type": chunk["source_type"],
                    "body":        chunk["body"],
                },
                class_name=class_name,
                vector=emb,
            )
```

## Chunk sizing math

The defaults (`target_tokens=1500`, `overlap_tokens=200`) target OpenAI's `text-embedding-3-small` (8191-token window) with comfortable headroom. The math:

| Parameter | Default | Why |
|---|---|---|
| `target_tokens` | 1500 | ~5× headroom below the 8191 token window; small enough that retrieval ranking distinguishes between chunks at similar semantic distance |
| `overlap_tokens` | 200 | ~13% of target — empirically enough to recover from a chunk boundary cutting near a query-relevant span |
| `idle_gap_break_seconds` | 86400 (24h) | Below this, threads tend to be one semantic unit; above this, context drift accelerates |
| `approx_tokens(text)` | `len(text) // 4` | OpenAI's published rule-of-thumb; ~10–15% error on average prose; replace with tiktoken if accuracy matters |

For larger embedding windows (`text-embedding-3-large` at 8191 or future 32K models), raise `target_tokens` proportionally and lower the relative overlap. For tighter rate-limit budgets at the embedding API, raise target to reduce vector count (linear in chunks).

## Two-pass design rationale

The pipeline is intentionally two-pass:

1. **Export pass**: pulls from Podium, writes JSONL.
2. **Chunk pass**: reads JSONL, emits chunks.

Why not one pass?

| Scenario | One-pass cost | Two-pass cost |
|---|---|---|
| Tuning `target_tokens` from 1500 to 2000 | Re-pull entire corpus from Podium | Re-run chunk pass on existing JSONL |
| Changing PII pattern set | Re-pull entire corpus (PII patterns are baked into the chunker) | Re-run chunk pass; JSONL is unchanged |
| Auditing what data Podium returned | Reverse-engineer from chunks | Cat the JSONL |
| Re-embedding with a new model | Re-pull entire corpus | Re-run chunk pass; re-embed |
| Adding a new resource (e.g., feedback responses) | Re-pull entire corpus | Pull just the new resource; existing JSONL is unchanged |

The JSONL artifact is the canonical record. The chunked output is a derived view. Treat JSONL retention like a data warehouse: keep it indefinitely (compressed, ~6 GB for a 2-year org); re-chunk on demand.

## PII redaction module sharing

The PII patterns module (`podium_pii.patterns`) is owned by `podium-call-transcript-pipeline`. This skill imports it; it does NOT fork or copy the regexes.

Rationale: a redaction policy change must apply to every PII surface in the pack atomically. Two copies guarantee one will drift. The shared module is the only place a regex is updated; both skills inherit the change on the next deploy.

To verify the module is shared (not duplicated):

```bash
python3 -c "from podium_pii import patterns; print(patterns.__file__)"
# Must print exactly one path — and it must be inside podium-call-transcript-pipeline.
```

If the import fails, install `podium-call-transcript-pipeline` in the same Python environment.

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_dedup_on_midwalk_update` | unit | A row updated between page N and N+1 is yielded exactly once |
| `test_cursor_persisted_per_page` | unit | A SIGKILL after page 7 resumes from page 8, not page 1 |
| `test_watermark_boundary_inclusion` | unit | A row with `updated_at == watermark` is included on the next pull |
| `test_overlap_margin_dedup` | unit | A row included via the overlap margin is not double-counted in the output |
| `test_attachment_403_refresh` | unit | A 403 on a signed URL triggers exactly one refresh+retry |
| `test_chunker_idle_gap_break` | unit | A 25h idle gap forces a chunk boundary |
| `test_chunker_4000_message_thread` | integration | Memory stays bounded; chunks are coherent; chunk IDs are deterministic |
| `test_pii_redaction_coverage` | unit | A corpus of synthetic PII produces 100% match rate |
| `test_pii_redacted_field_on_every_chunk` | static | `zcat ... \| jq 'select(.pii_redacted == false)' \| wc -l == 0` |
| `test_memory_bounded_on_long_thread` | integration | Peak RSS < 200 MB on a 4000-message thread |
| `test_watermark_partial_run_does_not_advance` | integration | An interrupted incremental run leaves the watermark at the previous value |
| `test_chunk_id_deterministic` | unit | Two runs over identical input produce identical chunk_ids |

## Operator runbook one-liner

For the routine nightly-sync use case, the entire pipeline is one cron entry:

```cron
15 2 * * * cd /opt/podium-export && \
    ./scripts/export_conversations.py --location-uid "$PODIUM_LOC" --mode incremental \
        --watermark-db ./watermarks.sqlite --out ./exports/conversations.$(date +\%F).jsonl.gz && \
    ./scripts/attachment_downloader.py --input ./exports/conversations.$(date +\%F).jsonl.gz \
        --out-dir ./exports/attachments --refresh-on-403 && \
    ./scripts/chunk_for_embedding.py --input ./exports/conversations.$(date +\%F).jsonl.gz \
        --output ./exports/chunks.$(date +\%F).jsonl.gz --redact-pii
```

That cron line is the canonical proof that this skill's interface is small enough to operationalize without a wrapper service.
