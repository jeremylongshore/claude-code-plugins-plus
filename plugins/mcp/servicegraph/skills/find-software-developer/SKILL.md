---
name: find-software-developer
description: Use whenever the user wants to find, shortlist, vet, or enrich US software development firms — custom software, web development, mobile app development, backend/API development, DevOps/cloud, system integration, and hosting. Triggers on "find a software dev shop in Austin", "shortlist three custom-software firms with healthcare experience", "we need a mobile app developer for our iOS launch", or "pull contact info for these 10 dev shop domains", even when described indirectly (build a tool, ship a feature, technical partner). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Defer to find-web-developer for strictly website/landing-page projects. Defer AI/ML, ML pipelines, model building, and data-engineering asks — those are a sibling industry, not software development. Skip in-house engineer hires, code-writing/debugging tasks, cloud-product comparisons, hardware/civil engineering, non-US firms, individual freelancers.
version: "0.4.0"
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
tags: [software-development, it-services, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: it_services
---

# find-software-developer

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US software development firms via the
`pro_services` dataset. The catalog has tens of thousands of US
IT-services firms tagged across ~21 service sub-tags including
`web-development`, `mobile-app-development`, `api-integration`
(singular), `devops-services`, `cloud-services`, `system-integration`,
`application-modernization`, `staff-augmentation`, and
`managed-services`.

The catalog has **no `custom-software`, `devops`, `api-integrations`
(plural), or `hosting` tag** — for those user-facing concepts, pin
`application-modernization` + `web-development` (for custom software),
`devops-services`, or `api-integration` (singular) as the closest tags
and add the keyword.

**Always pin `industry:it_services`.** This skill exists to do that
automatically — the user shouldn't have to think about catalog
taxonomy.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when scope is narrow

- **Strictly website / landing-page work** (build or refresh a marketing site, simple WordPress) → `find-web-developer`. If unsure, this skill is the safer default — it covers web dev too.
- **AI/ML modeling specifically** (recommendation engines, LLM apps, ML pipelines as the core deliverable) → `find-ai-consultancy`. Those firms live in a sibling industry (`data_ai_consulting`), not `it_services`.
- **Strictly marketing work** (SEO, paid media, branding, content) → `find-marketing-agency` or `find-seo-agency`.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `it_services` industry value and sub-tag names. |
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

**IT-flavored examples** (validate yours with `/check`):

```
industry:it_services custom software state:TX
industry:it_services service_provided:mobile-app-development
industry:it_services service_provided:devops-services aws
industry:it_services service_provided:api-integration fintech
industry:it_services python aws state:CA
industry:it_services service_provided:system-integration@high rating>=4 has:clutch
industry:it_services service_provided:application-modernization legacy
```

**Tech stack / vertical → keyword mapping** (the catalog tags services,
not languages or industries served):

| User mentions | Add as keyword |
|---|---|
| Python / Django / Flask | `python` |
| Node.js / TypeScript / React | `node`, `react` |
| Go / Rust / Java / .NET | `go`, `rust`, `java`, `.net` |
| AWS / GCP / Azure | `aws`, `gcp`, `azure` |
| Fintech / healthcare / govtech / SaaS | `fintech`, `healthcare`, `govtech`, `saas` |
| SOC 2 / HIPAA / compliance | `soc2`, `hipaa`, `compliance` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`thoughtworks.com`, not
`www.thoughtworks.com/about`).

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

### A. Custom-software shop in a state

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:application-modernization+custom+software+state:TX&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. Mobile app — vertical and platform

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:mobile-app-development+ios&limit=10
```

iOS / Android distinctions aren't separate tags — use barewords.

### C. DevOps + cloud migration

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:devops-services+aws+migration&limit=10
```

If thin, drop `migration` first — it's a vertical keyword, not a service tag.

### D. Indirect intent — "technical partner to build out tooling"

User: *"We need a technical partner to build out our internal tooling, Northeast preferred."*

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+custom+software+state:NY,MA,CT,NJ,PA&limit=10
```

Or use the translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "technical partner to build internal tooling, Northeast preferred" }
```

### E. Vertical + cert (fintech + SOC 2)

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+custom+software+fintech+soc2&limit=10
```

### F. Quality threshold + third-party signals

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:application-modernization+custom+software+rating>=4+review_count_total>=50&limit=10
```

### G. API/backend specialty + remote

User: *"API/backend team to extend our SaaS — Bay Area or remote-friendly."*

`remote-friendly` isn't structured. Use `geography_served:national_US`
(national-scope firms typically serve remotely) plus keywords:

```
GET /v1/datasets/pro_services/search?filter=industry:it_services+service_provided:api-integration+(state:CA OR geography_served:national_US)+saas&limit=10
```

### H. BYO apex list — enrich domains

User pastes 8–20 domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge).
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin `industry:it_services`.** Without it, `web-development` / `mobile-app-development` keywords leak into marketing or design firms.
- **Tag drift**: there is no `custom-software`, `devops`, `api-integrations` (plural), or `hosting` tag. Map to `application-modernization` + `web-development`, `devops-services`, `api-integration` (singular) plus keywords.
- **`industry:data_ai_consulting` is a sibling industry, not a sub-tag.** AI/ML-focused firms live there — defer to `find-ai-consultancy`.
- **Defer to `find-web-developer` for strictly website/landing-page projects.** This skill covers web dev as a sub-service, but the dedicated skill ranks higher on narrow web-only asks.
- **Programming language and tech stack are NOT structured tags.** `python`, `react`, `aws`, `kubernetes`, `rust` are keyword substring matches. Multi-word stacks split into ANDs unless quoted (`"ruby on rails"`).
- **Client-vertical (fintech, healthcare, govtech) is NOT a structured tag.** Keyword it.
- **Catalog is US-only B2B.** Refuse offshore asks ("a software firm in Bangalore"), individual freelancers, in-house engineering hires, and DIY/code tasks ("debug this", "review this PR").
- **Cloud product comparisons aren't procurement.** "Which is better, AWS or GCP?" is a knowledge question.
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

User: *"Three custom software firms with healthcare-industry experience,
SOC 2-ready, ideally with at least a 4-star rating."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:it_services+service_provided:application-modernization+custom+software+healthcare+soc2+rating>=4
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
