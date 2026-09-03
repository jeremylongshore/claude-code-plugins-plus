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

OrcaRouter provides gateway-level, zero-trust security for AI agents: guardrails screen prompt/response text and the Agent Firewall governs tool calls, attached to a scoped key with no application code change. See the `orcarouter-agent-security` skill for the wiring. Claims and behavior are documented at [Securing AI agents with OrcaRouter](https://docs.orcarouter.ai/security/concepts/securing-ai-agents) and [Firewall verdicts](https://docs.orcarouter.ai/security/firewall/verdicts).

## License

MIT
