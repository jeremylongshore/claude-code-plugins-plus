# Implementation Reference — podium-webhook-reliability

Language-portability layer plus Redis schema plus DLQ backend choices plus operator workflow.

## Node.js / TypeScript port

The Python receiver translates to Node + Express + ioredis. The two notable differences: `hmac.compare_digest` becomes `crypto.timingSafeEqual` (which requires the two Buffers to be the same length — wrap with an explicit length check), and raw body access requires the `express.raw()` middleware because `express.json()` consumes the body before signature verification can run.

```typescript
import express from "express";
import * as crypto from "crypto";
import IORedis from "ioredis";

const SECRET = Buffer.from(process.env.PODIUM_WEBHOOK_SECRET!, "utf-8");
const R = new IORedis(process.env.REDIS_URL || "redis://localhost:6379/0");
const app = express();

// CRITICAL: raw middleware MUST come before json — signature is on raw bytes.
app.post("/webhooks/podium",
  express.raw({ type: "application/json", limit: "512kb" }),
  async (req, res) => {
    const raw = req.body as Buffer;                // raw bytes; do not re-encode
    const header = req.header("X-Podium-Signature") || "";

    const parts: Record<string, string> = {};
    for (const p of header.split(",")) {
      const [k, v] = p.split("=", 2);
      if (k && v) parts[k] = v;
    }
    const ts = parts.t, sig = parts.v1;
    if (!ts || !sig) return res.status(401).send("missing signature parts");

    const signedPayload = Buffer.concat([Buffer.from(`${ts}.`, "utf-8"), raw]);
    const expected = crypto.createHmac("sha256", SECRET).update(signedPayload).digest("hex");

    // Constant-time compare. Buffers MUST be the same length or timingSafeEqual throws.
    const recvBuf = Buffer.from(sig, "utf-8");
    const expBuf = Buffer.from(expected, "utf-8");
    if (recvBuf.length !== expBuf.length || !crypto.timingSafeEqual(recvBuf, expBuf)) {
      return res.status(401).send("signature mismatch");
    }

    if (Math.abs(Date.now() / 1000 - parseInt(ts, 10)) > 300) {
      return res.status(401).send("replay window exceeded");
    }

    const event = JSON.parse(raw.toString("utf-8"));
    const claimed = await R.set(`podium:evt:${event.id}`, "1", "EX", 86400, "NX");
    if (claimed !== "OK") return res.status(200).json({ status: "duplicate", event_id: event.id });

    try {
      await dispatch(event);
      return res.status(200).json({ status: "ok", event_id: event.id });
    } catch (e: any) {
      await R.lpush("podium:dlq", JSON.stringify({
        event_id: event.id, raw_body: raw.toString("utf-8"),
        signature_header: header, received_at: Date.now() / 1000,
        exception: `${e?.name}: ${e?.message}`,
      }));
      return res.status(500).send("dispatch failed");
    }
  }
);
```

## Redis schema

| Key pattern | Type | TTL | Purpose |
|---|---|---|---|
| `podium:evt:{event_id}` | string | 86400s (24h) | Dedup claim. Value is `"1"`, only existence matters. |
| `podium:dlq` | list | none | Failed event entries. LPUSH on persist, LRANGE for inspection, BRPOPLPUSH for atomic drain. |
| `podium:dlq:replayed` | list | 30 days | Audit trail of replayed entries. Append after successful replay. |
| `podium:rate:{client_ip}` | string | 60s | Optional inbound rate-limit counter (defense in depth against probing). |

**ACL recommendation**: a dedicated Redis user for the receiver with only the commands it needs:

- `SET`, `GET`, `EXPIRE` (dedup)
- `LPUSH`, `LRANGE`, `LLEN`, `BRPOPLPUSH` (DLQ)
- `INCR`, `EXPIRE` (rate-limit, if used)

Never grant `FLUSHDB`, `KEYS`, or `CONFIG`.

## DLQ backend choice matrix

| Backend | Throughput ceiling | Durability | When to choose |
|---|---|---|---|
| Redis list | ~50k/s LPUSH; bounded by Redis persistence config | AOF + replicas | Default for prod. Pair with an hourly archiver to S3/GCS. |
| SQLite (WAL mode) | ~1k/s sustained writes | fsync per commit | Single-node deployments; dev. Backup the file. |
| JSONL file | ~10k/s with buffered writes | Depends on FS flush | Fallback when nothing else is available. Easy to grep, ugly to drain. |
| Cloud queues (SQS / Pub/Sub) | ~unbounded | Provider SLA | Skip — adds latency to the failure path and is not needed at this scale. |

