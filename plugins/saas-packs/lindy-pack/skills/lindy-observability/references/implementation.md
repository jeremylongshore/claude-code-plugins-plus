# Lindy Observability -- Data and Security Contract

## Minimal Event Schema

The monitoring workflow may export only:

```json
{
  "agent": "support-bot",
  "status": "succeeded",
  "durationSeconds": 12.4
}
```

The receiver owns the allowlist for `agent` and `status`, rejects extra keys, and
bounds duration and body size. Task IDs may appear in a short-lived operator alert
link but not as metric labels. Never export or log task titles, prompts, messages,
block inputs/outputs, email addresses, customer identifiers, authorization headers,
or error bodies.

## Secret Boundaries

Use three separate concepts:

| Secret | Purpose | Must not be reused for |
|---|---|---|
| Lindy-generated webhook secret | Authenticate callers to an inbound Webhook Received trigger | Metrics callbacks |
| `LINDY_CALLBACK_SECRET` | Authenticate Lindy's outbound HTTP Request to the collector | Inbound trigger calls |
| Metrics scrape credential | Authenticate the monitoring system to the collector | Either Lindy direction |

Fail receiver startup when the callback secret is missing or empty. Rotate it by
briefly accepting old/new values, update Lindy's protected header, verify a test
event, then retire the old value. Never print either value during diagnostics.

## Cardinality Budget

Metric labels are limited to a deployment-owned agent key and a three-value terminal
status enum. Put environment identity in deployment configuration or a separately
bounded label only when multiple environments share one registry. Do not derive any
label from task content. A new agent key requires configuration review and a bounded
allowlist update.

## Failure Investigation

1. Use the alert's authorized task link to open Tasks inside Lindy.
2. Review Get Task Details or the chronological task view there.
3. Record only the failing block name and an internal incident category externally.
4. Redact customer content from tickets and chat. If an exact excerpt is essential,
   use the approved restricted incident system and its retention policy.
5. Confirm remediation against a sanitized fixture before reactivating the workflow.

## Unsupported API Warning

Do not copy older examples that poll unofficial agent/run endpoints, register
callbacks through an undocumented REST surface, or request a generic workspace API
key. Follow Lindy's current Tasks, Agent Task Change, Get Task Details, and HTTP
Request documentation instead.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
