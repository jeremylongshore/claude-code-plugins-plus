---
name: find-pr-agency
description: Use whenever the user wants to find, shortlist, vet, or enrich US public-relations and communications agencies — media relations, crisis comms, investor relations (IR), product-launch PR, tech/startup PR, healthcare PR, B2B PR, public affairs, brand reputation, and internal communications. Triggers on "find me a tech PR agency in NY", "shortlist three IR firms for our IPO", "we need crisis comms help for a brand reputation issue", or "pull contact info for these 10 PR firm domains", even when described indirectly (we need press, get us into TechCrunch, manage our brand reputation). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Defer to find-marketing-agency when scope is broader marketing beyond PR/comms. Skip in-house PR/comms hires, "write me a press release" DIY asks, PR-software comparisons (Cision, Muck Rack), influencer-marketplace questions, non-US firms, individual freelance PR people.
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
tags: [public-relations, agencies, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  service: public-relations
---

# find-pr-agency

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US PR and communications agencies via the
`pro_services` dataset.

**Always pin `service_provided:public-relations`.** Note: the
catalog's nominal `industry:pr_comms` value returns zero firms in
the live release — PR/comms firms are tagged with
`service_provided:public-relations` instead, typically under adjacent
industries (`marketing_agency`, `other_pro_services`). **Pin the
service tag, not the industry.** Sub-types (media relations, crisis,
IR, public affairs, healthcare PR, tech PR, B2B PR, internal comms,
brand reputation) are NOT separate tags — sub-type specialization is
a keyword substring search on firm text.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when scope is broader

If the user wants a **multi-service marketing engagement** (PR plus
content plus paid plus social), defer to `find-marketing-agency` —
that skill covers full-service shops where PR is one of several
service lines.

This skill is correct when PR/comms is the primary deliverable —
launches, media relations, crisis, IR, public affairs.

## When NOT to use this skill

- "Write me a press release / draft these talking points" → DIY work.
- In-house comms/PR hires (Head of Comms, PR Manager).
- PR-software comparisons (Cision, Muck Rack, Prowly).
- Influencer-marketplace asks — that's paid media; defer to `find-marketing-agency` or refuse for marketplace product questions.
- "Explain how earned media works" → knowledge question.
- Non-US firms.
- Individual freelance PR people / publicists.

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
containing `servicegraph` in the name), prefer those — credentials
stay in the harness's OAuth 2.1 + PKCE sandbox and no token enters
LLM context. Otherwise use the REST flow below.

### API surface (dataset id: `pro_services`)

Every endpoint requires the bearer (`Authorization: Bearer vk_…`).
No anonymous tier.

| Endpoint | Cost | Use it for |
|---|---|---|
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `public-relations` is in the `service_provided` value list. |
| `GET /v1/datasets/pro_services/check?filter=…` | free | Validate filter. |
| `POST /v1/datasets/pro_services/translate-intent` | free | `{intent}` → LLM-generated DSL filter + sanity count. |
| `GET /v1/datasets/pro_services/search?filter=…&limit=` | free | Brief firm cards + per-row unlock hint + total. |
| `GET /v1/datasets/pro_services/:apex` | free | One row brief; detail only if unlocked. |
| `POST /v1/datasets/pro_services/unlocks` | **10 credits / firm** | `{apexes:[...]}` ≤100; atomic; 30-day TTL on detail. |
| `GET /v1/me/credits` | free | Balance. |

**Cost model.** Discovery / validation / search / brief reads are
free. Detail (url, phone, email, social, address, full `platforms`
map) costs **10 credits per firm** and lasts **30 days**.

### Auth

Tokens are `vk_*` API keys minted in the dashboard. **Keep the token
out of the LLM context** — never read `.env*` files; dispatch every
authed call through a shell wrapper.

1. **Try the call first** through a shell wrapper that sources
   `.env.local`:

   ```bash
   ( set -a; [ -f .env.local ] && . ./.env.local; set +a;
     curl -sS -H "Authorization: Bearer $SERVICEGRAPH_API_KEY" \
          'https://api.servicegraph.co/v1/datasets/pro_services/fields' )
   ```

2. **On `401 unauthorized`**, prompt the user:

   > "Open **https://servicegraph.co/profile/api-keys**, create a
   > key, and add `SERVICEGRAPH_API_KEY=vk_…` to `.env.local` here
   > (or export it in your shell). Tell me when done. Please don't
   > paste the key into chat."

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
comma list = OR within one predicate; negation is `-x` or `NOT x`
(no negative literals inside comma lists); bareword = keyword search
(multi-word phrases must be quoted or split).

**PR-flavored examples** (validate yours with `/check`):

```
service_provided:public-relations tech state:NY
service_provided:public-relations healthcare
service_provided:public-relations b2b saas
service_provided:public-relations crisis
service_provided:public-relations "investor relations"
service_provided:public-relations ipo state:NY,CA
service_provided:public-relations "public affairs" state:DC
service_provided:public-relations rating>=4 has:clutch
```

**Sub-type / vertical → keyword mapping**:

