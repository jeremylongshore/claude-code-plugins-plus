# HubSpot Agency Multi-Portal — Implementation Guide

Credential store design, bulk onboarding script, token rotation runbook, compliance report generator, and Python equivalents for the TypeScript patterns in `SKILL.md`. The core architecture lives in `SKILL.md`; this document covers the operational tooling.

## Credential Store Design

The credential store is a versioned JSON document stored in a secret manager. The version field is incremented on every write — use it to detect concurrent modification (optimistic locking) and to confirm a write landed.

### Schema

```json
{
  "version": 4,
  "lastUpdated": "2026-05-11T14:00:00Z",
  "portals": {
    "acme-corp": {
      "token": "pat-na1-{your-uuid}",
      "portalId": 12345678,
      "clientSlug": "acme-corp",
      "addedAt": "2026-01-15T09:00:00Z",
      "lastRotatedAt": "2026-04-01T10:00:00Z",
      "datacenter": "na1"
    },
    "beta-inc": {
      "token": "pat-eu1-{your-uuid}",
      "portalId": 87654321,
      "clientSlug": "beta-inc",
      "addedAt": "2026-02-01T09:00:00Z",
      "lastRotatedAt": "2026-02-01T09:00:00Z",
      "datacenter": "eu1"
    }
  }
}
```

### Secret manager paths (by backend)

| Backend | Path | Command to read |
|---|---|---|
| `pass` | `hubspot/agency-portals` | `pass show hubspot/agency-portals` |
| AWS Secrets Manager | `hubspot/agency-portals` | `aws secretsmanager get-secret-value --secret-id hubspot/agency-portals --query SecretString --output text` |
| GCP Secret Manager | `hubspot-agency-portals` | `gcloud secrets versions access latest --secret=hubspot-agency-portals` |
| HashiCorp Vault | `secret/hubspot/agency-portals` | `vault kv get -field=data secret/hubspot/agency-portals` |

### Optimistic locking write pattern

```python
import json
import subprocess
import time

def read_store(backend: str, path: str) -> dict:
    if backend == "pass":
        result = subprocess.run(["pass", "show", path], capture_output=True, text=True, check=True)
        return json.loads(result.stdout)
    elif backend == "aws":
        result = subprocess.run(
            ["aws", "secretsmanager", "get-secret-value",
             "--secret-id", path, "--query", "SecretString", "--output", "text"],
            capture_output=True, text=True, check=True
        )
        return json.loads(result.stdout)
    else:
        raise ValueError(f"Unsupported backend: {backend}")

def write_store(backend: str, path: str, store: dict, expected_version: int) -> None:
    # Re-read and check version before writing (optimistic lock)
    current = read_store(backend, path)
    if current["version"] != expected_version:
        raise RuntimeError(
            f"Concurrent modification detected: expected version {expected_version}, "
            f"found {current['version']}. Re-read and retry."
        )
    store["version"] = expected_version + 1
    store["lastUpdated"] = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    payload = json.dumps(store, indent=2)
    if backend == "pass":
        proc = subprocess.run(["pass", "insert", "-e", path], input=payload,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"pass insert failed: {proc.stderr}")
    elif backend == "aws":
        subprocess.run(
            ["aws", "secretsmanager", "put-secret-value",
             "--secret-id", path, "--secret-string", payload],
            check=True
        )
```

## Bulk Onboarding Script

Reads a CSV of client names and tokens, validates each against `account-info/v3/details`, and seeds the credential store. Designed for onboarding 10-100 portals in a single pass. No external Python dependencies required.

### CSV format

```csv
clientSlug,portalToken,expectedPortalId
acme-corp,pat-na1-{uuid-acme},12345678
beta-inc,pat-eu1-{uuid-beta},87654321
gamma-llc,pat-na1-{uuid-gamma},11223344
```

### bulk-onboard.py

