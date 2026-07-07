---
name: find-ai-consultancy
description: Use whenever the user wants to find, shortlist, vet, or enrich US AI/ML/data consulting firms (consultancies) — AI/ML development, MLOps, generative AI / LLM apps (RAG, chatbots, agents), computer vision, NLP, recommendation systems, data engineering, BI/analytics. Triggers on "find an AI/ML consulting firm to build our recommendation engine", "shortlist three RAG/LLM consultancies for an enterprise chatbot", "compare three AI/ML consulting firms with strong ratings", or "pull contact info for these 8 AI consultancy domains", even when described indirectly (we want to use AI for X, deploy ML to production). Drives the ServiceGraph API (api.servicegraph.co) — a 100k+ US firm catalog filterable by industry, services, location, size, ratings. Defer to find-software-developer for general app/backend work where AI is just a feature. Skip in-house ML/data hires, LLM/AI-tool comparisons (ChatGPT vs Claude), "how do I fine-tune X" DIY questions, AI courses for individuals, non-US firms, individual freelancers.
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
tags: [ai-consulting, machine-learning, service-providers, lead-generation, servicegraph]
metadata:
  api_base: https://api.servicegraph.co
  dataset_id: pro_services
  industry: data_ai_consulting
---

# find-ai-consultancy

## Overview

Drive the **ServiceGraph API** (`https://api.servicegraph.co`) to find,
shortlist, and enrich US AI/ML and data consultancies via the
`pro_services` dataset. The catalog tags firms with
`industry:data_ai_consulting` and a 4-tag service sub-taxonomy:
`ai-ml-development` (the largest at ~12k firms), `data-analytics`,
`cloud-services`, and `api-integration`. There is **no
`data-engineering` or `business-intelligence` sub-tag** —
`data-analytics` covers both. Confirm exact tag names via
`/v1/datasets/pro_services/fields?include_values=1`.

**Always pin `industry:data_ai_consulting`.** This skill exists to
do that automatically — the user shouldn't have to think about catalog
taxonomy.

Any HTTP client works (curl, fetch, requests). Examples below use curl.

## Sibling skills — defer when scope is different

- **General application or backend dev that uses AI as a feature**
  (e.g. "build us a SaaS with an AI chatbot tab") → `find-software-developer`.
- **Web/site projects that include some AI** → `find-web-developer`.
- **AI-related marketing or content** → `find-marketing-agency`.

This skill is for engagements where the AI/ML/data work IS the
deliverable.

## When NOT to use this skill

- **Consumer AI courses or learning** ("find me an online course to learn ML").
- **AI/LLM product comparisons** ("ChatGPT vs Claude vs Gemini", "Cursor vs Copilot").
- **DIY/code tasks** ("how do I fine-tune Llama", "review this PyTorch loop").
- **In-house ML/data hires** (Machine Learning Engineer, Data Scientist).
- **Generic AI knowledge questions**.
- **Non-US firms** / **individual freelance ML engineers**.

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
| `GET /v1/datasets/pro_services/fields[?include_values=1]` | free | Confirm `data_ai_consulting` industry value and sub-tag names. |
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

1. **Try the call first** through a shell wrapper that sources
   `.env.local`:

   ```bash
   ( set -a; [ -f .env.local ] && . ./.env.local; set +a;
     curl -sS -H "Authorization: Bearer $SERVICEGRAPH_API_KEY" \
          'https://api.servicegraph.co/v1/datasets/pro_services/fields' )
   ```

