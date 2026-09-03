# ADR: orcarouter-pack — model the pack on the existing OpenRouter pack, but focused

> In this repo, ADRs are filed per skill in `000-docs/` as `NNN-AT-DECR-<skill-slug>.md`.
> In this plugin, the ADR lives at `docs/ADR.md` — the sync mirrors it as-is.

**Author:** Kus Wardhanie
**Date:** 2026-08-30
**Status:** Accepted

## Context

`openrouter-pack` is the existing flagship gateway pack: 30 skills covering routing, fallbacks, cost, and multi-provider orchestration. OrcaRouter occupies the same conceptual slot — an OpenAI-compatible gateway that exposes a provider/model namespace — so the pack must look like a first-class sibling of `openrouter-pack`, not a generic "any OpenAI-compatible endpoint" passthrough (which would dilute the named-provider value and benefit every competitor equally).

The marketplace grading bar is deterministic: 8 frontmatter fields plus the required body sections. Any new pack must clear it per SKILL.md.

## Decision

We add a named `orcarouter-pack` that mirrors the `openrouter-pack` structure — `.claude-plugin/plugin.json`, `README.md`, `package.json`, `skills/<skill>/SKILL.md` with `references/` — but scoped to 6 focused skills rather than 30, following the `ga4-pack` "fewer, real, operational" precedent. Each skill targets the OrcaRouter endpoint (`https://api.orcarouter.ai/v1`) and the documented `orcarouter/*` and provider-prefixed model surface, and each declares least-privilege `allowed-tools` (no `Write`/`Edit`/`Grep`).

## Alternatives considered

| Alternative | Why rejected |
| ----------- | ------------ |
| A single generic "AI gateway" skill with `base_url` configurable | No OrcaRouter naming benefit; a generic passthrough helps every gateway and dilutes the brand — against the project's vendor-pack model |
| A 30-skill pack cloned from `openrouter-pack` | High maintenance, much content not live-verified; the operational core is 6 skills |
| Docs-only addition to an existing pack's README | OrcaRouter is a distinct gateway; it needs its own installable, discoverable pack |

## Consequences

**Positive:**

- OrcaRouter becomes a named, installable, discoverable first-class pack in the marketplace, parallel to `openrouter-pack`.
- Each skill cites the current OrcaRouter documentation for its API and security/cost claims.
- The security and cost skills surface OrcaRouter's differentiators (gateway-level guardrails/firewall, per-request cost).

**Negative / accepted tradeoffs:**

- The pack is 6 skills, not 30 — users needing deeper coverage (fine-tuning, BYOK) must wait or request additions.
- The author is an OrcaRouter engineer; the pack is unbiased in tone but OrcaRouter-branded, which is the point of a named vendor pack.

## Tool-permission scope

Every skill declares a least-privilege `allowed-tools`: `Read` plus scoped `Bash(curl:*)`, `Bash(python3:*)`, `Bash(node:*)`, `Bash(jq:*)` as the workflow needs. `Bash(curl:*)`/`Bash(jq:*)` are needed for the gateway round-trips; `Bash(python3:*)`/`Bash(node:*)` for the SDK examples. No `Write`/`Edit`/`Grep` and no bare `Bash` is granted — the skills make API calls and run example snippets, they do not edit files.

## Evidence and citations

Pack claims are written against the current OrcaRouter documentation, cited in each SKILL.md:

- Zero-markup billing: [Billing & usage](https://docs.orcarouter.ai/operations/billing-and-usage), [Introduction](https://docs.orcarouter.ai/introduction)
- Per-request cost (`usage.cost_usd`, opt-in header; `GET /v1/generation`): [Per-request cost](https://docs.orcarouter.ai/operations/per-request-cost)
- Gateway security (scoped keys, guardrails, firewall, default verdicts, no app change): [Securing AI agents](https://docs.orcarouter.ai/security/concepts/securing-ai-agents), [Firewall verdicts](https://docs.orcarouter.ai/security/firewall/verdicts)
- Model surface and routing: [Models](https://docs.orcarouter.ai/getting-started/models), [Auto Router](https://docs.orcarouter.ai/routing/auto-router), [Fusion](https://docs.orcarouter.ai/routing/fusion), [Model Fallbacks](https://docs.orcarouter.ai/routing/model-fallbacks), [Response Headers](https://docs.orcarouter.ai/routing/response-headers)
- Trust boundary of gateway inspection: [How OrcaRouter inspects requests](https://docs.orcarouter.ai/security/concepts/how-orcarouter-inspects)

## Manual trust review

See `orcarouter-agent-security/references/security-patterns.md` § Trust boundary for the manual review of the external routing and prompt-governance boundary: the gateway inspects calls that cross it (prompts, responses, model-emitted tool calls, MCP dispatches, reported egress); it does not see tools that run entirely in-process without contacting the gateway, and remote/tool-derived content must be treated as untrusted data governed by output-stage rules.