```python
#!/usr/bin/env python3
"""
HubSpot agency bulk portal onboarding.

Usage:
  python3 bulk-onboard.py --csv clients.csv --secret-backend pass \
    --secret-path hubspot/agency-portals [--dry-run]
"""

import argparse
import csv
import json
import sys
import time
import urllib.request
import urllib.error
from datetime import datetime, timezone


ACCOUNT_INFO_URL = "https://api.hubapi.com/account-info/v3/details"
TOKEN_RE_PATTERN = r"^pat-(na1|eu1|au1)-[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}$"


def verify_portal(token: str, expected_portal_id: int) -> dict:
    """Call account-info/v3/details and verify the portal ID matches."""
    req = urllib.request.Request(
        ACCOUNT_INFO_URL,
        headers={"Authorization": f"Bearer {token}"},
    )
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:
            data = json.loads(resp.read())
    except urllib.error.HTTPError as e:
        body = e.read().decode()
        raise RuntimeError(f"account-info returned {e.code}: {body}") from e

    if data["portalId"] != expected_portal_id:
        raise RuntimeError(
            f"Portal ID mismatch: token belongs to portal {data['portalId']}, "
            f"expected {expected_portal_id}"
        )

    return data


def extract_datacenter(token: str) -> str:
    """Extract datacenter code from token prefix."""
    import re
    match = re.match(TOKEN_RE_PATTERN, token, re.IGNORECASE)
    if not match:
        raise ValueError(f"Invalid token format: {token[:20]}...")
    return match.group(1)


def load_store(backend: str, path: str) -> dict:
    """Load credential store from secret backend."""
    import subprocess
    if backend == "pass":
        result = subprocess.run(["pass", "show", path], capture_output=True, text=True)
        if result.returncode != 0:
            # Store does not exist yet; return empty store
            return {"version": 0, "portals": {}}
        return json.loads(result.stdout)
    elif backend == "aws":
        result = subprocess.run(
            ["aws", "secretsmanager", "get-secret-value",
             "--secret-id", path, "--query", "SecretString", "--output", "text"],
            capture_output=True, text=True
        )
        if result.returncode != 0:
            return {"version": 0, "portals": {}}
        return json.loads(result.stdout)
    else:
        raise ValueError(f"Unsupported backend: {backend}")


def write_store(backend: str, path: str, store: dict) -> None:
    """Write credential store to secret backend."""
    import subprocess
    store["lastUpdated"] = datetime.now(timezone.utc).isoformat()
    payload = json.dumps(store, indent=2)
    if backend == "pass":
        proc = subprocess.run(["pass", "insert", "-e", path], input=payload,
                              capture_output=True, text=True)
        if proc.returncode != 0:
            raise RuntimeError(f"pass insert failed: {proc.stderr}")
    elif backend == "aws":
        subprocess.run(
            ["aws", "secretsmanager", "put-secret-value",
             "--secret-id", path, "--secret-string", payload],
            check=True
        )


def main():
    parser = argparse.ArgumentParser(description="Bulk-onboard HubSpot portals")
    parser.add_argument("--csv", required=True, help="Path to clients CSV file")
    parser.add_argument("--secret-backend", choices=["pass", "aws"], default="pass")
    parser.add_argument("--secret-path", default="hubspot/agency-portals")
    parser.add_argument("--dry-run", action="store_true",
                        help="Validate tokens but do not write to secret store")
    args = parser.parse_args()

    store = load_store(args.secret_backend, args.secret_path)
    now = datetime.now(timezone.utc).isoformat()

    results = {"verified": [], "failed": [], "skipped": []}

    with open(args.csv, newline="") as f:
        reader = csv.DictReader(f)
        rows = list(reader)

    print(f"Processing {len(rows)} portals...")

    for row in rows:
        slug = row["clientSlug"].strip()
        token = row["portalToken"].strip()
        expected_id = int(row["expectedPortalId"].strip())

        if slug in store["portals"]:
            existing_id = store["portals"][slug]["portalId"]
            if existing_id == expected_id:
                print(f"  SKIP  {slug} — already in store with correct portal ID {existing_id}")
                results["skipped"].append(slug)
                continue
            else:
                print(f"  WARN  {slug} — in store with portal ID {existing_id}, "
                      f"CSV says {expected_id}. Skipping to prevent overwrite.")
                results["skipped"].append(slug)
                continue

        try:
            datacenter = extract_datacenter(token)
            print(f"  CHECK {slug} (portal {expected_id}, {datacenter})...", end=" ", flush=True)
            details = verify_portal(token, expected_id)
            print(f"OK — {details['portalType']}, {details['currency']}, {details['timeZone']}")

            if not args.dry_run:
                store["portals"][slug] = {
                    "token": token,
                    "portalId": expected_id,
                    "clientSlug": slug,
                    "addedAt": now,
                    "lastRotatedAt": now,
                    "datacenter": datacenter,
                }
                store["version"] = store.get("version", 0) + 1

            results["verified"].append(slug)

        except Exception as e:
            print(f"FAIL — {e}")
            results["failed"].append({"slug": slug, "error": str(e)})

        # Respect rate limits — short sleep between verifications
        time.sleep(0.2)

    if not args.dry_run and results["verified"]:
        write_store(args.secret_backend, args.secret_path, store)
        print(f"\nWrote {len(results['verified'])} portals to credential store.")

    print(f"\nSummary:")
    print(f"  Verified:  {len(results['verified'])}")
    print(f"  Skipped:   {len(results['skipped'])}")
    print(f"  Failed:    {len(results['failed'])}")

    if results["failed"]:
        print("\nFailed portals:")
        for item in results["failed"]:
            print(f"  {item['slug']}: {item['error']}")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

### Running the bulk onboard

```bash
# Dry run first — validates all tokens, writes nothing
python3 references/bulk-onboard.py \
  --csv clients.csv \
  --secret-backend pass \
  --secret-path hubspot/agency-portals \
  --dry-run