2. **On `401`** prompt the user (don't accept the key in chat):

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

**AI-flavored examples** (validate yours with `/check`):

```
industry:data_ai_consulting service_provided:ai-ml-development
industry:data_ai_consulting service_provided:ai-ml-development@high state:CA
industry:data_ai_consulting service_provided:data-analytics pipelines
industry:data_ai_consulting llm rag
industry:data_ai_consulting "computer vision" healthcare
industry:data_ai_consulting mlops
industry:data_ai_consulting (service_provided:ai-ml-development OR service_provided:data-analytics)
industry:data_ai_consulting service_provided:ai-ml-development@high rating>=4 has:clutch
```

**Sub-niche → keyword/tag mapping**:

| User asks for | Use |
|---|---|
| AI/ML model building | `service_provided:ai-ml-development` |
| Data engineering / pipelines | `service_provided:data-analytics` + keywords `pipelines` / `engineering` (no `data-engineering` tag) |
| BI / analytics | `service_provided:data-analytics` (covers BI too — no separate `business-intelligence` tag) |
| Cloud architecture for data/ML | `service_provided:cloud-services` |
| API / data integration | `service_provided:api-integration` |
| LLM apps / RAG / agents | `llm`, `rag`, `agent` (keywords) |
| Generative AI | `"generative ai"`, `genai` |
| Computer vision | `"computer vision"`, `cv` |
| NLP / IDP / document understanding | `nlp`, `idp`, `"document understanding"` |
| MLOps / model deployment | `mlops`, `deployment` |
| Recommendation systems | `recommendation`, `recsys` |
| Predictive analytics / churn / forecasting | `predictive`, `forecasting`, `churn` |

### Identifying firms — `apex`

Firms are identified by their **apex domain** (`scaleai.com`, not
`www.scaleai.com/about`).

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

### A. AI/ML consultancy for a recommendation engine

User: *"AI/ML consultancy to build our recommendation engine for an ecommerce site."*

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+service_provided:ai-ml-development+recommendation+ecommerce&limit=10

# Present, get pick of 3. "Unlocking 3 = 30 credits, 30-day TTL."
POST /v1/datasets/pro_services/unlocks
  { "apexes": ["firm-a.com", "firm-b.com", "firm-c.com"] }
```

### B. RAG / LLM consultancies for a chatbot

User: *"Three RAG/LLM consultancies for an enterprise chatbot."*

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+(rag OR llm)+chatbot+enterprise&limit=10
```

If thin, drop `enterprise` and surface client-tier signals from the
unlocked detail later.

### C. Data engineering partner

User: *"Data-engineering partner to build our analytics pipelines."*

No `data-engineering` tag — `data-analytics` is the closest and
covers both BI and engineering. Pin the tag plus keyword:

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+service_provided:data-analytics+(pipelines OR engineering)&limit=10
```

### D. MLOps for model deployment

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+mlops&limit=10
```

### E. Indirect intent — "use AI to predict customer churn"

User: *"We want to use AI to predict customer churn — who can help us build that?"*

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+service_provided:ai-ml-development+(churn OR predictive)&limit=10
```

Or let the translator do the mapping:

```
POST /v1/datasets/pro_services/translate-intent
  { "intent": "AI consultancy to build customer churn prediction" }
```

### F. Computer vision + healthcare vertical

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+"computer vision"+healthcare&limit=10
```

### G. Quality threshold + Fortune 500 clients

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+service_provided:ai-ml-development@high+rating>=4+fortune&limit=10
```

"Fortune 500" as a structured filter isn't a thing — surface from
briefs or treat it as a keyword.

### H. Custom LLM agent for customer service

```
GET /v1/datasets/pro_services/search?filter=industry:data_ai_consulting+(llm OR agent)+("customer service" OR support)&limit=10
```

### I. BYO apex list — enrich domains

User pastes 8–20 AI consultancy domains:

1. `GET /v1/datasets/pro_services/:apex` per domain — free brief
   (404 = not in catalog, no charge).
2. User picks N to fully enrich. `POST /unlocks` = **10×N credits**,
   atomic, detail returned.
3. Re-runs within 30-day TTL are free.

A 404 here often means the firm is actually a SaaS product company
(many AI vendors brand as "AI services" but operate as a product) —
filtered out of the catalog.

## Gotchas

- **Always pin `industry:data_ai_consulting`.** Without it, `ai-ml-development` as a service tag surfaces IT firms that list AI as a sub-service.
- **Defer to `find-software-developer` for general dev that uses AI as a feature.** When the deliverable is a SaaS product or app and AI is one of several features, that's software-dev work; this skill is for engagements where AI/ML/data work IS the deliverable.
- **Catalog audit notes**: AI/ML-tagged firms have a higher historical rate of misclassification (some are SaaS products, some are B2C ed-tech). If an unlock returns a SaaS product, flag and skip rather than recommend.
- **Many sub-niches are keyword-only.** Multi-word sub-niches split into ANDed barewords unless quoted (`computer vision` → `computer` AND `vision`; `"computer vision"` → one phrase).
- **LLM-product comparisons (ChatGPT vs Claude vs Gemini) are NOT procurement** — refuse.
- **AI courses for individuals (Coursera, fast.ai) are NOT in the catalog** — refuse.
- **Briefs DO include `apex`, `name`, `industry`, `service_provided`, location, ratings.** They DON'T include `url`, `phone_primary`, `email_primary`, `legal_name`, `address_full`, full `platforms` — those require an unlock.
- **`not_found` / `not_in_dataset` 404 = not in `pro_services`.** Not charged. Skip.
- **Unlock is atomic.** N apexes either all charge (up to 10×N credits) or none on 402.
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

User: *"Three AI/ML consultancies to build a recommendation engine for
an ecommerce site, ideally with 4-star ratings and Fortune 500 clients."*

```
GET /v1/datasets/pro_services/fields?include_values=1
GET /v1/datasets/pro_services/check?filter=industry:data_ai_consulting+service_provided:ai-ml-development@high+recommendation+ecommerce+rating>=4
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
