# Lindy Observability - Implementation Guide

## Supported Architecture

Use Lindy's documented UI-native path:

```text
Tasks (manual investigation)
       |
Agent Task Change (selected lifecycle events)
       |
Get Task Details (Auto agent/task association)
       |
Condition + explicit field mapping
       +--> internal alert with task link
       +--> HTTP Request to a protected metrics receiver
```

Do not poll an assumed Lindy REST API. Lindy's public documentation describes Tasks,
Agent Task Change, Get Task Details, and the outbound HTTP Request action for this
use case; it does not document the `/v1/runs`, `/v1/agents`, or `/v1/webhooks`
endpoints previously shown in this reference.

## UI Configuration Checklist

### Monitored Agent

1. Open **Tasks** and inspect enough normal and failed tasks to cover each workflow
   path.
2. Choose a stable, low-cardinality key such as `support-bot`. Keep the display name,
   task ID, user ID, email address, and task title out of metric labels.
3. Record expected task volume and duration from this workspace, not generic values.

### Monitoring Agent

1. Add **Agent Task Change**.
2. Select the monitored agent and events: succeeded, failed, and canceled.
3. Add **Get Task Details**. Keep Agent and Sub Task on Auto; choose a block limit
   large enough for the observed workflow.
4. Add a condition for failure alerts and link back to the task.
5. Add **HTTP Request** with POST and JSON content type.
6. Store a receiver-owned callback secret as a protected Authorization bearer value.
   It must be distinct from any secret used to invoke an inbound Lindy webhook.
7. Map exactly `agent`, `status`, and `durationSeconds`. Do not map Get Task Details
   inputs, outputs, prompts, messages, or error bodies.

## Acceptance Tests

| Test | Expected result |
|---|---|
| Known agent, known status, bounded duration, valid secret | `200` and one metric increment |
| Missing or wrong bearer value | `401`; no metric increment |
| Unknown agent/status/field or invalid duration | `400`; no metric increment |
| Body larger than receiver limit | Request rejected |
| Prometheus scrape | Counter and histogram appear with only configured labels |
| Failure alert | Contains task link and operational metadata, no task content |

## Threshold Calibration

Collect a representative baseline before creating alerts. For each workflow class,
record task count, outcome ratio, median duration, p95 duration, and observation
window. Choose alert windows that contain enough expected tasks to be meaningful.
Document the chosen threshold, owner, review date, and rollback action. Recalculate
after intentional workflow or traffic changes.

## Official References

- [Monitor Your Agents](https://docs.lindy.ai/testing/monitoring-your-agents)
- [Tasks](https://docs.lindy.ai/fundamentals/lindy-101/tasks)
- [Observability utilities](https://docs.lindy.ai/skills/lindy-utilities/observability)
- [HTTP Request](https://docs.lindy.ai/skills/by-lindy/http-request)
