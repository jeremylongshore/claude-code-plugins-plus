---
name: palantir-webhooks-events
description: |
  Implement Palantir Foundry webhook handling for Ontology change events.
  Use when reacting to Ontology object changes, dataset updates,
  or build completion events from Foundry.
  Trigger with phrases like "palantir webhook", "foundry events",
  "palantir notifications", "ontology change events".
allowed-tools: Read, Write, Edit, Bash(curl:*)
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, webhooks, events]
compatible-with: claude-code, codex, openclaw
---

# Palantir Webhooks & Events

## Overview
Handle Foundry webhook events for Ontology changes, dataset updates, and build completions. Covers webhook registration via the Foundry API, signature verification, event routing, and idempotent processing.

## Prerequisites
- Foundry enrollment with webhook support enabled
- HTTPS endpoint accessible from Foundry's network
- `foundry-platform-sdk` installed

## Instructions

### Step 1: Register a Webhook via API
```python
import os, foundry

client = foundry.FoundryClient(
    auth=foundry.ConfidentialClientAuth(
        client_id=os.environ["FOUNDRY_CLIENT_ID"],
        client_secret=os.environ["FOUNDRY_CLIENT_SECRET"],
        hostname=os.environ["FOUNDRY_HOSTNAME"],
        scopes=["api:read-data", "api:write-data"],
    ),
    hostname=os.environ["FOUNDRY_HOSTNAME"],
)

# Register webhook for object change events
webhook = client.webhooks.Webhook.create(
    url="https://myapp.example.com/webhooks/foundry",
    event_types=["ontology.object.created", "ontology.object.updated"],
    secret="whsec_your_webhook_secret_here",
)
print(f"Webhook registered: {webhook.rid}")
```

### Step 2: Webhook Endpoint with Signature Verification
```python
from flask import Flask, request, jsonify
import hmac, hashlib

app = Flask(__name__)

@app.post("/webhooks/foundry")
def handle_foundry_webhook():
    # Verify signature
    signature = request.headers.get("X-Foundry-Signature", "")
    timestamp = request.headers.get("X-Foundry-Timestamp", "")
    secret = os.environ["FOUNDRY_WEBHOOK_SECRET"]

    signed_payload = f"{timestamp}.{request.get_data(as_text=True)}"
    expected = hmac.new(
        secret.encode(), signed_payload.encode(), hashlib.sha256
    ).hexdigest()

    if not hmac.compare_digest(signature, expected):
        return jsonify({"error": "Invalid signature"}), 401

    # Replay protection — reject timestamps older than 5 minutes
    import time
    if abs(time.time() - int(timestamp)) > 300:
        return jsonify({"error": "Timestamp too old"}), 401

    event = request.get_json()
    handle_event(event)
    return jsonify({"received": True}), 200
```

### Step 3: Event Router
```python
def handle_event(event: dict):
    event_type = event.get("type", "")
    handlers = {
        "ontology.object.created": on_object_created,
        "ontology.object.updated": on_object_updated,
        "ontology.object.deleted": on_object_deleted,
        "dataset.updated": on_dataset_updated,
        "build.completed": on_build_completed,
    }
    handler = handlers.get(event_type)
    if handler:
        handler(event["data"])
    else:
        print(f"Unhandled event type: {event_type}")

def on_object_created(data: dict):
    obj_type = data["objectType"]
    primary_key = data["primaryKey"]
    print(f"Object created: {obj_type}/{primary_key}")
    # Sync to external system, trigger workflow, etc.

def on_object_updated(data: dict):
    obj_type = data["objectType"]
    changes = data.get("changedProperties", {})
    print(f"Object updated: {obj_type} — changed: {list(changes.keys())}")

def on_object_deleted(data: dict):
    print(f"Object deleted: {data['objectType']}/{data['primaryKey']}")

def on_dataset_updated(data: dict):
    print(f"Dataset updated: {data['datasetRid']} branch={data['branch']}")

def on_build_completed(data: dict):
    status = data["buildStatus"]
    print(f"Build {data['buildRid']}: {status}")
```

### Step 4: Idempotent Processing
```python
import redis

r = redis.Redis.from_url(os.environ.get("REDIS_URL", "redis://localhost:6379"))

def idempotent_handle(event: dict):
    event_id = event["id"]
    key = f"foundry:event:{event_id}"
    if r.exists(key):
        print(f"Skipping duplicate event: {event_id}")
        return
    handle_event(event)
    r.setex(key, 86400 * 7, "processed")  # 7-day TTL
```

## Output
- Webhook registered with Foundry for Ontology/dataset events
- Signature verification with replay protection
- Event router dispatching to typed handlers
- Idempotent processing preventing duplicate handling

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Invalid signature | Wrong webhook secret | Verify secret matches registration |
| Timestamp rejected | Server clock drift | Sync NTP; widen tolerance |
| Duplicate events | Network retry | Use event ID deduplication |
| Handler timeout | Slow processing | Offload to background queue |

## Resources
- [Foundry API Reference](https://www.palantir.com/docs/foundry/api/general/overview/introduction)
- [Foundry Documentation](https://www.palantir.com/docs/foundry)

## Next Steps
For performance optimization, see `palantir-performance-tuning`.
