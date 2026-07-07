---
name: find-cybersecurity-firm
description: Use whenever the user wants to find, shortlist, vet, or enrich US cybersecurity firms — pen-testing/red team, security audits, vCISO, SOC 2 readiness, incident response, managed SOC, IAM, cloud security, and AppSec. Triggers on "find me a pen-testing firm for our SOC 2 audit", "shortlist three vCISO services for our healthcare-tech startup", "we need an incident response retainer", or "pull contact info for these 8 security firm domains", even when described indirectly (we got breached, prepare us for the compliance audit, get us SOC 2 ready). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Skip in-house security hires, "how do I patch CVE-X" or "configure firewall Y" DIY questions, security-product reviews (CrowdStrike vs SentinelOne, etc.), generic security knowledge questions, consumer/personal security advice, non-US firms, individual freelancers and bug-bounty hunters.
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
tags: [cybersecurity, service-providers, lead-generation, b2b, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  service: cybersecurity
---

# find-cybersecurity-firm

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US cybersecurity firms via the `pro_services`
dataset.

**Always pin `service_provided:cybersecurity`** — that's the only
relevant structured tag in the live catalog. Older docs and the
catalog source mention sub-tags like `pen-testing` and
`security-audit`, but in the current release **none of those exist as
separate tags** — `cybersecurity` is the broad catch-all and every
sub-type (pen-testing, red-team, vCISO, SOC 2 readiness, IR retainer,
IAM, cloud security, AppSec) is a keyword substring search on firm
text. Confirm via `/v1/datasets/pro_services/fields?include_values=1`
once per session.

The industry tag also drifts between releases — newer catalogs may
use `industry:cybersecurity`, older ones used `industry:security`.
Confirm the value via `/fields` and pin both `industry` and
`service_provided:cybersecurity` for safety.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## When NOT to use this skill

- **Consumer/personal cybersecurity** ("my Gmail got hacked", "how do I secure my home wifi") — the catalog is B2B procurement only.
- In-house security hires (Security Engineer, CISO, SOC analyst).
- DIY/configuration questions ("how do I patch CVE-X", "configure firewall rules", "review this Terraform").
- Security-product comparisons (CrowdStrike vs SentinelOne, EDR vendors, SIEM vendors).
- Generic security knowledge ("explain zero-trust", "what is OWASP Top 10").
- Non-US firms / individual freelance pen-testers / bug-bounty hunters.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm industry value name and `cybersecurity` is in `service_provided`. |
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

**Cybersecurity examples** (validate yours with `/check`; replace
`cybersecurity` with whatever `/fields` returns as the industry value):

```
industry:cybersecurity service_provided:cybersecurity
service_provided:cybersecurity pen-testing
service_provided:cybersecurity "security audit" "soc 2"
service_provided:cybersecurity vciso
service_provided:cybersecurity "incident response" retainer
service_provided:cybersecurity cloud aws
service_provided:cybersecurity "application security" sast
service_provided:cybersecurity rating>=4 has:clutch
service_provided:cybersecurity hipaa
```

The live catalog has no separate `pen-testing` / `security-audit` /
`appsec` tags — pin `service_provided:cybersecurity` and treat all
sub-types as keywords.

**Sub-type → keyword mapping** (all sub-types are keyword-only):

| User asks for | Use |
|---|---|
| Pen test / red team | `pen-testing`, `"red team"` |
| Security audit / assessment | `audit`, `assessment` |
| vCISO / fractional CISO | `vciso`, `"fractional ciso"` |
| SOC 2 readiness | `"soc 2"`, `readiness` |
| Incident response / forensics | `"incident response"`, `forensics`, `"ir retainer"` |
| Cloud security | `"cloud security"`, `aws`, `gcp`, `azure` |
| Identity / IAM | `iam`, `identity` |
| Application security / SAST/DAST | `"application security"`, `appsec`, `sast`, `dast` |
| Compliance frameworks | `pci`, `hipaa`, `"iso 27001"`, `nist` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`mandiant.com`, not
`www.mandiant.com/about`).

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

### A. Pen test for SOC 2

User: *"Pen-testing firm for our SOC 2 audit."*

```
GET /v1/datasets/pro_services/search?filter=service_provided:cybersecurity+pen-testing+"soc 2"&limit=10
# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. vCISO for a healthcare-tech startup

```
GET /v1/datasets/pro_services/search?filter=service_provided:cybersecurity+vciso+(healthcare OR hipaa)&limit=10
```

### C. Incident response retainer

User: *"Incident response retainer in case we get breached."*

```
GET /v1/datasets/pro_services/search?filter=service_provided:cybersecurity+"incident response"+retainer&limit=10
```

If thin, drop `retainer` — most IR firms offer retainer engagements as standard.

### D. Cloud security + AWS + HIPAA

```
GET /v1/datasets/pro_services/search?filter=service_provided:cybersecurity+cloud+aws+hipaa&limit=10
```

### E. Indirect intent — "we got breached"

User: *"We got hit with ransomware last week — we need help fast."*

That's emergency IR:

```
GET /v1/datasets/pro_services/search?filter=service_provided:cybersecurity+"incident response"+ransomware&limit=10
```

Skip validation; present briefs immediately given urgency.

### F. AppSec / SAST

```
GET /v1/datasets/pro_services/search?filter=service_provided:cybersecurity+"application security"+(sast OR "code review")&limit=10
```

### G. SOC 2 readiness ahead of enterprise sales

```
GET /v1/datasets/pro_services/search?filter=service_provided:cybersecurity+"soc 2"+(readiness OR preparation)&limit=10
```

### H. BYO apex list — enrich domains

User pastes 8–20 cybersecurity firm domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge).
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

## Gotchas

- **Always pin the cybersecurity service tag.** Without it, `pen-testing` / `vciso` / `appsec` keywords leak into IT-services rows that mention security.
- **Confirm the industry value name via `/fields`** — older catalogs used `industry:security`, newer ones may use `industry:cybersecurity`. Don't hardcode.
- **Refuse consumer-personal asks.** "My Gmail got hacked", "how do I secure my home wifi", "should I use a VPN" — not B2B procurement.
- **DIY/configuration questions** ("patch CVE-X", "configure firewall rules", "review this Terraform") are NOT procurement.
- **Security-product comparisons** (EDR, SIEM, identity providers) are NOT procurement either.
- **"Hire a security engineer / CISO" is recruiting**, not procurement of a firm. Refuse.
- **Bug-bounty / freelance pen-testers** are out of scope (catalog is firm-level only).
- **Sub-types are keyword-only.** Multi-word sub-types split into ANDed barewords unless quoted (`"incident response"` → one phrase).
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

User: *"Three pen-testing firms for our SOC 2 audit, 4-star ratings,
ideally with HIPAA experience for a healthcare-tech context."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=service_provided:cybersecurity+pen-testing+"soc 2"+hipaa+rating>=4
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
