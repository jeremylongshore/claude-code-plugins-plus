# navan-incident-runbook — One-Pager

Structured incident response procedures for Navan travel platform disruptions, from booking failures to API outages.

## The Problem

Travel disruptions hit at the worst moments — a flight cancellation during a company offsite, expense sync failures before quarter close, or a full API outage during peak booking season. Without a documented runbook, teams scramble to find escalation paths, waste time on wrong troubleshooting steps, and miss Navan's built-in support tools like the Ava AI assistant.

## The Solution

This skill provides severity-classified incident response procedures covering the full spectrum of Navan disruptions. It includes triage steps with real API health checks, escalation paths to Navan support, mitigation strategies for each failure mode, and post-incident review templates. The runbook leverages Navan's Ava AI assistant as the first-line support channel before human escalation.

## Who / What / When

| Aspect | Details |
|--------|---------|
| **Who** | Travel admins, IT operations, on-call engineers supporting Navan integrations |
| **What** | Severity-classified runbook with triage scripts, escalation contacts, mitigation playbooks, and post-incident templates |
| **When** | Flight cancellations, booking API failures, expense sync errors, OAuth outages, Navan platform degradation |

## Key Features

1. **Severity Classification** — P1 through P4 with response time SLAs and escalation triggers
2. **Ava-First Triage** — Leverages Navan's AI assistant for rapid initial diagnosis before human support escalation
3. **API Health Checks** — curl-based probes against /authenticate and /get_user_trips to distinguish local vs platform issues

## Quick Start

See [SKILL.md](../SKILL.md) for full instructions.
