---
name: lindy-reference-architecture
description: 'Reference architectures for Lindy AI agent integrations.

  Use when designing systems, planning multi-agent architectures,

  or implementing production integration patterns.

  Trigger with phrases like "lindy architecture", "lindy design",

  "lindy system design", "lindy patterns", "lindy multi-agent".

  '
allowed-tools: Read, Write, Edit
version: 1.18.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- lindy
- lindy-reference
compatibility: Portable instructions for agent harnesses that can read Markdown and edit architecture documents
---
# Lindy Reference Architecture

## Overview

Choose an integration shape for Lindy workflows without inventing a public SDK or
control-plane API. The supported application boundary in these patterns is a
dashboard-created Lindy webhook trigger, optionally paired with Lindy's HTTP Request
or callback action for outbound delivery.

## Prerequisites

- Understanding of Lindy agent model (triggers, actions, skills)
- Familiarity with webhook-based architectures
- Production requirements defined (throughput, latency, reliability)
- Current workspace evidence for the triggers, actions, integrations, and plan
  entitlements you intend to use
- A separate secret for each Lindy trigger and a different secret for each callback
  receiver; neither belongs in source control or architecture diagrams

## Instructions

1. Write the workload's trust boundaries before selecting a pattern: event producers,
   Lindy trigger, callback receiver, stores, operators, and third parties.
2. Record data classification, maximum payload size, expected event rate, recovery
   objective, and whether duplicate delivery is safe.
3. Select the smallest pattern below that meets those requirements. Treat product
   features as available only after verifying them in the current Lindy workspace.
4. For every webhook edge, require HTTPS, an exact approved hostname, a per-edge
   secret, schema validation, payload bounds, idempotency, bounded retry, and a
   dead-letter or manual recovery path.
5. Test authorized and unauthorized requests with synthetic data. A 2xx response is
   insufficient evidence unless the expected task or durable queue record exists.
6. Produce the architecture decision record and dataflow inventory described in
   **Output**, then have a security reviewer approve the exact deployment revision.

## Trust-Boundary Contract

- A Lindy trigger URL is created in the dashboard and uses the documented
  `https://public.lindy.ai/api/v1/webhooks/...` shape. Validate `https:` and the exact
  `public.lindy.ai` hostname before attaching its Lindy-generated trigger secret.
- Authenticate your own event ingress independently. Do not reuse a Lindy trigger
  secret to protect your application or callback endpoint.
- Minimize and redact event data before enqueueing it. Do not forward credentials,
  session tokens, raw customer records, or unrestricted third-party webhook bodies.
- Acknowledge external events only after a durable, idempotent queue write. Check the
  Lindy response before marking delivery successful, and retry only transient failures
  with a strict attempt and elapsed-time budget.
- Installed skills and local configuration are consumers of this design; they are not
  publication sources and must never upload secrets or runtime state.

## Architecture 1: Simple Webhook Integration

Single agent triggered by your application, results sent via callback.

```
┌─────────────┐       POST (webhook)       ┌──────────────┐
│  Your App   │ ─────────────────────────→  │ Lindy Agent  │
│             │                             │              │
│  /callback  │ ←─────────────────────────  │ HTTP Request │
│             │       POST (callback)       │   Action     │
└─────────────┘                             └──────────────┘
```

**Implementation**:

- Your app sends a bounded request to its dashboard-created Lindy webhook using that
  trigger's Lindy-generated bearer secret.
- When a response is required, pass an allowlisted callback URL or opaque callback ID.
- The Lindy workflow uses the currently available callback or HTTP Request action. Your
  callback receiver verifies its own distinct secret and accepts only the documented
  response schema.

**Best for**: Simple automations (email triage, lead scoring, content generation)

## Architecture 2: Event-Driven Pipeline

Multiple event sources feed agents through a central webhook router.

```
┌──────────┐
│ Stripe   │──webhook──┐
└──────────┘           │
                       ▼
┌──────────┐     ┌───────────┐     ┌──────────────┐
│ Shopify  │──→  │  Router   │──→  │ Lindy Agents │
└──────────┘     │  Service  │     │              │
                 └───────────┘     │ • Order Bot  │
┌──────────┐           ▲          │ • Support Bot│
│ Your App │──webhook──┘          │ • Analytics  │
└──────────┘                      └──────────────┘
```

**Implementation**:

```text
authenticated producer
  -> schema and size validation
  -> field allowlist and redaction
  -> idempotent durable queue
  -> route chosen from a static event-to-trigger map
  -> exact HTTPS/public.lindy.ai sink check
  -> attach only that route's trigger secret
  -> bounded delivery and response validation
  -> receipt with event ID, route, attempt count, and status (never payload/secret)
```

Keep the event-to-trigger map in trusted configuration rather than request data. The
downloadable implementation guide contains a secure sender boundary; it deliberately
uses documented webhook primitives rather than an assumed SDK client.

**Best for**: Multiple event sources, different agents per event type

## Architecture 3: Multi-Agent Society (Delegation)

Specialized workflows collaborate through the agent-to-agent actions or webhook edges
that are visibly available in the current workspace. Do not assume an action name,
delivery guarantee, or universal delegation entitlement from this document.

```
┌─────────────────┐
│ Orchestrator    │
│ Lindy           │
│ (receives       │
│  initial task)  │
└───┬────────┬────┘
    │        │
    ▼        ▼
┌────────┐ ┌────────┐
│Research│ │Analysis│
│ Lindy  │ │ Lindy  │
└───┬────┘ └───┬────┘
    │          │
    ▼          ▼
┌─────────────────┐
│ Writer Lindy    │
│ (synthesizes    │
│  final output)  │
└─────────────────┘
```

**Setup in Lindy**:

