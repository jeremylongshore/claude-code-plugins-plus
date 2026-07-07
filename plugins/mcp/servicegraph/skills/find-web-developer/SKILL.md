---
name: find-web-developer
description: Use whenever the user wants to find, shortlist, vet, or enrich US web development firms — building, refreshing, or rebuilding marketing sites, landing pages, ecommerce, WordPress/Webflow/Shopify, headless CMS, microsites, and web frontend work. Triggers on "find a web developer for a marketing landing page", "shortlist three Webflow agencies in California", "rebuild our ecommerce site on Shopify", or "pull contact info for these 8 web dev shop domains", even when described indirectly (redesign and rebuild our site, ship a microsite). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Defer to find-software-developer for custom backend/API/mobile/internal-tool work — anything beyond a website. Defer to find-marketing-agency when scope spans broader marketing beyond the build. Skip in-house web-engineer hires, "how do I build X" DIY questions, hosting/CMS-product comparisons, non-US firms, individual freelancers.
version: "0.3.0"
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
tags: [web-development, agencies, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: it_services
  service: web-development
---

# find-web-developer

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US web development firms via the `pro_services`
dataset. The catalog tags ~14k firms with
`service_provided:web-development` under `industry:it_services`
(web-development is the second-largest service tag in the catalog).

**Always pin both `industry:it_services` and
`service_provided:web-development`.** Platforms (WordPress, Webflow,
Shopify, Next.js, etc.) and verticals (B2B, ecommerce,
agency-vs-studio) are NOT separate tags — they're keyword substring
matches on firm text.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when scope is different

- **Custom backend / API / internal tools / mobile app / distributed systems** → `find-software-developer`. The end-product is software beyond a standard website.
- **Broader marketing strategy and execution beyond the site build** (paid media, content strategy, full digital agency engagement) → `find-marketing-agency`.
- **SEO-only work on an existing site** → `find-seo-agency`. Web devs build sites; SEO agencies optimize them. If the user wants new pages built AND optimized, this skill is fine.

If unsure, this skill is correct for "build / rebuild / refresh a
website" tasks. The deferral kicks in when the deliverable is
non-website software or non-build marketing work.

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
2. `GET /v1/datasets/pro_services/fields?include_values=1` — confirm the
   fields and values you plan to filter on exist.
3. Build the filter (Filter DSL below) and validate it with
   `GET /v1/datasets/pro_services/check` — or draft it from plain English via
   `POST /v1/datasets/pro_services/translate-intent`.
4. `GET /v1/datasets/pro_services/search` — present the free brief cards and
   let the user pick.
5. Quote the unlock cost (10 credits per row, 30-day TTL) and get an explicit
   go-ahead.
6. `POST /v1/datasets/pro_services/unlocks` with the chosen apexes; report the
   revealed detail.
7. `GET /v1/me/credits` to report the remaining balance when asked.

### MCP server (preferred for authed calls)

If your harness has the ServiceGraph MCP server loaded (tools
containing `servicegraph`), prefer those — OAuth 2.1 + PKCE keeps the
token in the harness sandbox. Otherwise use the REST flow below.

### API surface (dataset id: `pro_services`)

Every endpoint requires the bearer (`Authorization: Bearer vk_…`).
No anonymous tier.

| Endpoint | Cost | Use it for |
|---|---|---|
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `web-development` is in the `service_provided` value list. |
| `GET /v1/datasets/pro_services/check?filter=…` | free | Validate filter. |
| `POST /v1/datasets/pro_services/translate-intent` | free | `{intent}` → DSL filter + sanity count. |
| `GET /v1/datasets/pro_services/search?filter=…&limit=` | free | Brief firm cards + per-row unlock hint + total. |
| `GET /v1/datasets/pro_services/:apex` | free | One row brief; detail only if unlocked. |
| `POST /v1/datasets/pro_services/unlocks` | **10 credits / firm** | `{apexes:[...]}` ≤100; atomic; 30-day TTL on detail. |
| `GET /v1/me/credits` | free | Balance. |

**Cost model.** Discovery / validation / search / brief reads are
free. Detail (url, phone, email, social, address, full `platforms`
map) costs **10 credits per firm** and lasts **30 days**.

### Auth

`vk_*` API keys minted in the dashboard. **Keep the token out of the
LLM context** — never read `.env*` into your context; dispatch via
shell.

1. **Try the call first** through a shell wrapper that sources `.env.local`:

   ```bash
   ( set -a; [ -f .env.local ] && . ./.env.local; set +a;
     curl -sS -H "Authorization: Bearer $SERVICEGRAPH_API_KEY" \
          'https://api.servicegraph.co/v1/datasets/pro_services/fields' )
   ```

2. **On `401`** prompt the user:

   > "Open **https://servicegraph.co/profile/api-keys**, create a
   > key, and add `SERVICEGRAPH_API_KEY=vk_…` to `.env.local` here
   > (or export it). Tell me when done. Please don't paste the key
   > into chat."

3. **Retry** after the user signals ready.

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
valueOrList := value ("," value)*
value    := IDENT | NUMBER | tagAtEvidence
tagAtEvidence := IDENT "@" ("low"|"medium"|"high")
bareword := IDENT | NUMBER          # → keyword:<bareword>
```

**Four rules that bite:** AND binds tighter than OR (use parens);
comma list = OR within one predicate; negation is `-x` or `NOT x`;
bareword = keyword search (quote multi-word phrases).

**Web-dev examples** (validate yours with `/check`):

```
industry:it_services service_provided:web-development
industry:it_services service_provided:web-development@high state:CA webflow
industry:it_services service_provided:web-development shopify ecommerce
industry:it_services service_provided:web-development wordpress
industry:it_services service_provided:web-development headless next.js
industry:it_services service_provided:web-development@high rating>=4 has:clutch
industry:it_services service_provided:web-development b2b
```

**Platform / vertical / framework → keyword mapping** (none are
structured tags — keyword them):

| User mentions | Add as keyword |
|---|---|
| WordPress | `wordpress` |
| Webflow | `webflow` |
| Shopify / Shopify Plus | `shopify` |
| Squarespace / Wix | `squarespace` / `wix` |
| Headless / JAMstack / Next.js / Gatsby | `headless`, `next.js`, `gatsby` |
| Sanity / Contentful / Strapi | `sanity`, `contentful`, `strapi` |
| Ecommerce / D2C / DTC | `ecommerce`, `d2c`, `dtc` |
| B2B / SaaS / fintech | `b2b`, `saas`, `fintech` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`focuslabllc.com`, not
`www.focuslabllc.com/work`).

## Output

All responses are JSON.

- **Search** returns free **brief** firm cards — `apex`, `name`, location, and
  rating signals — plus a per-row unlock hint and the match `total`. Briefs
  never include `url`, `phone_primary`, `email_primary`, `legal_name`,
  `address_full`, or the full `platforms` map.
- **Unlock** (`POST …/unlocks`) returns each unlocked firm's detail block —
  contact fields, address, socials, the `platforms` map — plus per-item
  billing; detail stays readable for 30 days.
- **Errors** arrive as a JSON envelope
  `{"error": {"code": "…", "message": "…"}}` — see Errors below.

## Examples

### A. Marketing landing page (the baseline)

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:web-development&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. Webflow agency in a state

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:web-development+webflow+state:CA&limit=10
```

### C. Shopify ecommerce rebuild

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:web-development+shopify+ecommerce&limit=10
```

For Shopify Plus, add `plus` as an additional bareword.

### D. WordPress site refresh / maintenance

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:web-development+wordpress&limit=10
```

### E. Headless CMS / Next.js

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:web-development+headless+next.js&limit=10
```

If sparse, drop `next.js` — `headless` alone captures the architectural pattern.

### F. Indirect intent — "redesign and rebuild our site"

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:web-development&limit=10
```

Or use the translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "agency to redesign and rebuild our outdated company site" }
```

If the user gave a constraint (location, platform, budget proxy via
`pricing_model`), add it.

### G. Quality threshold + platform

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:web-development@high+rating>=4+shopify+plus&limit=10
```

