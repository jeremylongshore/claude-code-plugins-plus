---
name: persona-hello-world
description: |
  Create your first Persona identity verification inquiry and check its status.
  Use when learning Persona API basics, testing inquiry creation,
  or building a simple verification flow.
  Trigger with phrases like "persona hello world", "first persona inquiry",
  "persona quick start", "test identity verification".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, persona, identity, kyc, getting-started]
compatible-with: claude-code, codex, openclaw
---

# Persona Hello World

## Overview
Create a Persona inquiry, generate an embed URL for the verification flow, and poll for the inquiry status. Uses the real Persona REST API with sandbox credentials.

## Prerequisites
- Completed `persona-install-auth` setup
- An Inquiry Template ID from the Persona Dashboard (format: `itmpl_*`)

## Instructions

### Step 1: Create an Inquiry
```python
import os, requests

API_KEY = os.environ["PERSONA_API_KEY"]
BASE = "https://withpersona.com/api/v1"
HEADERS = {
    "Authorization": f"Bearer {API_KEY}",
    "Persona-Version": "2023-01-05",
    "Content-Type": "application/json",
}

# Create a new inquiry from a template
resp = requests.post(f"{BASE}/inquiries", headers=HEADERS, json={
    "data": {
        "attributes": {
            "inquiry-template-id": "itmpl_YOUR_TEMPLATE_ID",
            "reference-id": "user-12345",  # Your internal user ID
        }
    }
})
resp.raise_for_status()
inquiry = resp.json()["data"]
inquiry_id = inquiry["id"]
status = inquiry["attributes"]["status"]
print(f"Inquiry created: {inquiry_id} (status: {status})")
```

### Step 2: Get the Verification URL
```python
# The inquiry includes a session token for the embedded flow
session_token = inquiry["attributes"].get("session-token")
if session_token:
    # Option A: Hosted flow (redirect user to Persona)
    hosted_url = f"https://withpersona.com/verify?inquiry-id={inquiry_id}&session-token={session_token}"
    print(f"Send user to: {hosted_url}")

    # Option B: Embedded flow (JavaScript SDK in your page)
    print(f"Embed with: Persona.Client({{ templateId: 'itmpl_...', inquiryId: '{inquiry_id}' }})")
```

### Step 3: Poll for Completion
```python
import time

for _ in range(30):  # Poll for up to 5 minutes
    resp = requests.get(f"{BASE}/inquiries/{inquiry_id}", headers=HEADERS)
    resp.raise_for_status()
    status = resp.json()["data"]["attributes"]["status"]
    print(f"  Status: {status}")

    if status in ("completed", "approved", "declined"):
        break
    time.sleep(10)

# Get verification details
if status == "completed":
    verifications = resp.json()["data"]["relationships"]["verifications"]["data"]
    for v in verifications:
        print(f"  Verification: {v['type']} — {v['id']}")
```

### Step 4: Retrieve Verification Results
```python
# Get detailed verification result
verification_id = verifications[0]["id"]
v_resp = requests.get(f"{BASE}/verifications/{verification_id}", headers=HEADERS)
v_resp.raise_for_status()
v_data = v_resp.json()["data"]["attributes"]
print(f"  Check: {v_data['status']}")
print(f"  Name: {v_data.get('name-first', 'N/A')} {v_data.get('name-last', 'N/A')}")
```

## Output
- Inquiry created with unique ID
- Hosted or embedded verification URL generated
- Inquiry status polled until completion
- Verification results retrieved

## Error Handling
| Error | Cause | Solution |
|-------|-------|----------|
| `422 Unprocessable` | Invalid template ID | Verify template ID in Dashboard |
| Inquiry stays `created` | User hasn't started flow | Share the hosted URL with user |
| Empty verifications | Inquiry not completed | Wait for user to complete verification |
| `404 Not Found` | Wrong inquiry ID | Check ID format: `inq_*` |

## Resources
- [Inquiries Overview](https://docs.withpersona.com/inquiries)
- [Accessing Inquiry Status](https://docs.withpersona.com/accessing-inquiry-status)
- [API Quickstart Tutorial](https://docs.withpersona.com/api-quickstart-tutorial)

## Next Steps
- Build full KYC flow: `persona-core-workflow-a`
- Handle webhook events: `persona-webhooks-events`
