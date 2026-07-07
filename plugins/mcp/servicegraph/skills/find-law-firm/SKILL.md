---
name: find-law-firm
description: Use whenever the user wants to find, shortlist, vet, or enrich US B2B law firms — corporate, IP/patent, M&A and securities, employment, commercial litigation, regulatory/compliance, data privacy/cyber, real estate, and tax. Triggers on "find three boutique IP law firms in California", "shortlist M&A counsel for a Series-B fundraise", "patent prosecution for our hardware startup", or "pull contact info for these 10 law firm domains", even when described indirectly (outside counsel, cap-table review, GDPR/SOC2 oversight). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Skip personal/consumer legal services where the user is the end client (divorce, personal injury, criminal defense, family law, estate planning, wills) — the catalog is B2B-only. Also skip in-house GC hires, "is this NDA enforceable" DIY questions, non-US firms, individual freelancers.
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
tags: [legal, law-firms, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: legal
---

# find-law-firm

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US **business-to-business** law firms via the
`pro_services` dataset.

**The catalog is B2B-only.** A historical audit dropped over half of
high-rank "legal" firms because they served personal/consumer matters
(divorce, personal injury, criminal defense, family law, estate
planning). The remaining catalog skews toward corporate, IP, M&A,
securities, employment, commercial litigation, regulatory, data
privacy, real-estate transactions, and corporate tax.

**Always pin `industry:legal`.** Sub-areas of law are NOT separate
tags — `industry:legal` is the most specific structured level — so
practice-area specialization (IP, M&A, employment, securities, etc.)
is a keyword substring search on firm text.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## When NOT to use this skill

The single biggest failure mode is firing on **consumer-personal**
legal asks. Refuse those — don't fall back to a partial filter.

- Personal/family matters where the user is the end client: divorce, child custody, family law, estate planning, wills/trusts, personal injury, criminal defense, individual bankruptcy, immigration for the user themselves, landlord/tenant disputes.
- DIY legal research: "is this enforceable?", "do I owe…?", "what does this clause mean?".
- In-house counsel hires (GC, paralegal, contracts manager).
- Non-US firms / individual freelancers / contract attorneys.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `legal` is in the `industry` value list. |
| `GET /v1/datasets/pro_services/check?filter=…` | free | Validate filter. |
| `POST /v1/datasets/pro_services/translate-intent` | free | `{intent}` → DSL filter + sanity count. |
| `GET /v1/datasets/pro_services/search?filter=…&limit=` | free | Brief firm cards + per-row unlock hint + total. |
| `GET /v1/datasets/pro_services/:apex` | free | One row brief; detail only if unlocked. |
| `POST /v1/datasets/pro_services/unlocks` | **10 credits / firm** | `{apexes:[...]}` ≤100; atomic; 30-day TTL on detail. |
| `GET /v1/me/credits` | free | Balance. |

**Cost model.** Discovery / validation / search / brief reads are
free. Detail (url, phone, email, social, address, full `platforms`
map) costs **10 credits per firm** and lasts **30 days**.

Note: `service_provided` tags are not populated for `industry:legal`
in the current catalog (Clutch and similar directories don't break
legal down further). Use barewords for practice areas.

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

**Legal-flavored examples** (validate yours with `/check`):

```
industry:legal state:CA patent
industry:legal state:NY,DE m&a
industry:legal employment
industry:legal securities ipo
industry:legal "data privacy" gdpr
industry:legal "commercial litigation" state:TX
industry:legal -company_size_signal:solo rating>=4 review_count_total>=20
industry:legal corporate startup
```

**Practice area → keyword mapping** (sub-areas are not structured tags):

| User asks for | Add as keyword(s) |
|---|---|
| IP / patents / trademarks | `patent`, `trademark`, `ip` |
| M&A / mergers and acquisitions | `m&a` |
| Securities / IPO / capital markets | `securities`, `ipo` |
| Employment law (employer-side) | `employment`, `labor` |
| Commercial litigation / disputes | `litigation`, `commercial` |
| Regulatory / compliance | `regulatory`, `compliance` |
| Data privacy / cyber / GDPR / CCPA | `privacy`, `gdpr`, `ccpa`, `cyber` |
| Real estate (commercial) | `"real estate"`, `"commercial real estate"` |
| Tax (corporate) | `tax` |
| Corporate / formation / governance | `corporate`, `formation`, `governance` |
| Antitrust | `antitrust` |
| Bankruptcy (corporate) | `bankruptcy` |
| Immigration (corporate sponsorship) | `immigration` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`dlapiper.com`, not
`www.dlapiper.com/about`).

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

### A. IP / patent firm in a state

User: *"Three boutique IP law firms in California for hardware-startup patent prosecution."*

```
GET /v1/datasets/pro_services/search?filter=industry:legal+state:CA+patent+-company_size_signal:large_50plus&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. M&A counsel for a fundraise

```
GET /v1/datasets/pro_services/search?filter=industry:legal+state:NY+m&a&limit=10
```

### C. Securities / IPO experience

```
GET /v1/datasets/pro_services/search?filter=industry:legal+securities+ipo&limit=10
```

### D. Indirect intent — "outside counsel for GDPR/SOC2"

User: *"Our compliance is getting complex — we need outside counsel for GDPR, CCPA, and SOC2 oversight."*

```
GET /v1/datasets/pro_services/search?filter=industry:legal+(gdpr OR ccpa OR privacy)+compliance&limit=10
```

Or use the intent translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "outside counsel for GDPR/CCPA compliance and SOC2 oversight" }
```

### E. Employment law for a tech employer

```
GET /v1/datasets/pro_services/search?filter=industry:legal+employment+tech+company_size_signal:medium_10_50,small_2_10&limit=10
```

### F. Quality threshold + commercial litigation

```
GET /v1/datasets/pro_services/search?filter=industry:legal+commercial+litigation+state:TX+rating>=4&limit=10
```

### G. BYO apex list — enrich domains

User pastes 8–20 law-firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge). A 404 often means the firm is
   consumer-focused (divorce, PI) and was filtered out of the B2B
   catalog.
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin `industry:legal`.** Without it, "patent" or "m&a" as keywords leak into marketing/IT meta tags.
- **Refuse consumer-personal legal asks.** Divorce, personal injury, criminal defense, family law, estate planning, wills, individual immigration, personal bankruptcy — NOT in the catalog. Tell the user the catalog is B2B-only and suggest elsewhere (state bar referral, Avvo). Do NOT return a partial result hoping it's close enough.
- **`industry:legal` is the only structured handle.** Practice areas are keyword-only. Multi-word areas split into ANDed barewords unless quoted (`"commercial litigation"` → one phrase).
- **Catalog skews toward mid/large B2B firms.** Solo practitioners and <5-attorney shops are under-represented. For "boutique", exclude `company_size_signal:large_50plus` rather than requiring solo.
- **DIY/legal-research questions** ("is this NDA enforceable?", "explain fair use") are NOT procurement.
- **Software-product comparisons** (Ironclad vs DocuSign) are NOT procurement.
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

User: *"Three boutique IP law firms in California that handle patent
prosecution for hardware startups, ideally with at least a 4-star rating."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:legal+state:CA+patent+rating>=4+-company_size_signal:large_50plus
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
