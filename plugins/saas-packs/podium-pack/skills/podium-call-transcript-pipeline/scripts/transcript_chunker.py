#!/usr/bin/env python3
"""transcript_chunker.py — chunk a Podium transcript with speaker-preserving overlap.

Two invariants:
  1. Chunk boundaries land at segment boundaries. A speaker turn is NEVER split
     mid-utterance. If a single segment exceeds target_tokens, it produces a
     one-segment oversize chunk (ERR_TXP_006) rather than splitting the speaker.
  2. Each chunk carries `speakers: [...]` — the speaker roles present in the chunk.

Overlap: the trailing segments of chunk K (whose token sum is <= overlap_tokens)
are re-included as the leading segments of chunk K+1. This preserves cross-chunk
context for retrieval.

Usage:
  transcript_chunker.py --input redacted.json --output chunks.json \\
                        [--target-tokens 1500] [--overlap-tokens 200] \\
                        [--dry-run --warn-on-oversize]

Exit codes:
  0  success — chunks written
  1  input unreadable / malformed
  2  output write failed
"""

from __future__ import annotations
import argparse
import json
import sys
from dataclasses import dataclass, field, asdict
from pathlib import Path


@dataclass
class Segment:
    speaker_role: str
    start_ms: int
    end_ms: int
    text: str


@dataclass
class Chunk:
    chunk_index: int
    speakers: list[str] = field(default_factory=list)
    token_count: int = 0
    segments: list[Segment] = field(default_factory=list)


def estimate_tokens(text: str) -> int:
    """Heuristic: ~4 chars/token. Replace with the target model's tokenizer when known."""
    return max(1, len(text) // 4)


def build_overlap(segments: list[Segment], budget_tokens: int) -> list[Segment]:
    """Return the longest tail of segments whose token sum is <= budget."""
    out: list[Segment] = []
    total = 0
    for seg in reversed(segments):
        t = estimate_tokens(seg.text)
        if total + t > budget_tokens:
            break
        out.insert(0, seg)
        total += t
    return out


def chunk_segments(
    segments: list[Segment],
    target_tokens: int = 1500,
    overlap_tokens: int = 200,
    warn_on_oversize: bool = False,
) -> tuple[list[Chunk], int]:
    """Chunk a list of segments. Returns (chunks, oversize_count)."""
    chunks: list[Chunk] = []
    current = Chunk(chunk_index=0)
    oversize = 0

    for seg in segments:
        seg_tokens = estimate_tokens(seg.text)

        # If the current chunk would overflow AND we already have content, close it.
        if current.token_count + seg_tokens > target_tokens and current.segments:
            chunks.append(current)
            overlap = build_overlap(current.segments, overlap_tokens)
            new_index = len(chunks)
            new_speakers = list(dict.fromkeys(s.speaker_role for s in overlap))
            current = Chunk(
                chunk_index=new_index,
                speakers=new_speakers,
                token_count=sum(estimate_tokens(s.text) for s in overlap),
                segments=list(overlap),
            )

        current.segments.append(seg)
        current.token_count += seg_tokens
        if seg.speaker_role not in current.speakers:
            current.speakers.append(seg.speaker_role)

        # Detect oversize single-segment chunks (ERR_TXP_006).
        if len(current.segments) == 1 and current.token_count > target_tokens:
            oversize += 1
            if warn_on_oversize:
                duration_s = (seg.end_ms - seg.start_ms) / 1000
                print(
                    f"WARN ERR_TXP_006 segment idx={segments.index(seg)} "
                    f"speaker={seg.speaker_role} duration={duration_s:.1f}s "
                    f"~{current.token_count} tokens > {target_tokens} target. "
                    f"This chunk will not be split.",
                    file=sys.stderr,
                )

    if current.segments:
        chunks.append(current)

    return chunks, oversize


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", type=Path, default=None, help="Required unless --dry-run")
    ap.add_argument("--target-tokens", type=int, default=1500)
    ap.add_argument("--overlap-tokens", type=int, default=200)
    ap.add_argument(
        "--process-loop",
        action="store_true",
        help="Run as a processor loop reading from the inbox SQLite (not implemented as CLI; placeholder)",
    )
    ap.add_argument("--interval", type=int, default=5)
    ap.add_argument("--dry-run", action="store_true")
    ap.add_argument("--warn-on-oversize", action="store_true")
    args = ap.parse_args()

    if args.process_loop:
        print(
            "process-loop mode: invoke the processor module directly — this CLI is for one-shot chunking",
            file=sys.stderr,
        )
        return 2

    if not args.dry_run and args.output is None:
        print("--output is required unless --dry-run", file=sys.stderr)
        return 2

    try:
        transcript = json.loads(args.input.read_text())
    except Exception as e:
        print(f"could not read {args.input}: {e}", file=sys.stderr)
        return 1

    data = transcript.get("data") or transcript
    transcript_id = data.get("transcript_id") or "unknown"
    raw_segments = data.get("segments") or []

    segments = [
        Segment(
            speaker_role=s.get("speaker_role", "unknown"),
            start_ms=int(s.get("start_ms", 0)),
            end_ms=int(s.get("end_ms", 0)),
            text=s.get("text", ""),
        )
        for s in raw_segments
    ]

    chunks, oversize = chunk_segments(
        segments,
        target_tokens=args.target_tokens,
        overlap_tokens=args.overlap_tokens,
        warn_on_oversize=args.warn_on_oversize,
    )

    out_payload = {
        "transcript_id": transcript_id,
        "chunk_count": len(chunks),
        "oversize_chunk_count": oversize,
        "chunks": [
            {
                "chunk_index": c.chunk_index,
                "speakers": c.speakers,
                "token_count": c.token_count,
                "segments": [asdict(s) for s in c.segments],
            }
            for c in chunks
        ],
    }

    if args.dry_run:
        print(
            json.dumps(
                {
                    "status": "dry-run",
                    "chunk_count": len(chunks),
                    "oversize_chunk_count": oversize,
                }
            )
        )
        return 0

    try:
        args.output.write_text(json.dumps(out_payload, indent=2))
    except OSError as e:
        print(f"output write failed: {e}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "chunk_count": len(chunks),
                "oversize_chunk_count": oversize,
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
