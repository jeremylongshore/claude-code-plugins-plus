---
name: find-cpa-firm
description: Use whenever the user wants to find, shortlist, vet, or enrich US accounting and tax firms (CPA firms) — financial-statement audit, SOC 1/2 audit, corporate tax, bookkeeping for businesses, advisory/fractional CFO, M&A diligence, 409A valuations, R&D tax credits, IPO readiness, sales-and-use tax. Triggers on "find me a CPA firm for our delaware c-corp series A audit", "shortlist three audit firms with SaaS experience", "we need a tax advisor for our M&A", or "pull contact info for these 10 accounting firm domains", even when described indirectly (audit our books, fractional CFO support, file our 1120). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Skip personal/consumer tax preparation (1040, individual estate, retirement planning), in-house controller/CFO hires, "how do I file my taxes" DIY questions, accounting-software comparisons (QuickBooks vs Xero), non-US firms, individual freelance bookkeepers.
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
tags: [accounting, tax, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: accounting_tax
---

# find-cpa-firm

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US **business-to-business** accounting and tax
firms (CPA firms) via the `pro_services` dataset.

**The catalog is B2B-only.** Personal tax prep (individual 1040s,
retirement planning, individual estate planning, personal bookkeeping
for freelancers) is out of scope — those firms were filtered during
the catalog audit.

**Always pin `industry:accounting_tax`.** Sub-services (audit, tax,
bookkeeping, advisory, M&A diligence, 409A, R&D credits, etc.) are
NOT separate tags — `industry:accounting_tax` is the most specific
structured level — so practice-area specialization is a keyword
substring search on firm text.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## When NOT to use this skill

- Personal/individual tax matters: 1040 prep, IRA/Roth conversions, personal estate planning, "what should I do with my refund".
- Bookkeeping for a freelancer or solo creator's personal income.
- In-house finance hires (Controller, CFO, Accountant).
- DIY tax/accounting questions ("how do I claim X", "explain depreciation").
- Accounting-software comparisons (QuickBooks, Xero, NetSuite).
- Non-US firms / individual freelance bookkeepers.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `accounting_tax` is in the `industry` value list. |
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

**Accounting-flavored examples** (validate yours with `/check`):

```
industry:accounting_tax state:CA audit saas
industry:accounting_tax cpa state:DE,NY
industry:accounting_tax "m&a" diligence
industry:accounting_tax tax 409a
industry:accounting_tax "fractional cfo"
industry:accounting_tax "r&d" tax
industry:accounting_tax "soc 2"
industry:accounting_tax -company_size_signal:solo rating>=4
```

**Practice area → keyword mapping**:

| User asks for | Add as keyword(s) |
|---|---|
| Audit / financial-statement audit | `audit` |
| SOC 1 / SOC 2 audit | `"soc 2"` |
| Corporate tax / 1120 | `tax`, `"corporate tax"`, `1120` |
| Bookkeeping (for a business) | `bookkeeping` |
| Advisory / fractional CFO | `"fractional cfo"`, `advisory` |
| M&A diligence | `m&a`, `diligence` |
| 409A valuation | `409a` |
| R&D tax credits | `"r&d"`, `"r&d tax"` |
| IPO readiness | `ipo`, `readiness` |
| Sales-and-use tax | `"sales tax"`, `"sales and use"` |
| International tax / transfer pricing | `"international tax"`, `"transfer pricing"` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`pwc.com`, not
`www.pwc.com/about`).

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

### A. CPA firm for a Delaware C-corp audit

User: *"CPA firm for our delaware c-corp series A audit, under 50 ppl."*

