#!/usr/bin/env python3
"""Classify a sanitized Grammarly asynchronous job receipt offline.

The input is intentionally narrower than a provider response. No network, token,
document content, body, header, subprocess, or write operation is used. The caller
supplies the attempt cap; it is not a Grammarly limit.
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

FORBIDDEN_KEY_PARTS = ("content", "body", "text", "header", "token")
ALLOWED_FIELDS = {"status", "attempts", "max_attempts", "http_status", "retry_after_seconds"}
VALID_STATUSES = {"PENDING", "FAILED", "COMPLETED"}


class ReceiptError(ValueError):
    """Raised when a receipt is not safe and structurally valid."""


def _walk_forbidden_keys(value: Any, path: str = "$") -> None:
    if isinstance(value, dict):
        for key, child in value.items():
            if not isinstance(key, str):
                raise ReceiptError(f"{path}: object keys must be strings")
            lowered = key.casefold()
            if any(part in lowered for part in FORBIDDEN_KEY_PARTS):
                raise ReceiptError(f"{path}.{key}: forbidden metadata key")
            _walk_forbidden_keys(child, f"{path}.{key}")
    elif isinstance(value, list):
        for index, child in enumerate(value):
            _walk_forbidden_keys(child, f"{path}[{index}]")


def _integer(value: Any, field: str, minimum: int, maximum: int | None = None) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise ReceiptError(f"{field}: must be an integer")
    if value < minimum or (maximum is not None and value > maximum):
        bound = f"{minimum}" if maximum is None else f"{minimum}..{maximum}"
        raise ReceiptError(f"{field}: must be in {bound}")
    return value


def classify(receipt: Any) -> dict[str, Any]:
    _walk_forbidden_keys(receipt)
    if not isinstance(receipt, dict):
        raise ReceiptError("$: root must be one JSON object")
    unknown = sorted(set(receipt) - ALLOWED_FIELDS)
    if unknown:
        raise ReceiptError(f"$: unknown field(s): {', '.join(unknown)}")
    required = {"status", "attempts", "max_attempts"}
    missing = sorted(required - set(receipt))
    if missing:
        raise ReceiptError(f"$: missing required field(s): {', '.join(missing)}")

    status = receipt["status"]
    if not isinstance(status, str) or status not in VALID_STATUSES:
        raise ReceiptError("status: must be exactly PENDING, FAILED, or COMPLETED")
    attempts = _integer(receipt["attempts"], "attempts", 0)
    max_attempts = _integer(receipt["max_attempts"], "max_attempts", 1)
    if attempts > max_attempts:
        raise ReceiptError("attempts: cannot exceed max_attempts")

    http_status = None
    if "http_status" in receipt:
        http_status = _integer(receipt["http_status"], "http_status", 100, 599)
    retry_after = None
    if "retry_after_seconds" in receipt:
        retry_after = _integer(receipt["retry_after_seconds"], "retry_after_seconds", 0)
        if status != "FAILED" or http_status != 429:
            raise ReceiptError("retry_after_seconds: allowed only for FAILED with http_status 429")
    if http_status == 429 and status != "FAILED":
        raise ReceiptError("http_status 429: status must be FAILED")

    if status == "COMPLETED":
        classification = "COMPLETED_TERMINAL"
        guidance = "Terminal completion; do not retry."
    elif attempts >= max_attempts:
        classification = "ATTEMPT_CAP_REACHED"
        guidance = "Stop: the caller-supplied attempt cap has been reached."
    elif status == "PENDING":
        classification = "PENDING_OBSERVATION"
        guidance = "Still pending within the caller cap; no polling interval, timeout, SLA, or quota is inferred."
    elif http_status == 429 and retry_after is not None:
        classification = "RETRY_AFTER_EVIDENCE"
        guidance = f"Retry only under caller policy after the supplied Retry-After evidence: {retry_after} seconds."
    elif http_status == 429:
        classification = "RETRY_429_EXPONENTIAL_2S_BASE"
        guidance = "For 429 only, Grammarly documents a 2-second-base exponential-backoff guidance; no maximum or SLA is inferred."
    else:
        classification = "MANUAL_REVIEW"
        guidance = "Failed without documented retry evidence in this receipt; review before any retry."

    result: dict[str, Any] = {
        "status": status,
        "attempts": attempts,
        "max_attempts": max_attempts,
        "classification": classification,
        "guidance": guidance,
    }
    if http_status is not None:
        result["http_status"] = http_status
    if retry_after is not None:
        result["retry_after_seconds"] = retry_after
    return result


def _load(source: str) -> Any:
    raw = sys.stdin.read() if source == "-" else Path(source).read_text(encoding="utf-8")

    def reject_duplicates(pairs: list[tuple[str, Any]]) -> dict[str, Any]:
        result: dict[str, Any] = {}
        for key, value in pairs:
            if key in result:
                raise ReceiptError(f"duplicate JSON key: {key}")
            result[key] = value
        return result

    def reject_constant(value: str) -> Any:
        raise ReceiptError(f"non-standard JSON constant: {value}")

    try:
        return json.loads(raw, object_pairs_hook=reject_duplicates, parse_constant=reject_constant)
    except (json.JSONDecodeError, UnicodeDecodeError) as exc:
        raise ReceiptError(f"input is not valid UTF-8 JSON: {exc}") from exc


def _self_test() -> None:
    cases = [
        ({"status": "COMPLETED", "attempts": 1, "max_attempts": 3}, "COMPLETED_TERMINAL"),
        ({"status": "PENDING", "attempts": 0, "max_attempts": 3}, "PENDING_OBSERVATION"),
        (
            {"status": "FAILED", "attempts": 1, "max_attempts": 3, "http_status": 429, "retry_after_seconds": 17},
            "RETRY_AFTER_EVIDENCE",
        ),
        ({"status": "FAILED", "attempts": 1, "max_attempts": 3, "http_status": 429}, "RETRY_429_EXPONENTIAL_2S_BASE"),
        ({"status": "FAILED", "attempts": 3, "max_attempts": 3}, "ATTEMPT_CAP_REACHED"),
    ]
    for receipt, expected in cases:
        actual = classify(receipt)["classification"]
        if actual != expected:
            raise AssertionError(f"expected {expected}, got {actual}")
    invalid = [
        {"status": "RETRYING", "attempts": 1, "max_attempts": 3},
        {"status": "FAILED", "attempts": 4, "max_attempts": 3},
        {"status": "FAILED", "attempts": 1, "max_attempts": 3, "diagnostics": {"response_body": "x"}},
        {"status": "FAILED", "attempts": 1, "max_attempts": 3, "headers": {}},
        {"status": "FAILED", "attempts": 1, "max_attempts": 3, "http_status": 500, "retry_after_seconds": 2},
    ]
    for receipt in invalid:
        try:
            classify(receipt)
        except ReceiptError:
            continue
        raise AssertionError(f"unsafe or invalid receipt was accepted: {receipt}")
    print("self-test: 10 passed")


def main() -> int:
    parser = argparse.ArgumentParser(description="Classify a sanitized Grammarly job receipt offline.")
    parser.add_argument("source", nargs="?", default="-", help="JSON file, or - for stdin")
    parser.add_argument("--self-test", action="store_true", help="run deterministic built-in checks")
    args = parser.parse_args()
    try:
        if args.self_test:
            _self_test()
        else:
            print(json.dumps(classify(_load(args.source)), sort_keys=True))
    except (OSError, ReceiptError, AssertionError, RecursionError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
