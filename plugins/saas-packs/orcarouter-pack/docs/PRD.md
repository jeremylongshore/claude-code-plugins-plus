# PRD: orcarouter-pack

**Author:** Kus Wardhanie
**Date:** 2026-08-30
**Status:** Active

## Problem

Engineers running Claude Code against multiple LLMs face three costs: (1) wiring each provider's SDK and base URL separately, (2) hand-rolling routing/fallback logic that every gateway user re-implements, and (3) securing AI agents against prompt injection and unauthorized tool calls with no built-in enforcement. Existing marketplace packs are provider-specific (`openrouter-pack`, `groq-pack`, `anthropic-pack`); none cover an OpenAI-compatible gateway that also ships guardrails and agent-tool governance on the same endpoint.

## Target users

| User | Context | Primary need |
| ---- | ------- | ------------ |
| Claude Code users on OrcaRouter | Setting up a new integration | Auth + connectivity in one place |
| Engineers routing across models | Choosing per-task models without hard-coding IDs | Routers / fusion panels with a visible resolved model |
| Production LLM app owners | Hardening calls against 429/5xx/outages | Fallback chains + retries |
| Agent builders | Governing what an agent may do | Guardrail + firewall policies on a scoped key |
| FinOps/observability | Tracking LLM spend | Per-request cost attribution |

## Success criteria

1. A new user can install the pack, export `ORCAROUTER_API_KEY`, and get a chat completion against `https://api.orcarouter.ai/v1` in under 10 minutes.
2. Each of the 6 SKILL.md files passes the marketplace-tier validator with the 8 required frontmatter fields and required body sections.
3. Each skill's API references match the current OrcaRouter documentation (cited in-file), with no unsupported product claims.

## Functional requirements

- **FR-1:** Provide `orcarouter-install-auth` — key setup and connectivity verification.
- **FR-2:** Provide `orcarouter-hello-world` — minimal chat completion and response-format reading.
- **FR-3:** Provide `orcarouter-model-routing` — router/fusion vs pinned provider-prefixed model selection.
- **FR-4:** Provide `orcarouter-fallback-reliability` — fallback chains and retry/backoff.
- **FR-5:** Provide `orcarouter-agent-security` — gateway screening and tool-governance guidance.
- **FR-6:** Provide `orcarouter-cost-observability` — per-request cost and spend aggregation.

## Out of scope

- Re-implementing OrcaRouter's console (budget controls, guardrail policy editing).
- Covering fine-tuned model provisioning or advanced BYOK flows — future additions on request.
- A generic "any OpenAI-compatible endpoint" skill — this pack is OrcaRouter-specific.