# If all tokens verify, run without --dry-run
python3 references/bulk-onboard.py \
  --csv clients.csv \
  --secret-backend pass \
  --secret-path hubspot/agency-portals

# Verify the store was written correctly
pass show hubspot/agency-portals | jq '.version, (.portals | length), (.portals | keys)'
```

## Token Rotation Runbook

**Time to complete:** 10-20 minutes per portal. No downtime with staged rotation.

**Key constraint:** HubSpot's token rotation is UI-only and immediately revokes the old token. There is no overlap window. Update all downstream systems before clicking "Rotate token" in HubSpot.

### Pre-rotation checklist

Run before touching HubSpot UI for any portal:

```bash
CLIENT_SLUG="acme-corp"

# 1. Identify all systems holding this token
echo "=== Systems to update ==="
echo "[ ] Secret manager: hubspot/agency-portals"
echo "[ ] CI/CD secrets: GitHub / GitLab / CircleCI for $CLIENT_SLUG"
echo "[ ] Staging environment: .env or secret mount for $CLIENT_SLUG"
echo "[ ] Any webhook receiver storing this token"
echo "[ ] Any third-party integrations (Zapier, Make, etc.) using this token"

# 2. Get current portal ID from store (to verify new token after rotation)
PORTAL_ID=$(pass show hubspot/agency-portals | jq -r ".portals[\"$CLIENT_SLUG\"].portalId")
echo "Portal ID to verify against: $PORTAL_ID"
```

### Rotation steps

```bash
CLIENT_SLUG="acme-corp"
PORTAL_ID=$(pass show hubspot/agency-portals | jq -r ".portals[\"$CLIENT_SLUG\"].portalId")

# STEP 1: Get new token from HubSpot UI
# Go to: Settings → Integrations → Private Apps → {app name} → Auth tab → Rotate token
# Copy the new token — it is shown ONCE
NEW_TOKEN="pat-na1-..."  # paste new token here

