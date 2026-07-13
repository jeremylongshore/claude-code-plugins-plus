# navan-data-handling — One-Pager

Extract and transform Navan booking and transaction data using pagination, filtering, and data pipeline connectors.

## The Problem

Navan API responses return nested booking objects keyed by UUIDs, with no cursor-based pagination documentation and inconsistent date filtering behavior. Developers building analytics dashboards or data warehouses need to handle bulk data extraction reliably, but the direct API has rate limits and the connector ecosystem (Fivetran, Airbyte, Estuary) each has its own configuration quirks. The BOOKING table is re-imported weekly while TRANSACTION is incremental, creating different handling requirements.

## The Solution

This skill covers data extraction from both the direct REST API and managed connectors. For the API path, it provides pagination patterns, date-range filtering, and UUID-based deduplication. For the connector path, it documents Fivetran setup, Airbyte connector configuration (v0.0.42), and Estuary Flow bindings. Both paths include schema mapping for downstream analytics.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Data engineers and analytics developers building Navan data pipelines |
| **What** | Paginated data extraction, connector configuration, and schema mapping for BOOKING and TRANSACTION tables |
| **When** | Building a data warehouse integration, setting up recurring data pulls, or debugging data quality issues |

## Key Features

1. **Dual extraction paths** — Direct REST API calls and managed connectors (Fivetran, Airbyte, Estuary)
2. **UUID-based deduplication** — Handle the BOOKING table's weekly re-import without duplicate records
3. **Schema mapping** — Document actual response fields for downstream transformation and analytics

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
