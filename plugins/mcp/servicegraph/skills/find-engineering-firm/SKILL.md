---
name: find-engineering-firm
description: Use whenever the user wants to find, shortlist, vet, or enrich US engineering firms — civil, structural, MEP, mechanical, electrical, geotechnical, transportation, environmental, and manufacturing. **For real-world engineering (buildings, infrastructure, manufacturing) — NOT software engineering.** Triggers on "find civil engineering firms in Florida for transportation", "shortlist three structural engineering firms with high-rise experience", "MEP consultancy for a hospital project", or "pull contact info for these 12 engineering firm domains", even when described indirectly (PE-stamped drawings, building-permit review). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Defer software-dev / "engineering team" / SaaS-architecture asks to find-software-developer. Skip in-house engineering-manager hires, DIY questions, software-product comparisons (Revit, AutoCAD), non-US firms, individual freelancers.
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
tags: [engineering, professional-services, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: engineering_services
---

# find-engineering-firm

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US **real-world** engineering firms — buildings,
infrastructure, energy, manufacturing — via the `pro_services`
dataset. The catalog tags firms with `industry:engineering_services`
and a ~23-tag service sub-taxonomy.

**This is NOT for software engineering.** "Software engineering firm",
"engineering team", "engineering manager hire", "system architecture
review" — those are all software-developer territory. The first thing
this skill confirms is that the user means real engineering, not
software.

**Always pin `industry:engineering_services`.** Note the **`_services`
suffix** — older docs sometimes show `industry:engineering` but the
literal pin returns zero results in the live catalog. Sub-disciplines
are typically structured `service_provided` tags
(`civil-engineering`, `structural-engineering`, `mep-engineering`,
etc.) — confirm exact names via
`/v1/datasets/pro_services/fields?include_values=1`. Surveying is
`surveying-mapping`, not `surveying`.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## When NOT to use this skill

The dominant failure mode is firing on software-engineering asks. Refuse those.

- **Software / SaaS / app-development asks** — even when phrased as "software engineering firm", "engineering team partner", "build our platform" → defer to `find-software-developer`.
- **In-house "engineering manager" hires** — in modern B2B usage this is almost always software-engineering recruiting. Refuse.
- **System / cloud / database architecture questions** ("Postgres vs DynamoDB", "monolith vs microservices") — software topics.
- **Architecture (buildings)** — `find-architecture-firm` covers that industry (when it exists). This skill covers engineering disciplines that *work with* architects (structural, MEP, civil), but the architect-of-record procurement is a different fire.
- **Consumer/residential** ("architect for a residential remodel", "engineer to inspect my house"). Catalog is B2B procurement only.
- **Non-US firms / individual freelance engineers / DIY questions / engineering-software product comparisons (Revit, AutoCAD, SolidWorks, Ansys).**

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `engineering_services` industry value and sub-tag names. |
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

**Engineering-flavored examples** (validate yours with `/check`):

```
industry:engineering_services service_provided:civil-engineering state:FL transportation
industry:engineering_services service_provided:structural-engineering high-rise
industry:engineering_services service_provided:mep-engineering hospital
industry:engineering_services service_provided:mechanical-engineering hvac industrial
industry:engineering_services service_provided:environmental-engineering remediation
industry:engineering_services service_provided:geotechnical-engineering state:CA
industry:engineering_services service_provided:civil-engineering@high has:clutch
industry:engineering_services service_provided:electrical-engineering manufacturing
```

**Sub-discipline → tag mapping** (verify exact names via `/fields`;
~23 sub-tags so this isn't exhaustive):

| User asks for | Use |
|---|---|
| Civil engineering / sitework / transportation | `service_provided:civil-engineering` |
| Structural engineering | `service_provided:structural-engineering` |
| MEP (mechanical/electrical/plumbing) | `service_provided:mep-engineering` |
| Mechanical / HVAC | `service_provided:mechanical-engineering` |
| Electrical engineering | `service_provided:electrical-engineering` |
| Geotechnical / soils / foundations | `service_provided:geotechnical-engineering` |
| Surveying / land surveys / mapping | `service_provided:surveying-mapping` (NOT `surveying`) |
| Transportation engineering | `service_provided:transportation-engineering` |
| Environmental / remediation | `service_provided:environmental-engineering` |
| Manufacturing / process | `service_provided:manufacturing-engineering` |
| Aerospace | `service_provided:aerospace-engineering` |
| Energy (oil/gas/renewables) | `service_provided:energy-engineering` |
| Industrial automation / controls | `service_provided:industrial-automation` |
| Materials testing | `service_provided:materials-testing` |
| Acoustic / vibration | `service_provided:acoustic-engineering` |
| Biomedical | `service_provided:biomedical-engineering` |

Verticals (hospital, high-rise, semiconductor, retail, datacenter)
and credentials (PE-licensed, LEED, AICP) are keyword-only.

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`aecom.com`, not
`www.aecom.com/about`).

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

### A. Civil engineering for transportation, in a state

```
GET /v1/datasets/pro_services/search?filter=industry:engineering_services+service_provided:civil-engineering+state:FL+transportation&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. Structural engineering + commercial high-rise

```
GET /v1/datasets/pro_services/search?filter=industry:engineering_services+service_provided:structural-engineering+(high-rise OR commercial)&limit=10
```

### C. MEP for a hospital project

```
GET /v1/datasets/pro_services/search?filter=industry:engineering_services+service_provided:mep-engineering+hospital&limit=10
```

### D. Mechanical / HVAC for industrial facility

```
GET /v1/datasets/pro_services/search?filter=industry:engineering_services+service_provided:mechanical-engineering+hvac+industrial&limit=10
```

### E. Indirect intent — "stamp the drawings"

User: *"We're building a 10-story office and need a structural engineer to stamp the drawings."*

```
GET /v1/datasets/pro_services/search?filter=industry:engineering_services+service_provided:structural-engineering+commercial&limit=10
```

PE-license details surface from the unlocked `platforms` map / firm
detail. If the user wants only PE-licensed firms, add `pe` as a keyword.

### F. Geotechnical in California

```
GET /v1/datasets/pro_services/search?filter=industry:engineering_services+service_provided:geotechnical-engineering+state:CA&limit=10
```

Avoid pinning narrow keywords like `seismic` on top — engineering
verticals tend to collapse below k=20 quickly. The full state pool
of ~20 geotechnical firms is more useful than a 2-firm pool after
keyword narrowing.

### G. Quality threshold — be careful

Engineering firms aren't reviewed like agencies; `rating>=N` collapses
civil/structural/MEP pools sharply. Prefer `@high` + size + geography
as the quality proxy instead of a rating gate:

```
GET /v1/datasets/pro_services/search?filter=industry:engineering_services+service_provided:civil-engineering@high+state:CA+-company_size_signal:solo&limit=10
```

If the user insists on rated firms, add `has:clutch` (more lenient
than `rating>=4`).

### H. BYO apex list — enrich domains

User pastes 8–20 engineering firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge). A 404 often means the domain
   is a software firm tagged `industry:it_services` instead of real
   engineering.
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin `industry:engineering_services`.** Without it, `civil-engineering` / `mep-engineering` / `electrical-engineering` keywords could leak into other industries (architecture firms sometimes list MEP coordination as a sub-service).
- **It's `engineering_services`, not `engineering`.** The literal pin `industry:engineering` returns zero results. Same drift logic for `surveying-mapping` (not `surveying`).
- **The hardest boundary is software-engineering.** "Engineering firm" / "engineering team" in modern B2B usage almost always means software in tech contexts. Defer those to `find-software-developer`. Real engineering is for buildings, infrastructure, energy, manufacturing — not for SaaS apps.
- **"Engineering manager" hires are recruiting**, not procurement.
- **Architecture firms are a separate industry.** Architect-of-record procurement (form/aesthetics) is a different fire; this skill is for the engineering disciplines that work with architects.
- **Consumer/residential is out of scope** ("architect for my house remodel", "engineer to inspect my deck"). B2B-only.
- **Engineering verticals are rating-sparse.** Civil/structural/MEP firms aren't reviewed like agencies — `rating>=N` collapses pools below k=20. Use `@high` evidence + size + geography as the quality proxy.
- **Narrow keywords artificially shrink pools.** A keyword like `seismic` on top of a CA geotech filter yields only ~2 firms vs ~20 without it. Drop narrowing keywords for default-required verticals.
- **Engineering-software product comparisons (Revit, AutoCAD, SolidWorks, Ansys, Bentley)** are NOT procurement.
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

User: *"Three civil engineering firms in Florida focused on
transportation infrastructure, ideally with PE-licensed engineers."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:engineering_services+service_provided:civil-engineering+state:FL+transportation+pe
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
