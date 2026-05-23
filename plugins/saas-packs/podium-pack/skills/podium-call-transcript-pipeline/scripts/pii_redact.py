#!/usr/bin/env python3
"""pii_redact.py — redact PII from a Podium transcript JSON.

Reads a transcript JSON (the `data` field of a call.transcript.completed event,
or the full event), applies the regex layer plus presidio (if installed), and
writes:
  --output      : redacted transcript JSON
  --audit-log   : JSONL — one line per redaction event

The audit log is suitable for SIEM ingestion or a downstream privacy audit.

Categories detected by the regex layer (the floor — always runs):
  CREDIT_CARD   — Luhn-validated 13-19 digit sequences
  PHONE         — E.164 and common international formats
  EMAIL         — RFC-5322-ish basic match
  SSN_US        — US Social Security Number ###-##-####

Categories detected by presidio (if available):
  PERSON, LOCATION, DATE_TIME, IP_ADDRESS, URL, NRP, ORGANIZATION

Usage:
  pii_redact.py --input transcript.json --output redacted.json --audit-log redactions.jsonl

Exit codes:
  0  success
  1  input file unreadable / malformed
  2  output write failed
"""

from __future__ import annotations
import argparse
import json
import re
import sys
import time
from dataclasses import dataclass, asdict
from pathlib import Path


# ---------------------------------------------------------------------------
# Regex layer
# ---------------------------------------------------------------------------


@dataclass
class Redaction:
    transcript_id: str
    segment_index: int
    category: str
    rule_id: str
    start: int
    end: int
    ts: float


REGEX_PATTERNS = [
    # (category, rule_id, pattern, optional validator)
    ("CREDIT_CARD", "card_luhn_16", re.compile(r"\b(?:\d[ -]?){13,19}\b"), "luhn"),
    ("PHONE", "phone_intl", re.compile(r"\+?\d{1,3}[ -]?\(?\d{2,4}\)?[ -]?\d{3,4}[ -]?\d{3,4}"), None),
    ("EMAIL", "email_basic", re.compile(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}"), None),
    ("SSN_US", "ssn_us", re.compile(r"\b\d{3}-\d{2}-\d{4}\b"), None),
]


def luhn_valid(s: str) -> bool:
    digits = [int(c) for c in s if c.isdigit()]
    if not 13 <= len(digits) <= 19:
        return False
    checksum = 0
    for i, d in enumerate(reversed(digits)):
        if i % 2 == 1:
            d *= 2
            if d > 9:
                d -= 9
        checksum += d
    return checksum % 10 == 0


def regex_redact(text: str, transcript_id: str, segment_index: int) -> tuple[str, list[Redaction]]:
    found: list[Redaction] = []
    now = time.time()
    for category, rule_id, pattern, validator in REGEX_PATTERNS:
        for m in pattern.finditer(text):
            if validator == "luhn" and not luhn_valid(m.group()):
                continue
            found.append(
                Redaction(
                    transcript_id=transcript_id,
                    segment_index=segment_index,
                    category=category,
                    rule_id=rule_id,
                    start=m.start(),
                    end=m.end(),
                    ts=now,
                )
            )
    # Apply substitutions in reverse to keep offsets stable.
    out = text
    for r in sorted(found, key=lambda r: r.start, reverse=True):
        out = out[: r.start] + f"[REDACTED:{r.category}]" + out[r.end :]
    return out, found


# ---------------------------------------------------------------------------
# Presidio layer (optional)
# ---------------------------------------------------------------------------


def presidio_redact(text: str, transcript_id: str, segment_index: int) -> tuple[str, list[Redaction]]:
    try:
        from presidio_analyzer import AnalyzerEngine  # noqa: F401 — capability probe; instance built in _get_analyzer
    except ImportError:
        return text, []
    try:
        analyzer = _get_analyzer()
    except Exception as e:
        print(f"WARN ERR_TXP_004 presidio init failed: {e} — falling back to regex-only", file=sys.stderr)
        return text, []

    results = analyzer.analyze(text=text, language="en")
    now = time.time()
    found = [
        Redaction(
            transcript_id=transcript_id,
            segment_index=segment_index,
            category=r.entity_type,
            rule_id=f"presidio:{r.entity_type.lower()}",
            start=r.start,
            end=r.end,
            ts=now,
        )
        for r in results
        if r.score >= 0.6
    ]
    out = text
    for r in sorted(found, key=lambda r: r.start, reverse=True):
        out = out[: r.start] + f"[REDACTED:{r.category}]" + out[r.end :]
    return out, found


_analyzer_singleton = None


def _get_analyzer():
    global _analyzer_singleton
    if _analyzer_singleton is None:
        from presidio_analyzer import AnalyzerEngine

        _analyzer_singleton = AnalyzerEngine(supported_languages=["en"])
    return _analyzer_singleton


# ---------------------------------------------------------------------------
# Top-level transcript pipeline
# ---------------------------------------------------------------------------


def redact_transcript(transcript: dict, use_presidio: bool = True) -> tuple[dict, list[Redaction]]:
    """Redact a transcript event payload in place. Returns (redacted, audit)."""
    data = transcript.get("data") or transcript  # accept full event or bare data
    transcript_id = data.get("transcript_id") or "unknown"

    segments = data.get("segments") or []
    audit: list[Redaction] = []

    for idx, seg in enumerate(segments):
        text = seg.get("text", "")
        if not text:
            continue
        # Regex first (precise), then presidio (recall on names/addresses).
        text, regex_audit = regex_redact(text, transcript_id, idx)
        if use_presidio:
            text, presidio_audit = presidio_redact(text, transcript_id, idx)
            audit.extend(presidio_audit)
        audit.extend(regex_audit)
        seg["text"] = text

    return transcript, audit


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--input", required=True, type=Path)
    ap.add_argument("--output", required=True, type=Path)
    ap.add_argument("--audit-log", required=True, type=Path)
    ap.add_argument("--no-presidio", action="store_true", help="Skip the presidio layer (regex only)")
    args = ap.parse_args()

    try:
        transcript = json.loads(args.input.read_text())
    except Exception as e:
        print(f"could not read {args.input}: {e}", file=sys.stderr)
        return 1

    redacted, audit = redact_transcript(transcript, use_presidio=not args.no_presidio)

    try:
        args.output.write_text(json.dumps(redacted, indent=2))
        with args.audit_log.open("a") as f:
            for r in audit:
                f.write(json.dumps(asdict(r)) + "\n")
    except OSError as e:
        print(f"output write failed: {e}", file=sys.stderr)
        return 2

    print(
        json.dumps(
            {
                "status": "ok",
                "redaction_count": len(audit),
                "categories": sorted({r.category for r in audit}),
            }
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
