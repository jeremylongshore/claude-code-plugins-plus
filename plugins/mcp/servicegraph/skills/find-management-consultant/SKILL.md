---
name: find-management-consultant
description: Use whenever the user wants to find, shortlist, vet, or enrich US management consultancies — strategy, operations, executive coaching, leadership development, org-development/change management, PMO/program management, sales/revenue operations consulting. Triggers on "find me three top strategy consultancies in California", "shortlist boutique ops-consulting firms with healthcare experience", "we need an executive coach for our new CEO", or "pull contact info for these 10 consulting firm domains", even when described indirectly (post-merger integration help, change-management partner, fractional COO). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Skip in-house strategy hires, "help me build a strategy" do-the-work asks, framework comparisons (Lean vs Agile, BCG matrix, etc.), academic/MBA-program questions, life/career coaching for individuals, non-US firms, individual freelancers.
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
tags: [management-consulting, strategy, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: management_consulting
---

# find-management-consultant

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US management consulting firms via the
`pro_services` dataset. The catalog tags firms with
`industry:management_consulting` and a 7-tag service sub-taxonomy:
`strategy-consulting`, `operations-consulting`, `executive-coaching`,
`leadership-development`, `organizational-development`,
`pmo-project-management`, `sales-revenue-consulting`.

**Always pin `industry:management_consulting`.** Sub-services are
structured `service_provided` tags — confirm exact names via
`/v1/datasets/pro_services/fields?include_values=1`.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## When NOT to use this skill

- "Help me build a strategy / write a plan / make a recommendation" — do-the-work, not procurement.
- In-house strategy/operations hires (Chief Strategy Officer, COO).
- **Life or career coaching for an individual** — the catalog's `executive-coaching` tag is for B2B (the firm hires the coach for their executives), not for the user themselves.
- Framework explanations (Lean vs Agile, Porter's Five Forces).
- MBA program questions, academic research.
- Non-US firms / individual freelance consultants.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `management_consulting` industry value and sub-tag names. |
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

**Management-consulting examples** (validate yours with `/check`):

```
industry:management_consulting service_provided:strategy-consulting@high
industry:management_consulting service_provided:operations-consulting state:NY
industry:management_consulting service_provided:executive-coaching
industry:management_consulting (service_provided:strategy-consulting@high OR service_provided:operations-consulting@high)
industry:management_consulting service_provided:organizational-development change
industry:management_consulting service_provided:strategy-consulting@high rating>=4 has:clutch
industry:management_consulting service_provided:pmo-project-management
```

**Sub-service tag → typical user phrasing**:

| User asks for | Tag |
|---|---|
| Strategy / strategic planning | `service_provided:strategy-consulting` |
| Operations / ops consulting | `service_provided:operations-consulting` |
| Executive coach (for senior leaders) | `service_provided:executive-coaching` |
| Leadership development programs | `service_provided:leadership-development` |
| Org design / change management | `service_provided:organizational-development` |
| PMO / program management | `service_provided:pmo-project-management` |
| Sales/revenue ops | `service_provided:sales-revenue-consulting` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`mckinsey.com`, not
`www.mckinsey.com/about`).

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

### A. Strategy consultancy in a state

```
GET /v1/datasets/pro_services/search?filter=industry:management_consulting+state:CA+service_provided:strategy-consulting@high&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. Boutique ops consulting + vertical

```
GET /v1/datasets/pro_services/search?filter=industry:management_consulting+service_provided:operations-consulting+healthcare+-company_size_signal:large_50plus&limit=10
```

### C. Executive coach for a CEO

```
GET /v1/datasets/pro_services/search?filter=industry:management_consulting+service_provided:executive-coaching@high&limit=10
```

### D. Indirect intent — post-merger / change

```
GET /v1/datasets/pro_services/search?filter=industry:management_consulting+service_provided:organizational-development+(merger OR integration)&limit=10
```

If thin, drop the keywords — `organizational-development@high` alone
captures change-management work.

### E. Indirect intent — "fractional COO"

```
GET /v1/datasets/pro_services/search?filter=industry:management_consulting+service_provided:operations-consulting+fractional&limit=10
```

### F. Quality threshold + Big-3 alumni

```
GET /v1/datasets/pro_services/search?filter=industry:management_consulting+service_provided:strategy-consulting@high+rating>=4+(mckinsey OR bcg OR bain)&limit=10
```

The "alumni" angle isn't structured — keyword the firm names of the
shops the alumni came from; many spinout consultancies advertise it
in bio text.

### G. BYO apex list — enrich domains

User pastes 8–20 consulting-firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge).
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin `industry:management_consulting`.** Without it, `service_provided:strategy-consulting` surfaces marketing or IT firms that list "strategy" as a sub-service.
- **`executive-coaching` is for B2B.** When a firm hires a coach for their executives, this skill applies. When an *individual* asks for a life coach or career coach for themselves, it's out of scope.
- **"Help me build a strategy" is do-the-work, not procurement.**
- **Framework comparisons** (Lean vs Agile) and **MBA questions** are knowledge, not procurement.
- **In-house hires (CSO, COO) are NOT procurement.**
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

User: *"Three top management-consulting firms in California focused on
strategy, with strong third-party ratings."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:management_consulting+state:CA+service_provided:strategy-consulting@high+rating>=4+review_count_total>=20
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
