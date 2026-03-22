---
name: palantir-reference-architecture
description: |
  Implement Palantir Foundry reference architecture with best-practice project layout.
  Use when designing new Foundry integrations, planning data pipeline architecture,
  or establishing patterns for Ontology-driven applications.
  Trigger with phrases like "palantir architecture", "foundry best practices",
  "foundry project structure", "how to organize palantir".
allowed-tools: Read, Grep
version: 2.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags: [saas, palantir, foundry, architecture, patterns]
compatible-with: claude-code, codex, openclaw
---

# Palantir Reference Architecture

## Overview
Production-ready architecture for Foundry-integrated applications. Covers the standard data pipeline pattern (ingest > clean > model > serve), Ontology design, external API integration, and multi-repo project layout.

## Prerequisites
- Foundry enrollment with project access
- Understanding of Ontology concepts (object types, link types, actions)
- Familiarity with `palantir-core-workflow-a` (transforms) and `palantir-core-workflow-b` (Ontology)

## Instructions

### Step 1: Data Pipeline Architecture
```
┌─────────────┐     ┌──────────────┐     ┌─────────────┐     ┌───────────┐
│  Raw Layer   │────>│  Clean Layer │────>│ Model Layer │────>│ Ontology  │
│ (ingested)   │     │  (validated) │     │ (enriched)  │     │ (objects) │
└─────────────┘     └──────────────┘     └─────────────┘     └───────────┘
  ↑ Connectors        @transform_df       @transform_df       Object types
  ↑ REST sync          null checks         joins, aggs         Link types
  ↑ File upload        type casting        ML features         Actions
```

### Step 2: Project Layout (Foundry)
```
Foundry Project: "Customer Analytics"
├── Datasets/
│   ├── raw/                    # Ingested from sources
│   │   ├── raw_orders          # REST connector → CRM
│   │   ├── raw_customers       # JDBC connector → DB
│   │   └── raw_products        # File upload (CSV/Parquet)
│   ├── clean/                  # Validated, typed
│   │   ├── clean_orders        # Nulls removed, dates parsed
│   │   ├── clean_customers     # Deduped, normalized
│   │   └── clean_products      # Schema enforced
│   └── model/                  # Enriched, analytics-ready
│       ├── order_enriched      # Joined with customer + product
│       ├── customer_360        # Aggregated customer view
│       └── daily_summary       # Time-series aggregation
├── Code Repositories/
│   ├── pipeline-ingestion/     # Connectors and raw → clean
│   ├── pipeline-analytics/     # Clean → model transforms
│   └── ontology-actions/       # Action implementations
└── Ontology/
    ├── Object Types: Customer, Order, Product
    ├── Link Types: Customer→Orders, Order→Products
    └── Actions: createOrder, updateCustomerSegment
```

### Step 3: External API Integration Pattern
```python
# External app consuming Foundry Ontology via Platform SDK
my-external-app/
├── src/
│   ├── foundry/
│   │   ├── client.py           # Singleton FoundryClient
│   │   ├── objects.py          # Object query helpers
│   │   ├── actions.py          # Action wrappers
│   │   └── cache.py            # TTL cache layer
│   ├── api/
│   │   ├── routes.py           # REST endpoints
│   │   └── webhooks.py         # Foundry event handlers
│   └── main.py
├── tests/
│   ├── conftest.py             # Mocked FoundryClient
│   ├── test_objects.py
│   └── test_actions.py
├── .env                        # FOUNDRY_HOSTNAME, credentials
└── requirements.txt
```

### Step 4: Ontology Design Patterns
| Pattern | When to Use | Example |
|---------|-------------|---------|
| Hub-and-spoke | Central entity with many relationships | Customer → Orders, Tickets, Payments |
| Event sourcing | Audit trail needed | OrderEvent (created, shipped, delivered) |
| Computed properties | Derived values | `totalRevenue` on Customer (sum of orders) |
| Composite actions | Multi-step mutations | `processReturn`: update order + create credit + notify |

### Step 5: Security Layers
```
┌──────────────────────────────────────────┐
│ Layer 1: Network (VPN/private link)       │
├──────────────────────────────────────────┤
│ Layer 2: OAuth2 (service user per app)    │
├──────────────────────────────────────────┤
│ Layer 3: Scopes (minimum per app)         │
├──────────────────────────────────────────┤
│ Layer 4: Project roles (Viewer/Editor)    │
├──────────────────────────────────────────┤
│ Layer 5: Marking (data classification)    │
└──────────────────────────────────────────┘
```

## Output
- Standard 3-layer data pipeline (raw > clean > model)
- Ontology design with typed objects, links, and actions
- External app architecture with caching and webhooks
- Security model with 5 defense layers

## Error Handling
| Architecture Issue | Symptom | Fix |
|--------------------|---------|-----|
| Circular dependencies | Builds fail | Restructure pipeline DAG |
| Missing clean layer | Bad data in model | Always validate between raw and model |
| Monolithic transforms | Slow builds | Split into focused transforms |
| No caching | API rate limits | Add TTL cache layer |

## Resources
- [Foundry Documentation](https://www.palantir.com/docs/foundry)
- [Ontology SDK Overview](https://www.palantir.com/docs/foundry/ontology-sdk/overview)
- [Transforms Guide](https://www.palantir.com/docs/foundry/transforms-python/transforms)

## Next Steps
For data handling and compliance, see `palantir-data-handling`.