### H. BYO apex list — enrich domains

User pastes 8–20 web-dev shop domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge). A 404 often means the firm
   isn't tagged with `web-development` specifically — it might be in
   the catalog under a different tag.
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin both `industry:it_services` AND `service_provided:web-development`.** Without the industry pin, `web-development` also appears on some marketing-agency rows; without the service pin, you'd return all IT-services firms.
- **Defer to `find-software-developer` for non-website software.** Internal tools, custom CRMs, mobile apps (iOS/Android), backend/API, distributed systems — those are software-developer territory. The boundary: is the end-product a public website, or something else?
- **Defer to `find-marketing-agency` for full marketing engagements.** "Build our site AND run our marketing" is broader than this skill — fire find-marketing-agency, which has web-design as a sub-service too.
- **Platforms (WordPress, Webflow, Shopify, Next.js) are NOT structured tags.** Keyword them.
- **Frameworks (React, Vue, Astro, Gatsby) are NOT structured tags either.** Keyword them.
- **CMS/hosting/builder product comparisons aren't procurement.** "WordPress vs Webflow vs Squarespace" is a knowledge question.
- **Multi-word phrases must be split or quoted.** `headless cms` parses as two AND'd keywords; `"headless cms"` is one phrase.
- **Catalog is US-only B2B.** Refuse offshore asks ("Manila", "Karachi"), individual freelancers, and DIY/code-help asks ("debug this CSS").
- **Briefs DO include `apex`, `name`, location, ratings.** They DON'T include `url`, `phone_primary`, `email_primary`, `legal_name`, `address_full`, full `platforms` — those require an unlock.
- **`not_found` / `not_in_dataset` 404 = not in `pro_services`.** Skip; not charged.
- **Unlock is atomic.** N apexes either all charge (up to 10×N credits) or none on 402.
- **Within-TTL re-views are free** (`was_cached:true`).

## Errors

JSON envelope: `{"error": {"code": "...", "message": "..."}}`.

| Status | Code | What to do |
|---|---|---|
| 400 | `filter_parse_error` | `position` included; fix and re-validate with `/check`. |
| 400 | `kind_in_filter` | Strip any `kind:` from filter. |
| 400 | `field_not_in_dataset` | Drop the disallowed field. |
| 400 | `invalid_apex` | Re-normalize. |
| 401 | `unauthorized` / `invalid_audience` | Re-prompt for fresh `vk_…`. |
| 402 | `insufficient_credits` | `needed` and `balance`; nothing charged. |
| 404 | `not_found` / `not_in_dataset` | Skip; not charged. |
| 429 | `rate_limited` | Honor `Retry-After`. |

## End-to-end example

User: *"Three Webflow agencies in California for our marketing site,
ideally with at least a 4-star rating and a Clutch profile."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:it_services+service_provided:web-development@high+webflow+state:CA+rating>=4+has:clutch
GET /v1/datasets/pro_services/search?filter=...&limit=10
# Present briefs. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
GET /v1/me/credits
```

## Resources

- Upstream source: <https://github.com/nostrband/ServiceGraph>
- ServiceGraph API: <https://api.servicegraph.co> — keys at
  <https://servicegraph.co/profile/api-keys>
- Hub skill: `servicegraph` (this plugin) — the dataset-agnostic entry point
  when the user names ServiceGraph explicitly.
