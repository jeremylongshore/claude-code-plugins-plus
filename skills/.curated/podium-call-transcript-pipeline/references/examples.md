# Examples — podium-call-transcript-pipeline

Ten complete worked examples. Each is runnable end-to-end with the env vars listed at the top of the snippet.

## 1. Minimal single-location ingest (FastAPI + SQLite + Redis Streams)

```python
# env: PODIUM_WEBHOOK_SECRET, PODIUM_TRANSCRIPT_INBOX_PATH, REDIS_URL
import json, time
from fastapi import FastAPI, Request, HTTPException
from podium_webhook_reliability import verify_webhook    # consumed by reference
from podium_call_transcript_pipeline.inbox import Inbox

app = FastAPI()
inbox = Inbox(path="podium_transcripts.db")

@app.post("/podium/transcripts")
async def webhook(req: Request):
    raw = await req.body()
    if not verify_webhook(raw, req.headers.get("podium-signature", "")):
        raise HTTPException(401, "invalid signature")
    event = json.loads(raw)
    if not event.get("type", "").startswith("call.transcript."):
        return {"status": "ignored"}
    inbox.insert(
        transcript_id=event["data"]["transcript_id"],
        event_type=event["type"],
        received_at=time.time(),
        raw_payload=raw,
    )
    return {"status": "accepted"}
```

Run with: `uvicorn webhook_ingest:app --host 0.0.0.0 --port 8080`.

## 2. Processor loop (separate process)

```python
import time
from podium_call_transcript_pipeline.inbox import Inbox
from podium_call_transcript_pipeline.processor import process_pending
from podium_call_transcript_pipeline.queue import RedisStreamsQueue

inbox = Inbox(path="podium_transcripts.db")
queue = RedisStreamsQueue(url="redis://localhost:6379/0")

while True:
    n = process_pending(inbox, queue, max_batch=50)
    if n == 0:
        time.sleep(5)
```

Deploy as a `systemd` service or container alongside the webhook handler.

## 3. Redact a transcript JSON via the CLI

```bash
# Input is the raw transcript event payload from Podium.
# Output is a redacted copy + a JSONL audit log of every redaction.
python3 scripts/pii_redact.py \
  --input  transcript-raw.json \
  --output transcript-redacted.json \
  --audit-log redactions.jsonl
```

Audit log line example:

```json
{"transcript_id": "{transcript-id}", "segment_index": 3, "category": "CREDIT_CARD", "rule_id": "card_luhn_16", "start": 42, "end": 61, "ts": 1736900000.12}
```

## 4. Chunk a redacted transcript with speaker-preserving overlap

```bash
python3 scripts/transcript_chunker.py \
  --input transcript-redacted.json \
  --output chunks.json \
  --target-tokens 1500 \
  --overlap-tokens 200
```

Output `chunks.json`:

```json
{
  "transcript_id": "{transcript-id}",
  "chunks": [
    {
      "chunk_index": 0,
      "speakers": ["caller", "agent"],
      "token_count": 1480,
      "segments": [
        {"speaker_role": "caller", "start_ms": 0,    "end_ms": 4200,  "text": "Hi, calling about the booking..."},
        {"speaker_role": "agent",  "start_ms": 4400, "end_ms": 9100,  "text": "Sure, can I get the booking reference?"}
      ]
    },
    {
      "chunk_index": 1,
      "speakers": ["agent", "caller"],
      "token_count": 1520,
      "segments": [
        {"speaker_role": "agent",  "start_ms": 7800, "end_ms": 9100,  "text": "Sure, can I get the booking reference?"},
        {"speaker_role": "caller", "start_ms": 9300, "end_ms": 18200, "text": "It's RV-{redacted-id}..."}
      ]
    }
  ]
}
```

Note that chunk 1's first segment is the trailing overlap from chunk 0.

## 5. Fallback poller for missing transcripts

```bash
# Run on cron / scheduled task. Idempotent — re-running over the same window is safe.
python3 scripts/transcript_poller.py \
  --since-hours 12 \
  --max-age-hours 4 \
  --location-uid "{location-uid}" \
  --inbox-path ./podium_transcripts.db
```

The poller:

1. Lists conversations updated in the last 12h with a call.
2. For each conversation without a transcript event in the inbox AND whose call ended >4h ago, fetches the transcript directly.
3. Synthesizes a `call.transcript.completed` inbox row tagged `source=poller`.

## 6. Multi-location agency (multi-tenant)

