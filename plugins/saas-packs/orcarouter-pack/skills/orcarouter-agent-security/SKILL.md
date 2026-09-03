---
name: orcarouter-agent-security
description: |
  Use OrcaRouter's gateway-level zero-trust security for AI agents: prompt and
  response screening and tool-call governance on the same endpoint. Use when
  hardening an agent against prompt injection, governing which tool calls an
  agent may make, or reviewing agent security posture. Triggers: "orcarouter
  security", "agent security", "guardrails", "prompt injection", "tool
  governance", "zero trust".
  Trigger with "orcarouter-agent-security" keywords like "orcarouter", "gateway", or the skill name.
allowed-tools: Bash(curl:*), Bash(python3:*), Bash(jq:*)
version: 1.0.0
license: MIT
author: Kus Wardhanie <kuswardhanietidims-svg@users.noreply.github.com>
tags:
- saas
- orcarouter
- security
- guardrails
- agent-security
- zero-trust
compatibility: Designed for Claude Code
---
# OrcaRouter Agent Security

## Overview

OrcaRouter runs gateway-level, zero-trust security for AI agents on the same endpoint it serves models from. A [scoped API key](https://docs.orcarouter.ai/security/keys/overview) binds a [guardrail](https://docs.orcarouter.ai/security/guardrails/overview) (screens prompt and response text) and an [Agent Firewall](https://docs.orcarouter.ai/security/firewall/overview) policy (governs tool calls and egress).

Enforcement happens at the gateway, so an agent's code keeps issuing the same OpenAI-shaped calls with no application change. This skill covers what to configure, how to verify a policy is active, and how to structure agent traffic so governance applies.

## Prerequisites

- An OrcaRouter API key (`sk-orca-...`) exported as `ORCAROUTER_API_KEY`
- An agent or application that sends traffic through the gateway
- Access to the OrcaRouter console to attach guardrail/firewall policies (Developer+ role)

## Instructions

1. Confirm your agent's traffic flows through `https://api.orcarouter.ai/v1` (the same endpoint for model calls and security).
2. Attach a guardrail policy and a firewall policy to the API key in the console.
3. For default-deny tool governance, set the firewall policy's `default_verdict` to `deny` and allow-list the tools the agent needs. A new policy defaults to `audit` — it observes and blocks nothing until you add rules.
4. Verify screening is active by sending a test prompt that should trip a rule and observing the typed error.
5. Structure agent calls with metadata (`request_id`, `agent`, `session`) so governance rules and audit events can key on them.

## How a policy binds to a key

A guardrail (`guardrail_id`) and a firewall policy (`firewall_policy_id`) attach to a scoped key. Every call that key makes is screened; editing the policy shifts every attached key on the next request. See [Bind policies to a key](https://docs.orcarouter.ai/security/keys/bind-policies).

## Verifying Screening Is Active

Send a request that should be blocked by an input-stage rule and check for the typed error. A `block` action returns **HTTP 400** with `error.code` set to `guardrail_blocked` (content) or `firewall_blocked` (a denied tool call on the inbound surface):

```bash
curl -s -w "\nHTTP %{http_code}\n" https://api.orcarouter.ai/v1/chat/completions \
  -H "Authorization: Bearer $ORCAROUTER_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{
    "model": "orcarouter/fusion",
    "messages": [{"role": "user", "content": "This is a benign test request."}],
    "max_tokens": 100
  }'
```

Branch on `error.code`, never on the message string. The security codes are [documented](https://docs.orcarouter.ai/security/reference/error-codes): `guardrail_blocked`, `firewall_blocked`, and `firewall_approval_pending`, all **HTTP 400**, all marked skip-retry (a block is deterministic — do not put these in a retry loop).

## Tagging Agent Traffic

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "List the repo files"}],
    max_tokens=200,
    extra_body={
        "metadata": {
            "agent": "code-assistant",
            "session": "sess_001",
            "request_id": "req_007",
        }
    },
)
```

Structured metadata lets gateway policies scope governance per agent or session, and correlates firewall events to the run that caused them.

## Output

With a policy attached, a request either completes normally (screening passed) or is rejected with a typed error (`guardrail_blocked` / `firewall_blocked` / `firewall_approval_pending`). Every evaluation lands in the guardrail Matches feed and firewall Events feed with its verdict, so you get an audit trail of what each agent was allowed to do.

## Examples

```text
# Input-stage block:
HTTP 400 {"error": {"code": "guardrail_blocked", "message": "request blocked by guardrail \"pii-shield\": rule ssn (block)"}}

