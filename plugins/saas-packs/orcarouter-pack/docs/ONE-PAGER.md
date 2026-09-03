# orcarouter-pack

**Claude Code skills for OrcaRouter — the OpenAI-compatible AI gateway with routing, fallback, observability, guardrails, and agent-tool governance behind one endpoint.**

## Problem

Engineers on Claude Code who use multiple LLMs re-implement routing, fallback, cost tracking, and agent security on every project. Existing marketplace packs are single-provider; none cover a gateway that does routing **and** security **and** cost observability on one OpenAI-compatible endpoint.

## Solution

A named `orcarouter-pack` with 6 focused skills against the `https://api.orcarouter.ai/v1` endpoint: install/auth, hello-world, model routing, fallback reliability, agent security, and cost observability. Users get OrcaRouter as a first-class option — not an anonymous custom base URL.

## W5

| | |
| - | - |
| **Who** | Claude Code users and teams routing across models, hardening agents, or tracking LLM spend |
| **What** | 6 SKILL.md files with real API calls to `https://api.orcarouter.ai/v1` |
| **When** | Setting up OrcaRouter, choosing models per task, adding resilience, governing agents, or watching cost |
| **Where** | Runs in Claude Code; all requests go through the OrcaRouter gateway |
| **Why** | Named, installable — parallel to `openrouter-pack` |

## Stack

| Layer | Choice |
| ----- | ------ |
| Skill runtime | Claude Code SKILL.md |
| Client | OpenAI SDK (base_url override) / cURL + jq |
| External APIs | `https://api.orcarouter.ai/v1` |

## Differentiators

1. **Named first-class gateway pack** — parallel to `openrouter-pack`, not a generic passthrough.
2. **Gateway security + cost on the same endpoint** — skills cover guardrail/firewall tool governance and per-request cost (`usage.cost_usd` opt-in + `GET /v1/generation`), which provider packs don't.

## Evidence and citations

Pack claims are written against the current OrcaRouter documentation:

- Zero-markup billing: [Billing & usage](https://docs.orcarouter.ai/operations/billing-and-usage), [Introduction](https://docs.orcarouter.ai/introduction)
- Per-request cost field name and opt-in header: [Per-request cost](https://docs.orcarouter.ai/operations/per-request-cost)
- Gateway security (guardrails, firewall, scoped keys, no app change): [Securing AI agents](https://docs.orcarouter.ai/security/concepts/securing-ai-agents), [Firewall verdicts](https://docs.orcarouter.ai/security/firewall/verdicts)
- Routing / routers / fallback chains: [Models](https://docs.orcarouter.ai/getting-started/models), [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks), [Response Headers](https://docs.orcarouter.ai/routing/response-headers)

The agent-security skill includes a manual trust review of the routing and prompt-governance boundary (what the gateway sees and does not see); see `orcarouter-agent-security/references/security-patterns.md` § Trust boundary.
