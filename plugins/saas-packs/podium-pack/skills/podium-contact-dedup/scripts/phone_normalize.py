#!/usr/bin/env python3
"""phone_normalize.py — normalize a phone string to E.164 and emit the natural key.

Usage:
  phone_normalize.py --phone "0412 345 678" [--region AU] [--output json|human]

The natural_key is the E.164 form. Use it as the primary key for duplicate detection
across an entire Podium contact corpus.

Exit codes:
  0  valid number; normalized output emitted
  1  parse failed (not a number, empty input, free-form text in phone field)
  2  parsed but not a valid number for the resolved region (reserved range, wrong length)
  3  missing required argument or unsupported region

Importable module:
  from phone_normalize import normalize_phone
  norm = normalize_phone("0412 345 678", default_region="AU")
  if norm["valid"]: print(norm["natural_key"])
"""

from __future__ import annotations
import argparse
import json
import sys

try:
    import phonenumbers
    from phonenumbers import NumberParseException
except ImportError:
    sys.stderr.write("missing dependency: install phonenumbers — pip install phonenumbers\n")
    sys.exit(3)


def normalize_phone(raw: str, default_region: str = "AU") -> dict:
    """Parse raw phone into E.164. Returns dict with `valid` and (on success) `natural_key`."""
    if not raw or not raw.strip():
        return {"valid": False, "reason": "empty_input"}
    try:
        parsed = phonenumbers.parse(raw, default_region)
    except NumberParseException as e:
        return {"valid": False, "reason": f"parse_failed: {e}"}
    if not phonenumbers.is_valid_number(parsed):
        return {"valid": False, "reason": "not_a_valid_number"}
    e164 = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
    national = phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.NATIONAL)
    country = phonenumbers.region_code_for_number(parsed)
    return {
        "valid": True,
        "e164": e164,
        "national": national,
        "country": country,
        "natural_key": e164,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phone", required=True, help="raw phone string to normalize")
    ap.add_argument("--region", default="AU", help="ISO 3166-1 alpha-2 default region (default: AU)")
    ap.add_argument("--output", choices=("json", "human"), default="json")
    args = ap.parse_args()

    result = normalize_phone(args.phone, default_region=args.region)

    if args.output == "json":
        print(json.dumps(result))
    else:
        for k, v in result.items():
            print(f"{k}: {v}")

    if not result["valid"]:
        reason = result.get("reason", "")
        if reason.startswith("parse_failed") or reason == "empty_input":
            return 1
        return 2
    return 0


if __name__ == "__main__":
    sys.exit(main())
