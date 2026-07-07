---
name: find-marketing-agency
description: Use whenever the user wants to find, shortlist, vet, or enrich US marketing agencies — including branding, content marketing, PPC/paid media, social media, email marketing, performance/demand-gen, video production, and full-service digital agencies. Triggers on requests like "shortlist three B2B branding agencies in California", "find a PPC shop with ecommerce experience", "we need a content marketing partner for a SaaS launch", or "pull contact info for these 12 agency domains", even when the need is described indirectly. Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings, and third-party listings. Skip SEO-only asks (use find-seo-agency), web/software-development asks (use find-web-developer or find-software-developer), recruiting an in-house marketing hire, "write me a marketing plan" do-the-work asks, non-US firms, individual freelancers, marketing-software-product recommendations, and consumer/personal-brand asks.
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
tags: [marketing, agencies, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: marketing_agency
---

# find-marketing-agency

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US marketing agencies via the `pro_services`
dataset. The catalog has tens of thousands of US marketing firms
tagged across ~26 service sub-tags including `branding`,
`content-marketing`, `ppc`, `social-media-marketing`, `email-marketing`,
`web-design`, `video-production`, `inbound-marketing`,
`marketing-strategy`, `conversion-optimization`, and
`ecommerce-marketing`. (Note: there is no `performance-marketing` or
`demand-gen` / `demand-generation` tag — those user-phrasings map to
`inbound-marketing` / `marketing-strategy` / `conversion-optimization`
plus a keyword fallback.)

**Always pin `industry:marketing_agency`.** This skill exists to do
that automatically — the user shouldn't have to think about catalog
taxonomy.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when scope is narrow

If the user's ask is **strictly** one of the following, defer to the
dedicated skill:

- Strictly SEO/search-ranking work → `find-seo-agency`
- Strictly web/app/software development → `find-web-developer` /
  `find-software-developer`

If the user wants a marketing agency that *also* does SEO or web work
as part of a broader engagement, this skill is correct — pin
`industry:marketing_agency` and add the relevant `service_provided:`
tags.

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

If your harness has the ServiceGraph MCP server loaded (recognizable
by tool names containing `servicegraph`), prefer those tools — the
harness handles credentials in its own sandbox via OAuth 2.1 + PKCE,
so no token enters LLM context. Otherwise use the REST flow below.

### API surface (dataset id: `pro_services`)

Every endpoint requires the bearer (`Authorization: Bearer vk_…`).
There is no anonymous tier.

| Endpoint | Cost | Use it for |
|---|---|---|
| `GET /v1/datasets/pro_services/fields[?include_values=1&q=]` | free | Filter-field catalog + DSL grammar. Call first per session. |
| `GET /v1/datasets/pro_services/values/:field[?q=&limit=]` | free | Enumerate values for one field. |
| `GET /v1/datasets/pro_services/check?filter=…` | free | Validate a filter. Returns `{valid, normalized}` or `{valid:false, error}`. |
| `POST /v1/datasets/pro_services/translate-intent` | free | `{intent}` → LLM-generated DSL filter + sanity count. |
| `GET /v1/datasets/pro_services/search?filter=…&limit=&offset=` | free | Brief firm cards + per-row `unlock` hint + `total`. |
| `GET /v1/datasets/pro_services/:apex` | free | Single row brief; **detail block only if unlocked**. |
| `POST /v1/datasets/pro_services/unlocks` | **10 credits / firm** | `{apexes:[...]}` ≤100. Atomic batch; 30-day TTL on detail; `was_cached:true` rows free. |
| `GET /v1/me/credits` | free | Balance. |

**Cost model.** Discovery / validation / search / brief reads are
free. Detail (url, phone, email, social, address, full `platforms`
map) costs **10 credits per firm** and lasts **30 days**. Re-fetching
an unlocked firm within TTL is free.

### Auth

Tokens are `vk_*` API keys minted in the dashboard.

**Keep the token out of the LLM context** — never read `.env*` into
your context; dispatch every authed call through a shell wrapper.

1. **Just try the call** through a shell wrapper that sources
   `.env.local`:

   ```bash
   ( set -a; [ -f .env.local ] && . ./.env.local; set +a;
     curl -sS -H "Authorization: Bearer $SERVICEGRAPH_API_KEY" \
          'https://api.servicegraph.co/v1/datasets/pro_services/fields' )
   ```

2. **On `401 unauthorized`**, prompt the user (don't accept the key in chat):

   > "Open **https://servicegraph.co/profile/api-keys**, sign in,
   > click **Create key**, and copy the `vk_…` value. Then add
   > `SERVICEGRAPH_API_KEY=vk_…` to `.env.local` here (or export it
   > in your shell). Tell me when done. Please don't paste the key
   > into chat."

3. **Retry** the same call after the user signals ready. A later 401
   means the key was rotated/revoked — re-prompt.

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

**Four rules that bite:**

1. **AND binds tighter than OR.** `a OR b c` parses as `a OR (b AND c)`. Use parens.
2. **Comma list = OR within one predicate.** `state:CA,NY,TX` = any of three.
3. **Negation is `-x` or `NOT x`.** `state:CA,-NY` is rejected; use `state:CA -state:NY`.
4. **Bareword = keyword search.** Free-text substring across name / brand / title / meta / legal_name. Multiple barewords AND. Wrap multi-word phrases in double quotes (`keyword:"foo bar"`).

**Marketing-flavored examples** (validate yours with `/check`):

```
industry:marketing_agency service_provided:branding@high
industry:marketing_agency service_provided:ppc service_provided:content-marketing
industry:marketing_agency state:CA,NY -company_size_signal:solo
industry:marketing_agency (service_provided:inbound-marketing@high OR service_provided:marketing-strategy@high)
b2b industry:marketing_agency service_provided:content-marketing@high
industry:marketing_agency rating>=4 review_count_total>=20 has:clutch
industry:marketing_agency NOT (service_provided:seo OR service_provided:web-development)
```

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`ogilvy.com`, not
`www.ogilvy.com/about`). Strip user-supplied URLs to the apex before
calling `:apex` endpoints or building unlock batches.

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

### A. Branding agency in a state

User: *"Three B2B branding agencies in California for a Series-A SaaS company."*

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+state:CA+service_provided:branding@high+b2b&limit=10
# → 10 brief cards + total + per-row unlock.status

# Present, get user's pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
# → brief + detail for all 3
```

### B. PPC + ecommerce vertical

User: *"PPC shop that specializes in ecommerce."*

The catalog has a real `ecommerce-marketing` tag — pin it alongside
PPC for tighter shortlists than relying on the `ecommerce` keyword
alone:

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:ppc+service_provided:ecommerce-marketing&limit=10
```

### C. Multi-tag intersection — content + email + B2B vertical

User: *"Content marketing partner for a SaaS launch — should also do email."*

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:content-marketing@high+service_provided:email-marketing+saas
```

If the NY-area pool collapses with a `fintech`/`saas` keyword (it
tends to — vertical pins under-perform on agency copy), drop the
keyword and surface vertical experience to the user from briefs.

### D. Performance / demand-gen (indirect intent)

User: *"Someone to run our quarterly demand-gen campaigns and own the funnel."*

The catalog has **no** `performance-marketing` / `demand-gen` /
`demand-generation` tag — map to `inbound-marketing`,
`marketing-strategy`, or `conversion-optimization`, plus a keyword
for the user's wording:

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+(service_provided:inbound-marketing@high OR service_provided:marketing-strategy@high OR service_provided:conversion-optimization@high)+(demand OR funnel)&limit=10
```

If breakdowns are thin, drop `@high` or fall back to pure keyword.

Alternatively, use the intent translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "agency to run quarterly demand-gen campaigns and own the funnel" }
```

### E. Quality threshold (third-party signals)

User: *"Compare three social media agencies that have worked with Fortune 500 — high evidence."*

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:social-media-marketing@high+rating>=4+review_count_total>=20+has:clutch&limit=10
```

