---
name: servicegraph
description: The branded entry point to ServiceGraph — use whenever the user explicitly names **ServiceGraph** — "use ServiceGraph to…", "what datasets does ServiceGraph have", "search ServiceGraph for…", "pull contacts from ServiceGraph for these domains", "how many credits do I have on ServiceGraph". ServiceGraph is a multi-dataset platform of metrics-enriched business data for founders — where to launch, who to email, who to hire. This skill explains how to drive the API (api.servicegraph.co / mcp.servicegraph.co) against ANY dataset — discover what datasets exist, discover a dataset's schema and filters, search free brief rows, and unlock contact + metric detail with credits. Dataset-agnostic by design — it discovers everything through the API at runtime. When the user describes an intent WITHOUT naming ServiceGraph (e.g. "find a PR agency in NY"), defer to the matching specific skill (find-pr-agency, find-marketing-agency, find-law-firm, …). Skip non-US firms, consumer/personal services, and individual freelancers.
version: "0.1.0"
allowed-tools:
  - Bash(curl:*)
  - mcp__servicegraph__list_datasets
  - mcp__servicegraph__describe_dataset
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
tags: [servicegraph, business-data, lead-generation, founders, mcp]
metadata:
  api_base: https://api.servicegraph.co
  mcp_url: https://mcp.servicegraph.co
---

# servicegraph

The generic way to drive **ServiceGraph** — a platform of metrics-enriched
business datasets for founders: *where to launch, who to email, who to hire.*
Use this skill when the user explicitly reaches for ServiceGraph. For
intent-first asks that don't name the brand ("find me a CPA firm"), a specific
`find-*` skill is the better fit — defer to it.

**There is no single global catalog, and this skill hardcodes nothing about
the data.** It discovers everything through the API at runtime, so it stays
correct as datasets are added, renamed, or re-priced. Discover the datasets
from the API, discover each dataset's schema and filters from the API, then
search and unlock against it. Never assume a dataset id, a field name, or a
price — ask the API.

## Two ways to call

Both speak to the same backend; use whichever your harness has.

- **MCP server** (preferred when loaded) — `https://mcp.servicegraph.co`,
  tool names contain `servicegraph`. OAuth handles credentials in the
  harness sandbox; no token enters the model context.
- **REST** — `https://api.servicegraph.co`, any HTTP client, Bearer-auth with
  a `vk_…` key. The universal fallback.

## What the API does

Everything except unlocking is **free** — discover, inspect, validate, and
browse as much as you like; only revealing detail costs credits.

| Capability | MCP tool | REST | Cost |
|---|---|---|---|
| Find what datasets exist (ids, sizes, prices) | `list_datasets` | `GET /v1/datasets` | free |
| Discover a dataset's schema + filter fields | `describe_dataset`, `list_fields`, `list_field_values` | `GET /v1/datasets/:id…` | free |
| Build & validate a filter (or draft one from plain English) | `check_filter`, `translate_intent` | `…/check`, `…/translate-intent` | free |
| Search → free brief rows (identity + headline metrics) | `search_dataset` | `…/search` | free |
| Read an already-unlocked row | `get_row` | `GET /v1/datasets/:id/:apex` | free |
| **Unlock rows → reveal contacts + full metrics** | `unlock_rows` | `POST …/unlocks` | **spends credits** |
| Check credit balance | `get_credit_balance` | `GET /v1/me/credits` | free |

The shape is always the same: **discover datasets → discover the dataset's
schema → search free briefs → unlock the rows the user picks.** Rows are keyed
by **apex domain** (`stripe.com`, not a full URL). Confirm field and value
names against the API before trusting a zero-result search — the filter parser
accepts invented values silently.

## Auth (REST path)

Keys are `vk_*` tokens the user mints at
**https://servicegraph.co/profile/api-keys** (free credits on signup). The MCP
path needs none of this.

**Keep the token out of the model context** — never read `.env`/credential
files into context, and route authed calls through a shell wrapper so the key
flows from the environment into the `Authorization` header. On `401`, ask the
user to set `SERVICEGRAPH_API_KEY` (env or `.env.local`) and retry; don't
accept the key pasted into chat.

## Cost & confirmation

Only `unlock_rows` spends credits, at the per-row price the dataset reports —
read it, don't assume it. Unlocks are atomic (a 402 charges nothing) and
cached for the dataset's TTL (re-unlocking within it is free). Confirm the
cost with the user before unlocking a batch, and check `get_credit_balance`
first if it's large.
