#!/usr/bin/env python3
"""session_timeout_monitor.py — scan in-flight webchat sessions for idle expiry.

Reads a JSON sessions snapshot file (one record per active session), classifies
each by idle status, and emits prompts or closures as appropriate.

Usage:
  session_timeout_monitor.py \\
    --sessions-file /var/run/webchat/active-sessions.json \\
    [--warn-after 1200] [--close-after 1680] \\
    [--partial-state-dir /var/lib/webchat-partial-state] \\
    [--output json|human]

Sessions-file format (JSON array):
  [
    {
      "session_uid": "sess-abc",
      "phone_e164":  "+61412345678",
      "location_uid":"{your-location-uid}",
      "last_message_at": 1746000000.0,
      "partial_state":   {"step": 1, "answer_so_far": "1"}
    },
    ...
  ]

Exit codes:
  0  scan completed (some sessions may have been warned or closed)
  1  sessions-file missing or unreadable
  2  partial-state persistence failure for one or more closed sessions
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import time
from pathlib import Path


def status_for(last_message_at: float, warn_after: int, close_after: int) -> str:
    idle = time.time() - last_message_at
    if idle >= close_after:
        return "close"
    if idle >= warn_after:
        return "warn"
    return "active"


def persist_partial_state(record: dict, dir_path: Path) -> None:
    phone = record["phone_e164"]
    loc = record["location_uid"]
    safe_phone = phone.replace("+", "p")
    path = dir_path / f"{safe_phone}__{loc}.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(
        json.dumps(
            {
                "session_uid": record["session_uid"],
                "phone_e164": phone,
                "location_uid": loc,
                "partial_state": record.get("partial_state") or {},
                "persisted_at": time.time(),
            }
        )
    )
    os.replace(tmp, path)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sessions-file", required=True, type=Path)
    ap.add_argument("--warn-after", type=int, default=20 * 60)
    ap.add_argument("--close-after", type=int, default=28 * 60)
    ap.add_argument("--partial-state-dir", type=Path, default=Path("/tmp/webchat-partial-state"))
    ap.add_argument("--output", choices=("json", "human"), default="human")
    args = ap.parse_args()

    if args.close_after <= args.warn_after:
        print("close-after must be strictly greater than warn-after", file=sys.stderr)
        return 1

    try:
        sessions = json.loads(args.sessions_file.read_text())
    except FileNotFoundError:
        print(f"sessions-file not found: {args.sessions_file}", file=sys.stderr)
        return 1
    except (OSError, json.JSONDecodeError) as e:
        print(f"could not read sessions-file: {e}", file=sys.stderr)
        return 1

    scanned = len(sessions)
    active = warned = closed = errors = 0
    persist_failures: list[str] = []

    for rec in sessions:
        st = status_for(rec["last_message_at"], args.warn_after, args.close_after)
        if st == "active":
            active += 1
            continue
        if st == "warn":
            warned += 1
            print(f"WARN session={rec['session_uid']} phone=****{rec['phone_e164'][-4:]}", file=sys.stderr)
            continue
        # close
        try:
            persist_partial_state(rec, args.partial_state_dir)
            closed += 1
            print(f"CLOSE session={rec['session_uid']} phone=****{rec['phone_e164'][-4:]}", file=sys.stderr)
        except OSError as e:
            errors += 1
            persist_failures.append(rec["session_uid"])
            print(f"ERR_WEBCHAT_013 partial_state_hydration_failure session={rec['session_uid']}: {e}", file=sys.stderr)

    summary = {
        "scanned": scanned,
        "active": active,
        "warned": warned,
        "closed": closed,
        "errors": errors,
        "persist_failures": persist_failures,
    }
    if args.output == "json":
        print(json.dumps(summary))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
    return 2 if errors else 0


if __name__ == "__main__":
    sys.exit(main())
