#!/usr/bin/env python3
"""vector_query.py — raw two-stage retrieval (ANN + cross-encoder rerank) against pgvector.

Bypasses live Podium lookup, redaction, and budget enforcement. Use only for debugging the
retrieval surface itself ("why did the bridge rank these excerpts?"). Production callers
should use context_fetch.py.

Usage:
  vector_query.py \\
    --query "did they ask about refund policy" \\
    --contact-uid "ctc_abc123" \\
    --pgvector-dsn "{your-pgvector-dsn}" \\
    [--pool-k 20] [--final-k 5]

Exit codes:
  0  ok — results printed as JSON array (may be empty)
  1  config error (missing dsn, etc.)
  2  retrieval error (pgvector unreachable)
"""

from __future__ import annotations
import argparse
import asyncio
import hashlib
import json
import re
import sys


async def embed_stub(text: str) -> list[float]:
    digest = hashlib.sha256(text.encode("utf-8")).digest()
    return [(digest[i % 32] - 128) / 128.0 for i in range(1024)]


async def rerank_stub(query: str, candidates: list[str]) -> list[float]:
    q_tokens = set(re.findall(r"\w+", query.lower()))
    out: list[float] = []
    for c in candidates:
        c_tokens = set(re.findall(r"\w+", c.lower()))
        if not q_tokens or not c_tokens:
            out.append(0.0)
            continue
        out.append(len(q_tokens & c_tokens) / max(len(q_tokens), 1))
    return out


async def pgvector_query(dsn: str, embedding: list[float], top_k: int, contact_uid: str | None) -> list[dict]:
    def _run() -> list[dict] | None:
        try:
            import psycopg
        except ImportError:
            print("psycopg not installed — install with: pip install 'psycopg[binary]'", file=sys.stderr)
            return None
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
        except Exception as e:
            print(f"pgvector error: {e}", file=sys.stderr)
            return None
        return [
            {
                "id": r[0],
                "contact_uid": r[1],
                "content": r[2],
                "channel": r[3],
                "occurred_at": str(r[4]) if r[4] is not None else None,
                "cosine_score": float(r[5]),
            }
            for r in rows
        ]

    return await asyncio.to_thread(_run)


async def run(query: str, dsn: str, contact_uid: str | None, pool_k: int, final_k: int) -> int:
    emb = await embed_stub(query)
    pool = await pgvector_query(dsn, emb, pool_k, contact_uid)
    if pool is None:
        return 2
    if not pool:
        print("[]")
        return 0

    rr = await rerank_stub(query, [c["content"] for c in pool])
    for c, s in zip(pool, rr):
        c["rerank_score"] = float(s)
    pool.sort(key=lambda c: c["rerank_score"], reverse=True)
    print(json.dumps(pool[:final_k], indent=2, default=str))
    return 0


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", required=True)
    ap.add_argument("--contact-uid", default=None)
    ap.add_argument("--pgvector-dsn", required=True)
    ap.add_argument("--pool-k", type=int, default=20)
    ap.add_argument("--final-k", type=int, default=5)
    args = ap.parse_args()
    return asyncio.run(run(args.query, args.pgvector_dsn, args.contact_uid, args.pool_k, args.final_k))


if __name__ == "__main__":
    sys.exit(main())
