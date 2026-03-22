---
name: persona-core-workflow-b
description: |
  Work with Persona verification types: government ID, selfie, database checks.
  Use when implementing specific verification checks, reviewing verification results,
  or building custom verification workflows.
  Trigger with phrases like "persona verification", "government ID check",
  "selfie verification", "persona database check", "verification results".
allowed-tools: Read, Write, Edit, Bash(curl:*), Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, verification, government-id, selfie, kyc]
compatible-with: claude-code, codex, openclaw
---

# Persona Core Workflow B — Verification Checks

## Overview
Work with Persona's verification types: government ID (passport, driver's license), selfie liveness detection, and database checks (SSN, watchlist). Covers retrieving verification details, interpreting check results, and handling edge cases.

## Prerequisites
- Completed `persona-core-workflow-a` (inquiry flow)
- Inquiry Template with verification checks configured

## Instructions

### Step 1: List Verifications for an Inquiry
```python
import os, requests

HEADERS = {
    "Authorization": f"Bearer {os.environ['PERSONA_API_KEY']}",
    "Persona-Version": "2023-01-05",
}
BASE = "https://withpersona.com/api/v1"

# Get all verifications for an inquiry
resp = requests.get(f"{BASE}/inquiries/inq_XXXXX", headers=HEADERS)
resp.raise_for_status()
inquiry = resp.json()["data"]
verifications = inquiry["relationships"]["verifications"]["data"]

for v in verifications:
    v_resp = requests.get(f"{BASE}/verifications/{v['id']}", headers=HEADERS)
    v_data = v_resp.json()["data"]["attributes"]
    print(f"  Type: {v['type']}")
    print(f"  Status: {v_data['status']}")  # passed, failed, requires_retry
    print(f"  Checks: {v_data.get('checks', [])}")
```

### Step 2: Government ID Verification Results
```python
# Government ID verification includes extracted data
def get_gov_id_details(verification_id: str) -> dict:
    resp = requests.get(f"{BASE}/verifications/{verification_id}", headers=HEADERS)
    resp.raise_for_status()
    attrs = resp.json()["data"]["attributes"]

    return {
        "status": attrs["status"],
        "first_name": attrs.get("name-first"),
        "last_name": attrs.get("name-last"),
        "dob": attrs.get("birthdate"),
        "id_number": attrs.get("identification-number"),
        "id_class": attrs.get("id-class"),          # dl, pp, id
        "country": attrs.get("country-code"),
        "expiry": attrs.get("expiration-date"),
        "checks": {
            check["name"]: check["status"]
            for check in attrs.get("checks", [])
        },
    }

# Example checks: id_barcode_detection, id_integrity, id_selfie_comparison
```

### Step 3: Selfie Liveness Check
```python
def get_selfie_result(verification_id: str) -> dict:
    resp = requests.get(f"{BASE}/verifications/{verification_id}", headers=HEADERS)
    attrs = resp.json()["data"]["attributes"]

    return {
        "status": attrs["status"],
        "center_photo_url": attrs.get("center-photo-url"),
        "checks": {
            check["name"]: check["status"]
            for check in attrs.get("checks", [])
        },
        # Key checks: selfie_pose_detection, selfie_liveness_detection
    }
```

### Step 4: Database Verification (SSN, Watchlist)
```python
def get_database_check(verification_id: str) -> dict:
    resp = requests.get(f"{BASE}/verifications/{verification_id}", headers=HEADERS)
    attrs = resp.json()["data"]["attributes"]

    return {
        "status": attrs["status"],
        "checks": {
            check["name"]: {
                "status": check["status"],
                "reasons": check.get("reasons", []),
            }
            for check in attrs.get("checks", [])
        },
        # Key checks: database_ssn_check, database_watchlist_check
    }
```

### Step 5: Decision Logic
```python
def make_verification_decision(inquiry_id: str) -> str:
    resp = requests.get(f"{BASE}/inquiries/{inquiry_id}", headers=HEADERS)
    verifications = resp.json()["data"]["relationships"]["verifications"]["data"]

    all_passed = True
    for v in verifications:
        v_resp = requests.get(f"{BASE}/verifications/{v['id']}", headers=HEADERS)
        status = v_resp.json()["data"]["attributes"]["status"]
        if status != "passed":
            all_passed = False
            print(f"  FAILED: {v['type']} — {status}")

    return "approved" if all_passed else "manual_review"
```

## Output
- Verification results retrieved with extracted data
- Government ID fields (name, DOB, ID number) parsed
- Selfie liveness status checked
- Database checks (SSN, watchlist) interpreted

## Error Handling
| Verification Status | Meaning | Action |
|--------------------|---------|--------|
| `passed` | All checks passed | Approve user |
| `failed` | One or more checks failed | Decline or manual review |
| `requires_retry` | Poor image quality | Ask user to retry |
| `initiated` | Check still running | Poll again |

## Resources
- [Government ID Verifications](https://docs.withpersona.com/api-reference/verifications/government-id-verifications)
- [Verification Checks](https://docs.withpersona.com/api-reference/verifications)

## Next Steps
- Handle events via webhooks: `persona-webhooks-events`
- Debug verification issues: `persona-common-errors`
