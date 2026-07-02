# HubSpot Skill Pack

> Claude Code skill pack for HubSpot CRM integration -- 10 production-engineer skills built from a real-world pain catalog, covering auth, webhooks, dedup, migrations, pipeline automation, and rate-limit survival on the CRM v3 API.

## What is HubSpot?

HubSpot is a CRM platform for marketing, sales, and customer service. The HubSpot API (v3) provides programmatic access to CRM objects (contacts, companies, deals, tickets), marketing tools (emails, forms, lists), and automation (webhooks, workflows). The official Node.js SDK is `@hubspot/api-client`.

## Pack Overview

Version 2.0.0 is a deliberate rebuild: the original 30 template skills were replaced by 10 deeper, pain-catalog-grounded skills written for production engineers. Each skill targets the failure modes that actually burn HubSpot integrations — wrong-winner merges, webhook replay storms, portal quota exhaustion, cross-portal contamination — using real HubSpot API endpoints (`/crm/v3/objects/*`), the actual `@hubspot/api-client` SDK, and documented error responses.

## Installation

```bash
/plugin install hubspot-pack@claude-code-plugins-plus
```

## Quick Start

```bash
npm install @hubspot/api-client
export HUBSPOT_ACCESS_TOKEN=pat-na1-xxxxxxxx-xxxx-xxxx-xxxx-xxxxxxxxxxxx
```

```typescript
import * as hubspot from '@hubspot/api-client';

const client = new hubspot.Client({
  accessToken: process.env.HUBSPOT_ACCESS_TOKEN!,
  numberOfApiCallRetries: 3,
});

// Create a contact
const contact = await client.crm.contacts.basicApi.create({
  properties: { email: 'jane@example.com', firstname: 'Jane', lifecyclestage: 'lead' },
  associations: [],
});

// Search contacts
const results = await client.crm.contacts.searchApi.doSearch({
  filterGroups: [{
    filters: [{ propertyName: 'lifecyclestage', operator: 'EQ', value: 'customer' }],
  }],
  properties: ['email', 'firstname'],
  limit: 10, after: 0, sorts: [],
});

// Batch read (100 contacts in 1 API call)
const batch = await client.crm.contacts.batchApi.read({
  inputs: ids.map(id => ({ id })),
  properties: ['email'], propertiesWithHistory: [],
});
```

## Skills Included

| Skill | What it covers |
|-------|----------------|
| `hubspot-auth` | Authenticate production integrations (private app tokens vs OAuth), scope design, and auth-side failure modes |
| `hubspot-webhook-handlers` | v3 webhook handlers that survive production: HMAC-SHA256 signature verification, Redis SET NX deduplication, async batch processing |
| `hubspot-rate-limit-survival` | The daily 500K portal quota, per-10s burst limits, batch API efficiency (100x), token bucket pattern, queue-based smoothing |
| `hubspot-contact-dedup` | Deduplication at production scale: import storms, wrong-winner merges, fuzzy-match blind spots, association orphans |
| `hubspot-bulk-migration` | Bulk migration in or out of HubSpot (Salesforce, Pipedrive, Copper) with field mapping, ID continuity, association re-linking |
| `hubspot-deal-pipeline-automation` | Stage automation loops, stale-deal safe-close logic, and pipeline auditing without destroying real pipeline |
| `hubspot-lifecycle-and-lists` | Lifecycle stage progression guards and list segmentation without silently destroying CRM trust |
| `hubspot-product-event-sync` | Idempotent batched sync of backend product events into contact/company custom properties (the Segment pattern without Segment) |
| `hubspot-warehouse-sync` | CRM-to-warehouse sync (BigQuery, Snowflake, Postgres): initial backfill of millions of records under quota, then incremental |
| `hubspot-agency-multi-portal` | Managing 10-100 client portals with credential isolation, per-portal audit trails, and GDPR/CCPA separation |

## Key HubSpot API Concepts

- **Base URL:** `https://api.hubapi.com`
- **Auth:** Private app access tokens (`pat-na1-*`) or OAuth 2.0
- **Rate limits:** 10 requests/second, 500,000/day (shared per portal)
- **Batch limit:** 100 records per batch operation
- **Search limit:** 10,000 results maximum (use `getPage` for full exports)
- **SDK package:** `@hubspot/api-client` (not `@hubspot/sdk`)

## Usage

Skills trigger automatically when you discuss HubSpot topics:

- "Set up HubSpot auth for production" triggers `hubspot-auth`
- "Our webhook handler is double-processing events" triggers `hubspot-webhook-handlers`
- "I'm getting 429s from HubSpot" triggers `hubspot-rate-limit-survival`
- "We have thousands of duplicate contacts" triggers `hubspot-contact-dedup`

## License

MIT