| User asks for | Add as keyword(s) |
|---|---|
| Tech / startup PR | `tech`, `startup`, `saas` |
| Healthcare / pharma PR | `healthcare`, `pharma`, `biotech` |
| Crisis comms | `crisis` |
| Investor relations / IR | `"investor relations"`, `ir`, `ipo` |
| B2B PR | `b2b` |
| Public affairs | `"public affairs"` |
| Brand reputation | `"brand reputation"`, `reputation` |
| Internal communications | `"internal communications"`, `"internal comms"` |
| Earned media / media relations | `"earned media"`, `"media relations"` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`edelman.com`, not
`www.edelman.com/about`).

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

### A. Tech PR for a Series-B announcement

User: *"Tech PR agency in NY for our Series-B announcement."*

```
GET /v1/datasets/pro_services/search?filter=service_provided:public-relations+tech+state:NY&limit=10
# → 10 brief cards + total + per-row unlock.status

# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. IR firms for an IPO

User: *"Three IR firms for our upcoming IPO roadshow."*

```
GET /v1/datasets/pro_services/search?filter=service_provided:public-relations+("investor relations" OR ir)+ipo&limit=10
```

### C. Crisis comms (urgent)

User: *"Crisis comms help — brand reputation issue blowing up online."*

```
GET /v1/datasets/pro_services/search?filter=service_provided:public-relations+crisis&limit=10
```

Skip the validation hop and present briefs immediately given the
urgency.

### D. Healthcare / regulatory PR

User: *"Healthcare PR agency familiar with FDA regulatory comms."*

```
GET /v1/datasets/pro_services/search?filter=service_provided:public-relations+healthcare+(fda OR regulatory)&limit=10
```

### E. Indirect intent — "we need press"

User: *"We need press for our Series-B — get us into TechCrunch, WSJ,
and the trade press."*

That's product-launch / tech PR. Either translate by hand:

```
GET /v1/datasets/pro_services/search?filter=service_provided:public-relations+(tech OR startup)+(launch OR series-b)&limit=10
```

…or hand the intent off:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "PR agency to get our Series-B into TechCrunch and trade press" }
```

If thin, drop the launch/series-b keyword — most tech PR firms run
launches as a default deliverable.

### F. Public affairs (state government)

User: *"Public affairs firms with state-government experience in California."*

```
GET /v1/datasets/pro_services/search?filter=service_provided:public-relations+"public affairs"+state:CA&limit=10
```

### G. BYO apex list — enrich domains

User pastes 8–20 PR-firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge). Flag misses.
2. User picks N to fully enrich. `POST /unlocks` with all of them =
   **10×N credits**, atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Pin `service_provided:public-relations`, not `industry:pr_comms`.** The industry value is empty in the live catalog; PR firms sit under adjacent industries. Without the service pin, "tech PR" / "crisis" / "investor relations" keywords leak into general marketing.
- **Defer to `find-marketing-agency` for full-service marketing.** When PR is one of several service lines (PR + content + paid + social), the marketing-agency skill is the right fire.
- **Sub-types are keyword-only.** Multi-word sub-types split into ANDed barewords unless quoted (`investor relations` → `investor` AND `relations`; `"investor relations"` → one phrase).
- **"Write me a press release" / "draft talking points" is do-the-work.** Refuse and offer to find a firm if the user wants to engage one.
- **Influencer marketing is NOT PR.** Influencer marketplaces (Aspire, Grin) and influencer outreach are paid-media work; defer to `find-marketing-agency` or refuse for marketplace product questions.
- **PR-software comparisons** (Cision, Muck Rack, Prowly) are NOT procurement.
- **Briefs DO include `apex`, `name`, location, ratings.** They DON'T include `url`, `phone_primary`, `email_primary`, `legal_name`, `address_full`, full `platforms` — those require an unlock.
- **`not_found` / `not_in_dataset` 404 = not in `pro_services`.** Not charged. Skip.
- **Unlock is atomic.** 5 apexes either all charge (up to 50 credits) or none charge on 402.
- **Within-TTL re-views are free** (`was_cached:true`).

## Errors

JSON envelope: `{"error": {"code": "...", "message": "..."}}`.

| Status | Code | What to do |
|---|---|---|
| 400 | `filter_parse_error` | `position` included; fix and re-validate with `/check`. |
| 400 | `kind_in_filter` | Strip any `kind:` from filter — URL is authoritative. |
| 400 | `field_not_in_dataset` | Drop the disallowed field. |
| 400 | `invalid_apex` | Re-normalize to apex domain. |
| 401 | `unauthorized` / `invalid_audience` | Re-prompt for fresh `vk_…`. |
| 402 | `insufficient_credits` | `needed` and `balance` in payload; nothing charged. |
| 404 | `not_found` / `not_in_dataset` | Skip; not charged. |
| 429 | `rate_limited` | Honor `Retry-After`. |

## End-to-end example

User: *"Three tech PR agencies in NY for a Series-B announcement,
ideally with 4-star ratings and Fortune 500 client experience."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=service_provided:public-relations+tech+state:NY+rating>=4
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
