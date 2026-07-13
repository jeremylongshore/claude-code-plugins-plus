#!/usr/bin/env python3
"""context_fetch.py — given a transcript chunk + contact uid, emit a structured RAG context bundle.

Two-stage retrieval (ANN + cross-encoder rerank) over a pgvector corpus, fan-out with a live
Podium contact lookup, redaction + token-budget enforcement, hard wall-clock deadline.

Usage:
  context_fetch.py \\
    --transcript "I had a question about my last order" \\
    --contact-uid "ctc_abc123" \\
    --pgvector-dsn "{your-pgvector-dsn}" \\
    [--podium-token-env PODIUM_ACCESS_TOKEN] \\
    [--pool-k 20] [--final-k 5] [--timeout-ms 800] [--max-tokens 1500] \\
    [--output json|human]

Exit codes:
  0  ok — bundle emitted (may still be partial; check meta.partial)
  1  configuration error (missing dsn, unreadable transcript, etc.)
  2  fatal retrieval error (all surfaces unreachable AND no degraded-mode bundle possible)
"""

from __future__ import annotations
import argparse
import asyncio
import json
import os
import re
import sys
import time
from typing import Any

import urllib.request
import urllib.error


# --- redaction ---------------------------------------------------------------

REDACTION_PATTERNS = [
    (re.compile(r"\b\d{13,19}\b"), "[REDACTED:CC]"),
    (re.compile(r"\b\d{3}-?\d{2}-?\d{4}\b"), "[REDACTED:SSN]"),
    (re.compile(r"\b[\w.+-]+@[\w-]+\.[\w.-]+\b"), "[REDACTED:EMAIL]"),
    (re.compile(r"\+?\d[\d\s\-().]{8,}\d"), "[REDACTED:PHONE]"),
    (re.compile(r"\b(0?[1-9]|1[0-2])[/-](0?[1-9]|[12]\d|3[01])[/-](19|20)\d{2}\b"), "[REDACTED:DOB]"),
    (re.compile(r"\b\d{1,5}\s+\w+\s+(St|Ave|Rd|Blvd|Lane|Ln|Dr|Drive|Court|Ct)\b", re.I), "[REDACTED:ADDR]"),
]


def redact(text: str) -> str:
    for pat, repl in REDACTION_PATTERNS:
        text = pat.sub(repl, text)
    return text


# --- vector store + (stubbed) embedder + reranker ----------------------------
#
# The CLI keeps the runtime dependency footprint minimal so this script can be
# invoked from CI or an integration test without installing sentence-transformers.
# Production callers should swap these for the real implementations documented in
# references/implementation.md.


async def embed_stub(text: str) -> list[float]:
    """Deterministic hashed pseudo-embedding so the CLI can be exercised without a model.

    Production: replace with BgeEmbedder().embed(text) or OpenAIEmbedder().embed(text).
    Returns a 1024-dim float vector (matches default pgvector schema).
    """
    import hashlib

    digest = hashlib.sha256(text.encode("utf-8")).digest()
    # Spread the 32-byte digest into 1024 floats in [-1, 1]. NOT semantically meaningful;
    # the CLI is wired this way so the pipeline can be smoke-tested end-to-end.
    out = []
    for i in range(1024):
        b = digest[i % 32]
        out.append((b - 128) / 128.0)
    return out


async def rerank_stub(query: str, candidates: list[str]) -> list[float]:
    """Toy reranker: substring overlap. Production: BgeReranker / LLMReranker."""
    q_tokens = set(re.findall(r"\w+", query.lower()))
    scores: list[float] = []
    for c in candidates:
        c_tokens = set(re.findall(r"\w+", c.lower()))
        if not q_tokens or not c_tokens:
            scores.append(0.0)
            continue
        overlap = len(q_tokens & c_tokens)
        scores.append(overlap / max(len(q_tokens), 1))
    return scores


async def pgvector_query(dsn: str, embedding: list[float], top_k: int, contact_uid: str | None) -> list[dict]:
    """Synchronous psycopg call wrapped in a thread.

    Returns the empty list if psycopg is unavailable or the connection fails — degraded mode.
    """

    def _run() -> list[dict]:
        try:
            import psycopg
        except ImportError:
            return []
        try:
            with psycopg.connect(dsn, connect_timeout=2) as conn:
                with conn.cursor() as cur:
                    cur.execute(
                        "SELECT id, contact_uid, content, channel, occurred_at, "
                        "       1 - (embedding <=> %s::vector) AS cosine_score "
                        "FROM podium_conversations "
                        "WHERE (%s::text IS NULL OR contact_uid = %s) "
                        "ORDER BY embedding <=> %s::vector "
                        "LIMIT %s",
                        (embedding, contact_uid, contact_uid, embedding, top_k),
                    )
                    rows = cur.fetchall()
            return [
                {
                    "id": r[0],
                    "contact_uid": r[1],
                    "content": r[2],
                    "channel": r[3],
                    "occurred_at": str(r[4]) if r[4] is not None else None,
                    "score": float(r[5]),
                }
                for r in rows
            ]
        except Exception:
            return []

    return await asyncio.to_thread(_run)


# --- live podium lookup ------------------------------------------------------

LIVE_FIELDS = {"phone", "email", "opt_out_sms", "opt_out_email", "location_uid", "last_seen_at"}


async def fetch_live_contact(token: str | None, contact_uid: str | None) -> dict:
    if not token or not contact_uid:
        return {"live_fields_available": False}

    def _run() -> dict:
        url = f"https://api.podium.com/v4/contacts/{contact_uid}"
        req = urllib.request.Request(url, headers={"Authorization": f"Bearer {token}"})
        try:
            with urllib.request.urlopen(req, timeout=2.0) as resp:
                body = json.loads(resp.read().decode("utf-8"))
        except urllib.error.HTTPError as e:
            return {"error": e.code, "live_fields_available": False}
        except Exception:
            return {"live_fields_available": False}
        return {k: body.get(k) for k in LIVE_FIELDS} | {"live_fields_available": True}

    return await asyncio.to_thread(_run)