`fortune 500` is hard to filter structurally; let the user pick from
briefs or add `fortune` as a keyword.

### F. DTC ecommerce agencies

User: *"Paid-social agency for our DTC apparel brand."*

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:ecommerce-marketing+service_provided:social-media-marketing+dtc&limit=10
```

### G. Video production

User: *"Video production studio for a 90-second product launch film, NYC or LA."*

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:video-production+state:NY,CA&limit=10
```

State is HQ-only; surface city from the unlocked detail for NYC-vs-LA disambiguation.

### H. BYO apex list — enrich domains

User pastes 8–20 domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge). Flag misses.
2. User picks N to fully enrich. `POST /unlocks` with all of them =
   **10×N credits**, single atomic charge, detail bundles returned.
3. Within 30-day TTL, repeated unlock POSTs are free.

## Gotchas

- **Always pin `industry:marketing_agency`.** Without it, `service_provided:branding` matches design firms, IT services, and others.
- **Defer to sibling skills for narrow asks.** SEO-only → `find-seo-agency`. Strictly web/app development → `find-web-developer` / `find-software-developer`.
- **Briefs DO include `apex`, `name`, `industry`, `service_provided`, state, ratings.** They DON'T include `url`, `phone_primary`, `email_primary`, `legal_name`, `address_full`, full `platforms`. Those require an unlock.
- **`not_found` / `not_in_dataset` 404 is not a bug.** Apex isn't in `pro_services` (might be in another dataset). Skip; not charged.
- **Catalog is US-only B2B.** Refuse non-US asks, individual freelancers, and personal-brand consulting for the user themselves.
- **Multi-word phrases must be split or quoted.** `b2b saas` parses as two AND'd keywords; `"b2b saas"` is one phrase.
- **Unlock is atomic.** `POST /unlocks` with 5 apexes either charges (up to) 50 credits or leaves balance untouched on 402. Plan the batch.
- **Within-TTL re-views are free.** Re-running unlock on an apex still inside its 30-day window returns `was_cached:true`.

