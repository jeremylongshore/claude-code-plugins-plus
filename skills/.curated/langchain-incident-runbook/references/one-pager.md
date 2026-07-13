# langchain-incident-runbook — One-Pager

Triage a LangChain 1.0 / LangGraph 1.0 production incident at 3am without guessing — LLM-specific SLOs, a latency/cost/error-rate decision tree, and concrete remediations per symptom.

## The Problem

PagerDuty fires at 3:07am: "LangChain p95 latency > 10s for 5 minutes." You open LangSmith and see an agent running 25 iterations against `recursion_limit=25` default — the cost dashboard shows $400 in the last 10 minutes and climbing (P10). Or the p99 pattern shows a clean 800ms baseline with occasional 12s spikes — classic Cloud Run cold start on a Python + LangChain service with scale-to-zero, where p99 is 10x p95 (P36). Most teams do not have LLM-specific SLOs defined — they monitor HTTP status like a REST API, miss time-to-first-token entirely, and discover cost-per-request only when the monthly bill lands. There is no standard runbook: latency triage, cost-spike response, and provider-outage failover all require different first moves, and choosing wrong burns budget or makes the outage worse.

## The Solution

A triage decision tree with three root paths — latency / cost / error-rate — each with a 3-step diagnostic sequence and a first-response action. Canonical LLM SLO set (p95 TTFT <1s, p99 total <10s, error-rate <0.5%, cost-per-req <$0.05) with Prometheus burn-rate recording rules so you page on symptoms that map to user experience, not provider 200s. Provider-outage playbook wired to `.with_fallbacks(backup)` so failover is one config flip, not a code change. Agent-loop containment via `recursion_limit` tuning and middleware token-budget caps so runaway agents stop burning cost before the `GraphRecursionError`. Post-incident template with LangSmith trace URL, debug-bundle cross-ref, and user-facing status page entry. Pinned to LangChain 1.0.x / LangGraph 1.0.x, four deep references.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | On-call engineers responding to a LangChain/LangGraph production incident, SREs defining LLM SLOs for the first time, team leads writing the first LLM runbook |
| **What** | LLM SLO set + Prometheus burn-rate rules, triage decision tree (latency/cost/error-rate), provider outage playbook with `.with_fallbacks` failover, agent-loop containment via `recursion_limit` + middleware budgets, post-incident template, 4 references (llm-slos, latency-triage, cost-overrun-response, provider-outage-playbook) |
| **When** | During an active on-call page, in a post-mortem write-up, or writing your team's first LLM runbook — before the first 3am incident, not after |

## Key Features

1. **LLM-specific SLO set with burn-rate alerting** — p95 TTFT <1s, p99 total latency <10s, error-rate <0.5%, cost-per-req <$0.05, wired to Prometheus recording rules that page on 2%/5min (fast burn) and 10%/1h (slow burn), so alerts fire on user-visible regression, not provider-side 200s
2. **Triage decision tree with three root paths** — Latency spike → check provider status + cold starts (P36) + streaming; cost spike → check agent recursion (P10) + retry rate (P30) + token-use per req; error-rate spike → check provider 429/500 + auth + schema drift. Each path has a 3-step diagnostic with concrete LangSmith filters and a first-response action
3. **Provider outage playbook with one-flip failover** — Status page watchers (Anthropic, OpenAI), in-app canary probe, `ChatAnthropic`/`ChatOpenAI` circuit breaker, failover to `.with_fallbacks(backup)` from `langchain-rate-limits`. Includes user-comms template for the status page and internal Slack channel

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
