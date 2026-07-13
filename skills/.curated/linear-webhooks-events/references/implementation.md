# Linear Webhooks & Events -- Implementation Reference

## Overview

Configure Linear webhooks to receive real-time events for issues, projects, comments,
and cycles. Includes signature verification, event routing, and idempotent processing.

## Prerequisites

- Linear API key with admin scope (for webhook creation)
- Public HTTPS endpoint (ngrok for local dev)
- Python 3.9+ or Node.js 18+

## Webhook Registration

```python
import os
import json
import urllib.request

LINEAR_API_KEY = os.environ["LINEAR_API_KEY"]
TEAM_ID = os.environ["LINEAR_TEAM_ID"]
WEBHOOK_URL = os.environ["WEBHOOK_URL"]
WEBHOOK_SECRET = os.environ["LINEAR_WEBHOOK_SECRET"]


def graphql(query: str, variables: dict) -> dict:
    headers = {
        "Content-Type": "application/json",
        "Authorization": LINEAR_API_KEY,
    }
    body = json.dumps({"query": query, "variables": variables}).encode()
    req = urllib.request.Request(
        "https://api.linear.app/graphql",
        data=body, headers=headers, method="POST",
    )
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read())["data"]


def register_webhook(resource_types: list = None) -> dict:
    if resource_types is None:
        resource_types = ["Issue", "Comment", "Project", "Cycle"]

    mutation = """
    mutation CreateWebhook($input: WebhookCreateInput!) {
      webhookCreate(input: $input) {
        success
        webhook { id label url enabled secret }
      }
    }
    """
    result = graphql(mutation, {
        "input": {
            "url": WEBHOOK_URL,
            "teamId": TEAM_ID,
            "label": "Production webhook",
            "secret": WEBHOOK_SECRET,
            "resourceTypes": resource_types,
            "enabled": True,
        }
    })
    webhook = result["webhookCreate"]["webhook"]
    print(f"Registered webhook: {webhook['id']}")
    return webhook


def list_webhooks() -> list:
    query = """
    query {
      webhooks { nodes { id label url enabled resourceTypes } }
    }
    """
    return graphql(query, {})["webhooks"]["nodes"]
```

## FastAPI Webhook Handler with Signature Verification

```python
import hashlib
import hmac
import json
import logging
import os
from fastapi import FastAPI, Header, HTTPException, Request
from fastapi.responses import JSONResponse

logger = logging.getLogger(__name__)
app = FastAPI()

WEBHOOK_SECRET = os.environ["LINEAR_WEBHOOK_SECRET"]
_processed_events: set = set()  # Use Redis in production


def verify_signature(payload: bytes, signature: str) -> bool:
    expected = hmac.new(
        WEBHOOK_SECRET.encode(),
        payload,
        hashlib.sha256,
    ).hexdigest()
    sig = signature.removeprefix("sha256=") if signature.startswith("sha256=") else signature
    return hmac.compare_digest(expected, sig)


@app.post("/linear-events")
async def handle_linear_event(
    request: Request,
    x_linear_signature: str = Header(None),
):
    payload = await request.body()

    if not x_linear_signature or not verify_signature(payload, x_linear_signature):
        raise HTTPException(status_code=401, detail="Invalid signature")

    event = json.loads(payload)
    event_id = f"{event.get('webhookId', '')}:{event.get('createdAt', '')}"

    if event_id in _processed_events:
        return JSONResponse({"status": "already_processed"})
    _processed_events.add(event_id)

    await route_event(event)
    return JSONResponse({"status": "ok"})


async def route_event(event: dict) -> None:
    etype = event.get("type")
    action = event.get("action")
    data = event.get("data", {})

    logger.info("Linear event: %s/%s id=%s", etype, action, data.get("id"))

    handlers = {
        ("Issue", "create"): on_issue_created,
        ("Issue", "update"): on_issue_updated,
        ("Comment", "create"): on_comment_created,
        ("Project", "update"): on_project_updated,
    }
    handler = handlers.get((etype, action))
    if handler:
        await handler(data)


async def on_issue_created(data: dict) -> None:
    identifier = data.get("identifier", "?")
    title = data.get("title", "")
    priority = data.get("priority", 0)
    logger.info("New issue: %s -- %s (priority %d)", identifier, title, priority)
    # Add: Slack notification, Jira mirror, auto-assign logic, etc.


async def on_issue_updated(data: dict) -> None:
    identifier = data.get("identifier", "?")
    changes = data.get("updatedFrom", {})
    if "stateId" in changes:
        logger.info("Status change on %s", identifier)


async def on_comment_created(data: dict) -> None:
    body = data.get("body", "")
    issue_id = data.get("issueId", "?")
    logger.info("Comment on %s: %.60s...", issue_id, body)


async def on_project_updated(data: dict) -> None:
    name = data.get("name", "?")
    state = data.get("state", "?")
    logger.info("Project updated: %s => %s", name, state)
```

## Local Development with ngrok

```bash
# Terminal 1: start your FastAPI handler
uvicorn webhook_handler:app --reload --port 8000

# Terminal 2: expose via ngrok
ngrok http 8000
# Copy the https URL and set WEBHOOK_URL, then:
python3 -c "from webhook_handler import register_webhook; register_webhook()"

# Test webhook delivery manually
curl -X POST https://api.linear.app/graphql \
  -H "Authorization: $LINEAR_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{"query":"mutation { webhookTest(id: \"WEBHOOK_ID\") { success } }"}'
```

## Event Type Reference

| Type | Actions | Key Fields |
|------|---------|-----------|
| Issue | create, update, remove | id, identifier, title, stateId, assigneeId, priority |
| Comment | create, update, remove | id, body, issueId, userId |
| Project | create, update, remove | id, name, state, teamIds |
| Cycle | create, update | id, number, startsAt, endsAt |
| IssueLabel | create, update | id, name, color |

## TypeScript Express Handler

```typescript
import express from 'express';
import crypto from 'crypto';

const app = express();
app.use(express.raw({ type: 'application/json' }));

const WEBHOOK_SECRET = process.env.LINEAR_WEBHOOK_SECRET!;

function verifySignature(payload: Buffer, signature: string): boolean {
  const expected = crypto
    .createHmac('sha256', WEBHOOK_SECRET)
    .update(payload)
    .digest('hex');
  return crypto.timingSafeEqual(
    Buffer.from(expected),
    Buffer.from(signature.replace('sha256=', ''))
  );
}

app.post('/linear-events', (req, res) => {
  const sig = req.headers['x-linear-signature'] as string;
  if (!sig || !verifySignature(req.body, sig)) {
    return res.status(401).json({ error: 'Invalid signature' });
  }

  const event = JSON.parse(req.body.toString());
  console.log(`Linear event: ${event.type}/${event.action}`);

  res.json({ status: 'ok' });
});

app.listen(8000);
```

## Resources

- [Linear Webhooks Docs](https://developers.linear.app/docs/sdk/webhooks)
- [FastAPI](https://fastapi.tiangolo.com/)
- [ngrok](https://ngrok.com/docs)

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
