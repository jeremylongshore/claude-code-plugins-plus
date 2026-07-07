---
name: find-ai-directories
description: Use whenever the user wants to find, rank, or shortlist directories and listing sites where they can submit an AI product — an AI tool, AI app, AI agent, or agent skill / plugin — to get backlinks, referral traffic, and discovery. Triggers on "where can I list my AI tool", "directories to submit my AI agent", "agent-skills directories", "best AI tool directories for backlinks", "where do I get my GPT/Claude app discovered", or "pull submission details for these AI-directory domains", even when described indirectly. Drives the ServiceGraph API (api.servicegraph.co) — a catalog of 1,000+ product directories enriched with Domain Rating, backlinks, and organic traffic. Defer to find-mcp-directories for MCP-server listings specifically, and to find-product-directories for general SaaS/software/app launches with no AI angle. Skip finding an AI consultancy/agency to hire (use find-ai-consultancy), comparing AI products ("ChatGPT vs Claude"), building an AI tool (do-the-work), and AI link-building *services*.
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
tags: [ai-tools, directories, backlinks, product-launch, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: product_directory
  niche: ai_tools_agents_skills
---

# find-ai-directories

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find and
rank **directories where a founder can submit an AI product** — AI tools, AI
apps, AI agents, and **agent skills / plugins** — via the `product_directory`
dataset. The catalog has **1,000+ directories**, each enriched with **Domain
Rating (`dr`)**, backlink counts, and **organic traffic**. The AI slice is
large and fast-moving: ~370 dirs match "AI tools", ~28 match "AI agents", and
a growing set are dedicated **agent-skill / plugin registries** (e.g.
`clawhub.ai`, `smithery.ai`).

**This is a "where to launch / where to get backlinks" skill, not a "who to
hire" skill.** Each row is a *directory you submit to*, not a firm and not a
product. The payoff is a **backlink** from a high-authority domain (SEO) plus
**discovery traffic** from people browsing for AI tools.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when the niche is narrower or broader

- **MCP servers specifically** ("where do I list my MCP server", "MCP
  directories") → `find-mcp-directories`. (MCP registries that *also* list
  agent skills/tools overlap both — if the ask is broadly "AI agent tooling,"
  this skill is fine.)
- **General SaaS / software / app launch with no AI angle** ("Product Hunt
  alternatives for our SaaS") → `find-product-directories`.

This skill owns the **AI-tool / AI-agent / agent-skill** niche.

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
`niche` tag** (so `"ai agents"` matches dirs whose niche is "AI agent tools").
Multiple barewords AND; wrap multi-word phrases in double quotes.

```
"ai tools" dr>=50
("ai agents" OR "ai agent") dr>=40
skills agent          # → keyword:skills AND keyword:agent  (agent-skill registries)
industry:software_saas ai
```

### Fields that matter here

| Field | Free in brief? | Use it for |
|---|---|---|
| `dr` | **yes** | Domain Rating 0–100 — the primary authority filter. Briefs come **sorted by `dr` descending**, so rank for free. |
| `referring_main_domains`, `backlinks`, `organic_keywords` | yes (when populated) | Backlink-source strength signals. |
| `organic_traffic`, `total_visits` | **gated** | Real reach. Filterable while hidden (`organic_traffic>=10000`); value shows after unlock. |
| `editor_note` | **gated** | Submission instructions + backlink yes/no. |
| `industry` | yes | Coarse vertical refiner (`software_saas`, etc.); keyword on `niche` is usually sharper for AI sub-niches. |
| `has` | yes | Presence flags (`has:pricing`, `has:g2`, …). |

Because `dr` is free and briefs are pre-sorted by it, **rank a shortlist by
authority for zero credits** — unlock only to reveal submission notes + traffic.

### Identifying rows — `apex`

Keyed by **apex domain** (`aiagentsdirectory.com`, not a full URL). Strip
user-supplied URLs to the apex before `:apex` or unlock calls.

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

### A. AI-tool directories (the broad case)

User: *"Where can I list our new AI tool to get backlinks and traffic?"*

```
GET /v1/datasets/product_directory/search?filter="ai tools"+dr>=50&limit=20
# → aichief.com, aiagentstore.ai, … sorted by dr desc. Present top N (free).
```

Broaden with the bare `ai` keyword if the pool is thin; tighten with `dr>=60`.

### B. AI-agent directories

User: *"Directories specifically for AI agents, not just AI tools."*

```
GET /v1/datasets/product_directory/search?filter=("ai agents" OR "ai agent")&limit=20
# → aiagentsdirectory.com, agenthunter.io, aiagentstore.ai, smithery.ai, …
```

### C. Agent-skill / plugin registries

User: *"Where do I publish our Claude/agent skill so people find it?"*

These are emerging registries for agent **skills and plugins** (distinct from
generic AI-tool lists). Lead with the `skills`/`agent` keywords:

```
GET /v1/datasets/product_directory/search?filter=skills+agent&limit=15
# → skills.sh, smithery.ai, aiagentsdirectory.com, agentskills.so, … sorted by dr desc
```

Present the top hits by `dr` (free), then unlock the user's picks to get each
one's submission note + traffic numbers before publishing.

> Many agent-skill registries overlap with **MCP** registries (Smithery lists
> both). If the user's artifact is specifically an MCP *server*, route to
> `find-mcp-directories` for the tuned recipes.

### D. High-reach only (gate on traffic)

User: *"Only directories that actually drive traffic."*

```
GET /v1/datasets/product_directory/search?filter="ai tools"+organic_traffic>=20000&limit=15
# organic_traffic is gated but filterable — unlock picks to see the numbers.
```

### E. Intent translator

```
POST /v1/datasets/product_directory/translate-intent
  { "intent": "directories to list an AI agent for backlinks and discovery" }
# → {filter, normalized, count}. Sanity-check count, then search.
```

### F. Unlock submission instructions

```
# Present briefs ranked by dr (free). "Unlocking 6 = 60 credits, 30-day TTL —
# reveals each one's submission note (how + backlink yes/no) and traffic."
POST /v1/datasets/product_directory/unlocks
  { "apexes": ["clawhub.ai", "aiagentsdirectory.com", "aichief.com", "..."] }
```

Surface each `editor_note` verbatim — it tells the user the submission effort
and whether they actually get a backlink.

### G. BYO apex list — score AI directories I already have

1. `GET /v1/datasets/product_directory/:apex` per domain — free brief with `dr`
   (404 = not in catalog, no charge). Flag misses, rank hits by `dr`.
2. User picks N. `POST /unlocks` (10×N credits, atomic) reveals notes + traffic.
3. Within 30-day TTL, repeat unlocks are free.

## Gotchas

- **Rows are directories, not firms or products.** Hiring an AI consultancy →
  `find-ai-consultancy`. Comparing AI products ("ChatGPT vs Claude") is not
  what this dataset answers.
- **`dr` is free and briefs are pre-sorted by it** — rank for zero credits.
- **Gated fields are still filterable** (`organic_traffic>=10000`).
- **Catalog is global, not US-only.** Don't refuse non-US asks.
- **AI ↔ MCP ↔ agent-skill registries overlap.** When the artifact is
  specifically an MCP server, defer to `find-mcp-directories`.
- **Multi-word phrases must be quoted.** `ai agents` = two AND'd keywords;
  `"ai agents"` is one phrase.
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

User: *"We just shipped an AI agent and an accompanying agent skill. Find the
highest-authority directories to submit both to, and tell me how to submit to
the top few."*

```
# 1. Discover (once per session)
GET /v1/datasets/product_directory/fields?include_values=1

# 2. Two scoped searches (free), both pre-sorted by dr desc
GET /v1/datasets/product_directory/search?filter=("ai agents" OR "ai agent")+dr>=40&limit=15
GET /v1/datasets/product_directory/search?filter=skills+agent&limit=15   # agent-skill registries

# 3. Present merged shortlist ranked by dr. User picks 5.
#    "Unlocking 5 = 50 credits, 30-day TTL — reveals submission notes + traffic."

# 4. Atomic unlock (charges 50 credits)
POST /v1/datasets/product_directory/unlocks
  { "apexes": ["smithery.ai", "skills.sh", "aiagentsdirectory.com", "agenthunter.io", "aichief.com"] }

# 5. Surface each editor_note verbatim + traffic so the user can prioritize.
```

## Resources

- Upstream source: <https://github.com/nostrband/ServiceGraph>
- ServiceGraph API: <https://api.servicegraph.co> — keys at
  <https://servicegraph.co/profile/api-keys>
- Hub skill: `servicegraph` (this plugin) — the dataset-agnostic entry point
  when the user names ServiceGraph explicitly.
