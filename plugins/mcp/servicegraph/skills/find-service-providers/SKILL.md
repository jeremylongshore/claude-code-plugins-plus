---
name: find-service-providers
description: Use whenever the user wants to find, shortlist, vet, enrich, or research US professional-services firms — law, marketing, consulting, accounting, IT services, architecture, engineering, HR, PR, design, and similar B2B service providers. Triggers on requests like "find me a PPC agency in California", "shortlist three boutique IP law firms", "build a longlist of 50 mid-size IT consultancies", or "here are 12 agency domains — pull contact info and confirm which are US-based", even when the need is described indirectly without naming a category. Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog with filters for industry, services, location, size, ratings, and third-party listings. Skip when the user is asking for personal/consumer services for themselves (an individual's own legal, tax, or medical needs), non-US firms, individual freelancers, retail/ecommerce/SaaS-product companies, recruiting-an-employee tasks, or general web research that doesn't need a structured firm directory.
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
tags: [service-providers, professional-services, lead-generation, b2b, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
---

# find-service-providers

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US professional-services firms.

The API hosts several **datasets** behind a uniform per-dataset URL
shape (`/v1/datasets/:id/…`). This skill is for the agencies dataset —
**dataset id `pro_services`** — which holds 100k+ B2B service firms
classified across 22 industries with multi-tag service taxonomies,
location, size, and third-party rating signals.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

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

If your agent harness has the **ServiceGraph MCP server** loaded
(`https://mcp.servicegraph.co`) — recognizable by tool names
containing `servicegraph` — prefer those tools over raw HTTP. The
MCP server uses OAuth 2.1 + PKCE so the harness handles credentials
in its own sandbox and no token value ever enters the LLM context.
Otherwise, fall through to the REST flow described below.

### API surface

Every endpoint requires the bearer (`Authorization: Bearer vk_…`).
There is no anonymous tier.

| Endpoint | Cost | Use it for |
|---|---|---|
| `GET /v1/datasets` | free | Discover available datasets. |
| `GET /v1/datasets/pro_services` | free | Full schema for this dataset (brief vs detail fields, allowed filters, unlock price, TTL). |
| `GET /v1/datasets/pro_services/fields[?include_values=1&q=]` | free | Filter-field catalog + DSL grammar. Call this first per session. |
| `GET /v1/datasets/pro_services/values/:field[?q=&limit=&offset=]` | free | Enumerate values for one field (e.g. legal `industry` / `state` / `service_provided` values). |
| `GET /v1/datasets/pro_services/check?filter=…` | free | Validate a filter string. Returns `{valid, normalized}` or `{valid:false, error}`. |
| `POST /v1/datasets/pro_services/translate-intent` | free | Body `{intent, model?}`. LLM-translates plain English → DSL filter + sanity-check row count. |
| `GET /v1/datasets/pro_services/search?filter=…&limit=&offset=` | free | Brief firm cards + per-row `unlock` hint. No url, no phone, no email. |
| `GET /v1/datasets/pro_services/:apex` | free | One row: always brief; **detail block only if caller has an active unlock** for `(user, dataset, apex)`. Idempotent, never charges. |
| `POST /v1/datasets/pro_services/unlocks` | **10 credits / firm** | Body `{apexes: [...]}`, max 100. Atomic batch — either all uncached apexes unlock, or none do (402 if balance short). Already-unlocked rows return `was_cached:true` with no extra charge. Detail TTL: 30 days. Returns brief + detail + per-item billing. |
| `GET /v1/me/credits` | free | Current credit balance. |
| `GET /v1/me/credits/transactions[?limit=&offset=]` | free | Spend history; unlock rows carry `(dataset_id, apex, expires_at)`. |

**Cost model in one paragraph.** Discovery, validation, search, and
brief reads are free. Detail data (apex, full url, phone, email,
social, address, legal name, platforms map) costs **10 credits per
firm** and lasts **30 days**. Re-fetching an unlocked firm within the
TTL is free — both the detail GET and the unlock POST honor the
cache. Charges are atomic per `POST /unlocks` call: a 402 leaves
balance untouched.

### Auth

Tokens are `vk_*` API keys minted in the dashboard. The user creates
them themselves; this skill never sees raw email/password.

**Security model — keep the token out of the LLM context.**

- **Never** read `.env`, `.env.local`, or any other credential file
  into your context. The token's literal value must never appear in
  the conversation.
- Every authed call goes through a shell wrapper so the token flows
  from the user's environment / dotenv file into the
  `Authorization` header without round-tripping through the LLM.

**First-call resolution:**

1. **Just try the call.** Dispatch via shell, sourcing `.env.local`
   if present:

   ```bash
   ( set -a; [ -f .env.local ] && . ./.env.local; set +a;
     curl -sS -H "Authorization: Bearer $SERVICEGRAPH_API_KEY" \
          'https://api.servicegraph.co/v1/datasets/pro_services/fields' )
   ```

2. **On `401 unauthorized`**, prompt the user (don't accept the key
   in chat):

   > "I need a ServiceGraph API key. Open
   > **https://servicegraph.co/profile/api-keys**, sign in,
   > click **Create key**, and copy the `vk_…` value.
   >
   > Then either export it in your shell —
   > `export SERVICEGRAPH_API_KEY=vk_…` — or add the line
   > `SERVICEGRAPH_API_KEY=vk_…` to `.env.local` in this directory.
   > Tell me when done and I'll retry. Please don't paste the key
   > into chat — keep it out of the LLM context."

3. **After the user signals ready**, re-dispatch the same call. If a
   later call returns `401`, the key was revoked or rotated — re-prompt.

For the user's convenience: if `SERVICEGRAPH_API_KEY` is already set
or already in `.env.local`, the very first call will succeed and the
prompt step never happens.

### Filter DSL

One query parameter, GitHub-search-style.

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

1. **AND binds tighter than OR.** `a OR b c` parses as `a OR (b AND c)`.
   Use parens.
2. **Comma list = OR within one predicate.** `state:CA,NY,TX` matches
   any of the three.
3. **Negation is `-x` or `NOT x`.** Negative literals inside a comma
   list are **not** allowed: `state:CA,-NY` is rejected. Use
   `state:CA -state:NY`.
4. **Bareword = keyword search.** Any IDENT or NUMBER not followed by
   an operator becomes a free-text substring across name / brand /
   title / meta / legal_name. Multiple barewords AND. Wrap multi-word
   phrases in double quotes: `keyword:"foo bar"`. Punctuation
   (`& ' . ; ! ? * /` etc.) is silently dropped outside quotes, and
   stray commas are treated as ANDs — so paste-friendly inputs like
   `Cox, Castle & Nicholson` work without quoting.

**Field kinds you'll use most:**

- **categorical** — `industry`, `state`, `service_model`, `geography_served`, `company_size_signal`, `pricing_model` — op `:` only.
- **tag_set_with_evidence** — `service_provided` — `Map<tag, evidence∈{low,medium,high}>`. Op `:` with optional `@evidence`.
- **numeric** — `rating`, `review_count_total`, `founded_year`, `linkedin_employees`, etc. — ops `=`, `>=`, `<=`, `>`, `<`.
- **presence** — `has:phone`, `has:clutch`, `has:rating`, `has:linkedin_company`, etc.
- **keyword** — any bareword in the filter becomes a free-text substring across name / brand / title / meta / legal_name / linkedin company text.

**Examples** (validate yours with `/check`):

```
industry:marketing_agency service_provided:seo
dental industry:marketing_agency
industry:legal state:CA,NY -company_size_signal:solo
industry:management_consulting (service_provided:strategy-consulting@high OR service_provided:operations-consulting@high)
state:CA has:phone has:email
rating>=4 review_count_total>=20 has:clutch
industry:it_services NOT (service_provided:web-development OR service_provided:hosting)
"Cox, Castle & Nicholson"
```

Don't put `kind:` in the filter — the dataset URL is authoritative and
the API will reject it. Don't use fields outside this dataset's allowed
list either; `/check` will tell you which ones.

### Identifying firms — `apex`

Firms are identified by their **apex domain** (registered domain only:
`mckinsey.com`, not `www.mckinsey.com/about`). When the user gives you
URLs, strip to the apex before calling `/datasets/pro_services/:apex`
or `POST /unlocks`. The endpoint accepts any lowercase host-shaped
string; a 404 means the firm isn't in this dataset (no charge).

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

### A. Shortlist by industry + state

```
GET /v1/datasets/pro_services/search?filter=industry:legal+state:CA+-company_size_signal:solo&limit=20
# → 20 brief cards + total + per-row unlock.status; pick top 3 with user

# user agrees → unlocking 3 firms costs 30 credits, 30-day TTL
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
# → brief + detail (url, phone, email, social, address) for all 3
```

### B. Multi-tag service intersection

User: *"Marketing agency that does both branding and SEO at high evidence."*

```
GET /v1/datasets/pro_services/search?filter=industry:marketing_agency+service_provided:branding@high+service_provided:seo@high&limit=10
```

### C. Quality threshold

User: *"Consultancies with at least 4★ and 20+ reviews and a Clutch listing."*

```
GET /v1/datasets/pro_services/search?filter=industry:management_consulting+rating>=4+review_count_total>=20+has:clutch&limit=10
```

### D. Indirect intent — user describes a need without naming the category

User: *"I need someone to handle our open enrollment communications for 200 employees."*

That's HR/benefits comms. Either translate by hand or hand it to the
intent translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "open enrollment communications for 200 employees" }
# → {filter: "...", reasoning: "...", valid, normalized, count}
```

Then validate with `/check` and run `/search`. If the breakdown is
thin, broaden — drop the service tag, add adjacent industries, or
fall back to keyword.

### E. Keyword + structured filter

User: *"HIPAA-savvy IT consultancies in Texas."*

```
GET /v1/datasets/pro_services/search?filter=hipaa+industry:it_services+state:TX&limit=10
```

`hipaa` is a bareword keyword → substring match in firm text.

### F. BYO apex list — enrich domains the user already has

User pastes 12 domains. Two-step:

1. `GET /v1/datasets/pro_services/:apex` for each — free brief, 404
   for not-in-catalog (no charge). Flag misses to the user.
2. User picks the N they want fully enriched. One
   `POST /v1/datasets/pro_services/unlocks` with all of them =
   **10×N credits**, single atomic charge, single response with
   detail bundles.

Within the 30-day TTL, re-running step 2 is free for the same apexes.

## Gotchas

- **`looks_not_pro_services` / `not_in_dataset` 404 is not a bug.** A firm may exist in another dataset but 404 on `/datasets/pro_services/:apex` if its `kind` doesn't include `pro_services`. Skip and continue; not charged.
- **Briefs from `/search` do NOT include `apex` ... wait, they do.** Briefs include `apex` (and `name`, `industry`, `service_provided`, location, ratings). What they DON'T include: `url`, `phone_primary`, `email_primary`, `legal_name`, `address_full`, full `platforms` map. Those require an unlock.
- **Catalog is US-only B2B pro-services.** Refuse non-US asks rather than returning misleading partial matches. Refuse consumer-facing legal/financial requests (e.g. *"I need a divorce lawyer for personal matters"*) — the catalog is built for B2B procurement.
- **Always confirm legal field values via `/fields?include_values=1`.** Inventing `industry:law` instead of `industry:legal` returns zero results silently — the parser doesn't validate categorical values.
- **Multi-word phrases must be split or quoted.** `family law` parses as two AND'd keywords (`family` AND `law`); `"family law"` parses as a single phrase.
- **Unlock is atomic.** `POST /unlocks` with 5 apexes either charges 50 credits (or less if some were cached) or charges nothing on 402. Plan the batch — don't dribble single-apex calls.
- **Within-TTL re-views are free.** Re-running `POST /unlocks` for an apex that's still inside its 30-day TTL returns `was_cached:true` and no charge. Re-pagination of `/search` is free regardless.
- **`/translate-intent` is a convenience, not a contract.** It may return `filter:""` if the intent is too vague, or a filter that doesn't match what the user wanted. Always inspect `reasoning` and the sanity-check `count` before running `/search`.

## Errors

All errors return JSON: `{"error": {"code": "...", "message": "..."}}`.

| Status | Code | What to do |
|---|---|---|
| 400 | `filter_parse_error` | Payload includes `position`. Fix the filter, re-validate with `/check`. |
| 400 | `filter_required` | Empty filter where one is required. |
| 400 | `kind_in_filter` | The URL is authoritative — strip any `kind:` predicate from the filter. |
| 400 | `field_not_in_dataset` | The filter references a field this dataset doesn't expose. Drop it or pick a different dataset. |
| 400 | `invalid_apex` | Apex doesn't look like a domain. Re-normalize. |
| 401 | `unauthorized` / `invalid_audience` | Key missing/expired/wrong audience. Re-prompt for a new `vk_…` from `/profile/api-keys`. |
| 402 | `insufficient_credits` | Balance too low for the unlock batch. Response carries `needed` and `balance`. Surface to the user; nothing was charged. |
| 404 | `unknown_dataset` | Wrong dataset id in the URL. |
| 404 | `not_found` | Apex isn't in the catalog. Not charged. Skip and continue. |
| 404 | `not_in_dataset` / `apex_not_in_dataset` | Apex exists but its `kind` doesn't include `pro_services`. Not charged. Skip. |
| 429 | `rate_limited` | Honor `Retry-After` header. |

Authed responses carry `X-RateLimit-*` headers. `GET /me/credits` is
the source of truth for spend planning.

## End-to-end example

User: *"Find me three top management-consulting firms in California
focused on strategy, with strong third-party ratings."*

```
# 1. Discover fields once per session
GET /v1/datasets/pro_services/fields?include_values=1
# Confirms 'management_consulting', 'strategy-consulting', 'rating' are legal.

# 2. Validate the filter (free)
GET /v1/datasets/pro_services/check?filter=industry:management_consulting+state:CA+service_provided:strategy-consulting@high+rating>=4+review_count_total>=20

# 3. Search briefs (free)
GET /v1/datasets/pro_services/search?filter=...&limit=10
# → 10 brief cards + total + per-row unlock.status:'none'

# 4. Present briefs, get user's pick of 3. Tell them: "Unlocking 3
#    firms costs 30 credits and gives 30 days of detail access."

# 5. Atomic batch unlock (charges 30 credits, returns detail too)
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
# → brief + detail (url, phone, email, social, address, platforms) ×3

# 6. (Optional) Confirm remaining balance
GET /v1/me/credits
```

## Resources

- Upstream source: <https://github.com/nostrband/ServiceGraph>
- ServiceGraph API: <https://api.servicegraph.co> — keys at
  <https://servicegraph.co/profile/api-keys>
- Hub skill: `servicegraph` (this plugin) — the dataset-agnostic entry point
  when the user names ServiceGraph explicitly.
