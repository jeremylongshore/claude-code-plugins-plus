---
name: find-design-agency
description: Use whenever the user wants to find, shortlist, vet, or enrich US design and creative agencies — graphic design, UX/UI, product design, brand identity, packaging, illustration, motion design, and creative direction. Triggers on "find me a UX/UI design agency for our SaaS product", "shortlist three brand-identity studios in NY", "packaging design firm for a CPG launch", or "pull contact info for these 10 design studio domains", even when described indirectly (brand refresh, design our app, build our visual system). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Defer to find-marketing-agency for marketing-led engagements where design is one of several services. Defer to find-web-developer when the deliverable is a built website. Skip in-house designer hires, "design me a logo" DIY asks, design-software comparisons, consumer/personal-design (weddings, hobby projects), non-US firms, individual freelancers.
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
tags: [design, creative, agencies, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: design_creative
---

# find-design-agency

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US design and creative agencies via the
`pro_services` dataset. The catalog tags firms with
`industry:design_creative` and a ~13-tag service sub-taxonomy spanning
graphic design, UX/UI, product design, brand identity, packaging,
illustration, motion, and creative direction.

**Always pin `industry:design_creative`.** Sub-disciplines are
typically structured `service_provided` tags (`graphic-design`,
`ui-ux-design`, `product-design`, `branding`, etc.). Two known drifts:
the UX/UI tag is **`ui-ux-design`**, not `ux-ui-design`; and there is
**no `industrial-design` tag** — use `product-design` plus a hardware
keyword. Confirm exact names via
`/v1/datasets/pro_services/fields?include_values=1`.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when scope is different

- **Marketing-led engagements** where design is one of several services (PR + content + paid + design) → `find-marketing-agency`. This skill is for **design-led** engagements where the design work IS the primary deliverable.
- **Build-the-website work** (coded marketing site, ecommerce, custom CMS) → `find-web-developer`. Design agencies often partner with web devs; if the user wants the built artifact, fire web-developer.
- **Custom software with design needs** (SaaS app, internal tool) → `find-software-developer` when the deliverable is software. Pure design (Figma files, brand systems, print collateral) stays here.

## When NOT to use this skill

- **Consumer/personal design** — weddings, hobby projects, Etsy side projects, custom holiday cards, personal portfolio sites. Catalog is B2B procurement only.
- **DIY** — "design me a logo", "make me a hero illustration", "redesign my app's onboarding flow".
- **In-house designer hires** (Lead Designer, UX Researcher, Brand Designer).
- **Design-software product comparisons** (Figma vs Sketch vs Adobe XD, Webflow vs Framer).
- **Knowledge questions** ("explain the difference between UX and UI").
- **Non-US firms** / **individual freelance designers**.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `design_creative` industry value and sub-tag names. |
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

**Design-flavored examples** (validate yours with `/check`):

```
industry:design_creative service_provided:ui-ux-design saas
industry:design_creative service_provided:branding state:NY
industry:design_creative service_provided:packaging-design cpg
industry:design_creative service_provided:product-design hardware
industry:design_creative service_provided:graphic-design "annual report"
industry:design_creative motion animation
industry:design_creative service_provided:branding@high rating>=4 has:clutch
industry:design_creative service_provided:ui-ux-design@high fortune
```

**Sub-discipline → tag mapping** (verify exact names via `/fields`):

| User asks for | Use |
|---|---|
| Graphic design (logos, print, layouts) | `service_provided:graphic-design` |
| Logo design specifically | `service_provided:logo-design` |
| UX/UI design (digital products) | `service_provided:ui-ux-design` (note the `ui-ux-`, not `ux-ui-`) |
| Product design (digital + research) | `service_provided:product-design` |
| Brand identity / visual identity | `service_provided:branding` |
| Packaging design | `service_provided:packaging-design` |
| Print design / collateral | `service_provided:print-design` |
| Web design (visual) | `service_provided:web-design` (distinct from `web-development`) |
| Interior design | `service_provided:interior-design` |
| Illustration / motion design / creative direction | **no structured tag** — keyword-only (`illustration`, `motion`, `animation`, `"creative direction"`) |
| Industrial design (physical products) | **no structured tag** — closest is `service_provided:product-design` plus keyword `hardware` / `industrial` |

Verticals (SaaS, fintech, healthcare-tech, CPG, hospitality) and
credentials (AIGA, Awwwards) are keyword-only.

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`ideo.com`, not
`www.ideo.com/about`).

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

