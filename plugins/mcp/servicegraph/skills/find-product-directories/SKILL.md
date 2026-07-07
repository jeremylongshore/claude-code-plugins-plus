---
name: find-product-directories
description: Use whenever the user wants to find, rank, or shortlist directories, listing sites, or launch platforms where they can submit a software product, SaaS, app, tool, or startup — to get backlinks, referral traffic, and launch-day reach. Triggers on "where can I submit my SaaS for launch", "list of Product Hunt alternatives", "directories to get backlinks for our app", "where should I list my startup", or "pull submission details for these 8 directory domains", even when described indirectly. Drives the ServiceGraph API (api.servicegraph.co) — a catalog of 1,000+ product directories enriched with Domain Rating, backlinks, and organic traffic. Defer to find-mcp-directories for MCP-server listings and find-ai-directories for AI-tool / AI-agent / agent-skill listings. Skip finding a firm/agency to hire (use the find-* agency skills), finding products *inside* a directory ("recommend the best CRM"), building a directory site (do-the-work), local/business directories for brick-and-mortar, and link-building *services*.
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
tags: [product-directories, backlinks, product-launch, saas, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: product_directory
  niche: product_saas_launch
---

# find-product-directories

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find and
rank **directories where a founder can submit a software product** — SaaS
review sites (Capterra, G2, SaaSHub), launch platforms (Product Hunt and its
alternatives), app/startup listings, and general software directories — via
the `product_directory` dataset. The catalog has **1,000+ directories**, each
enriched with **Domain Rating (`dr`)**, backlink counts, and **organic
traffic**, so you can rank by *real SEO value and reach* instead of guessing.

**This is a "where to launch / where to get backlinks" skill, not a "who to
hire" skill.** Each row is a *directory you submit to*, not a firm and not a
product. The payoff for the user is twofold: a **backlink** from a
high-authority domain (SEO) and **launch-day referral traffic**.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when the niche is specific

If the user's product is specifically one of these, defer to the dedicated
skill (its catalog slice and recipes are tuned for it):

- **MCP servers** ("where do I list my MCP server", "MCP directories") →
  `find-mcp-directories`
- **AI tools / AI agents / agent skills** ("directories for my AI app",
  "where to list my AI agent", "agent-skills directories") →
  `find-ai-directories`

This skill is the **umbrella** for everything else founders launch — SaaS,
web apps, mobile apps, dev tools, startups in general — and is the right pick
when the ask spans niches or names none.

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

If your harness has the ServiceGraph MCP server loaded (recognizable by tool
names containing `servicegraph`), prefer those tools — the harness handles
credentials in its own sandbox via OAuth 2.1 + PKCE, so no token enters LLM
context. Otherwise use the REST flow below.

### API surface (dataset id: `product_directory`)

Every endpoint requires the bearer (`Authorization: Bearer vk_…`). There is
no anonymous tier.

| Endpoint | Cost | Use it for |
|---|---|---|
| `GET /v1/datasets/product_directory/fields[?include_values=1&q=]` | free | Filter-field catalog + DSL grammar. Call first per session. |
| `GET /v1/datasets/product_directory/values/:field[?q=&limit=]` | free | Enumerate values for one field (e.g. `industry`, `has`). |
| `GET /v1/datasets/product_directory/check?filter=…` | free | Validate a filter. Returns `{valid, normalized}` or `{valid:false, error}`. |
| `POST /v1/datasets/product_directory/translate-intent` | free | `{intent}` → LLM-generated DSL filter + sanity count. |
| `GET /v1/datasets/product_directory/search?filter=…&limit=&offset=` | free | Brief directory cards (incl. `dr`) + per-row `unlock` hint + `total`. |
| `GET /v1/datasets/product_directory/:apex` | free | Single row brief; **gated fields only if unlocked**. |
| `POST /v1/datasets/product_directory/unlocks` | **10 credits / row** | `{apexes:[...]}` ≤100. Atomic batch; 30-day TTL; `was_cached:true` rows free. |
| `GET /v1/me/credits` | free | Balance. |

**Cost model.** Discovery / validation / search / brief reads are free —
including the `dr` ranking signal. Unlocking a row costs **10 credits** and
lasts **30 days**; it reveals the **gated fields**: `editor_note` (the
hand-written submission note — *how* to submit and *whether the listing gives
a backlink*), `organic_traffic`, and `total_visits`. Re-fetching an unlocked
row within TTL is free.

### Auth

Tokens are `vk_*` API keys minted in the dashboard.

**Keep the token out of the LLM context** — never read `.env*` into your
context; dispatch every authed call through a shell wrapper.

1. **Just try the call** through a shell wrapper that sources `.env.local`:

   ```bash
   ( set -a; [ -f .env.local ] && . ./.env.local; set +a;
     curl -sS -H "Authorization: Bearer $SERVICEGRAPH_API_KEY" \
          'https://api.servicegraph.co/v1/datasets/product_directory/fields' )
   ```

2. **On `401 unauthorized`**, prompt the user (don't accept the key in chat):

   > "Open **https://servicegraph.co/profile/api-keys**, sign in, click
   > **Create key**, and copy the `vk_…` value. Then add
   > `SERVICEGRAPH_API_KEY=vk_…` to `.env.local` here (or export it in your
   > shell). Tell me when done. Please don't paste the key into chat."

3. **Retry** the same call after the user signals ready. A later 401 means the
   key was rotated/revoked — re-prompt.

### Filter DSL

GitHub-search-style.

```
filter   := orExpr
orExpr   := andExpr ("OR" andExpr)*
andExpr  := notExpr (("AND")? notExpr)*    # whitespace = implicit AND
notExpr  := ("NOT" | "-") notExpr | atom
atom     := "(" filter ")" | predicate
predicate:= IDENT op valueOrList | bareword
op       := ":" | "=" | ">=" | "<=" | ">" | "<"
```

**Four rules that bite:**

1. **AND binds tighter than OR.** `a OR b c` parses as `a OR (b AND c)`. Use parens.
2. **Comma list = OR within one predicate.** `industry:software_saas,fintech` = either.
3. **Negation is `-x` or `NOT x`.** Use `saas -crm`, not `keyword:saas,-crm`.
4. **Bareword = keyword search.** Free-text substring across the directory's
   name, title, description, listed metadata, **and the dir-catalog `niche`
   tag** (so `saas` matches dirs whose niche is "SaaS products"). Multiple
   barewords AND. Wrap multi-word phrases in double quotes (`"product launch"`).

### Fields that matter here

This dataset ranks directories by *SEO value and reach*, so the numeric
signals are the point:

| Field | Free in brief? | Use it for |
|---|---|---|
| `dr` | **yes** | Ahrefs-style Domain Rating 0–100. The **primary authority filter** — a backlink from `dr>=70` is worth far more than from `dr<30`. Briefs are returned **sorted by `dr` descending**, so the strongest domains come first. |
| `referring_main_domains` | yes (when populated) | Distinct apexes linking in — "is this a real backlink source?". `>=100` decent, `>=1000` strong. |
| `backlinks` | yes (when populated) | Total inbound links; a sanity floor, long-tailed. |
| `organic_keywords` | yes (when populated) | Distinct US Google keywords ranked for. |
| `organic_traffic` | **gated** | Est. monthly US organic visits — the real-reach metric. Filterable even while hidden (`organic_traffic>=10000`), but the value shows only after unlock. |
| `total_visits` | **gated** | Est. total monthly visits. |
| `editor_note` | **gated** | Hand-written submission note: how to submit, and **whether you get a backlink**. |
| `industry` | yes | High-level vertical of the directory (e.g. `software_saas`, `fintech`, `design_creative`). A coarse refiner; keyword on `niche` is usually sharper. |
| `has` | yes | Presence of a structured field / third-party listing (`has:pricing`, `has:g2`, …). |

Because `dr` is free and briefs are pre-sorted by it, **you can rank a
shortlist by authority without spending a single credit** — unlock only the
ones the user wants submission instructions for.

### Identifying rows — `apex`

Directories are keyed by **apex domain** (`producthunt.com`, not
`www.producthunt.com/posts`). Strip user-supplied URLs to the apex before
calling `:apex` endpoints or building unlock batches.

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

### A. Launch platforms (Product Hunt alternatives)

User: *"Where can I launch my SaaS next week besides Product Hunt?"*

```
GET /v1/datasets/product_directory/search?filter=launch&limit=15
# → cards sorted by dr desc; producthunt.com, uneed.best, peerpush.net, tinylaunch.com, …
```

Present the top N by `dr` (free). Tighten to high-authority only:

```
GET /v1/datasets/product_directory/search?filter=launch+dr>=60&limit=15
```

### B. SaaS review / listing directories for backlinks

User: *"High-authority directories to list our B2B SaaS for SEO."*

```
GET /v1/datasets/product_directory/search?filter=saas+dr>=60&limit=20
# → saashub.com, saasworthy.com, financesonline.com, capterra.com (via 'saas' niche), …
```

Software in general (broader than SaaS):

```
GET /v1/datasets/product_directory/search?filter=software+dr>=60&limit=20
```

### C. Rank by real reach (organic traffic)

User: *"Which directories actually send traffic, not just a backlink?"*

`organic_traffic` is gated but **filterable** — gate on it to surface
high-reach dirs, then unlock to see the numbers:

```
GET /v1/datasets/product_directory/search?filter=saas+organic_traffic>=50000&limit=15
# → small set of high-traffic dirs. Unlock the user's picks to reveal traffic + how to submit.
```

### D. Vertical / niche product

User: *"Directories for our fintech app."* / *"design-tool listing sites."*

Combine a keyword (matched against the `niche` tag) with the `industry`
refiner, or just lead with the keyword:

```
GET /v1/datasets/product_directory/search?filter=fintech&limit=15
GET /v1/datasets/product_directory/search?filter=design+dr>=50&limit=15
```

If a keyword over-narrows, drop it and use `industry:` (e.g.
`industry:software_saas`, `industry:fintech`) plus `dr>=`.

### E. Intent translator (let the API draft the filter)

User: *"Where do I get our new dev tool in front of developers and pick up backlinks?"*

```
POST /v1/datasets/product_directory/translate-intent
  { "intent": "directories to list a developer tool for backlinks and traffic" }
# → {filter, normalized, count}. Sanity-check the count, then search.
```

### F. Unlock submission instructions for the picks

User has a shortlist and wants to actually submit:

```
# Present briefs ranked by dr (free). "Unlocking 6 = 60 credits, 30-day TTL —
# this reveals each one's submission note (how to submit, backlink yes/no) and traffic."
POST /v1/datasets/product_directory/unlocks
  { "apexes": ["producthunt.com", "saashub.com", "uneed.best", "..."] }
# → editor_note + organic_traffic + total_visits for each.
```

The `editor_note` is the operational payoff — e.g. *"Listing doesn't give a
backlink but seeds several other directories; submit via CLI, see …"*. Surface
it verbatim so the user knows the effort and the SEO return before submitting.

### G. BYO apex list — score directories I already have

User pastes a list of directory domains:

1. `GET /v1/datasets/product_directory/:apex` per domain — free brief with
   `dr` (404 = not in catalog, no charge). Flag misses and rank the hits by `dr`.
2. User picks N to fully enrich. `POST /unlocks` with all of them = **10×N
   credits**, single atomic charge; reveals submission notes + traffic.
3. Within 30-day TTL, repeated unlock POSTs are free.

## Gotchas

- **Rows are directories, not firms or products.** If the user wants to *hire*
  an agency, route to a `find-*` agency skill. If they want to *find a product*
  listed somewhere ("best CRM for us"), this dataset can't answer that — it
  lists the directories, not their contents.
- **`dr` is free and briefs are pre-sorted by it** — rank and shortlist for
  zero credits; spend only to reveal submission notes + traffic.
- **Gated fields can still be filtered.** `organic_traffic>=10000` narrows the
  set even though the value stays hidden until unlock.
- **Catalog is global, not US-only, and not B2B-only.** Don't refuse non-US or
  consumer-product asks the way the agency skills do — a directory is a
  directory regardless of who launches.
- **Local / brick-and-mortar business directories are a different dataset**
  (`business_directory`). If the user wants to list a restaurant, clinic, or
  local service, this isn't it — point them at the branded `servicegraph` skill.
- **Multi-word phrases must be split or quoted.** `product launch` parses as
  two AND'd keywords; `"product launch"` is one phrase.
- **Unlock is atomic.** `POST /unlocks` with 6 apexes either charges (up to) 60
  credits or leaves balance untouched on 402. Plan the batch.
- **Within-TTL re-views are free** (`was_cached:true`).

## Errors

JSON envelope: `{"error": {"code": "...", "message": "..."}}`.

| Status | Code | What to do |
|---|---|---|
| 400 | `filter_parse_error` | `position` included; fix and re-validate with `/check`. |
| 400 | `kind_in_filter` | Strip any `kind:` from filter — URL is authoritative. |
| 400 | `field_not_in_dataset` | Field isn't allowed on `product_directory`; drop it. |
| 400 | `invalid_apex` | Re-normalize to apex. |
| 401 | `unauthorized` / `invalid_audience` | Re-prompt for a fresh `vk_…`. |
| 402 | `insufficient_credits` | `needed` and `balance` in payload; nothing charged. |
| 404 | `not_found` / `not_in_dataset` | Apex isn't in this dataset. Skip; not charged. |
| 429 | `rate_limited` | Honor `Retry-After`. |

## End-to-end example

User: *"We're launching our B2B SaaS in two weeks. Find the highest-authority
directories to submit to for backlinks, and tell me how to submit to the top
five."*

```
# 1. Discover (once per session)
GET /v1/datasets/product_directory/fields?include_values=1

# 2. Validate + scope (free)
GET /v1/datasets/product_directory/check?filter=saas+dr>=60

# 3. Search briefs (free) — already sorted by dr desc
GET /v1/datasets/product_directory/search?filter=saas+dr>=60&limit=20
# → present ranked by dr; note which look like launch platforms vs review sites

# 4. User picks 5. "Unlocking 5 = 50 credits, 30-day TTL — reveals each one's
#    submission note (how to submit + backlink yes/no) and traffic."

# 5. Atomic unlock (charges 50 credits)
POST /v1/datasets/product_directory/unlocks
  { "apexes": ["saashub.com", "saasworthy.com", "producthunt.com", "uneed.best", "financesonline.com"] }

# 6. Surface each editor_note verbatim + traffic so the user can prioritize.
```

## Resources

- Upstream source: <https://github.com/nostrband/ServiceGraph>
- ServiceGraph API: <https://api.servicegraph.co> — keys at
  <https://servicegraph.co/profile/api-keys>
- Hub skill: `servicegraph` (this plugin) — the dataset-agnostic entry point
  when the user names ServiceGraph explicitly.