## Errors

JSON envelope: `{"error": {"code": "...", "message": "..."}}`.

| Status | Code | What to do |
|---|---|---|
| 400 | `filter_parse_error` | `position` included; fix and re-validate with `/check`. |
| 400 | `kind_in_filter` | Strip any `kind:` from filter — URL is authoritative. |
| 400 | `field_not_in_dataset` | Field isn't allowed on `pro_services`; drop it. |
| 400 | `invalid_apex` | Re-normalize to apex. |
| 401 | `unauthorized` / `invalid_audience` | Re-prompt for a fresh `vk_…`. |
| 402 | `insufficient_credits` | `needed` and `balance` in payload; nothing charged. |
| 404 | `not_found` / `not_in_dataset` | Skip; not charged. |
| 429 | `rate_limited` | Honor `Retry-After`. |

## End-to-end example

User: *"Shortlist three B2B branding agencies in California for a
Series-A SaaS company — high evidence on branding, ideally with at
least a 4-star rating."*

```
# 1. Discover (once per session)
GET /v1/datasets/pro_services/fields?include_values=1
# Confirms 'branding' is in service_provided, rating is numeric.

# 2. Validate + scope (free)
GET /v1/datasets/pro_services/check?filter=industry:marketing_agency+state:CA+service_provided:branding@high+rating>=4+b2b

# 3. Search briefs (free)
GET /v1/datasets/pro_services/search?filter=...&limit=10
# → 10 cards + total + per-row unlock.status

# 4. Present, get pick of 3. "Unlocking 3 firms = 30 credits, 30-day TTL."

# 5. Atomic unlock (charges 30 credits)
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }

# 6. (Optional) Confirm balance
GET /v1/me/credits
```

## Resources

- Upstream source: <https://github.com/nostrband/ServiceGraph>
- ServiceGraph API: <https://api.servicegraph.co> — keys at
  <https://servicegraph.co/profile/api-keys>
- Hub skill: `servicegraph` (this plugin) — the dataset-agnostic entry point
  when the user names ServiceGraph explicitly.