```
GET /v1/datasets/pro_services/search?filter=industry:accounting_tax+audit+state:DE,NY,CA+-company_size_signal:large_50plus&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. SaaS-experienced audit firms

```
GET /v1/datasets/pro_services/search?filter=industry:accounting_tax+audit+saas&limit=10
```

### C. M&A diligence

User: *"Tax advisor for our M&A — Series-B-stage tech company."*

```
GET /v1/datasets/pro_services/search?filter=industry:accounting_tax+"m&a"+diligence+tech&limit=10
```

### D. Fractional CFO (indirect intent)

User: *"Fractional CFO to help us through a Series-A close."*

```
GET /v1/datasets/pro_services/search?filter=industry:accounting_tax+"fractional cfo"&limit=10
```

If thin, drop the `cfo` qualifier — `fractional` alone catches
fractional finance leaders broadly.

### E. R&D tax credits

User: *"R&D tax credit specialists for biotech."*

```
GET /v1/datasets/pro_services/search?filter=industry:accounting_tax+"r&d"+biotech&limit=10
```

### F. Multi-state DTC sales tax

User: *"Outside accountant for state and local tax filings — multi-state DTC business."*

```
GET /v1/datasets/pro_services/search?filter=industry:accounting_tax+("sales tax" OR salt)+multi-state&limit=10
```

If barely any results, drop `multi-state` and surface the dimension
from the unlocked detail later.

### G. BYO apex list — enrich domains

User pastes 8–20 accounting-firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge).
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

A 404 here often means the firm focuses on personal tax prep and was
filtered out of the B2B catalog.

## Gotchas

- **Always pin `industry:accounting_tax`.** Without it, "tax" / "audit" / "cfo" as keywords match management consulting and other industries.
- **Refuse personal-tax asks.** 1040 prep, IRA conversion strategy, personal estate planning, "should I use QuickBooks Self-Employed?" — not in catalog. Tell the user the catalog is B2B-only.
- **`industry:accounting_tax` is the only structured handle.** Practice areas (audit, tax, M&A, 409A, R&D credits) are keyword-only. Multi-word areas split into ANDed barewords unless quoted (`"r&d tax credits"` → one phrase).
- **In-house finance hires (Controller, CFO, Accountant) are NOT procurement.** Recruiting an employee is out of scope.
- **Accounting-software comparisons** (QuickBooks vs Xero vs NetSuite) are NOT procurement either.
- **Briefs DO include `apex`, `name`, location, ratings.** They DON'T include `url`, `phone_primary`, `email_primary`, `legal_name`, `address_full`, full `platforms` — those require an unlock.
- **`not_found` / `not_in_dataset` 404 = not in `pro_services`.** Skip; not charged.
- **Unlock is atomic.** N apexes either all charge (up to 10×N credits) or none on 402.
- **Within-TTL re-views are free** (`was_cached:true`).

## Errors

JSON envelope: `{"error": {"code": "...", "message": "..."}}`.

| Status | Code | What to do |
|---|---|---|
| 400 | `filter_parse_error` | `position` included; fix and re-validate with `/check`. |
| 400 | `kind_in_filter` | Strip any `kind:` from filter — URL is authoritative. |
| 400 | `field_not_in_dataset` | Drop the disallowed field. |
| 400 | `invalid_apex` | Re-normalize. |
| 401 | `unauthorized` / `invalid_audience` | Re-prompt for fresh `vk_…`. |
| 402 | `insufficient_credits` | `needed` and `balance` in payload; nothing charged. |
| 404 | `not_found` / `not_in_dataset` | Skip; not charged. |
| 429 | `rate_limited` | Honor `Retry-After`. |

## End-to-end example

User: *"CPA firm for our delaware c-corp series A audit, recommend 5
options under 50 ppl, ideally with SaaS experience and 4-star ratings."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:accounting_tax+audit+saas+rating>=4+-company_size_signal:large_50plus
GET /v1/datasets/pro_services/search?filter=...&limit=10
# Present briefs. "Unlocking 5 = 50 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com", "firm-d.com", "firm-e.com"] }
GET /v1/me/credits
```

## Resources

- Upstream source: <https://github.com/nostrband/ServiceGraph>
- ServiceGraph API: <https://api.servicegraph.co> — keys at
  <https://servicegraph.co/profile/api-keys>
- Hub skill: `servicegraph` (this plugin) — the dataset-agnostic entry point
  when the user names ServiceGraph explicitly.