1. Define one bounded contract per specialist: accepted fields, result schema, timeout,
   and failure owner.
2. Select a currently supported agent-to-agent action or the secured webhook pattern.
3. Pass only the fields the specialist needs and correlate every result with a task ID.
4. Require the orchestrator to handle timeout, partial completion, duplicate results,
   and human escalation before synthesis.

**Key decisions**:

| Decision | Option A | Option B |
|----------|---------|---------|
| Context passing | Full context (accurate, expensive) | Selective context (cheap, focused) |
| Error handling | Agent retries | Orchestrator retry logic |
| Parallelism | Sequential delegation | Parallel delegation with merge |

**Best for**: Complex tasks requiring multiple specialties (research + analysis + writing)

## Architecture 4: Scheduled Pipeline

Agents run on schedules, each feeding data to the next.

```
                    Schedule: Daily 6 AM
                         │
                         ▼
                  ┌──────────────┐
                  │ Data Fetch   │ Pulls from APIs/databases
                  │ Lindy        │
                  └──────┬───────┘
                         │ Agent Send Message
                         ▼
                  ┌──────────────┐
                  │ Analysis     │ Processes & summarizes
                  │ Lindy        │
                  └──────┬───────┘
                         │ Agent Send Message
                         ▼
                  ┌──────────────┐
                  │ Report       │ Formats & delivers
                  │ Lindy        │
                  │  → Slack     │
                  │  → Email     │
                  └──────────────┘
```

**Best for**: Daily reports, weekly digests, scheduled data processing

## Architecture 5: Chat + Knowledge Base

Agent exposed through a chat surface currently supported by the workspace and grounded
in an approved knowledge base.

```
┌──────────────┐     ┌──────────────┐     ┌──────────────┐
│  Website     │     │ Lindy Agent  │     │ Knowledge    │
│  (Embed      │◀──▶ │              │◀──▶ │ Base         │
│   Widget)    │     │ Chat Trigger │     │ PDFs, Docs,  │
└──────────────┘     │ + KB Search  │     │ Websites     │
                     │ + Condition  │     └──────────────┘
                     │ + Escalate   │
                     └──────────────┘
                            │
                            ▼ (if escalation needed)
                     ┌──────────────┐
                     │ Slack DM to  │
                     │ human agent  │
                     └──────────────┘
```

**Deployment boundary**:

- Publish only through a chat or embed surface shown in current Lindy documentation or
  the workspace UI; do not paste an unverified script URL from a template.
- Approve each knowledge source, record its owner and refresh cadence, and test that
  revoked or sensitive documents are not retrievable.
- Configure result count and matching behavior from measured answer quality rather than
  hard-coded template values.
- Add human escalation and an explicit no-answer path before public exposure.

**Best for**: Customer support, FAQ bots, internal knowledge assistants

## Architecture Decision Matrix

| Pattern | Choose when | Measure before approval | Primary risk |
|---------|-------------|-------------------------|--------------|
| Simple webhook | One bounded async workflow | end-to-end latency, duplicate rate | callback spoofing |
| Event-driven pipeline | Multiple producers or replay required | queue lag, retry volume | event/data fan-out |
| Multi-agent workflow | Specialist boundaries improve quality | completion rate, context size | authority drift |
| Scheduled pipeline | Work is naturally periodic | freshness, missed-run recovery | silent schedule gaps |
| Chat + knowledge base | Users need interactive retrieval | answer quality, escalation rate | sensitive retrieval |

## Error Handling

| Pattern | Failure Mode | Recovery |
|---------|-------------|----------|
| Simple webhook | Agent fails or callback is rejected | retain receipt; retry within budget; escalate |
| Event-driven | Router or downstream unavailable | keep durable event; replay idempotently |
| Multi-agent | Specialist times out or returns invalid data | stop synthesis or use approved partial-result policy |
| Scheduled | Run is missed | alert; perform an explicit catch-up run if safe |
| Chat + KB | Evidence is absent or access is denied | say no answer; escalate without exposing hidden data |

## Output

Return two reviewable artifacts:

1. **Architecture decision record**: chosen pattern, alternatives rejected, current
   Lindy capabilities verified, capacity assumptions, failure policy, rollback trigger,
   owners, and review date.
2. **Dataflow and trust-boundary inventory**: every edge's producer, destination,
   allowed schema, classification, authentication owner, secret scope, size/rate bound,
   idempotency key, retention, log policy, and recovery path.

No output may contain webhook URLs, bearer values, customer payloads, or copied runtime
configuration. Use route names and redacted identifiers in diagrams and receipts.

## Examples

For an order-triage workflow, choose the event-driven pattern and record:

```yaml
decision: event-driven-webhook
event: order.created.v1
allowed_fields: [event_id, order_id, country_code, risk_band]
durable_before_ack: true
idempotency_key: event_id
trigger_route: lindy-order-triage
trigger_sink: https/public.lindy.ai
callback_auth: distinct-from-trigger
retry_budget: "3 attempts within 5 minutes"
rollback: "pause consumer and retain queued events"
evidence: "authorized task created; unauthorized request created no task"
```

The record names the sink class, not the unique webhook path, and includes no order
contents or credentials. A reviewer can reproduce both the accepted and rejected paths
with synthetic IDs before production traffic is enabled.

## Resources

- [Lindy Introduction](https://docs.lindy.ai/fundamentals/lindy-101/introduction)
- [Lindy Webhooks](https://docs.lindy.ai/skills/by-lindy/webhooks)
- [Lindy HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
- [Monitoring Your Agents](https://docs.lindy.ai/testing/monitoring-your-agents)

## Next Steps

Proceed to Flagship tier skills for enterprise features: multi-env, observability,
incident response, data handling, RBAC, and migration.
