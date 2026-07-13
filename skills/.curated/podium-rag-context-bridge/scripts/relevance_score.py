#!/usr/bin/env python3
"""relevance_score.py — score a (query, candidate) pair on [0, 1].

The score is what the bridge's reranker would emit for ordering. Useful for building
labeled eval sets ("the bridge should rank candidate A above candidate B for query Q"),
asserting top-1 precision in CI, and debugging why the bridge ranked a specific excerpt.

The default backend is a deterministic substring-overlap stub so this CLI runs with no
external dependencies. Production callers should swap in a real cross-encoder (see
references/implementation.md § Reranker adapter contract).

Usage:
  relevance_score.py --query "did they ask about refund policy" \\
                     --candidate "Our policy is 30-day refunds with receipt"

Exit codes:
  0  ok — score printed to stdout
  1  input error (empty query, empty candidate)
"""

from __future__ import annotations
import argparse
import re
import sys


def score_overlap(query: str, candidate: str) -> float:
    """Substring-overlap fallback used when no cross-encoder is wired in.

    Production: replace with `BgeReranker.score(query, [candidate])[0]` or
    `LLMReranker.score(query, [candidate])[0]` for accurate domain-aware scoring.
    """
    q_tokens = set(re.findall(r"\w+", query.lower()))
    c_tokens = set(re.findall(r"\w+", candidate.lower()))
    if not q_tokens or not c_tokens:
        return 0.0
    overlap = q_tokens & c_tokens
    # Weighted toward query coverage (how much of the query is reflected) rather than
    # naive intersection size — matches the intuition the reranker would express.
    return len(overlap) / max(len(q_tokens), 1)


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--query", required=True)
    ap.add_argument("--candidate", required=True)
    ap.add_argument("--precision", type=int, default=2, help="decimal places to print")
    args = ap.parse_args()

    if not args.query.strip() or not args.candidate.strip():
        print("query and candidate must be non-empty", file=sys.stderr)
        return 1

    s = score_overlap(args.query, args.candidate)
    print(f"{s:.{args.precision}f}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
