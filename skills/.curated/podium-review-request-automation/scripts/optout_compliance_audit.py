#!/usr/bin/env python3
"""optout_compliance_audit.py — cross-flow opt-out drift detection for one contact.

Usage:
  optout_compliance_audit.py --phone "+61412345678"
  optout_compliance_audit.py --phone "+61412345678" --propagate

Strategy:
  Reads the merged contact record from the contacts service (env CONTACTS_API_URL),
  consults all known opt-out flags, computes the unified suppression decision, and
  detects drift between flow-specific flags and the unified outcome.

  With --propagate, writes the OR-union of all flags back to every flow-specific flag,
  resolving drift in place. This is a destructive operation — review the dry-run output first.

Exit codes:
  0  no drift detected
  1  drift detected; suppressed=true
  2  drift detected; suppressed=false (less common — typically a flag was incorrectly cleared)
  3  contacts service unreachable, contact not found, or invalid args
"""

from __future__ import annotations
import argparse
import json
import os
import sys
import urllib.request
import urllib.error

OPT_OUT_FLAGS = [
    "marketing_sms_opt_out",
    "review_request_opt_out",
    "global_unsubscribe",
    "podium_keyword_optout",
]


def fetch_contact(api_url: str, phone: str) -> dict | None:
    req = urllib.request.Request(
        f"{api_url}/contacts?phone={phone}",
        headers={"Accept": "application/json"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        if e.code == 404:
            return None
        raise
    contacts = data.get("contacts", [])
    return contacts[0] if contacts else None


def propagate_optout(api_url: str, contact_id: str, unified: bool) -> None:
    body = json.dumps({flag: unified for flag in OPT_OUT_FLAGS}).encode()
    req = urllib.request.Request(
        f"{api_url}/contacts/{contact_id}",
        data=body,
        method="PATCH",
        headers={"Content-Type": "application/json"},
    )
    with urllib.request.urlopen(req, timeout=10) as resp:
        if resp.status not in (200, 204):
            raise RuntimeError(f"propagate failed: status={resp.status}")


def audit(contact: dict) -> dict:
    flags = {flag: bool(contact.get(flag, False)) for flag in OPT_OUT_FLAGS}
    suppressed = any(flags.values())

    drift_detected = False
    drift_reason = None
    # Drift heuristic: if any flag is true and any other flag is false, that's drift.
    if suppressed and not all(flags.values()):
        drift_detected = True
        true_flags = [f for f, v in flags.items() if v]
        false_flags = [f for f, v in flags.items() if not v]
        drift_reason = (
            f"{','.join(false_flags)}=false despite {','.join(true_flags)}=true — propagate via podium-contact-dedup"
        )

    return {
        **flags,
        "suppressed": suppressed,
        "drift_detected": drift_detected,
        "drift_reason": drift_reason,
    }


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--phone", required=True, help="E.164 phone")
    ap.add_argument(
        "--api-url-env", default="CONTACTS_API_URL", help="Env var holding the merged-contacts API base URL"
    )
    ap.add_argument("--propagate", action="store_true", help="Write the OR-union of opt-outs back to all flow flags")
    args = ap.parse_args()

    api_url = os.environ.get(args.api_url_env)
    if not api_url:
        print(f"missing env: {args.api_url_env}", file=sys.stderr)
        return 3

    try:
        contact = fetch_contact(api_url, args.phone)
    except Exception as e:
        print(f"contacts service error: {e}", file=sys.stderr)
        return 3

    if contact is None:
        result = {
            "phone": args.phone,
            "contact_found": False,
            "suppressed": False,
            "drift_detected": False,
        }
        print(json.dumps(result, indent=2))
        return 0

    result = audit(contact)
    result["phone"] = args.phone
    result["contact_id"] = contact["id"]

    if args.propagate and result["drift_detected"]:
        try:
            propagate_optout(api_url, contact["id"], result["suppressed"])
            result["propagated"] = True
        except Exception as e:
            print(f"propagate failed: {e}", file=sys.stderr)
            result["propagated"] = False
            print(json.dumps(result, indent=2))
            return 3

    print(json.dumps(result, indent=2))
    if not result["drift_detected"]:
        return 0
    return 1 if result["suppressed"] else 2


if __name__ == "__main__":
    sys.exit(main())
