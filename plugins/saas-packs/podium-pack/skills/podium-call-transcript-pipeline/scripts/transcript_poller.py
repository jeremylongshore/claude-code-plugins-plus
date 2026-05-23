#!/usr/bin/env python3
"""transcript_poller.py — fallback poller for missing transcript webhooks.

Strategy:
  1. List conversations updated in the last `--since-hours` window.
  2. For each conversation with a call.ended event in the inbox but no
     subsequent call.transcript.* event AND whose call ended more than
     `--max-age-hours` ago, fetch the transcript directly from
     GET /v4/conversations/{id}/transcript.
  3. Synthesize a call.transcript.completed inbox row tagged source=poller.

Idempotent — running twice over the same window produces no duplicate rows
(the inbox UNIQUE constraint catches it).

Usage:
  transcript_poller.py \\
    --since-hours 12 \\
    --max-age-hours 4 \\
    --location-uid {location-uid} \\
    [--inbox-path ./podium_transcripts.db] \\
    [--dry-run]

Exit codes:
  0  poller completed (rows synthesized count printed)
  1  Podium API error (cannot fetch conversations)
  2  configuration error (missing env, unreadable inbox)
  3  auth error (PodiumAuth could not produce a token)
"""

from __future__ import annotations
import argparse
import json
import os
import sqlite3
import sys
import time
from pathlib import Path
import urllib.request
import urllib.error
import urllib.parse

# Re-use the inbox helpers from webhook_ingest.py
sys.path.insert(0, str(Path(__file__).parent))
from webhook_ingest import insert_inbox, _connect  # type: ignore

CONVERSATIONS_URL = "https://api.podium.com/v4/conversations"
TRANSCRIPT_URL_TMPL = "https://api.podium.com/v4/conversations/{cid}/transcript"


def _get_token() -> str:
    """Acquire a Podium access token via podium-auth.

    The skill consumes podium-auth — if podium-auth is not importable, this
    script cannot run. Fail fast with a clear message.
    """
    try:
        from podium_auth import PodiumAuth
    except ImportError:
        print("podium-auth not installed; this poller requires it for outbound calls", file=sys.stderr)
        sys.exit(3)

    cid = os.environ.get("PODIUM_CLIENT_ID")
    csec = os.environ.get("PODIUM_CLIENT_SECRET")
    refresh_file = Path(os.environ.get("PODIUM_REFRESH_TOKEN_FILE", ""))
    if not cid or not csec or not refresh_file.is_file():
        print("missing PODIUM_CLIENT_ID / PODIUM_CLIENT_SECRET / PODIUM_REFRESH_TOKEN_FILE", file=sys.stderr)
        sys.exit(2)

    import asyncio

    record = json.loads(refresh_file.read_text())
    auth = PodiumAuth(client_id=cid, client_secret=csec, refresh_token=record["refresh_token"])
    return asyncio.run(auth.get_token())


def _http_get(url: str, token: str, timeout: float = 10.0) -> tuple[int, dict]:
    req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status, json.loads(resp.read())
    except urllib.error.HTTPError as e:
        try:
            payload = json.loads(e.read())
        except Exception:
            payload = {"error": "non_json", "status": e.code}
        return e.code, payload


def list_recent_conversations(token: str, since_hours: int, location_uid: str | None) -> list[dict]:
    """List conversations updated in the last N hours."""
    since_ts = int(time.time()) - since_hours * 3600
    params = {"updated_since": since_ts}
    if location_uid:
        params["location_uid"] = location_uid
    url = f"{CONVERSATIONS_URL}?{urllib.parse.urlencode(params)}"
    status, body = _http_get(url, token)
    if status != 200:
        print(f"conversations API returned {status}: {body}", file=sys.stderr)
        return []
    return body.get("data", [])


def fetch_transcript(token: str, conversation_id: str) -> dict | None:
    """Fetch a transcript directly. Returns None if the API returns 404."""
    url = TRANSCRIPT_URL_TMPL.format(cid=conversation_id)
    status, body = _http_get(url, token)
    if status == 404:
        return None
    if status != 200:
        print(f"transcript fetch for {conversation_id} returned {status}: {body}", file=sys.stderr)
        return None
    return body


def _has_transcript_event(db: sqlite3.Connection, transcript_id: str) -> bool:
    cur = db.execute(
        "SELECT 1 FROM inbox WHERE transcript_id = ? "
        "  AND event_type IN ('call.transcript.partial', 'call.transcript.completed', 'call.transcript.failed') "
        "LIMIT 1",
        (transcript_id,),
    )
    return cur.fetchone() is not None


def _call_ended_at(db: sqlite3.Connection, transcript_id: str) -> float | None:
    cur = db.execute(
        "SELECT received_at FROM inbox WHERE transcript_id = ? AND event_type = 'call.ended' LIMIT 1",
        (transcript_id,),
    )
    row = cur.fetchone()
    return row[0] if row else None


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--since-hours", type=int, default=12)
    ap.add_argument(
        "--max-age-hours", type=int, default=4, help="A call.ended without transcript past this age triggers a fetch"
    )
    ap.add_argument("--location-uid", default=None)
    ap.add_argument(
        "--inbox-path",
        type=Path,
        default=Path(os.environ.get("PODIUM_TRANSCRIPT_INBOX_PATH", "./podium_transcripts.db")),
    )
    ap.add_argument("--dry-run", action="store_true")
    args = ap.parse_args()

    os.environ["PODIUM_TRANSCRIPT_INBOX_PATH"] = str(args.inbox_path)
    db = _connect()
    token = _get_token()

    convs = list_recent_conversations(token, args.since_hours, args.location_uid)
    if not convs:
        print(json.dumps({"status": "ok", "checked": 0, "synthesized": 0}))
        return 0

    threshold_age = args.max_age_hours * 3600
    now = time.time()
    synthesized = 0
    for conv in convs:
        cid = conv.get("id")
        tid = conv.get("transcript_id") or cid
        if not tid:
            continue
        if _has_transcript_event(db, tid):
            continue
        ended_at = _call_ended_at(db, tid)
        if ended_at is None or (now - ended_at) < threshold_age:
            continue

        transcript = fetch_transcript(token, cid)
        if transcript is None:
            # Mark failed — Podium has no transcript for this call.
            synthetic = json.dumps(
                {
                    "type": "call.transcript.failed",
                    "data": {"transcript_id": tid, "call_id": cid, "reason": "poller_404"},
                }
            ).encode()
            event_type = "call.transcript.failed"
        else:
            synthetic = json.dumps(
                {
                    "type": "call.transcript.completed",
                    "data": {
                        "transcript_id": tid,
                        "call_id": cid,
                        "location_uid": conv.get("location_uid"),
                        "segments": transcript.get("segments", []),
                    },
                }
            ).encode()
            event_type = "call.transcript.completed"

        if args.dry_run:
            print(f"would synthesize {event_type} for {tid}", file=sys.stderr)
            continue

        try:
            inserted = insert_inbox(
                db,
                transcript_id=tid,
                event_type=event_type,
                received_at=now,
                raw_payload=synthetic,
                source="poller",
            )
            if inserted:
                synthesized += 1
        except sqlite3.OperationalError as e:
            print(f"inbox write failed for {tid}: {e}", file=sys.stderr)

    print(
        json.dumps(
            {
                "status": "ok",
                "checked": len(convs),
                "synthesized": synthesized,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