# STEP 2: Verify the new token belongs to the expected portal (before updating anything)
curl -s "https://api.hubapi.com/account-info/v3/details" \
  -H "Authorization: Bearer $NEW_TOKEN" | \
  jq --argjson expected "$PORTAL_ID" '
    if .portalId == $expected
    then "VERIFIED — portal \(.portalId) (\(.portalType))"
    else "ERROR — token belongs to portal \(.portalId), expected \($expected). DO NOT PROCEED."
    end
  '

# STEP 3: Update the credential store
STORE=$(pass show hubspot/agency-portals)
NOW=$(date -u +%Y-%m-%dT%H:%M:%SZ)
UPDATED=$(echo "$STORE" | python3 -c "
import sys, json
store = json.load(sys.stdin)
import os
slug = os.environ['CLIENT_SLUG']
token = os.environ['NEW_TOKEN']
now = os.environ['NOW']
store['portals'][slug]['token'] = token
store['portals'][slug]['lastRotatedAt'] = now
store['version'] += 1
print(json.dumps(store, indent=2))
" )
echo "$UPDATED" | pass insert -e hubspot/agency-portals

# STEP 4: Update CI/CD secret (GitHub example)
gh secret set "HUBSPOT_TOKEN_${CLIENT_SLUG^^}" --body "$NEW_TOKEN" --repo your-org/your-repo

# STEP 5: Restart or signal the service to reload credentials
# If SIGHUP is wired:
kill -HUP $(pgrep -f hubspot-agency-router)
# Or restart:
systemctl restart hubspot-agency-router

# STEP 6: Verify the service is using the new token
curl -s "https://api.hubapi.com/crm/v3/objects/contacts?limit=1" \
  -H "Authorization: Bearer $NEW_TOKEN" | jq '.results | length'

echo "Rotation complete for $CLIENT_SLUG (portal $PORTAL_ID)"
```

### Cross-system update checklist

Produce this checklist for every rotation. Check off each system before clicking "Rotate token" in HubSpot.

```
Portal: acme-corp (ID: 12345678)
Rotation date: 2026-05-11

[ ] hubspot/agency-portals secret store updated with new token
[ ] CI/CD secret updated (GitHub Actions: HUBSPOT_TOKEN_ACME_CORP)
[ ] Staging environment updated (staging/.env or staging secret mount)
[ ] Production service restarted / signaled to reload
[ ] New token verified via account-info/v3/details
[ ] One CRM read confirmed with new token
[ ] Audit log shows calls with new token (check actor/requestId)
[ ] Old token confirmed invalid (401 on deliberate curl)
```

Confirm old token is revoked after rotation:

```bash
OLD_TOKEN="pat-na1-old-token-here"
STATUS=$(curl -s -o /dev/null -w "%{http_code}" \
  "https://api.hubapi.com/account-info/v3/details" \
  -H "Authorization: Bearer $OLD_TOKEN")
echo "Old token status: $STATUS (expect 401)"
```

## Compliance Report Generator

Reads the structured audit log (JSONL) and produces per-client call summaries for GDPR/CCPA data-processing reporting.

### compliance-report.py

```python
#!/usr/bin/env python3
"""
HubSpot agency compliance report generator.

Reads a JSONL audit log and produces per-client call summaries
for GDPR Article 30 and CCPA data-processing records.

Usage:
  python3 compliance-report.py \
    --audit-log /var/log/hubspot-agency/audit.jsonl \
    --client-slug acme-corp \
    --from 2026-05-01 \
    --to 2026-05-31 \
    --output acme-corp-may-2026.csv
"""

import argparse
import csv
import json
import sys
from collections import defaultdict
from datetime import date, datetime, timezone


def parse_args():
    parser = argparse.ArgumentParser(description="Generate HubSpot agency compliance report")
    parser.add_argument("--audit-log", required=True, help="Path to JSONL audit log file")
    parser.add_argument("--client-slug", help="Filter to single client (omit for all clients)")
    parser.add_argument("--from", dest="date_from", required=True, help="Start date (YYYY-MM-DD)")
    parser.add_argument("--to", dest="date_to", required=True, help="End date inclusive (YYYY-MM-DD)")
    parser.add_argument("--output", help="CSV output path (default: stdout)")
    return parser.parse_args()


def in_range(ts: str, date_from: date, date_to: date) -> bool:
    try:
        call_date = datetime.fromisoformat(ts.replace("Z", "+00:00")).date()
        return date_from <= call_date <= date_to
    except (ValueError, AttributeError):
        return False


def main():
    args = parse_args()
    date_from = date.fromisoformat(args.date_from)
    date_to = date.fromisoformat(args.date_to)

    # Aggregate: (clientSlug, portalId, date, method, objectType) -> {count, errors, total_ms}
    aggregates: dict[tuple, dict] = defaultdict(lambda: {"count": 0, "errors": 0, "total_ms": 0})
    portals_seen: dict[str, int] = {}  # slug -> portalId

    with open(args.audit_log) as f:
        for line_num, line in enumerate(f, 1):
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                print(f"Warning: skipping malformed line {line_num}", file=sys.stderr)
                continue

            slug = record.get("clientSlug", "unknown")
            if args.client_slug and slug != args.client_slug:
                continue
            if not in_range(record.get("ts", ""), date_from, date_to):
                continue

            portal_id = record.get("portalId", 0)
            portals_seen[slug] = portal_id
            call_date = datetime.fromisoformat(
                record["ts"].replace("Z", "+00:00")
            ).date().isoformat()
            method = record.get("method", "UNKNOWN")
            object_type = record.get("objectType", "other")
            status = record.get("statusCode", 0)
            duration = record.get("durationMs", 0)

            key = (slug, portal_id, call_date, method, object_type)
            aggregates[key]["count"] += 1
            aggregates[key]["total_ms"] += duration
            if status >= 400:
                aggregates[key]["errors"] += 1

    if not aggregates:
        print("No records found matching the filter criteria.", file=sys.stderr)
        sys.exit(0)

    rows = []
    for (slug, portal_id, call_date, method, object_type), stats in sorted(aggregates.items()):
        rows.append({
            "clientSlug": slug,
            "portalId": portal_id,
            "date": call_date,
            "method": method,
            "objectType": object_type,
            "callCount": stats["count"],
            "errorCount": stats["errors"],
            "avgDurationMs": round(stats["total_ms"] / stats["count"], 1) if stats["count"] else 0,
        })

    fieldnames = ["clientSlug", "portalId", "date", "method",
                  "objectType", "callCount", "errorCount", "avgDurationMs"]

    if args.output:
        with open(args.output, "w", newline="") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)
        # Print summary to stdout
        total_calls = sum(r["callCount"] for r in rows)
        total_errors = sum(r["errorCount"] for r in rows)
        clients = sorted(set(r["clientSlug"] for r in rows))
        print(f"Report written to {args.output}")
        print(f"Period: {date_from} to {date_to}")
        print(f"Clients: {', '.join(clients)}")
        print(f"Total calls: {total_calls} ({total_errors} errors)")
    else:
        writer = csv.DictWriter(sys.stdout, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


if __name__ == "__main__":
    main()
```

### Compliance report output

```csv
clientSlug,portalId,date,method,objectType,callCount,errorCount,avgDurationMs
acme-corp,12345678,2026-05-01,GET,contacts,1420,2,89.3
acme-corp,12345678,2026-05-01,POST,contacts,38,0,142.1
acme-corp,12345678,2026-05-01,PATCH,contacts,12,1,203.7
acme-corp,12345678,2026-05-01,GET,deals,340,0,95.2
```

### What the compliance report proves

For GDPR Article 30 (Records of Processing Activities) and CCPA data-processing disclosures, the report demonstrates:

- **Which client's data** was processed (`clientSlug` + `portalId` — verified at onboarding)
- **What operations** were performed (`method` + `objectType`)
- **When** operations occurred (`date`)
- **Volume** of processing (`callCount`)
- **Error rate** — material for SLA reporting (`errorCount`)

The `portalId` field in the report is the ground truth identifier — it was verified against HubSpot's account-info endpoint at onboarding and stored in the credential store. The `clientSlug` is the agency's internal identifier. Together, they make attribution irrefutable.

## Python Equivalent of the TypeScript Router

```python
import json
import urllib.request
import urllib.error
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Callable


@dataclass
class PortalCredential:
    token: str
    portal_id: int
    client_slug: str
    datacenter: str


@dataclass
class AuditRecord:
    ts: str
    portal_id: int
    client_slug: str
    method: str
    path: str
    status_code: int
    duration_ms: int
    object_type: str | None
    actor: str
    rate_limit_remaining: int | None


AuditWriter = Callable[[AuditRecord], None]


class PortalClient:
    BASE_URL = "https://api.hubapi.com"
    ACTOR = "hubspot-agency-router/2.0.0"

    def __init__(self, credential: PortalCredential, audit_writer: AuditWriter):
        self._cred = credential
        self._audit = audit_writer

    def request(self, method: str, path: str, body: dict | None = None) -> dict:
        import time
        url = f"{self.BASE_URL}{path}"
        data = json.dumps(body).encode() if body else None
        req = urllib.request.Request(
            url, data=data, method=method,
            headers={
                "Authorization": f"Bearer {self._cred.token}",
                "Content-Type": "application/json",
            }
        )
        start = time.monotonic()
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                duration_ms = int((time.monotonic() - start) * 1000)
                remaining = resp.headers.get("X-HubSpot-RateLimit-Daily-Remaining")
                response_body = json.loads(resp.read())
                self._write_audit(
                    method, path, resp.status, duration_ms,
                    int(remaining) if remaining else None
                )
                return response_body
        except urllib.error.HTTPError as e:
            duration_ms = int((time.monotonic() - start) * 1000)
            self._write_audit(method, path, e.code, duration_ms, None)
            raise

    def _write_audit(self, method, path, status, duration_ms, remaining):
        import re
        match = re.search(r"/crm/v\d+/objects/([^/?]+)", path)
        object_type = match.group(1) if match else None
        record = AuditRecord(
            ts=datetime.now(timezone.utc).isoformat(),
            portal_id=self._cred.portal_id,
            client_slug=self._cred.client_slug,
            method=method,
            path=path,
            status_code=status,
            duration_ms=duration_ms,
            object_type=object_type,
            actor=self.ACTOR,
            rate_limit_remaining=remaining,
        )
        try:
            self._audit(record)
        except Exception as e:
            import sys
            print(f"Audit write failed: {e}", file=sys.stderr)


class HubSpotAgencyRouter:
    def __init__(self, store: dict, audit_writer: AuditWriter):
        self._portals = {
            slug: PortalCredential(
                token=cred["token"],
                portal_id=cred["portalId"],
                client_slug=slug,
                datacenter=cred["datacenter"],
            )
            for slug, cred in store["portals"].items()
        }
        self._audit = audit_writer
        self._cache: dict[str, PortalClient] = {}

    def get_client(self, client_slug: str) -> PortalClient:
        if client_slug not in self._portals:
            raise KeyError(
                f"Unknown client slug: {client_slug!r}. "
                f"Available: {sorted(self._portals)}"
            )
        if client_slug not in self._cache:
            self._cache[client_slug] = PortalClient(
                self._portals[client_slug], self._audit
            )
        return self._cache[client_slug]


# Usage
import sys

def stdout_audit(record: AuditRecord) -> None:
    sys.stdout.write(json.dumps(record.__dict__) + "\n")

store = json.loads(open("/run/secrets/hubspot-agency-portals").read())
router = HubSpotAgencyRouter(store, stdout_audit)

client = router.get_client("acme-corp")
contacts = client.request("GET", "/crm/v3/objects/contacts?limit=10")
```
