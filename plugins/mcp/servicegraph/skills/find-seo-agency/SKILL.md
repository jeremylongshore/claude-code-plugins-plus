---
name: find-seo-agency
description: Use whenever the user wants to find, shortlist, vet, or enrich US SEO agencies — technical SEO, on-page/off-page, link-building, content-led SEO, local SEO, ecommerce SEO, B2B SEO, and SEO audits. Triggers on "find me an SEO agency in Texas", "shortlist three technical SEO consultancies for SaaS", "link-building and on-page for our ecommerce store", or "pull contact info for these 8 SEO firm domains", even when described indirectly (organic traffic flat, improve Google rankings, search visibility). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings, third-party listings. Defer to find-marketing-agency when scope spans multiple marketing services beyond SEO. Skip SEM/PPC/paid-search asks, web-dev asks (use find-web-developer), "how do I rank" DIY questions, SEO tool recommendations (Ahrefs, Semrush), in-house SEO hires, non-US firms, individual freelancers.
version: "0.2.0"
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
tags: [seo, marketing, agencies, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: marketing_agency
  service: seo
---

# find-seo-agency

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US SEO agencies via the `pro_services` dataset.
The catalog has thousands of US firms tagged with
`service_provided:seo` under `industry:marketing_agency`.

**Always pin both `industry:marketing_agency` and
`service_provided:seo`.** SEO sub-flavors (technical, local,
link-building, on-page, ecommerce, B2B, etc.) are not separate tags
— the catalog has one `seo` tag — so sub-flavor specialization is
inferred via keyword search across firm text.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when scope is broader

If the user wants a **multi-service** marketing engagement (SEO plus
PPC plus content plus social, or a "full-service digital agency"),
defer to `find-marketing-agency` — that skill covers the same
catalog with a broader filter and won't over-constrain on SEO.

If the user wants strictly web/app development (build a site, ship a
feature), defer to `find-web-developer` / `find-software-developer`.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `seo` is in the `service_provided` value list. |
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

**SEO-flavored examples** (validate yours with `/check`):

```
industry:marketing_agency service_provided:seo
industry:marketing_agency service_provided:seo@high state:TX
industry:marketing_agency service_provided:seo technical
industry:marketing_agency service_provided:seo local
industry:marketing_agency service_provided:seo ecommerce
industry:marketing_agency service_provided:seo b2b saas
industry:marketing_agency service_provided:seo@high rating>=4 review_count_total>=20 has:clutch
industry:marketing_agency service_provided:seo "core web vitals"
```

**Sub-flavor → keyword mapping** (catalog has one `seo` tag):

| User asks for | Add as keyword |
|---|---|
| Technical SEO | `technical` |
| Local SEO | `local` |
| Link-building | `link-building` or `links` |
| On-page SEO | `on-page` or `onpage` |
| Off-page SEO | `off-page` or `offpage` |
| Ecommerce SEO | `ecommerce` |
| B2B SEO | `b2b` |
| Shopify SEO | `shopify` |
| Core Web Vitals / page speed | `"core web vitals"` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`searchpilot.com`, not
`www.searchpilot.com/about`).

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

### A. SEO agency in a state (the baseline)

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:seo+state:TX&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. Technical SEO for a SaaS company

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:seo@high+technical+b2b+saas&limit=10
```

### C. Link-building + on-page for ecommerce

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:seo+link-building+on-page+ecommerce&limit=10
```

If the breakdown is sparse, drop `on-page` — agencies that do SEO at
all usually do both.

### D. Local SEO for a multi-location business

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:seo+local+state:NJ&limit=10
```

The catalog tags one `state` per firm (HQ); local-SEO firms can
serve NJ without being headquartered there. If results are narrow,
drop `state:NJ` and use `geography_served:national_US,multi_state_regional`.

### E. Indirect intent — "organic traffic flat"

User: *"Our organic traffic has been flat for 6 months — we need an SEO partner."*

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:seo&limit=10
```

Or use the translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "SEO partner — our organic traffic has been flat for 6 months" }
```

If the user gave a vertical or location elsewhere, add it. Otherwise
present the top-10 and ask for constraints.

### F. Quality threshold + third-party signals

Be cautious — TX `seo@high` collapses sharply with rating gates or
Clutch alone. Layer `@high` evidence + non-solo size first; add the
rating gate only if pool is still large:

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:seo@high+-company_size_signal:solo+state:TX&limit=10
```

For users insisting on third-party signals:

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:seo@high+rating>=4+review_count_total>=20+has:clutch&limit=10
```

### G. BYO apex list — enrich domains

User pastes 8–20 SEO firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge). Note: not every firm with `seo`
   in their domain is tagged `service_provided:seo`.
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin both `industry:marketing_agency` AND `service_provided:seo`.** Without the industry pin, `service_provided:seo` matches SEO services from IT firms or design shops too. Without the service pin, you'd return all marketing agencies regardless of SEO specialty.
- **SEO sub-flavors are NOT separate tags.** Use barewords for sub-flavor — they become keyword substring matches in firm text.
- **Defer to `find-marketing-agency` for multi-service scope.** SEO plus paid plus content plus social as one engagement is a full-service marketing ask.
- **Defer to `find-web-developer` for "fix our site speed / Core Web Vitals" if they want it BUILT.** SEO agencies advise on CWV; they don't refactor your front-end.
- **Rating/Clutch gates are sparse for SEO.** TX `seo@high` (~243 firms) collapses below k=20 with `rating>=4` OR `has:clutch` alone. Prefer `@high` + non-solo as the quality proxy and add rating only if the base pool is still wide.
- **"SEM" / "PPC" / "paid search" / "Google Ads" are NOT SEO.** Defer to `find-marketing-agency`. SEM-vs-SEO is a frequent terminology mix-up.
- **Multi-word phrases must be split or quoted.** `core web vitals` parses as three AND'd keywords; `"core web vitals"` is one phrase.
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

User: *"Three technical SEO consultancies for a B2B SaaS company,
ideally with at least a 4-star rating and a Clutch listing."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:marketing_agency+service_provided:seo@high+technical+b2b+saas+rating>=4+has:clutch
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