```python
# Each location_uid maps to its own inbox + queue stream. Cross-location records never mix.
import os
from podium_call_transcript_pipeline.inbox import Inbox
from podium_call_transcript_pipeline.queue import RedisStreamsQueue

LOCATIONS = {
    "kombilife-sydney":         "podium_sydney.db",
    "kombilife-burleigh-heads": "podium_burleigh.db",
}

inboxes = {loc: Inbox(path=path) for loc, path in LOCATIONS.items()}
queues  = {loc: RedisStreamsQueue(url=os.environ["REDIS_URL"], stream=f"podium:{loc}")
           for loc in LOCATIONS}

def ingest_for_location(location_uid: str, event: dict, raw: bytes) -> None:
    inboxes[location_uid].insert(
        transcript_id=event["data"]["transcript_id"],
        event_type=event["type"],
        received_at=time.time(),
        raw_payload=raw,
    )
```

The webhook handler routes by `event["data"]["location_uid"]` to the matching inbox.

## 7. Custom PII recognizer for Australian Tax File Number (TFN)

```python
# AU TFN is 8 or 9 digits, with a checksum. Not covered by the default regex layer.
import re
from podium_call_transcript_pipeline.redactor import register_recognizer

TFN_PATTERN = re.compile(r"\b\d{3}\s?\d{3}\s?\d{2,3}\b")
TFN_WEIGHTS = [1, 4, 3, 7, 5, 8, 6, 9, 10]   # 9-digit; truncate for 8-digit

def tfn_valid(s: str) -> bool:
    digits = [int(c) for c in s if c.isdigit()]
    if len(digits) not in (8, 9): return False
    weights = TFN_WEIGHTS[:len(digits)]
    return sum(d*w for d, w in zip(digits, weights)) % 11 == 0

register_recognizer(
    category="AU_TFN",
    rule_id="tfn_au_checksum",
    pattern=TFN_PATTERN,
    validator=tfn_valid,
)
```

Once registered, the redactor applies it on every segment.

## 8. SQS instead of Redis Streams

```python
# env: AWS_REGION, PODIUM_TRANSCRIPT_QUEUE_URL
import boto3, json
from podium_call_transcript_pipeline.queue import Queue

class SQSQueue(Queue):
    def __init__(self, queue_url: str):
        self.client = boto3.client("sqs")
        self.queue_url = queue_url

    def enqueue(self, record: dict) -> None:
        self.client.send_message(
            QueueUrl=self.queue_url,
            MessageBody=json.dumps(record),
            MessageAttributes={
                "language": {"StringValue": record["detected_language"], "DataType": "String"},
                "transcript_id": {"StringValue": record["transcript_id"], "DataType": "String"},
            },
        )
```

Drop into the processor in place of `RedisStreamsQueue` — same interface, no code-path changes.

## 9. Detect oversize segments before they hit the chunker

```bash
# Inspect a transcript for segments that will produce oversize chunks (ERR_TXP_006).
python3 scripts/transcript_chunker.py \
  --input transcript-redacted.json \
  --dry-run \
  --warn-on-oversize
```

Output (stderr):

```
WARN: segment 14 (speaker=caller, duration=842s) ~ 3200 tokens > 1500 target.
This chunk will not be split. Consider Podium upstream segment splitting.
```

## 10. End-to-end integration test (CI gate — no raw PII reaches queue)

```python
import json
import pytest
from podium_call_transcript_pipeline.processor import build_outbound_record

PII_FIXTURES = [
    "4111-1111-1111-1111",   # valid Luhn — must be redacted
    "alice@example.com",
    "+61 2 9000 0000",
    "123-45-6789",
]

@pytest.mark.parametrize("pii", PII_FIXTURES)
def test_pii_never_reaches_outbound_record(pii: str):
    raw = json.dumps({
        "type": "call.transcript.completed",
        "data": {
            "transcript_id": "tx_test_001",
            "call_id": "call_test_001",
            "location_uid": "loc_test",
            "segments": [
                {"speaker_role": "caller", "start_ms": 0, "end_ms": 1000,
                 "text": f"My number is {pii}"},
            ],
        },
    }).encode()
    record = build_outbound_record("tx_test_001", "call.transcript.completed", raw)
    # The redacted record must not contain the original PII anywhere.
    blob = json.dumps(record)
    assert pii not in blob, f"PII leaked into outbound record: {pii}"
    # The record must have a redaction_count > 0.
    assert record["redaction_count"] >= 1
```

Wire this test into CI; it fails the build if redaction regresses.
