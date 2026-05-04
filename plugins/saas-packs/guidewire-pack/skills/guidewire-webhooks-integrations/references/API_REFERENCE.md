# Guidewire Webhooks & Event Integrations — Reference

Event payload schemas, messaging configuration, and consumer-side patterns supporting `SKILL.md`.

## Standard event payload shape

Every Guidewire-emitted event carries a common header followed by a per-event-type body:

```json
{
  "messageId": "5f9d6f8e-7c3a-4b2e-9c1d-1e2f3a4b5c6d",
  "eventType": "claim.status.changed",
  "eventTime": "2026-04-15T14:30:00.123Z",
  "tenant": "acme",
  "correlationId": "8b1f9c2e-...-...",
  "schemaVersion": "1.0",
  "payload": {
    "claimId": "cc:8001",
    "claimNumber": "CLM-2026-0001",
    "oldStatus": "Open",
    "newStatus": "Closed"
  }
}
```

`messageId` is the dedup key. `correlationId` ties the event back to the originating user action / API call (cross-references `integration_audit` from `guidewire-security-and-rbac`). `schemaVersion` enables forward-compatible consumer behavior across future payload changes.

## Common event types

The list is carrier-configurable but the typical shape:

| Event type | Fired when |
|---|---|
| `account.created` | new account registered |
| `submission.quoted` | submission moves Draft → Quoted |
| `submission.bound` | submission moves Quoted → Bound |
| `policy.issued` | bound policy moves to In Force |
| `policy.endorsed` | endorsement bound |
| `policy.renewed` | renewal bound |
| `policy.cancelled` | cancellation effective |
| `claim.created` | FNOL accepted |
| `claim.status.changed` | claim status transitions (Open → Closed, Closed → Reopened) |
| `claim.reserve.changed` | reserve created or amount changed |
| `claim.payment.created` | payment requested |
| `claim.payment.status.changed` | payment moves through approval states |
| `claim.activity.completed` | required activity marked complete |

Subscribe to only the events the downstream system actually needs; subscribing to everything multiplies queue throughput and consumer cost without value.

## Messaging.xml destination configuration

```xml
<MessagingConfig>
  <Destination ID="acme-claim-events" 
               TransportClass="com.acme.messaging.SqsTransport" 
               Suspendable="true">
    <Property Name="queueUrl" Value="https://sqs.us-east-1.amazonaws.com/123/gw-claim-events" />
    <Property Name="awsRegion" Value="us-east-1" />
  </Destination>
  <MessageEvent Type="claim.status.changed" Destination="acme-claim-events" />
  <MessageEvent Type="claim.payment.status.changed" Destination="acme-claim-events" />
</MessagingConfig>
```

The `Suspendable="true"` flag lets administrators pause emission without dropping events — InsuranceSuite queues internally until resumed. Useful for deploy windows where the downstream consumer is offline by design.

## Idempotency datastore options

| Datastore | TTL recommendation | Tradeoff |
|---|---|---|
| Redis with EXPIRE | 7d (≥queue retention) | Fastest; data loss on Redis flush risks duplicate processing |
| Postgres table with index on messageId | 30d | Persistent; slightly slower; requires periodic cleanup of expired rows |
| DynamoDB with TTL | 30d | Managed; auto-expiry; consistent across regions |

The choice depends on throughput and durability requirements. High-throughput consumers (>1k events/sec) prefer Redis with periodic snapshot to Postgres for recovery; lower-throughput consumers can use Postgres directly.

## Deferred-events queue schema

```sql
CREATE TABLE deferred_events (
  id UUID PRIMARY KEY,
  message_id UUID UNIQUE NOT NULL,
  event_type TEXT NOT NULL,
  reason TEXT NOT NULL,                  -- "waiting-on-claim-created", "missing-exposure-parent"
  payload JSONB NOT NULL,
  first_attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  last_attempted_at TIMESTAMPTZ NOT NULL DEFAULT now(),
  attempt_count INT NOT NULL DEFAULT 1,
  escalate_after TIMESTAMPTZ NOT NULL DEFAULT (now() + interval '24 hours')
);

CREATE INDEX deferred_events_due ON deferred_events(escalate_after) 
  WHERE attempt_count < 100;
```

A periodic job (every minute) scans for events past `last_attempted_at + backoff` and re-enters them through the consumer pipeline. Events past `escalate_after` route to a manual-review queue.

## Replay APIs

Server-side event-replay availability varies by tenant. Where available, the Cloud API event endpoint:

```http
GET /cc/rest/v1/events?eventType=claim.status.changed&since=2026-04-15T00:00:00Z&until=2026-04-15T23:59:59Z
```

Pagination via `offsetToken` per `guidewire-sdk-patterns`. Each event in the response has the same shape as the live-emitted payload, so the consumer's existing handler is the replay handler — no parallel code path.

If server-side replay is not available for a given tenant, the consumer's local checkpoint + write-through audit log is the only replay substrate; this is why the audit-log discipline matters.

## Kafka partitioning strategies

For high-volume event integrations using Kafka instead of SQS, partition by entity id to preserve in-order delivery per entity:

| Partition key | Effect |
|---|---|
| `claimId` | all events for one claim hit the same partition; consumer for that partition processes them in order |
| `policyId` | same, for policy events |
| `tenantId` | per-tenant partitioning; useful for multi-tenant fan-out |
| (none / random) | maximum throughput, no ordering guarantee — only safe with idempotent consumer |

Idempotent consumer is required regardless — Kafka delivers at-least-once even with strict partitioning.

## Schema evolution

Events evolve over time (new fields, occasionally removed fields). Consumers must tolerate without breaking:

- New optional field added → consumer ignores; no version bump
- New required field added → producer-side coordination required; bump `schemaVersion`
- Field removed → producer-side coordination required; bump `schemaVersion`; consumer reads with default

The consumer should log unknown fields it does not yet handle, not error. Strict-parsing breaks compatibility every time the producer adds a field; lenient parsing breaks compatibility only on actually-removed fields.

## Multi-tenant event fan-out

When the same Guidewire integration serves multiple tenants and downstream consumers, route events to per-tenant queues:

```xml
<MessageEvent Type="claim.status.changed" 
              Destination="claim-events-{Tenant}" 
              ConditionExpression="claim.Policy.Tenant" />
```

Per-tenant queues isolate noisy tenants and let each tenant's consumer scale independently. Cost: more queues to manage; benefit: blast-radius containment when one tenant's consumer falls over.

## Related references

- `references/implementation-guide.md` — extended walkthrough
- Sibling `guidewire-core-workflow-a/references/API_REFERENCE.md` — workflows that emit policy events
- Sibling `guidewire-core-workflow-b/references/API_REFERENCE.md` — workflows that emit claim events
- Sibling `guidewire-observability-and-incident-response/references/API_REFERENCE.md` — queue-depth alerting