### Hourly archive (Redis → S3)

```python
import boto3, redis, json, gzip, time
from io import BytesIO

R = redis.from_url(os.environ["REDIS_URL"])
S3 = boto3.client("s3")
BUCKET = "podium-dlq-archive"

def archive_once() -> int:
    pipe = R.pipeline()
    pipe.lrange("podium:dlq", 0, -1)
    pipe.delete("podium:dlq")
    entries, _ = pipe.execute()
    if not entries:
        return 0
    buf = BytesIO()
    with gzip.GzipFile(fileobj=buf, mode="wb") as gz:
        for entry in entries:
            gz.write(entry + b"\n")
    key = f"dlq/{int(time.time())}-{len(entries)}.jsonl.gz"
    S3.put_object(Bucket=BUCKET, Key=key, Body=buf.getvalue())
    return len(entries)
```

Note: `LRANGE + DEL` is not atomic. If new entries arrive between the two, they're lost. For prod, use `BRPOPLPUSH` into a `podium:dlq:archiving` list, archive that, then delete it. Or just accept the race and accept the duplicate-archive on the next run (the entries are durable in the archive).

## In-memory dedup fallback (dev only)

For local dev without Redis, the receiver falls back to an in-process `dict` + lock + periodic eviction. Documented constraints:

- **Not shared across processes.** Two uvicorn workers will each have their own cache and duplicates can leak.
- **Lost on restart.** Within the first 24h after restart, replays may be processed twice.
- **Bounded size.** Hard-cap at 100k entries; eviction drops the oldest 10% when over the cap.

Production deployments MUST use Redis or SQLite. The in-memory backend is for `pytest` and `uvicorn --reload`, nothing else.

## Operator workflow

### Drain the DLQ after a handler fix

```bash
# 1. Verify the fix is deployed
curl -fsS https://your-receiver.example.com/healthz

# 2. Inspect the DLQ to confirm what will replay
redis-cli LLEN podium:dlq
redis-cli LRANGE podium:dlq 0 4 | jq .

# 3. Drain at a conservative rate that the downstream handler can absorb
python3 scripts/dlq_replay.py \
  --target-url https://your-receiver.example.com/webhooks/podium \
  --secret-env PODIUM_WEBHOOK_SECRET \
  --batch-size 25 --rate-per-sec 10

# 4. Confirm the DLQ is drained
redis-cli LLEN podium:dlq

# 5. Spot-check a replayed event landed correctly in the downstream system
```

### Signature-failure incident response

```bash
# 1. Identify the source IP(s) of failed signatures from access logs
# 2. Compute the rate — if > a few per minute, it's a probe
# 3. Add an iptables / Caddy / nginx-level block for the source IP(s)
# 4. Confirm the legitimate Podium delivery IP ranges are still allowed
# 5. Audit recent rotations — if the signing secret was rotated and a
#    Podium-side webhook config was NOT updated, all current deliveries fail.
```

## Library packaging notes

This skill ships the receiver inline in `scripts/webhook_server.py` rather than as a separate pip package. The rationale: the receiver is ~200 lines, every integration needs a custom dispatch function and secret-store binding, and an extracted package would require versioning that adds maintenance overhead without enabling reuse. If three concrete callers depend on identical behavior, promote to `@intentsolutions/podium-webhook` on npm or `intent-podium-webhook` on PyPI.

## Testing matrix (what `tests/` should cover when this skill is integrated)

| Test | Type | What it proves |
|---|---|---|
| `test_signature_verify_happy_path` | unit | Correct body + secret + header → True |
| `test_signature_verify_mutated_body` | unit | One byte changed → False |
| `test_signature_verify_uses_compare_digest` | unit | Verify via mocking that `==` is NOT used |
| `test_replay_window_skew_positive` | unit | ts > now + 300s → False |
| `test_replay_window_skew_negative` | unit | ts < now - 300s → False |
| `test_dedup_claim_atomic` | integration | 100 concurrent claims of same id → exactly 1 succeeds |
| `test_dedup_ttl_matches_retry_ceiling` | unit | TTL is exactly 86400s |
| `test_dlq_persist_before_5xx` | integration | Handler raise → DLQ entry exists BEFORE response sent |
| `test_dlq_replay_skips_duplicates` | integration | Replay 100 entries; 80 already processed → only 20 dispatch |
| `test_batch_sort_by_occurred_at` | unit | Out-of-order input → sorted output |
| `test_out_of_order_defers_to_dlq` | integration | delete-before-create defers, replay succeeds |
| `test_fail_closed_on_redis_outage` | chaos | Redis killed → receiver returns 503, not 200 |