# Firewall deny on a tool call (inbound surface):
HTTP 400 {"error": {"code": "firewall_blocked", "message": "tool \"shell.exec\" blocked by firewall: denied tool"}}

# Request passes:
{"choices": [{"message": {"content": "..."}}], "model": "openai/gpt-4o-mini"}
```

More agent-security patterns (default-deny allowlists, injection-test prompts, governance scoping): `references/security-patterns.md`.

## Error Handling

| HTTP | Cause | Fix |
|------|-------|-----|
| 400 | Request blocked by a guardrail/firewall policy | Adjust the prompt or the policy; branch on `error.code` |
| 401 | Invalid key | Verify `ORCAROUTER_API_KEY` |
| 429 | Rate limit or credit constraint | Respect `Retry-After` |

## Manual Trust Review

A reviewer asked for an explicit trust review of the external routing and prompt-governance boundary in this pack. Findings, based on the [How OrcaRouter inspects requests](https://docs.orcarouter.ai/security/concepts/how-orcarouter-inspects) doc:

**What is inside the boundary.** The gateway is a choke point between the agent and every model/tool/MCP dispatch/egress destination it routes through `https://api.orcarouter.ai/v1`. It sees every prompt, every response, every model-emitted `tool_calls` frame, every `tools/call` dispatched through the firewall MCP gateway, and every reported egress destination.

Guardrails (input/output text) and firewall (tool action) policies attach to a scoped key and apply to every call that key makes.

**What is outside the boundary.** The gateway does not see a tool that runs entirely inside the agent's process and never contacts it — a local file read, a library call, a subprocess the agent spawns directly. This pack's security skill does not claim otherwise; the skill directs agents to route MCP dispatch and network-calling tools through the gateway so those calls enter the governed path.

**How remote responses are treated as untrusted data.** Content an agent retrieves from an external source (a web page, a retrieved document, a tool result) is potential prompt-injection and is governed as untrusted: output-stage guardrails screen the model's reply that reacts to that content, and the firewall allow-list judges the *next* action on its own merits rather than trusting the agent's provenance.

The pack's test-prompt list (`Ignore previous instructions...`, DAN, etc.) verifies input screening is active; the reference notes that retrieved/tool content is not itself a trusted instruction channel.

**Recommendation to reviewers.** This boundary is inherent to a gateway security model — a gateway cannot enforce what never crosses it. Teams whose agents run consequential in-process tools should register them as MCP servers behind the gateway (or call the firewall evaluate hook) before relying on gateway governance as their only control. No change to this pack is required beyond what is documented here.

## Enterprise Considerations

- Default-deny is an explicit posture: set the firewall `default_verdict` to `deny` and allow-list what the agent needs — the gateway enforces it with no application changes
- A new firewall policy defaults to `audit`; roll out enforcing rules under [shadow mode](https://docs.orcarouter.ai/security/firewall/shadow-mode) before they block live traffic
- The gateway governs the calls that cross it. A tool that runs entirely inside your agent's process and never sends a message to the gateway is outside the boundary — route MCP dispatch and network-calling tools through the gateway to cover them
- Keep `request_id`/`agent` metadata on every call so the governance verdict is attributable
- Test guardrails in a staging console before enforcing in production

## References

- Injection-test prompts and default-deny allowlist patterns: `references/security-patterns.md`
- [Securing AI agents](https://docs.orcarouter.ai/security/concepts/securing-ai-agents) · [Security error codes](https://docs.orcarouter.ai/security/reference/error-codes) · [Firewall verdicts](https://docs.orcarouter.ai/security/firewall/verdicts) · [How OrcaRouter inspects requests](https://docs.orcarouter.ai/security/concepts/how-orcarouter-inspects)