### A. UX/UI for a SaaS product

User: *"UX/UI design agency for our SaaS product."*

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:ui-ux-design+saas&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. Brand-identity studio in a state

User: *"Three brand-identity studios in NY for our rebrand."*

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:branding+state:NY+-company_size_signal:large_50plus&limit=10
```

`-large_50plus` keeps the shortlist to studio-size shops. Note: a
rating gate (`rating>=4`) collapses the boutique-branding pool
sharply — these firms are vetted by portfolio, not Clutch/Google,
so prefer `@high` evidence + non-solo as the quality proxy.

### C. Packaging for CPG

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:packaging-design+(cpg OR consumer)&limit=10
```

### D. Product design with hardware experience

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:product-design+hardware+industrial&limit=10
```

### E. Indirect intent — "design our visual identity and packaging"

User: *"We need someone to design the visual identity and packaging for our new line of beverages."*

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:branding+service_provided:packaging-design+(beverage OR cpg)&limit=10
```

Or use the intent translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "design firm for visual identity and packaging for a new beverage line" }
```

If the list is thin, drop packaging-design — many brand-identity
studios deliver packaging as part of the system.

### F. Graphic design for corporate use cases

User: *"Graphic design firms experienced with annual reports and investor decks."*

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:graphic-design+(annual OR investor OR corporate)&limit=10
```

### G. Quality threshold + Fortune 500 clients

User: *"Three UX/UI agencies with at least 4-star ratings and Fortune 500 clients."*

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:ui-ux-design@high+rating>=4+fortune&limit=10
```

### H. Brand-system overhaul

User: *"Creative agency for a brand system overhaul — logo, typography, color, voice."*

```
GET /v1/datasets/pro_services/search?filter=industry:design_creative+service_provided:branding@high&limit=10
```

If the user mentions "voice" / copywriting, the line with
`find-marketing-agency` blurs — stay here unless they explicitly ask
for strategy/campaigns.

### I. BYO apex list — enrich domains

User pastes 8–20 design firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge).
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

A 404 often means the firm is tagged under `industry:marketing_agency`
instead — design/marketing overlap is heavy.

## Gotchas

- **Always pin `industry:design_creative`.** Without it, design keywords (branding, ui-ux-design) appear in marketing_agency rows too.
- **Tag drift**: it's `ui-ux-design`, not `ux-ui-design`. There is no `industrial-design` tag — use `product-design` plus a hardware keyword.
- **Defer to `find-marketing-agency` for marketing-led engagements.** If the user wants brand + content + paid + social as one engagement, that's marketing-agency territory.
- **Defer to `find-web-developer` for the build phase.** Design agencies make Figma files; web devs ship code.
- **Refuse consumer-personal design.** Weddings, custom holiday cards, hobby Etsy logos — not in catalog.
- **DIY asks** ("design me a logo", "make a hero image") are NOT procurement.
- **Design-software comparisons** (Figma vs Sketch) are NOT procurement.
- **Rating gates on boutique studios are sparse.** `rating>=4` on a `branding@high` non-solo pool collapses sharply — boutique design shops are vetted by portfolio, not Clutch reviews. Prefer `@high` evidence + non-solo + state as the quality proxy.
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

User: *"Three UX/UI design agencies for our SaaS product, ideally with
4-star ratings and healthcare-tech experience."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:design_creative+service_provided:ui-ux-design@high+saas+healthcare+rating>=4
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
