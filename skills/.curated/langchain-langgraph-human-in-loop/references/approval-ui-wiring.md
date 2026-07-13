# Approval UI Wiring

The HTTP contract and Slack Block Kit mapping for a LangGraph-backed approval
UI. Two endpoints, one concurrency primitive, one audit log. Everything else
is glue.

## Endpoint 1 — GET `/approvals/pending`

Lists all paused threads. The UI (web dashboard, Slack cron poster, whatever)
calls this to render the approval queue.

### Request

```
GET /approvals/pending?tenant=acme&limit=50
Authorization: Bearer <user_token>
```

### Response

```json
{
  "pending": [
    {
      "thread_id": "conv-abc123",
      "checkpoint_id": "01JABCXYZ000000000000000",
      "interrupted_at": "2026-04-21T15:32:11Z",
      "node": "send_email",
      "interrupt_kind": "before",
      "payload": null,
      "state_diff": {
        "draft": {
          "to": "user@example.com",
          "subject": "Welcome to Acme",
          "body_preview": "Hi Sarah, welcome..."
        }
      },
      "requested_by": "agent:onboarding-flow",
      "tags": ["email", "external-recipient"]
    }
  ],
  "total": 12,
  "as_of": "2026-04-21T15:34:02Z"
}
```

Fields:

- **`thread_id`** — pass back verbatim to POST /decision
- **`checkpoint_id`** — ULID from the checkpointer. Pass back in
  `expected_checkpoint_id` for optimistic concurrency
- **`node`** — which node is about to run (for `interrupt_before`) or just
  ran (for `interrupt_after`)
- **`interrupt_kind`** — `"before"`, `"after"`, or `"inline"`
- **`payload`** — for inline `interrupt(payload)`, the payload dict; null otherwise
- **`state_diff`** — subset of state relevant to this approval. DO NOT ship
  full state — it may contain PII, internal reasoning traces, or tokens
