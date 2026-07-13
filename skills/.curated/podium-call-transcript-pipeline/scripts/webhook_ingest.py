#!/usr/bin/env python3
"""webhook_ingest.py — FastAPI handler for Podium call-transcript webhooks.

Run with:
  uvicorn webhook_ingest:app --host 0.0.0.0 --port 8080 --workers 4

The handler does exactly three things synchronously:
  1. Verify the webhook signature (consumed from podium-webhook-reliability).
  2. Insert the raw event into the durable inbox (SQLite WAL).
  3. Return 200 OK.

All transcript processing (reconciliation, language detection, redaction,
chunking, queue write) happens out-of-band in the processor loop. This handler
is intentionally minimal — its p95 latency budget is 250ms.

Exit / response codes:
  200  event accepted and durably stored
  401  signature verification failed
  5xx  inbox insert failed — Podium will retry the webhook
"""

from __future__ import annotations
import json
import os
import sqlite3
import sys
import time
from pathlib import Path

# Import guard — this file is also a CLI for ad-hoc inbox queries.
try:
    from fastapi import FastAPI, Request, HTTPException

    FASTAPI_AVAILABLE = True
except ImportError:
    FASTAPI_AVAILABLE = False


INBOX_PATH = Path(os.environ.get("PODIUM_TRANSCRIPT_INBOX_PATH", "./podium_transcripts.db"))

SCHEMA = """
CREATE TABLE IF NOT EXISTS inbox (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id   TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    received_at     REAL NOT NULL,
    raw_payload     BLOB NOT NULL,
    processed_at    REAL,
    enqueued_at     REAL,
    attempt_count   INTEGER NOT NULL DEFAULT 0,
    next_attempt_at REAL,
    last_error      TEXT,
    source          TEXT NOT NULL DEFAULT 'webhook',
    UNIQUE(transcript_id, event_type)
);
CREATE INDEX IF NOT EXISTS idx_inbox_pending
    ON inbox(processed_at, next_attempt_at)
    WHERE processed_at IS NULL;

CREATE TABLE IF NOT EXISTS inbox_deadletter (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    transcript_id   TEXT NOT NULL,
    event_type      TEXT NOT NULL,
    received_at     REAL NOT NULL,
    raw_payload     BLOB NOT NULL,
    last_error      TEXT,
    attempt_count   INTEGER NOT NULL,
    dead_lettered_at REAL NOT NULL DEFAULT (strftime('%s','now'))
);
"""


def _connect() -> sqlite3.Connection:
    INBOX_PATH.parent.mkdir(parents=True, exist_ok=True)
    db = sqlite3.connect(str(INBOX_PATH), isolation_level=None, check_same_thread=False)
    db.executescript(SCHEMA)
    db.execute("PRAGMA journal_mode=WAL")
    db.execute("PRAGMA synchronous=NORMAL")
    return db


def insert_inbox(
    db: sqlite3.Connection,
    transcript_id: str,
    event_type: str,
    received_at: float,
    raw_payload: bytes,
    source: str = "webhook",
) -> bool:
    """Insert an event into the inbox. Returns True if inserted, False if duplicate."""
    cur = db.execute(
        "INSERT OR IGNORE INTO inbox(transcript_id, event_type, received_at, raw_payload, source) "
        "VALUES (?, ?, ?, ?, ?)",
        (transcript_id, event_type, received_at, raw_payload, source),
    )
    return cur.rowcount == 1


# ---------------------------------------------------------------------------
# FastAPI surface
# ---------------------------------------------------------------------------

if FASTAPI_AVAILABLE:
    app = FastAPI(title="podium-call-transcript-pipeline ingest")
    _db = _connect()

    def _verify(raw: bytes, signature: str) -> bool:
        """Verify the webhook signature.

        Wire this to your installed podium-webhook-reliability verify_webhook().
        The fallback below is a placeholder that REFUSES every request — never
        ship without wiring the real verifier.
        """
        try:
            from podium_webhook_reliability import verify_webhook

            return verify_webhook(raw, signature)
        except ImportError:
            # Refuse rather than allow — fail closed.
            return False

    @app.post("/podium/transcripts")
    async def transcript_webhook(request: Request):
        raw = await request.body()
        signature = request.headers.get("podium-signature", "")
        if not _verify(raw, signature):
            raise HTTPException(401, "ERR_TXP_008 signature verification failed")

        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            raise HTTPException(400, "ERR_TXP_010 malformed JSON")

        event_type = event.get("type", "")
        if not event_type.startswith("call.transcript.") and event_type != "call.ended":
            return {"status": "ignored", "reason": "not_a_transcript_or_call_event"}

        transcript_id = (event.get("data") or {}).get("transcript_id") or (event.get("data") or {}).get("call_id")
        if not transcript_id:
            raise HTTPException(400, "ERR_TXP_010 missing transcript_id / call_id")

        try:
            inserted = insert_inbox(
                _db,
                transcript_id=transcript_id,
                event_type=event_type,
                received_at=time.time(),
                raw_payload=raw,
            )
        except sqlite3.OperationalError as e:
            # Disk full, locked, etc. Return 5xx so Podium retries.
            raise HTTPException(503, f"ERR_TXP_009 inbox write failed: {e}")

        return {"status": "accepted" if inserted else "duplicate"}


# ---------------------------------------------------------------------------
# CLI surface (ad-hoc inbox queries)
# ---------------------------------------------------------------------------


def _cli() -> int:
    import argparse

    ap = argparse.ArgumentParser(description="Ad-hoc inbox queries (not for serving webhooks)")
    sub = ap.add_subparsers(dest="cmd", required=True)

    sub.add_parser("init", help="Create the inbox schema and exit")
    list_p = sub.add_parser("list", help="List pending or recent rows")
    list_p.add_argument("--pending", action="store_true")
    list_p.add_argument("--limit", type=int, default=20)

    args = ap.parse_args()
    db = _connect()

    if args.cmd == "init":
        print(f"inbox initialized at {INBOX_PATH}", file=sys.stderr)
        return 0

    if args.cmd == "list":
        where = "WHERE processed_at IS NULL" if args.pending else ""
        rows = db.execute(
            f"SELECT id, transcript_id, event_type, received_at, processed_at, attempt_count "
            f"FROM inbox {where} ORDER BY received_at DESC LIMIT ?",
            (args.limit,),
        ).fetchall()
        for r in rows:
            print(
                json.dumps(
                    {
                        "id": r[0],
                        "transcript_id": r[1],
                        "event_type": r[2],
                        "received_at": r[3],
                        "processed_at": r[4],
                        "attempt_count": r[5],
                    }
                )
            )
        return 0

    return 2


if __name__ == "__main__":
    sys.exit(_cli())
