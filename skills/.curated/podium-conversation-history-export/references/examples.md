# Examples — podium-conversation-history-export

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Minimal full export (Python, async)

```python
# env: PODIUM_CLIENT_ID, PODIUM_CLIENT_SECRET, PODIUM_REFRESH_TOKEN_FILE,
#      PODIUM_LOCATION_UID
import asyncio, os, json, gzip
from pathlib import Path
from podium_auth import PodiumAuth          # from podium-auth skill

CURSOR = Path("./.cursor.conversations.json")

async def main():
    record = json.loads(Path(os.environ["PODIUM_REFRESH_TOKEN_FILE"]).read_text())
    auth = PodiumAuth(
        client_id=os.environ["PODIUM_CLIENT_ID"],
        client_secret=os.environ["PODIUM_CLIENT_SECRET"],
        refresh_token=record["refresh_token"],
    )

    import httpx
    location_uid = os.environ["PODIUM_LOCATION_UID"]
    seen = set()
    cursor = None
    written = 0

    with gzip.open("./exports/conversations.jsonl.gz", "wt") as out:
        while True:
            token = await auth.get_token()
            params = {"location_uid": location_uid, "sort": "created_at:asc", "limit": 100}
            if cursor: params["cursor"] = cursor

            async with httpx.AsyncClient(timeout=30) as c:
                r = await c.get(
                    "https://api.podium.com/v4/conversations",
                    params=params,
                    headers={"Authorization": f"Bearer {token}"},
                )
            r.raise_for_status()
            body = r.json()

            for row in body.get("data", []):
                if row["id"] in seen: continue
                seen.add(row["id"])
                out.write(json.dumps(row, separators=(",", ":")) + "\n")
                written += 1

            CURSOR.write_text(json.dumps({"cursor": body.get("next_cursor"), "seen_ids": list(seen)[-50_000:]}))
            cursor = body.get("next_cursor")
            if not cursor: break

    print(f"wrote {written} conversations")

asyncio.run(main())
```

## 2. Incremental nightly sync with watermark

```bash
# Nightly cron: run incremental sync, advance watermark only on success.
python3 scripts/export_conversations.py \
  --location-uid "{your-location-uid}" \
  --mode incremental \
  --watermark-db ./watermarks.sqlite \
  --overlap-margin-seconds 60 \
  --out ./exports/conversations.$(date +%F).jsonl.gz \
  --client-id-env PODIUM_CLIENT_ID \
  --client-secret-env PODIUM_CLIENT_SECRET \
  --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE"
```

Output:

```json
{
  "resource": "conversations",
  "mode": "incremental",
  "watermark_before": 1715126400,
  "watermark_after":  1715212800,
  "rows_pulled": 142,
  "rows_emitted_after_dedup": 138,
  "duration_seconds": 47
}
```

## 3. Inspect the CDC watermark

```bash
# What's the current watermark for each resource?
python3 scripts/cdc_watermark.py --db ./watermarks.sqlite
```

Output:

```json
{
  "conversations": {"watermark": 1715212800, "iso8601": "2026-05-09T00:00:00Z", "age_seconds": 86400},
  "reviews":       {"watermark": 1715126400, "iso8601": "2026-05-08T00:00:00Z", "age_seconds": 172800},
  "contacts":      {"watermark": 1714521600, "iso8601": "2026-05-01T00:00:00Z", "age_seconds": 777600}
}
```

## 4. Reset a watermark (force full re-pull)

```bash
# After a schema change or a corrupted run, force a full re-pull.
# --confirm is required because reset burns rate-limit budget.
python3 scripts/cdc_watermark.py \
  --db ./watermarks.sqlite \
  --resource conversations \
  --reset \
  --confirm
```

## 5. Parallel attachment download with refresh-on-403

```bash
# Pulls every attachment referenced in the JSONL export.
# Refreshes pre-signed URLs on 403; concurrency capped at 8.
python3 scripts/attachment_downloader.py \
  --input ./exports/conversations.jsonl.gz \
  --out-dir ./exports/attachments \
  --concurrency 8 \
  --refresh-on-403 \
  --client-id-env PODIUM_CLIENT_ID \
  --client-secret-env PODIUM_CLIENT_SECRET \
  --refresh-token-file "$PODIUM_REFRESH_TOKEN_FILE"
```

Output:

```json
{
  "attachments_total": 1842,
  "downloaded_ok": 1837,
  "refreshed_signed_url": 142,
  "failed_after_refresh": 5,
  "failed_ids": ["att_a1b2", "att_c3d4", "..."]
}
```

## 6. Chunk a JSONL export with PII redaction

