---
name: groq-incident-runbook
description: 'Execute Groq incident response: triage, mitigation, fallback, and postmortem.

  Use when responding to Groq-related outages, investigating errors,

  or running post-incident reviews for Groq integration failures.

  Trigger with phrases like "groq incident", "groq outage",

  "groq down", "groq on-call", "groq emergency", "groq broken".

  '
allowed-tools: Read, Bash(kubectl:*), Bash(curl:*)
version: 1.11.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
tags:
- saas
- groq
- incident-response
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
---
# Groq Incident Runbook

## Overview

Rapid incident response procedures for Groq API failures. Groq is a third-party inference provider -- when it goes down, your mitigation options are: wait, fall back to a different model, or fall back to a different provider.

This SKILL.md is the high-level flow. Deep, copy-paste-ready material lives in `references/`:

- [triage-and-diagnostics.md](references/triage-and-diagnostics.md) — severity table, the Quick Triage script, and the full decision tree.
- [mitigations.md](references/mitigations.md) — fallback-model routing (TypeScript), 429 rate-limit actions, 401 key rotation.
- [communication-and-postmortem.md](references/communication-and-postmortem.md) — Slack/status-page templates, evidence collection, postmortem template.

## Prerequisites

- `GROQ_API_KEY` exported in the environment you run the triage commands from.
- `curl` for API probes; `kubectl` only if you collect logs from a Kubernetes deployment.
- Access to [console.groq.com](https://console.groq.com) to rotate keys or upgrade the plan.
- A configured fallback provider (e.g. OpenAI) if you need to fail away from Groq entirely.

**Authentication:** every Groq API call in this runbook authenticates with a bearer token — `Authorization: Bearer $GROQ_API_KEY`. Keep the key in a secret manager, never inline; the evidence-collection step in [communication-and-postmortem.md](references/communication-and-postmortem.md) redacts `gsk_` tokens from logs before archiving.

## Instructions

Work the incident in five phases. Each phase points to the reference file with the exact commands.

1. **Classify severity.** Match user impact to the P1–P4 table in
   [triage-and-diagnostics.md](references/triage-and-diagnostics.md) — this sets your response-time budget (P1 < 15 min, P4 next business day).
2. **Triage.** Run the Quick Triage script (status reachability, auth, per-model availability, rate-limit headers). The one-line probe that starts most incidents:

   ```bash
   curl -s -o /dev/null -w "%{http_code}\n" \
     https://api.groq.com/openai/v1/models \
     -H "Authorization: Bearer $GROQ_API_KEY"
   ```

3. **Decide.** Walk the decision tree in
   [triage-and-diagnostics.md](references/triage-and-diagnostics.md) to turn the HTTP code (timeout / 401 / 429 / 5xx / slow) into an action path.
4. **Mitigate.** Apply the matching fix from [mitigations.md](references/mitigations.md): fallback-model routing for 5xx on one model, wait-or-reroute for 429, key rotation for 401, enable the fallback provider for a Groq-wide outage.
5. **Communicate & close.** Post the internal alert and status-page update, then after resolution collect evidence and write the postmortem — all in [communication-and-postmortem.md](references/communication-and-postmortem.md).

## Output

Running this runbook produces:

- A **triage verdict** — the HTTP status per model and whether the fault is Groq-side or ours.
- An **applied mitigation** — traffic routed to a healthy model or provider, or a rotated key.
- A **communication trail** — internal alert + external status-page message.
- An **evidence bundle** — `groq-incident-TIMESTAMP.tar.gz` containing `models.json` and redacted `app-logs.txt`.
- A **postmortem document** — timeline, root cause, and dated action items.

## Error Handling

| Issue | Cause | Solution |
|-------|-------|----------|
| Can't reach status.groq.com | Network issue | Use mobile or different network |
| All models failing | Groq-wide outage | Enable fallback provider (OpenAI, etc.) |
| Key rotation fails | No admin access | Escalate to team lead with console access |
| Fallback provider also down | Multi-provider outage | Degrade gracefully, show cached content |

## Examples

**Example — 429 on the primary model.** Triage shows `llama-3.3-70b-versatile: HTTP 429`
while `llama-3.1-8b-instant: HTTP 200`. The decision tree routes "one model 429 → route to a
different model," so you switch traffic to the 8B model per
[mitigations.md](references/mitigations.md), post a P3 internal alert, and file an action item
to add fallback routing. The fallback-routing function lives in
[mitigations.md](references/mitigations.md); the alert and postmortem templates are in
[communication-and-postmortem.md](references/communication-and-postmortem.md).

## Resources

- [Groq Status Page](https://status.groq.com)
- [Groq Error Codes](https://console.groq.com/docs/errors)
- [Groq Rate Limits](https://console.groq.com/docs/rate-limits)

## Next Steps

For data-handling and compliance procedures after an incident, see the `groq-data-handling` skill in this pack.
