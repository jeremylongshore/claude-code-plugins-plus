---
name: find-mcp-directories
description: Use whenever the user wants to find, rank, or shortlist directories and registries where they can submit or list an MCP server (Model Context Protocol server) — to get backlinks, referral traffic, and discovery by agent builders. Triggers on "where do I list my MCP server", "best MCP directories", "MCP registries to submit to", "get my MCP server discovered", or "pull submission details for these MCP-directory domains", even when described indirectly (we built an MCP server, where do we publish it). Drives the ServiceGraph API (api.servicegraph.co) — a catalog of 1,000+ product directories enriched with Domain Rating, backlinks, and organic traffic. Defer to find-ai-directories for general AI-tool / AI-agent / agent-skill listings, and to find-product-directories for general SaaS/software launches. Skip building an MCP server or asking how MCP works (DIY), finding a firm to build one (use find-ai-consultancy / find-software-developer), and MCP link-building *services*.
version: "0.1.0"
allowed-tools:
  - Bash(curl:*)
  - mcp__servicegraph__list_fields
  - mcp__servicegraph__list_field_values
  - mcp__servicegraph__check_filter
  - mcp__servicegraph__translate_intent
  - mcp__servicegraph__search_dataset
  - mcp__servicegraph__get_row
  - mcp__servicegraph__unlock_rows
  - mcp__servicegraph__get_credit_balance