```bash
python3 scripts/chunk_for_embedding.py \
  --input ./exports/conversations.jsonl.gz \
  --output ./exports/chunks.jsonl.gz \
  --target-tokens 1500 \
  --overlap-tokens 200 \
  --idle-gap-break-seconds 86400 \
  --redact-pii
```

Each output line is one chunk:

```json
{
  "chunk_id": "conv_a1b2c3:msg_001:msg_042",
  "source_id": "conv_a1b2c3",
  "source_type": "conversation",
  "created_at_window": [1714521600, 1714525200],
  "token_estimate": 1487,
  "pii_redacted": true,
  "body": "[REDACTED_EMAIL] asked about availability for the [REDACTED_ADDR]..."
}
```

## 7. PII redaction audit pass

```bash
# Confirm no chunk slipped through with pii_redacted: false.
zcat ./exports/chunks.jsonl.gz | jq -c 'select(.pii_redacted == false)' | wc -l
# Must print 0 in production.

# Spot-check by grepping for unredacted PII patterns in the chunked corpus
# (regression test for the pattern set itself).
zcat ./exports/chunks.jsonl.gz \
  | grep -nE "\b[0-9]{3}-[0-9]{2}-[0-9]{4}\b" \
  | head -20
# Must print nothing.
```

## 8. End-to-end pipeline (shell composition)

```bash
#!/usr/bin/env bash
set -euo pipefail

LOCATION_UID="{your-location-uid}"
DATE=$(date +%F)
EXPORT_DIR="./exports/$DATE"
mkdir -p "$EXPORT_DIR"

# Stage 1: incremental sync
python3 scripts/export_conversations.py \
  --location-uid "$LOCATION_UID" \
  --mode incremental \
  --watermark-db ./watermarks.sqlite \
  --out "$EXPORT_DIR/conversations.jsonl.gz"

# Stage 2: pull any new attachments
python3 scripts/attachment_downloader.py \
  --input "$EXPORT_DIR/conversations.jsonl.gz" \
  --out-dir "$EXPORT_DIR/attachments" \
  --concurrency 8 \
  --refresh-on-403

# Stage 3: chunk for embedding (PII redacted)
python3 scripts/chunk_for_embedding.py \
  --input "$EXPORT_DIR/conversations.jsonl.gz" \
  --output "$EXPORT_DIR/chunks.jsonl.gz" \
  --redact-pii

# Stage 4: hand off to the embedding pipeline (consumer's responsibility)
echo "$EXPORT_DIR/chunks.jsonl.gz" | xargs -I{} ./bin/embed-to-vector-store.sh {}
```

## 9. Loading chunks into pgvector

```python
import gzip, json, psycopg2
from openai import OpenAI

oa = OpenAI()
con = psycopg2.connect("postgresql://...")

with gzip.open("./exports/chunks.jsonl.gz", "rt") as f:
    batch = []
    for line in f:
        chunk = json.loads(line)
        if not chunk.get("pii_redacted"):
            raise RuntimeError(f"refusing to embed un-redacted chunk: {chunk['chunk_id']}")
        batch.append(chunk)
        if len(batch) >= 100:
            embs = oa.embeddings.create(
                model="text-embedding-3-small",
                input=[c["body"] for c in batch],
            )
            with con.cursor() as cur:
                cur.executemany(
                    "INSERT INTO podium_chunks(chunk_id, source_id, source_type, body, embedding) "
                    "VALUES (%s, %s, %s, %s, %s) ON CONFLICT (chunk_id) DO NOTHING",
                    [(c["chunk_id"], c["source_id"], c["source_type"], c["body"], emb.embedding)
                     for c, emb in zip(batch, embs.data)],
                )
            con.commit()
            batch.clear()
```

The `ON CONFLICT (chunk_id) DO NOTHING` makes re-embedding the same export idempotent — deterministic chunk_ids do the heavy lifting.

## 10. Recovering a stuck cursor walk

```bash
# Symptom: export_conversations.py is paginating but the same cursor keeps
# returning the same page (a Podium-side cursor anchor went stale).
#
# Step 1: stop the run.
# Step 2: inspect the checkpoint.
cat ./.cursor.conversations.json
# {"cursor": "eyJzb3J0IjoiY3JlYXRlZF9hdDphc2MiLCJwb3MiOiJfX18ifQ==", "seen_ids": [...]}

# Step 3: delete the cursor (the seen_ids set is preserved by the run log,
# so dedup continues to work).
rm ./.cursor.conversations.json

# Step 4: for an incremental run, the watermark already covers the position —
# just re-run. For a full run, you lose progress; consider switching to
# incremental from the next-newest watermark and back-filling the gap manually.
python3 scripts/export_conversations.py \
  --location-uid "{your-location-uid}" \
  --mode incremental \
  --watermark-db ./watermarks.sqlite \
  --out ./exports/conversations.recovery.jsonl.gz
```
