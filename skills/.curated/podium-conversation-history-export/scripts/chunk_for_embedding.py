#!/usr/bin/env python3
"""chunk_for_embedding.py — chunk a JSONL export into vector-store-ready chunks.

Streams a gzip-JSONL export line-by-line, chunks each record's messages with
windowed semantic boundaries (token cap + idle-gap break + overlap), redacts
PII at chunk-emit time, and writes deterministic-id chunks to a gzip-JSONL
output. Memory cost is O(window-size) per chunk, not O(thread-size).

Usage:
  chunk_for_embedding.py \\
    --input ./exports/conversations.jsonl.gz \\
    --output ./exports/chunks.jsonl.gz \\
    [--target-tokens 1500] \\
    [--overlap-tokens 200] \\
    [--idle-gap-break-seconds 86400] \\
    [--redact-pii]

Output format (one JSON per line):
  {
    "chunk_id":          "<source_id>:<start_msg_id>:<end_msg_id>",
    "source_id":         "<conv_or_review_id>",
    "source_type":       "conversation|review|contact",
    "created_at_window": [start_unix, end_unix],
    "token_estimate":    1487,
    "pii_redacted":      true,
    "body":              "..."
  }

Exit codes:
  0  success
  1  IO error
  2  ERR_EXPORT_006 PII pattern raised
  3  ERR_EXPORT_012 PII patterns module missing
"""

from __future__ import annotations
import argparse
import gzip
import json
import re
import sys
from pathlib import Path
from typing import Iterator

# Inline PII patterns as a fallback. In production, prefer importing the shared
# pattern set from podium-call-transcript-pipeline (podium_pii.patterns) so a
# single change updates every PII surface in the pack atomically.
_FALLBACK_PII_PATTERNS = [
    (re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), "[REDACTED_SSN]"),
    (re.compile(r"\b(?:\d[ -]*?){13,16}\b"), "[REDACTED_CARD]"),
    (re.compile(r"\b[A-Z]{1,2}\d{6,9}\b"), "[REDACTED_LICENSE]"),
    (
        re.compile(r"\b\d{1,5} [\w ]{1,40}(?:Street|St|Ave|Avenue|Rd|Road|Blvd|Drive|Dr|Lane|Ln|Way|Court|Ct)\b", re.I),
        "[REDACTED_ADDR]",
    ),
    (re.compile(r"[\w\.-]+@[\w\.-]+\.\w+"), "[REDACTED_EMAIL]"),
    (re.compile(r"\+?\d{1,3}[ -.]?\(?\d{3}\)?[ -.]?\d{3}[ -.]?\d{4}"), "[REDACTED_PHONE]"),
]


def load_pii_patterns():
    """Prefer the shared patterns from podium-call-transcript-pipeline; fall back to inline."""
    try:
        from podium_pii import patterns as shared  # type: ignore

        return shared.PII_PATTERNS
    except Exception:
        return _FALLBACK_PII_PATTERNS


