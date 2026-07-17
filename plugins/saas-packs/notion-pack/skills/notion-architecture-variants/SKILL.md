---
name: notion-architecture-variants
description: |
  Use when you are choosing or scaffolding how an app talks to Notion via the
  API — deciding between a headless CMS (blog/content site), a task tracker
  (project management), a knowledge base (wiki), a form-submission handler, or a
  data-pipeline source, and wiring the database schema plus integration code.
  Trigger with phrases like "notion cms", "notion headless blog",
  "notion task tracker", "notion wiki", "notion form handler", "notion data pipeline".
allowed-tools: Read, Write, Edit, Bash(node:*)
version: 1.38.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- productivity
- notion
compatibility: Designed for Claude Code
---
# Notion Architecture Variants

## Overview

Five validated architecture patterns for using Notion as a backend via the API, each with database schema design, integration code, and deployment tradeoffs. The full copy-ready code for every variant lives in [references/implementation.md](references/implementation.md); this page gives the decision framework, the shared skeleton, and one worked example so you can pick the right pattern and drill into depth on demand.

The five variants:

| Variant | Use case | Core operation |
| --------- | ---------- | ---------------- |
| Headless CMS | Blog / content site | Query `Status = Published`, render blocks to HTML |
| Task Tracker | Project management | Group by status for a board, `pages.update` on move |
| Knowledge Base | Wiki / internal docs | Workspace `search` filtered to the wiki database |
| Form Handler | Contact / lead capture | One `pages.create` per submission |
| Data Pipeline | Analytics / ETL source | Paginate on a `last_edited_time` watermark |

## Prerequisites

- `@notionhq/client` v2.x installed (`npm install @notionhq/client`)
- Python: `notion-client` installed (`pip install notion-client`)
- `NOTION_TOKEN` environment variable set
- Notion databases created and shared with your integration

## Authentication

All variants authenticate the same way: an internal integration token in the
`NOTION_TOKEN` environment variable, passed as `auth` when constructing the
client (`new Client({ auth: process.env.NOTION_TOKEN })` / `Client(auth=...)`).
Create the integration at notion.so/my-integrations, then **share each database
with the integration** from its Notion page — an unshared database returns
`object_not_found` even with a valid token. Never hard-code the token; read it
from the environment.

## Instructions

1. **Pick the variant** that matches your workload using the decision helper in
   [references/examples.md](references/examples.md) — content authoring vs.
   real-time status vs. high read volume each point to a different pattern.
2. **Model the database schema** in Notion for that variant (property names and
   types are documented inline with each variant's code). Share the database
   with your integration.
3. **Read** any existing integration module, then **Write** the client setup:
   construct one `Client` with `auth: process.env.NOTION_TOKEN` and reference
   each database by its own `NOTION_*_DB` env var.
4. **Implement the variant's operations** from
   [references/implementation.md](references/implementation.md) — copy the
   TypeScript (or Python equivalent) for CMS fetch/render, task board grouping,
   wiki search, form intake, or pipeline extraction.
5. **Handle the edge cases** in the table below (empty rich_text, unshared
   databases, expiring image URLs, rate limits) before shipping.

The shared client skeleton every variant builds on:

```typescript
import { Client } from '@notionhq/client';

const notion = new Client({ auth: process.env.NOTION_TOKEN });
const CONTENT_DB = process.env.NOTION_CONTENT_DB!; // one env var per database

// Query published rows (CMS index example — full code in references/implementation.md)
const response = await notion.databases.query({
  database_id: CONTENT_DB,
  filter: { property: 'Status', select: { equals: 'Published' } },
  sorts: [{ property: 'Published Date', direction: 'descending' }],
  page_size: 100,
});
```

See [references/implementation.md](references/implementation.md) for the complete
implementation of all five variants (TypeScript + Python).

## Output

- Headless CMS with post fetching, block rendering, and slug routing
- Task tracker with sprint board view, status updates, and task creation
- Knowledge base with full-text search and table of contents generation
- Form submission handler with validation and status tracking
- Data pipeline extractor with property flattening for analytics

## Error Handling

| Issue | Cause | Solution |
| ------- | ------- | ---------- |
| Empty `rich_text` array | Property has no content | Always check `?.[0]?.plain_text ?? ''` |
| `object_not_found` on query | Database not shared with integration | Share database in Notion UI |
| Image URLs expire | Notion-hosted files have temporary URLs | Cache or proxy images |
| Search returns unrelated pages | `search` is workspace-wide | Filter by `parent.database_id` |
| Form message too long | `rich_text` max 2000 chars | Truncate with `.substring(0, 2000)` |
| Pipeline duplicates | Re-processing same records | Track `last_edited_time` watermark |

## Examples

Pick a variant with the `recommendArchitecture` decision helper, which maps
author type, update frequency, and read volume onto the right pattern (CMS vs.
task tracker vs. data pipeline). The full helper plus an at-a-glance selection
table are in [references/examples.md](references/examples.md).

```typescript
recommendArchitecture({ contentAuthors: 'non-technical', updateFrequency: 'daily', readVolume: 'low' });
// → "CMS: Non-technical authors + infrequent updates = perfect Notion CMS fit"
```

## Resources

- [references/implementation.md](references/implementation.md) — full code for all five variants (TypeScript + Python)
- [references/examples.md](references/examples.md) — architecture decision helper + selection table
- [Notion API Introduction](https://developers.notion.com/reference/intro)
- [Notion Database Properties](https://developers.notion.com/reference/property-object)
- [Notion Block Types](https://developers.notion.com/reference/block)
- [Notion Search](https://developers.notion.com/reference/post-search)

## Next Steps

For common mistakes across all architectures, see `notion-known-pitfalls`.
For scaling any architecture, see `notion-load-scale`.