author: Artur Briugeman <artur@nostr.band>
license: MIT
compatibility: Designed for Claude Code
tags: [mcp, directories, backlinks, product-launch, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: product_directory
  niche: mcp_servers
---

# find-mcp-directories

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find and
rank **directories and registries where a builder can list an MCP server**
(Model Context Protocol) via the `product_directory` dataset. The catalog has
**1,000+ directories**; ~20 are dedicated **MCP registries** (e.g.
`registry.modelcontextprotocol.io`, `smithery.ai`, `mcp.so`, `glama.ai`,
`pulsemcp.com`), each enriched with **Domain Rating (`dr`)**, backlinks, and
**organic traffic**.

**This is a "where to publish / where to get backlinks" skill, not a "who to
hire" skill.** Each row is a *registry you submit to*, not a firm and not a
server. The payoff is a **backlink** from a high-authority domain (SEO) plus
**discovery** by agent builders browsing for servers.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when the niche is broader

- **General AI tools / AI agents / agent skills** ("where to list my AI tool",
  "agent-skills directories") → `find-ai-directories`. (Several registries list
  MCP servers *and* skills/tools — if the artifact is specifically an MCP
  server, this skill is the right pick.)
- **General SaaS / software / app launch** ("Product Hunt alternatives") →
  `find-product-directories`.

## Prerequisites

- **ServiceGraph access**, either:
  - the **ServiceGraph MCP server** (`https://mcp.servicegraph.co`) loaded in
    your harness — this plugin's `.mcp.json` wires it up; OAuth 2.1 + PKCE
    keeps credentials in the harness sandbox — or
  - a **ServiceGraph API key** (`vk_…`, minted at
    <https://servicegraph.co/profile/api-keys>) available as
    `SERVICEGRAPH_API_KEY` in the environment or `.env.local` for the REST
    path (setup steps under Auth below).
- An HTTP client for the REST path — the examples use `curl`.

## Instructions

The loop is free-first: discovery, validation, search, and brief reads cost
nothing; only unlock after the user confirms the spend.

1. Pick the call path — the ServiceGraph MCP tools if loaded, otherwise the
   REST flow (MCP server and Auth sections below).
2. `GET /v1/datasets/product_directory/fields?include_values=1` — confirm the
   fields and values you plan to filter on exist.
3. Build the filter (Filter DSL below) and validate it with
   `GET /v1/datasets/product_directory/check` — or draft it from plain English via
   `POST /v1/datasets/product_directory/translate-intent`.
4. `GET /v1/datasets/product_directory/search` — present the free brief cards and
   let the user pick.
5. Quote the unlock cost (10 credits per row, 30-day TTL) and get an explicit
   go-ahead.
6. `POST /v1/datasets/product_directory/unlocks` with the chosen apexes; report the
   revealed detail.
7. `GET /v1/me/credits` to report the remaining balance when asked.

### MCP server (preferred for authed calls)

If your harness has the ServiceGraph MCP server loaded (tool names contain
`servicegraph`), prefer those tools — credentials stay in the harness sandbox
via OAuth 2.1 + PKCE, no token in LLM context. Otherwise use the REST flow.

### API surface (dataset id: `product_directory`)

Every endpoint requires the bearer (`Authorization: Bearer vk_…`).

| Endpoint | Cost | Use it for |
|---|---|---|
| `GET /v1/datasets/product_directory/fields[?include_values=1&q=]` | free | Filter-field catalog + DSL grammar. Call first per session. |
| `GET /v1/datasets/product_directory/values/:field[?q=&limit=]` | free | Enumerate values for one field. |
| `GET /v1/datasets/product_directory/check?filter=…` | free | Validate a filter. |
| `POST /v1/datasets/product_directory/translate-intent` | free | `{intent}` → DSL filter + sanity count. |
| `GET /v1/datasets/product_directory/search?filter=…&limit=&offset=` | free | Brief cards (incl. `dr`) + per-row `unlock` hint + `total`. |
| `GET /v1/datasets/product_directory/:apex` | free | Single row brief; **gated fields only if unlocked**. |
| `POST /v1/datasets/product_directory/unlocks` | **10 credits / row** | `{apexes:[...]}` ≤100. Atomic; 30-day TTL; `was_cached:true` free. |
| `GET /v1/me/credits` | free | Balance. |

**Cost model.** Discovery / search / brief reads are free — including the `dr`
ranking signal. Unlocking a row costs **10 credits**, lasts **30 days**, and
reveals the **gated fields**: `editor_note` (how to submit + whether the
listing gives a backlink), `organic_traffic`, and `total_visits`.

### Auth

Tokens are `vk_*` API keys. **Keep the token out of the LLM context** — never
read `.env*` into context; route authed calls through a shell wrapper.

1. **Try the call** through a wrapper that sources `.env.local`:

   ```bash
   ( set -a; [ -f .env.local ] && . ./.env.local; set +a;
     curl -sS -H "Authorization: Bearer $SERVICEGRAPH_API_KEY" \
          'https://api.servicegraph.co/v1/datasets/product_directory/fields' )
   ```

2. **On `401`**, prompt the user (don't accept the key in chat):

   > "Open **https://servicegraph.co/profile/api-keys**, sign in, create a key,
   > and add `SERVICEGRAPH_API_KEY=vk_…` to `.env.local` (or export it). Tell me
   > when done — please don't paste the key into chat."

3. **Retry** after the user signals ready.

### Filter DSL

GitHub-search-style. AND binds tighter than OR; comma list = OR within one
predicate; negation is `-x` / `NOT x`; any **bareword is a keyword search**
across the directory's name, title, description, listed metadata, **and the
`niche` tag** (so `mcp` matches dirs whose niche is "MCP servers"). Multiple
barewords AND; wrap multi-word phrases in double quotes.

```
mcp dr>=60
mcp OR "model context protocol"
mcp servers          # → keyword:mcp AND keyword:servers
```

### Fields that matter here

| Field | Free in brief? | Use it for |
|---|---|---|
| `dr` | **yes** | Domain Rating 0–100 — the primary authority filter. Briefs come **sorted by `dr` descending**, so rank for free. |
| `referring_main_domains`, `backlinks`, `organic_keywords` | yes (when populated) | Backlink-source strength signals. |
| `organic_traffic`, `total_visits` | **gated** | Real reach. Filterable while hidden (`organic_traffic>=1000`); value shows after unlock. |
| `editor_note` | **gated** | Submission instructions + backlink yes/no. |
| `industry`, `has` | yes | Coarse refiners; for MCP the `mcp` keyword on `niche` is sharpest. |

Because `dr` is free and briefs are pre-sorted by it, **rank a shortlist by
authority for zero credits** — unlock only to reveal submission notes + traffic.

### Identifying rows — `apex`

Keyed by **apex domain** (`smithery.ai`, not a full URL; subdomains like
`registry.modelcontextprotocol.io` are kept as-is when that's the catalog
key). Strip user-supplied URLs before `:apex` or unlock calls.

## Output

All responses are JSON.

- **Search** returns free **brief** directory cards — `apex`, name, and the
  `dr` (Domain Rating) signal, pre-sorted by `dr` descending — plus a per-row
  unlock hint and the match `total`.
- **Unlock** (`POST …/unlocks`) reveals each directory's gated fields —
  `editor_note` (how to submit and whether the listing gives a backlink),
  `organic_traffic`, and `total_visits` — with per-item billing and a 30-day
  TTL (`was_cached:true` rows are free).
- **Errors** arrive as a JSON envelope
  `{"error": {"code": "…", "message": "…"}}` — see Errors below.

## Examples

### A. The MCP registry shortlist

User: *"Where should I list our new MCP server?"*

```
GET /v1/datasets/product_directory/search?filter=mcp&limit=20
# → registry.modelcontextprotocol.io (dr 90), smithery.ai (75), glama.ai (72),
#   mcp.so (72), cursor.directory (69), pulsemcp.com (68), … sorted by dr desc
```

Present the top N by `dr` (free).

### B. High-authority only (backlink quality)

User: *"Only the registries with real domain authority for SEO."*

```
GET /v1/datasets/product_directory/search?filter=mcp+dr>=60&limit=15
# → the ~7 strongest MCP registries by DR
```

### C. Rank by real reach (organic traffic)

`organic_traffic` is gated but **filterable** — gate to surface high-traffic
registries, then unlock to see the numbers:

```
GET /v1/datasets/product_directory/search?filter=mcp+organic_traffic>=2000&limit=15
```

### D. Broaden — MCP + agent tooling

Some registries list MCP servers alongside agent skills/tools. Cast wider
when the strict-MCP pool is thin:

```
GET /v1/datasets/product_directory/search?filter=mcp OR "model context protocol" OR (agent skills)&limit=20
```

If the user's artifact is broader than MCP (general AI tool / agent skill),
defer to `find-ai-directories`.

### E. Unlock submission instructions for the picks

```
# Present briefs ranked by dr (free). "Unlocking 6 = 60 credits, 30-day TTL —
# reveals each one's submission note (how + backlink yes/no) and traffic."
POST /v1/datasets/product_directory/unlocks
  { "apexes": ["smithery.ai", "mcp.so", "glama.ai", "pulsemcp.com", "cursor.directory", "registry.modelcontextprotocol.io"] }
```

Surface each `editor_note` verbatim — MCP registries vary a lot in submission
mechanics (some take a CLI/PR, some a web form) and in whether the listing
actually grants a backlink. The note tells the user before they spend effort.

### F. BYO apex list — score MCP registries I already have

1. `GET /v1/datasets/product_directory/:apex` per domain — free brief with `dr`
   (404 = not in catalog, no charge). Flag misses, rank hits by `dr`.
2. User picks N. `POST /unlocks` (10×N credits, atomic) reveals notes + traffic.
3. Within 30-day TTL, repeat unlocks are free.

## Gotchas

- **Rows are registries, not firms or servers.** Building an MCP server →
  `find-software-developer` / `find-ai-consultancy`. "How does MCP work" is a
  DIY question, not this dataset.
- **`dr` is free and briefs are pre-sorted by it** — rank for zero credits.
- **Gated fields are still filterable** (`organic_traffic>=1000`).
- **Catalog is global, not US-only.** Don't refuse non-US asks.
- **The strict-MCP pool is small (~20).** If the user wants more reach, broaden
  to agent-skill/AI-tool registries (Recipe D) or defer to `find-ai-directories`.
- **Multi-word phrases must be quoted.** `model context protocol` = three AND'd
  keywords; `"model context protocol"` is one phrase.
- **Unlock is atomic** (402 charges nothing) and **within-TTL re-views are free**.

## Errors

JSON envelope: `{"error": {"code": "...", "message": "..."}}`.

| Status | Code | What to do |
|---|---|---|
| 400 | `filter_parse_error` | `position` included; fix and re-validate with `/check`. |
| 400 | `field_not_in_dataset` | Drop the field. |
| 400 | `invalid_apex` | Re-normalize to apex. |
| 401 | `unauthorized` | Re-prompt for a fresh `vk_…`. |
| 402 | `insufficient_credits` | `needed`/`balance` in payload; nothing charged. |
| 404 | `not_found` / `not_in_dataset` | Apex not in dataset. Skip; not charged. |
| 429 | `rate_limited` | Honor `Retry-After`. |

## End-to-end example

User: *"We just shipped an MCP server. Find the highest-authority registries to
list it on, and tell me how to submit to the top five."*

```
# 1. Discover (once per session)
GET /v1/datasets/product_directory/fields?include_values=1

# 2. Validate + scope (free)
GET /v1/datasets/product_directory/check?filter=mcp+dr>=50

# 3. Search briefs (free) — pre-sorted by dr desc
GET /v1/datasets/product_directory/search?filter=mcp+dr>=50&limit=20

# 4. User picks 5. "Unlocking 5 = 50 credits, 30-day TTL — reveals submission
#    notes (how + backlink yes/no) and traffic."

# 5. Atomic unlock (charges 50 credits)
POST /v1/datasets/product_directory/unlocks
  { "apexes": ["smithery.ai", "mcp.so", "glama.ai", "pulsemcp.com", "cursor.directory"] }

# 6. Surface each editor_note verbatim + traffic so the user can prioritize.
```

## Resources

- Upstream source: <https://github.com/nostrband/ServiceGraph>
- ServiceGraph API: <https://api.servicegraph.co> — keys at
  <https://servicegraph.co/profile/api-keys>
- Hub skill: `servicegraph` (this plugin) — the dataset-agnostic entry point
  when the user names ServiceGraph explicitly.