def approx_tokens(text: str) -> int:
    return max(1, len(text) // 4)


def redact(text: str, patterns) -> str:
    out = text
    for pat, repl in patterns:
        try:
            out = pat.sub(repl, out)
        except Exception as e:
            raise RuntimeError(f"ERR_EXPORT_006 pii pattern raised: {e}")
    return out


def chunk_messages(
    source_id: str,
    source_type: str,
    messages: list[dict],
    target_tokens: int,
    overlap_tokens: int,
    idle_gap_break_seconds: int,
    patterns,
    redact_pii: bool,
) -> Iterator[dict]:
    """Yield chunks. Bounded memory: only holds the current window in RAM."""
    if not messages:
        return

    current: list[dict] = []
    current_tokens = 0
    prev_ts = None

    def _emit(buf: list[dict]) -> dict:
        body_raw = "\n".join(f"[{m.get('sender_type', 'unknown')}] {m.get('body', '')}" for m in buf)
        body = redact(body_raw, patterns) if redact_pii else body_raw
        return {
            "chunk_id": f"{source_id}:{buf[0]['id']}:{buf[-1]['id']}",
            "source_id": source_id,
            "source_type": source_type,
            "created_at_window": [buf[0].get("created_at"), buf[-1].get("created_at")],
            "token_estimate": approx_tokens(body),
            "pii_redacted": bool(redact_pii),
            "body": body,
        }

    for msg in messages:
        msg_tokens = approx_tokens(msg.get("body", ""))
        ts = msg.get("created_at")
        idle_gap = (ts - prev_ts) if (ts is not None and prev_ts is not None) else 0
        prev_ts = ts

        force_break = current and (
            current_tokens + msg_tokens > target_tokens or (idle_gap is not None and idle_gap > idle_gap_break_seconds)
        )
        if force_break:
            yield _emit(current)
            # Carry overlap window
            carry: list[dict] = []
            carry_tokens = 0
            for m in reversed(current):
                t = approx_tokens(m.get("body", ""))
                if carry_tokens + t > overlap_tokens:
                    break
                carry.insert(0, m)
                carry_tokens += t
            current = carry
            current_tokens = carry_tokens

        current.append(msg)
        current_tokens += msg_tokens

    if current:
        yield _emit(current)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--target-tokens", type=int, default=1500)
    ap.add_argument("--overlap-tokens", type=int, default=200)
    ap.add_argument("--idle-gap-break-seconds", type=int, default=86400)
    ap.add_argument("--redact-pii", action="store_true", default=False)
    ap.add_argument("--source-type", default="conversation", choices=("conversation", "review", "contact"))
    args = ap.parse_args()

    try:
        patterns = load_pii_patterns()
    except Exception as e:
        print(f"ERR_EXPORT_012 pii patterns module missing: {e}", file=sys.stderr)
        return 3

    open_in = gzip.open if str(args.input).endswith(".gz") else open
    args.output.parent.mkdir(parents=True, exist_ok=True)

    chunks_emitted = 0
    sources_processed = 0
    with open_in(args.input, "rt", encoding="utf-8") as fin, gzip.open(args.output, "wt", encoding="utf-8") as fout:
        for line in fin:
            row = json.loads(line)
            sources_processed += 1

            source_id = row.get("id") or row.get("uid")
            if not source_id:
                continue

            # Reviews and contacts collapse to a single "message" by treating
            # the row body itself as the only message in the thread.
            if args.source_type == "conversation":
                messages = row.get("messages") or []
                # If messages aren't embedded in the export (separate endpoint),
                # use the conversation summary fields as a single fallback message.
                if not messages:
                    messages = [
                        {
                            "id": f"{source_id}_summary",
                            "body": row.get("preview") or row.get("subject") or "",
                            "created_at": row.get("created_at"),
                            "sender_type": "system",
                        }
                    ]
            else:
                messages = [
                    {
                        "id": f"{source_id}_body",
                        "body": row.get("body") or row.get("review_body") or row.get("notes") or "",
                        "created_at": row.get("created_at"),
                        "sender_type": args.source_type,
                    }
                ]

            try:
                for chunk in chunk_messages(
                    source_id=str(source_id),
                    source_type=args.source_type,
                    messages=messages,
                    target_tokens=args.target_tokens,
                    overlap_tokens=args.overlap_tokens,
                    idle_gap_break_seconds=args.idle_gap_break_seconds,
                    patterns=patterns,
                    redact_pii=args.redact_pii,
                ):
                    fout.write(json.dumps(chunk, separators=(",", ":")))
                    fout.write("\n")
                    chunks_emitted += 1
                    if chunks_emitted % 1000 == 0:
                        fout.flush()
            except RuntimeError as e:
                print(str(e), file=sys.stderr)
                return 2

    print(
        json.dumps(
            {
                "sources_processed": sources_processed,
                "chunks_emitted": chunks_emitted,
                "pii_redacted": bool(args.redact_pii),
                "out": str(args.output),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
