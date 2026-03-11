---
name: clay-architecture-variants
description: |
  Choose and implement Clay validated architecture blueprints for different scales.
  Use when designing new Clay integrations, choosing between monolith/service/microservice
  architectures, or planning migration paths for Clay applications.
  Trigger with phrases like "clay architecture", "clay blueprint",
  "how to structure clay", "clay project layout", "clay microservice".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Clay Architecture Variants

## Overview
Deployment architectures for Clay data enrichment at different scales. Clay's table-based enrichment model, credit billing, and webhook-driven workflow fit differently depending on volume, team size, and data freshness requirements.

## Prerequisites
- Clay account with API access
- Clear understanding of data volume and freshness needs
- Infrastructure for chosen architecture tier

## Instructions

### Step 1: Direct Integration (Simple)

**Best for:** Small teams, < 1K enrichments/day, ad-hoc usage.

```
Application -> Clay API -> Enriched Data -> Application DB
```

```python
import requests

def enrich_lead(email: str) -> dict:
    response = requests.post(
        f"{CLAY_API}/tables/{TABLE_ID}/rows",
        json={"rows": [{"email": email}]},
        headers={"Authorization": f"Bearer {API_KEY}"}
    )
    # Poll for enrichment completion
    row_id = response.json()["row_ids"][0]
    return poll_enrichment(TABLE_ID, row_id)
```

**Trade-offs:** Simple but synchronous. Each enrichment blocks until complete (30-60s). No retry or buffering.

### Step 2: Queue-Based Pipeline (Moderate)

**Best for:** Growing teams, 1K-50K enrichments/day, CRM integration.

```
CRM Webhook -> Queue (Redis/SQS) -> Worker -> Clay API
                                        |
                                        v
                                   Enriched Data -> CRM Update
```

```python
from rq import Queue
import redis

q = Queue(connection=redis.Redis())

def on_new_lead(lead: dict):
    q.enqueue(enrich_and_update, lead, job_timeout=120)

def enrich_and_update(lead: dict):
    # Batch multiple leads for efficiency
    enriched = clay_enrich_batch([lead])
    crm_client.update_contact(lead["id"], enriched[0])
```

**Trade-offs:** Decouples enrichment from user flow. Handles retries and batching. Needs queue infrastructure.

### Step 3: Event-Driven with Webhooks (Scale)

**Best for:** Enterprise, 50K+ enrichments/day, real-time data needs.

```
Data Sources -> Event Bus (Kafka) -> Clay Enrichment Service
                                            |
                                     Clay Webhooks -> Event Bus -> Downstream Services
```

```python
# Clay enrichment microservice
class ClayEnrichmentService:
    def __init__(self, kafka_producer, credit_budget):
        self.producer = kafka_producer
        self.budget = credit_budget

    async def handle_event(self, event: dict):
        if not self.budget.can_afford(1):
            self.producer.send("dlq.clay", event)
            return
        result = await self.enrich(event)
        self.producer.send("enriched.contacts", result)
        self.budget.record(1)

# Clay webhook receiver
@app.post('/clay-webhook')
async def clay_webhook(request):
    payload = await request.json()
    # Clay sends enrichment results via webhook
    await kafka_producer.send("enriched.contacts", payload)
    return {"status": "ok"}
```

**Trade-offs:** Fully async, horizontally scalable. Requires event bus, monitoring, and DLQ handling.

## Decision Matrix

| Factor | Direct | Queue-Based | Event-Driven |
|--------|--------|-------------|--------------|
| Volume | < 1K/day | 1K-50K/day | 50K+/day |
| Latency | Sync (30-60s) | Async (minutes) | Async (seconds) |
| Cost Control | Manual | Budget caps | Credit circuit breaker |
| Complexity | Low | Medium | High |
| Team Size | 1-3 | 3-10 | 10+ |

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Slow enrichment in request path | Using direct integration at scale | Move to queue-based |
| Lost enrichment results | No webhook receiver | Set up Clay webhooks |
| Credit overspend | No budget enforcement | Add credit circuit breaker |
| Stale data | No re-enrichment schedule | Add periodic refresh jobs |

## Examples


**Basic usage**: Apply clay architecture variants to a standard project setup with default configuration options.

**Advanced scenario**: Customize clay architecture variants for production environments with multiple constraints and team-specific requirements.

## Resources
- [Clay API Docs](https://docs.clay.com/api)
- [Clay Webhooks](https://docs.clay.com/webhooks)

## Output

- Configuration files or code changes applied to the project
- Validation report confirming correct implementation
- Summary of changes made and their rationale