- **`tags`** — your categorization. Lets the UI filter ("show only email
  approvals," "show only high-risk")

### Implementation sketch (FastAPI + PostgresSaver)

```python
@app.get("/approvals/pending")
async def list_pending(
    tenant: str,
    user: User = Depends(current_user),
    limit: int = 50,
) -> list[dict]:
    # Authorize: user must have "approve" permission for tenant
    if not user.can_approve(tenant):
        raise HTTPException(403)

    results = []
    async for thread_id in _list_threads_for_tenant(tenant, limit=limit):
        snapshot = await graph.aget_state({"configurable": {"thread_id": thread_id}})
        if not snapshot.next:
            continue  # thread completed, skip
        results.append({
            "thread_id": thread_id,
            "checkpoint_id": snapshot.config["configurable"]["checkpoint_id"],
            "interrupted_at": snapshot.created_at,
            "node": snapshot.next[0],
            "interrupt_kind": _classify_interrupt(snapshot),
            "payload": snapshot.values.get("_interrupt_payload"),
            "state_diff": _redact_and_diff(snapshot.values),
            "tags": _tags_from_state(snapshot.values),
        })
    return {"pending": results, "total": len(results), "as_of": utcnow()}
```

Cache policy: `Cache-Control: no-store`. The queue changes as soon as any
approver acts.

## Endpoint 2 — POST `/approvals/{thread_id}/decision`

The approver submits their decision. Idempotent by `expected_checkpoint_id`.

### Request

```
POST /approvals/conv-abc123/decision
Authorization: Bearer <user_token>
Content-Type: application/json

{
  "decision": "edit",
  "edits": {
    "draft": {"subject": "Welcome to Acme (Revised)"}
  },
  "approver": "jeremy@intentsolutions.io",
  "reason": "Matches ticket INT-4821",
  "expected_checkpoint_id": "01JABCXYZ000000000000000",
  "idempotency_key": "c2f5e8a0-...-abc"
}
```

Fields:

- **`decision`** — `"approve"`, `"reject"`, or `"edit"`
- **`edits`** — only present when `decision == "edit"`. Dict of state patches
  (merged via reducers)
- **`approver`** — who approved. Your auth middleware should set this, not
  trust the client — but echoing it here makes audit-log inspection easy
- **`reason`** — free-text justification. Required for `reject` and `edit`;
  optional for `approve`
- **`expected_checkpoint_id`** — optimistic lock. Server returns 409 if the
  thread has advanced since the approver loaded it
- **`idempotency_key`** — client-generated UUID. Server dedupes duplicate
  POSTs (network retry, double-click, etc.)

### Response

```json
{
  "thread_id": "conv-abc123",
  "checkpoint_id_before": "01JABCXYZ000000000000000",
  "checkpoint_id_after": "01JABCXYZ111111111111111",
  "status": "applied",
  "audit_id": "aud-7c3f9e"
}
```

### Response codes

| Code | Meaning | UI action |
|------|---------|-----------|
| 200 | Applied | Show success, refresh queue |
| 400 | Malformed request, missing field | Surface the validation error |
| 403 | Approver lacks permission for this thread | "You cannot approve this" |
| 404 | Thread not found | "Thread was deleted" |
| 409 | `expected_checkpoint_id` mismatch | "Another approver acted first" — refresh |
| 410 | Thread already completed (not paused) | "Nothing to approve" — dismiss |
| 422 | Reducer conflict (edit shape mismatches schema) | Surface the error |
| 423 | Thread locked for concurrent edit | Retry after short backoff |

### Implementation sketch

```python
@app.post("/approvals/{thread_id}/decision")
async def post_decision(
    thread_id: str,
    body: DecisionBody,
    user: User = Depends(current_user),
) -> dict:
    # 1. Authz
    if not user.can_approve_thread(thread_id):
        raise HTTPException(403)

    # 2. Idempotency
    cached = await idempotency_store.get(body.idempotency_key)
    if cached:
        return cached

    config = {"configurable": {"thread_id": thread_id}}

    # 3. Optimistic concurrency check
    snapshot = await graph.aget_state(config)
    if not snapshot.next:
        raise HTTPException(410, "Thread not paused")
    actual_ckpt = snapshot.config["configurable"]["checkpoint_id"]
    if actual_ckpt != body.expected_checkpoint_id:
        raise HTTPException(409, f"Checkpoint moved; expected {body.expected_checkpoint_id}, got {actual_ckpt}")

    # 4. Audit log BEFORE mutation
    audit_id = await audit_log.write(
        thread_id=thread_id,
        checkpoint_id=actual_ckpt,
        decision=body.decision,
        edits=body.edits,
        approver=user.email,
        reason=body.reason,
        outcome="pending",
    )

    # 5. Build command
    if body.decision == "reject":
        cmd = Command(
            update={"last_decision": "rejected", "reject_reason": body.reason},
            resume="rejected",
        )
    elif body.decision == "edit":
        cmd = Command(update=body.edits, resume="approved")
    else:  # approve
        cmd = Command(resume="approved")

    # 6. Apply
    try:
        result = await graph.ainvoke(cmd, config)
    except Exception as e:
        await audit_log.update(audit_id, outcome="error", error=str(e))
        raise HTTPException(500, "Graph invocation failed; audit entry recorded")

    # 7. Finalize audit
    new_snapshot = await graph.aget_state(config)
    await audit_log.update(audit_id, outcome="applied", applied_at=utcnow())

    response = {
        "thread_id": thread_id,
        "checkpoint_id_before": actual_ckpt,
        "checkpoint_id_after": new_snapshot.config["configurable"]["checkpoint_id"],
        "status": "applied",
        "audit_id": audit_id,
    }
    await idempotency_store.put(body.idempotency_key, response, ttl=24*3600)
    return response
```

## State-diff rendering

Shipping full state to the UI is dangerous (PII, internal tokens) and usually
noisy. Filter to the keys that matter for *this* approval:

```python
INTEREST_KEYS_BY_NODE = {
    "send_email": ["draft", "recipient_verification"],
    "charge_card": ["amount", "card_last4", "merchant"],
    "deploy_release": ["version", "environment", "changeset"],
}

def build_state_diff(node: str, state: dict) -> dict:
    keys = INTEREST_KEYS_BY_NODE.get(node, [])
    return {k: state.get(k) for k in keys if k in state}
```

For `draft` or `body` that might contain long text, send a preview:

```python
def preview(s: str, n: int = 200) -> str:
    return s if len(s) <= n else s[:n] + "..."
```

## Slack Block Kit mapping

Slack is the most common approval UI because it works without building a web
dashboard. Post one message per pending approval:

```python
def pending_to_slack_blocks(pending: dict) -> list[dict]:
    return [
        {
            "type": "header",
            "text": {"type": "plain_text", "text": f"Approval needed: {pending['node']}"},
        },
        {
            "type": "section",
            "fields": [
                {"type": "mrkdwn", "text": f"*Thread:* `{pending['thread_id']}`"},
                {"type": "mrkdwn", "text": f"*Waiting since:* {pending['interrupted_at']}"},
            ],
        },
        {
            "type": "section",
            "text": {"type": "mrkdwn", "text": f"```{json.dumps(pending['state_diff'], indent=2)}```"},
        },
        {
            "type": "actions",
            "block_id": f"approval:{pending['thread_id']}:{pending['checkpoint_id']}",
            "elements": [
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Approve"},
                    "style": "primary",
                    "action_id": "approve",
                    "value": pending["checkpoint_id"],
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Reject"},
                    "style": "danger",
                    "action_id": "reject",
                    "value": pending["checkpoint_id"],
                },
                {
                    "type": "button",
                    "text": {"type": "plain_text", "text": "Edit..."},
                    "action_id": "edit",
                    "value": pending["checkpoint_id"],
                },
            ],
        },
    ]
```

The `block_id` encodes `thread_id` + `checkpoint_id`. When Slack POSTs the
interaction, parse it and call POST /decision. Validate the Slack signing
secret (`X-Slack-Signature`) before trusting any fields.

The "Edit..." button opens a modal with the state-diff as editable fields.
Map the modal submission to `edits` in the decision body.

## Rate-limiting the approval endpoint

POST /decision is cheap (one DB read, one graph invoke) but the graph invoke
can fan out to expensive tool calls. Rate-limit per approver to prevent a
compromised account from mass-approving:

- Per approver: 10 decisions/minute
- Per tenant: 100 decisions/minute
- Global: whatever your infra handles

429 on limit; include `Retry-After` header.

## What NOT to put in the approval UI

- Raw LLM system prompts (leaks your prompt engineering)
- Internal tool names (leaks architecture)
- Full state object (PII risk; too noisy)
- Any token, secret, credential — ever
- Raw tool_use block JSON — map to a human-friendly description

## Audit log retention

SOC2 / ISO 27001 typically require 1-7 years of audit log retention. LangGraph
checkpoints live on the checkpointer DB; the audit log should live separately
with retention policies matching your compliance posture.

Minimum fields to retain:

- `thread_id`, `checkpoint_id_before`, `checkpoint_id_after`
- `approver` (email/user ID), `approved_at`
- `decision`, `edits` (redacted), `reason`
- Hash of state-diff the approver saw (to prove what was shown)

Periodically garbage-collect completed threads from the checkpointer, but
NEVER garbage-collect audit entries before their retention expires.