# --- pipeline ---------------------------------------------------------------


def approx_tokens(s: str, chars_per_token: int = 4) -> int:
    return max(1, len(s) // chars_per_token)


def merge_live_over_vector(vec_hits: list[dict], live_contact: dict) -> dict:
    return {
        "contact": live_contact,
        "historical_excerpts": [
            {
                "id": h.get("id"),
                "content": h["content"],
                "channel": h.get("channel"),
                "occurred_at": h.get("occurred_at"),
                "rerank_score": float(h.get("rerank_score", h.get("score", 0.0))),
            }
            for h in vec_hits
        ],
    }


def redact_bundle(bundle: dict) -> dict:
    bundle["historical_excerpts"] = [{**e, "content": redact(e["content"])} for e in bundle["historical_excerpts"]]
    return bundle


def enforce_budget(bundle: dict, max_tokens: int) -> dict:
    excerpts = bundle["historical_excerpts"]
    excerpts.sort(key=lambda e: e["rerank_score"], reverse=True)
    dropped = 0
    total = sum(approx_tokens(e["content"]) for e in excerpts)
    while total > max_tokens and len(excerpts) > 1:
        d = excerpts.pop()
        total -= approx_tokens(d["content"])
        dropped += 1
    if total > max_tokens and excerpts:
        e = excerpts[0]
        e["content"] = e["content"][: max_tokens * 4]
        e["truncated"] = True
    bundle["historical_excerpts"] = excerpts
    bundle["token_count"] = total
    bundle.setdefault("meta", {})["dropped_excerpts_count"] = dropped
    return bundle


async def with_deadline(coro, deadline: float) -> Any:
    remaining = max(0.005, deadline - time.monotonic())
    try:
        return await asyncio.wait_for(coro, timeout=remaining)
    except (asyncio.TimeoutError, asyncio.CancelledError):
        return None


async def build_context(
    transcript: str,
    contact_uid: str | None,
    dsn: str,
    podium_token: str | None,
    pool_k: int,
    final_k: int,
    timeout_ms: int,
    max_tokens: int,
) -> dict:
    started = time.monotonic()
    deadline = started + timeout_ms / 1000.0

    async def vector_path() -> list[dict]:
        emb = await embed_stub(transcript)
        pool = await pgvector_query(dsn, emb, pool_k, contact_uid)
        if not pool:
            return []
        rr_scores = await rerank_stub(transcript, [c["content"] for c in pool])
        for c, s in zip(pool, rr_scores):
            c["rerank_score"] = float(s)
        pool.sort(key=lambda c: c["rerank_score"], reverse=True)
        return pool[:final_k]

    vec_task = asyncio.create_task(with_deadline(vector_path(), deadline))
    live_task = asyncio.create_task(with_deadline(fetch_live_contact(podium_token, contact_uid), deadline))

    vec_hits = (await vec_task) or []
    live = (await live_task) or {"live_fields_available": False}

    elapsed_ms = int((time.monotonic() - started) * 1000)
    bundle = merge_live_over_vector(vec_hits, live)
    redact_bundle(bundle)
    enforce_budget(bundle, max_tokens)
    bundle["meta"] = {
        **bundle.get("meta", {}),
        "elapsed_ms": elapsed_ms,
        "timeout_ms": timeout_ms,
        "partial": elapsed_ms >= timeout_ms,
        "had_vector_hits": bool(vec_hits),
        "had_live_lookup": bool(live.get("live_fields_available")),
    }
    return bundle


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--transcript", required=True)
    ap.add_argument("--contact-uid", default=None)
    ap.add_argument(
        "--pgvector-dsn",
        required=True,
        help="postgresql:// DSN. Load from secret store; pass {your-pgvector-dsn} placeholder.",
    )
    ap.add_argument(
        "--podium-token-env",
        default="PODIUM_ACCESS_TOKEN",
        help="env var holding a live Podium access token (from podium-auth)",
    )
    ap.add_argument("--pool-k", type=int, default=20)
    ap.add_argument("--final-k", type=int, default=5)
    ap.add_argument("--timeout-ms", type=int, default=800)
    ap.add_argument("--max-tokens", type=int, default=1500)
    ap.add_argument("--output", choices=("json", "human"), default="json")
    args = ap.parse_args()

    podium_token = os.environ.get(args.podium_token_env)

    try:
        bundle = asyncio.run(
            build_context(
                transcript=args.transcript,
                contact_uid=args.contact_uid,
                dsn=args.pgvector_dsn,
                podium_token=podium_token,
                pool_k=args.pool_k,
                final_k=args.final_k,
                timeout_ms=args.timeout_ms,
                max_tokens=args.max_tokens,
            )
        )
    except Exception as e:
        print(f"fatal: {e}", file=sys.stderr)
        return 2

    if args.output == "json":
        print(json.dumps(bundle, indent=2, default=str))
    else:
        print(
            f"elapsed_ms={bundle['meta']['elapsed_ms']} "
            f"partial={bundle['meta']['partial']} "
            f"vector_hits={bundle['meta']['had_vector_hits']} "
            f"live_lookup={bundle['meta']['had_live_lookup']} "
            f"excerpts={len(bundle['historical_excerpts'])} "
            f"tokens={bundle.get('token_count')}",
            file=sys.stderr,
        )
        print(json.dumps(bundle, indent=2, default=str))
    return 0


if __name__ == "__main__":
    sys.exit(main())
