# orcarouter-pack

> Claude Code skill pack for [OrcaRouter](https://www.orcarouter.ai) — the OpenAI-compatible AI gateway. 6 skills covering install/auth, hello-world, model routing, fallback reliability, agent security, and cost observability, all against the `https://api.orcarouter.ai/v1` endpoint.

**Install:** `/plugin install orcarouter-pack@claude-code-plugins-plus`

**Links:** [OrcaRouter](https://www.orcarouter.ai) · [Docs](https://docs.orcarouter.ai) · API base `https://api.orcarouter.ai/v1` · key prefix `sk-orca-`

---

## What's in the box

| Skill | When to use it |
|---|---|
| `orcarouter-install-auth` | First-time setup: export `ORCAROUTER_API_KEY`, verify connectivity, point the OpenAI SDK at `https://api.orcarouter.ai/v1`. |
| `orcarouter-hello-world` | First chat completion through the gateway, and reading the response format. |
| `orcarouter-model-routing` | Task-based model selection: `orcarouter/*` routers and fusion panels vs pinned provider-prefixed model IDs. |
| `orcarouter-fallback-reliability` | Resilience: server-side fallback chains (`extra_body.models`), client retries with backoff. |
| `orcarouter-agent-security` | Gateway-level zero-trust security for agents — prompt/response screening and tool-call governance attached to a scoped key. |
| `orcarouter-cost-observability` | Per-request cost (`usage.cost_usd` via opt-in header), spend aggregation per model/agent, and budget controls. |

Six skills, intentionally focused. OrcaRouter's surface is an OpenAI-compatible gateway with routing, failover, observability, guardrails, and agent-tool governance behind one endpoint; these six cover the operational paths an engineer actually wires up. For a specialized use case (e.g. fine-tuned model provisioning, advanced BYOK), open an issue.

## When NOT to use this pack

- **You only need a single provider directly**: use that provider's pack (`anthropic-pack`, `openai-*`, `groq-pack`, etc.) instead.
- **You want raw multi-provider routing with no gateway features**: OrcaRouter is a superset — if you don't need routing/failover/security, a plain provider endpoint is simpler.
- **You're already on another gateway** (e.g. OpenRouter): use that vendor's pack; this pack is OrcaRouter-specific.

## Prerequisites

- An OrcaRouter account with an API key (`sk-orca-...`) exported as `ORCAROUTER_API_KEY`
- No separate SDK — the OpenAI SDK points at OrcaRouter via `base_url="https://api.orcarouter.ai/v1"`
- `curl`/`jq`, or Python 3.8+ / Node.js 18+

See `orcarouter-install-auth` for the actual setup steps.

## Quick start

```bash
export ORCAROUTER_API_KEY="sk-orca-..."
```

```python
from openai import OpenAI
import os

client = OpenAI(
    base_url="https://api.orcarouter.ai/v1",
    api_key=os.environ["ORCAROUTER_API_KEY"],
)

r = client.chat.completions.create(
    model="orcarouter/fusion",
    messages=[{"role": "user", "content": "Say OK"}],
    max_tokens=200,
)
print(r.choices[0].message.content)
```

## Trigger examples

| You ask Claude | Skill that fires |
|---|---|
| "Set up OrcaRouter auth and verify my key" | `orcarouter-install-auth` |
| "Send a hello world to OrcaRouter" | `orcarouter-hello-world` |
| "Route this request to the best model" | `orcarouter-model-routing` |
| "Make my LLM calls resilient with fallback" | `orcarouter-fallback-reliability` |
| "Harden my agent against prompt injection" | `orcarouter-agent-security` |
| "Track what this gateway is costing me" | `orcarouter-cost-observability` |

## Security

OrcaRouter provides gateway-level, zero-trust security for AI agents: guardrails screen prompt/response text and the Agent Firewall governs tool calls, attached to a scoped key.

**Scope.** These controls apply to **model calls that cross the gateway** (`https://api.orcarouter.ai/v1`) — prompts, responses, model-emitted tool calls, MCP dispatch routed through the firewall gateway, and reported egress. A tool an agent runs entirely in-process (a local file read, an in-process library call) is invisible to the gateway until it is registered as an MCP server behind it or the firewall evaluate hook is called per action. Pointing an SDK at the gateway base URL covers the calls that already cross it; governing in-process tools is a code change. See the `orcarouter-agent-security` skill for the wiring, the configured-rule screening test, and the full trust-boundary discussion.

**Hosted data.** Request content crosses the gateway and is retained for routing, settled-cost lookup, and the guardrail/firewall audit feeds. Routed requests are forwarded to the upstream provider of the serving model under that provider's terms, and a fallback chain or fusion panel can reach more than one provider for a single call. Obtain organizational approval before routing sensitive or regulated data, and confirm retention and subprocessor terms against the account agreement. Claims and behavior are documented at [Securing AI agents with OrcaRouter](https://docs.orcarouter.ai/security/concepts/securing-ai-agents) and [Firewall verdicts](https://docs.orcarouter.ai/security/firewall/verdicts).

## License

MIT — see [`LICENSE`](./LICENSE) (Copyright (c) 2026 Kus Wardhanie), matching the `license: MIT` declared in every skill's frontmatter.

## Contribution and relationship disclosure

Contributed by Kus Wardhanie ([@kuswardhanietidims-svg](https://github.com/kuswardhanietidims-svg)), an engineer on the OrcaRouter team. The contributor/provider relationship is disclosed so reviewers can weigh the pack's vendor-specific claims accordingly; the maintainer may also request confirming this directly with the OrcaRouter organization — no credentials or private identity material are involved.
