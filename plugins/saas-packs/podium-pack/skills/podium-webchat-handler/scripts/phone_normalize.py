#!/usr/bin/env python3
"""phone_normalize.py — parse a raw phone string and emit its E.164 form + metadata.

Usage:
  phone_normalize.py --phone "0412 345 678" --default-country AU [--output json|human]

Exit codes:
  0  parsed successfully and number is valid for the supplied country
  1  parse failed or number is invalid for the supplied country (ERR_WEBCHAT_001)
  2  configuration error (missing args, phonenumbers not installed)

Requires:
  pip install phonenumbers
"""

from __future__ import annotations
import argparse
import json
import sys


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phone", required=True, help="raw phone string from the widget")
    ap.add_argument("--default-country", required=True, help="ISO-3166 country code, e.g. AU, US, GB")
    ap.add_argument("--output", choices=("json", "human"), default="human")
    args = ap.parse_args()

    try:
        import phonenumbers
        from phonenumbers import (
            NumberParseException,
            PhoneNumberFormat,
            is_valid_number,
            is_possible_number,
            number_type,
            carrier,
        )
        from phonenumbers.phonenumberutil import PhoneNumberType
    except ImportError:
        print("phonenumbers not installed — pip install phonenumbers", file=sys.stderr)
        return 2

    try:
        parsed = phonenumbers.parse(args.phone, args.default_country)
    except NumberParseException as e:
        print(f"ERR_WEBCHAT_001 unparseable phone {args.phone!r} for {args.default_country}: {e}", file=sys.stderr)
        return 1

    valid = is_valid_number(parsed)
    possible = is_possible_number(parsed)
    if not valid:
        print(f"ERR_WEBCHAT_001 invalid phone {args.phone!r} for {args.default_country}", file=sys.stderr)
        return 1

    e164 = phonenumbers.format_number(parsed, PhoneNumberFormat.E164)
    ntype = number_type(parsed)
    type_name = {
        PhoneNumberType.MOBILE: "MOBILE",
        PhoneNumberType.FIXED_LINE: "FIXED_LINE",
        PhoneNumberType.FIXED_LINE_OR_MOBILE: "FIXED_LINE_OR_MOBILE",
        PhoneNumberType.TOLL_FREE: "TOLL_FREE",
        PhoneNumberType.VOIP: "VOIP",
        PhoneNumberType.PREMIUM_RATE: "PREMIUM_RATE",
        PhoneNumberType.SHARED_COST: "SHARED_COST",
        PhoneNumberType.PERSONAL_NUMBER: "PERSONAL_NUMBER",
        PhoneNumberType.PAGER: "PAGER",
        PhoneNumberType.UAN: "UAN",
        PhoneNumberType.VOICEMAIL: "VOICEMAIL",
        PhoneNumberType.UNKNOWN: "UNKNOWN",
    }.get(ntype, "UNKNOWN")

    carrier_name = carrier.name_for_number(parsed, "en") or ""

    summary = {
        "input": args.phone,
        "e164": e164,
        "country": args.default_country,
        "country_code": parsed.country_code,
        "national_number": parsed.national_number,
        "is_valid": valid,
        "is_possible": possible,
        "number_type": type_name,
        "carrier": carrier_name,
    }

    if args.output == "json":
        print(json.dumps(summary))
    else:
        for k, v in summary.items():
            print(f"{k}: {v}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
