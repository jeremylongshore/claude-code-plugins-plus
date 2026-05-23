#!/usr/bin/env python3
"""transcript_to_llm.py — format a transcript turn + RAG context bundle into an LLM prompt.

Reads a bundle (the JSON output of context_fetch.py) and a transcript turn, emits a
structured prompt with explicit blocks so the model can distinguish live state (always
authoritative) from historical excerpts (hints).

Usage:
  transcript_to_llm.py \\
    --transcript "I had a question about my last order" \\
    --bundle-file ./bundle.json \\
    [--system-prompt-file ./system.txt] \\
    [--max-tokens 4000] \\
    [--output llm|json]

Exit codes:
  0  ok — prompt emitted
  1  config error (unreadable bundle or system prompt)
  2  budget error (assembled prompt exceeds --max-tokens; truncation would be unsafe)
"""

from __future__ import annotations
import argparse
import json
import sys
from pathlib import Path


def approx_tokens(s: str, chars_per_token: int = 4) -> int:
    return max(1, len(s) // chars_per_token)


def format_prompt(transcript: str, bundle: dict, system: str) -> str:
    parts: list[str] = []
    if system:
        parts.append("=== SYSTEM ===")
        parts.append(system.strip())
        parts.append("")

    parts.append("=== LIVE CONTACT (current truth, always authoritative) ===")
    contact = bundle.get("contact") or {}
    if contact.get("live_fields_available"):
        for k in ("phone", "email", "opt_out_sms", "opt_out_email", "location_uid", "last_seen_at"):
            if k in contact and contact[k] is not None:
                parts.append(f"  {k}: {contact[k]}")
    else:
        parts.append("  (live contact lookup unavailable; treat any contact info in transcript as unverified)")
    parts.append("")

    parts.append("=== HISTORICAL CONTEXT (hints, not authoritative; ordered by rerank score) ===")
    excerpts = bundle.get("historical_excerpts") or []
    if not excerpts:
        parts.append("  (no relevant historical context found)")
    for i, e in enumerate(excerpts, 1):
        score = e.get("rerank_score", 0.0)
        occ = e.get("occurred_at", "unknown")
        ch = e.get("channel", "unknown")
        trunc = " [TRUNCATED]" if e.get("truncated") else ""
        parts.append(f"  [{i}] channel={ch} occurred_at={occ} rerank={score:.2f}{trunc}")
        parts.append(f"      {e.get('content', '')}")
    parts.append("")

    meta = bundle.get("meta") or {}
    if meta.get("partial"):
        parts.append("=== DEGRADED MODE NOTICE ===")
        parts.append(
            f"  This context was assembled under timeout (elapsed={meta.get('elapsed_ms')}ms,"
            f" budget={meta.get('timeout_ms')}ms)."
        )
        parts.append(f"  had_vector_hits={meta.get('had_vector_hits')} had_live_lookup={meta.get('had_live_lookup')}")
        parts.append("  Ground answers conservatively; ask the customer to confirm any uncertain details.")
        parts.append("")

    parts.append("=== TRANSCRIPT TURN ===")
    parts.append(transcript.strip())

    return "\n".join(parts)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--bundle-file", required=True, type=Path)
    ap.add_argument("--system-prompt-file", type=Path, default=None)
    ap.add_argument(
        "--max-tokens", type=int, default=4000, help="hard cap on the assembled prompt; refuse to truncate if exceeded"
    )
    ap.add_argument("--output", choices=("llm", "json"), default="llm")
    args = ap.parse_args()

    try:
        bundle = json.loads(args.bundle_file.read_text())
    except Exception as e:
        print(f"could not read bundle: {e}", file=sys.stderr)
        return 1

    system = ""
    if args.system_prompt_file:
        try:
            system = args.system_prompt_file.read_text()
        except Exception as e:
            print(f"could not read system prompt: {e}", file=sys.stderr)
            return 1

    prompt = format_prompt(args.transcript, bundle, system)
    tokens = approx_tokens(prompt)

    if tokens > args.max_tokens:
        print(
            f"assembled prompt ~{tokens} tokens exceeds --max-tokens {args.max_tokens};"
            " reduce bundle budget upstream rather than silently truncating",
            file=sys.stderr,
        )
        return 2

    if args.output == "json":
        print(
            json.dumps(
                {
                    "prompt": prompt,
                    "token_count_estimate": tokens,
                    "partial_context": (bundle.get("meta") or {}).get("partial", False),
                },
                indent=2,
            )
        )
    else:
        print(prompt)
    return 0


if __name__ == "__main__":
    sys.exit(main())
