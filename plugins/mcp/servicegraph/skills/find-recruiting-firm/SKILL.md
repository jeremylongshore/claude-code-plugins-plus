---
name: find-recruiting-firm
description: Use whenever the user wants to find, shortlist, vet, or enrich US recruiting and staffing firms — executive search/retained search, RPO, tech/sales/healthcare recruiting, contingent/contract staffing, and temp staffing. Triggers on "find me an executive search firm for a CFO search", "shortlist three retained-search boutiques in NY focused on tech", "we need RPO support for a 50-engineer hiring push", or "pull contact info for these 8 staffing firm domains", even when described indirectly (need help hiring at scale, executive recruiter for senior roles). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Skip when the user wants to hire someone as their own employee (job-board questions, in-house recruiter hires, "where should I post the role"), individual job-seekers looking for recruiters to represent them, candidate-side career coaching, non-US firms, individual freelance recruiters.
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
tags: [recruiting, staffing, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: hr_recruiting_staffing
---

# find-recruiting-firm

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US recruiting and staffing firms via the
`pro_services` dataset.

**This skill is for procuring an external recruiting/staffing firm**
to do hiring on the user's behalf. It is NOT for:
- recruiting an in-house employee (the user wants to hire someone for their own team — that's job-posting, not procurement),
- candidate-side asks (an individual job-seeker looking for someone to represent them).

Both share keyword overlap with the positive case ("recruiter", "hire"), so the boundary matters.

**Always pin `industry:hr_recruiting_staffing`.** Sub-types
(executive search, RPO, contingent staffing, temp, vertical
specializations) are NOT separate tags — sub-type specialization is
a keyword substring search on firm text.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## When NOT to use this skill

- "I want to hire a [role] for my team — where should I post the job?" → recruiting-an-employee.
- "Find me a recruiter to represent me in my job search" → candidate side.
- "Hire an in-house recruiter / Head of Talent" → recruiting an employee.
- "Help me write a job description" → DIY/do-the-work.
- ATS or HR-software comparisons (Greenhouse vs Lever, Workday).
- Career coaching for individual job-seekers.
- Non-US firms / individual freelance recruiters.

## MCP server (preferred for authed calls)

If your harness has the ServiceGraph MCP server loaded (tools
containing `servicegraph`), prefer those — OAuth 2.1 + PKCE keeps the
token in the harness sandbox. Otherwise use the REST flow below.

## API surface (dataset id: `pro_services`)

Every endpoint requires the bearer (`Authorization: Bearer vk_…`).
No anonymous tier.

| Endpoint | Cost | Use it for |
|---|---|---|
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `hr_recruiting_staffing` is in the `industry` value list. |
| `GET /v1/datasets/pro_services/check?filter=…` | free | Validate filter. |
| `POST /v1/datasets/pro_services/translate-intent` | free | `{intent}` → DSL filter + sanity count. |
| `GET /v1/datasets/pro_services/search?filter=…&limit=` | free | Brief firm cards + per-row unlock hint + total. |
| `GET /v1/datasets/pro_services/:apex` | free | One row brief; detail only if unlocked. |
| `POST /v1/datasets/pro_services/unlocks` | **10 credits / firm** | `{apexes:[...]}` ≤100; atomic; 30-day TTL on detail. |
| `GET /v1/me/credits` | free | Balance. |

**Cost model.** Discovery / validation / search / brief reads are
free. Detail (url, phone, email, social, address, full `platforms`
map) costs **10 credits per firm** and lasts **30 days**.

## Auth

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

## Filter DSL

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

**Recruiting-flavored examples** (validate yours with `/check`):

```
industry:hr_recruiting_staffing "executive search"
industry:hr_recruiting_staffing "retained search" state:NY tech
industry:hr_recruiting_staffing rpo state:CA
industry:hr_recruiting_staffing contingent staffing
industry:hr_recruiting_staffing healthcare state:TX,FL
industry:hr_recruiting_staffing sales saas
industry:hr_recruiting_staffing rating>=4 has:clutch
```

**Sub-type → keyword mapping**:

| User asks for | Add as keyword(s) |
|---|---|
| Executive search / retained search | `executive`, `retained` |
| RPO (recruitment process outsourcing) | `rpo`, `"recruitment process outsourcing"` |
| Contingent / contract staffing | `contingent`, `contract` |
| Temp / temporary staffing | `temp`, `temporary` |
| Tech recruiting | `tech`, `technical`, `engineering` |
| Sales recruiting | `sales` |
| Healthcare recruiting | `healthcare`, `clinical`, `nursing` |
| Finance / accounting recruiting | `finance`, `accounting` |
| Legal recruiting | `legal`, `attorney` |

## Identifying firms — `apex`

Firms are identified by their **apex domain** (`korn-ferry.com`, not
`www.korn-ferry.com/about`).

## Recipes

### A. Executive search for a CFO

```
GET /v1/datasets/pro_services/search?filter=industry:hr_recruiting_staffing+executive+search&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. Retained boutique in a state, vertical

```
GET /v1/datasets/pro_services/search?filter=industry:hr_recruiting_staffing+retained+state:NY+tech+-company_size_signal:large_50plus&limit=10
```

### C. RPO for a hiring surge

```
GET /v1/datasets/pro_services/search?filter=industry:hr_recruiting_staffing+rpo+(tech OR engineering)&limit=10
```

### D. Indirect intent — "scaling fast, need help hiring"

```
GET /v1/datasets/pro_services/search?filter=industry:hr_recruiting_staffing+(rpo OR contingent)&limit=10
```

Or use the translator:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "RPO or volume recruiting partner for a 50-engineer hiring push" }
```

### E. Vertical: healthcare staffing

```
GET /v1/datasets/pro_services/search?filter=industry:hr_recruiting_staffing+healthcare+state:OH,IL,MI,IN,WI,MN&limit=10
```

### F. Quality threshold + tech-sector

```
GET /v1/datasets/pro_services/search?filter=industry:hr_recruiting_staffing+executive+search+tech+rating>=4&limit=10
```

### G. BYO apex list — enrich domains

User pastes 8–20 staffing/recruiting firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge).
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin `industry:hr_recruiting_staffing`.** Without it, "recruiter" / "executive search" keywords leak into other industries.
- **Distinguish "find me a recruiting firm" (procurement, fires) from "find me a recruiter / hire a recruiter for our team" (recruiting-an-employee, refuses).** When ambiguous, lean on context: explicit firm/agency/RPO language or volume framing → procurement; "for our team" / "to post the job" / "I want to hire" → in-house hire.
- **Candidate-side asks** ("represent me as a candidate", "find me a job") are out of scope.
- **Career coaching for individuals** is a different need (and shares the `executive-coaching` keyword with management consulting). Refuse — this skill is firm-procurement.
- **Sub-types are keyword-only.** Multi-word sub-types split into ANDed barewords unless quoted (`"executive search"` → one phrase).
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

User: *"Three retained executive search firms in NY focused on tech
CFOs, ideally with 4-star ratings and a Clutch profile."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:hr_recruiting_staffing+retained+executive+state:NY+tech+rating>=4+has:clutch
GET /v1/datasets/pro_services/search?filter=...&limit=10
# Present briefs. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
GET /v1/me/credits
```
