# Integration Patterns

Use this guide when deciding how Hermes Tweet fits with browser-cookie skills,
official API examples, OpenClaw skills, MCP servers, and catalog listings. The
goal is to keep Hermes Tweet positioned as the Hermes Agent runtime path, not as
a replacement for every local X/Twitter tool.

## Positioning

Hermes Tweet is the native Hermes Agent plugin for X/Twitter work through
Xquik. It is best when the workflow needs:

- a Hermes plugin entry point from PyPI or GitHub
- `tweet_explore` catalog discovery before tool calls
- API-key managed reads through `tweet_read`
- explicit action gating through `tweet_action`
- the same toolset across Desktop, remote gateway, dashboard, TUI, CLI, cron,
  and CI smoke-test surfaces

Keep local browser-cookie skills as the local account/session path. Keep direct
official API examples as implementation references. Keep Hermes Tweet as the
managed Hermes Agent path for reads, monitoring, support triage, research,
launch checks, and approval-gated account actions.

## Complementary Routes

Browser-cookie skills:
Keep them for local browser sessions, media download, archive jobs, and
account-specific local state. Add Hermes Tweet when the workflow should run from
Hermes Desktop, a remote gateway, a dashboard-managed runtime, or unattended
cron without relying on a laptop Chrome session.

Official X API examples:
Keep them for direct OAuth or API implementation details. Add Hermes Tweet when
the agent should avoid raw OAuth handling and call managed Hermes tools through
`XQUIK_API_KEY`.

OpenClaw skills:
Keep them for OpenClaw-native browser workflows and SKILL.md discovery. Add
Hermes Tweet when a Hermes Agent user needs the same X/Twitter read or action
capability from a Hermes runtime.

MCP servers:
Keep them for MCP-native clients and tool schemas. Add Hermes Tweet when the
user wants a native Hermes plugin with slash commands, bundled skill guidance,
and Hermes plugin enablement.

Claude marketplace bridges:
Keep bridges that install Claude plugin marketplaces from a different agent
runtime as compatibility routes, not as catalog targets. Add Hermes Tweet to a
bridge only when the bridge has its own public marketplace or recommended-source
list. Otherwise, point bridge users to
`hermes plugins install Xquik-dev/hermes-tweet --enable` and the source-native
`.claude-plugin/plugin.json` metadata.

Codex marketplace bridges:
Keep Codex plugin catalogs as source-readiness routes when they require
`.codex-plugin/plugin.json` metadata, a root security policy, local icon, and
HOL Plugin Scanner evidence before listing. Add Hermes Tweet only after those
source gates are present and target duplicate checks are clean.

Skill catalogs and awesome lists:
Keep them for discovery and comparison. Add Hermes Tweet when the listing
accepts Hermes Agent plugins, X/Twitter skills, social automation tools, or
optional backend notes. Before opening a public submission, use
`docs/SUBMISSION_READINESS.md` to check fit, duplicates, wording, validation,
and public-safety requirements.

AI frameworks:
Treat framework repositories as adapter surfaces, not simple listing targets.
Research them with crawler and GitHub query families such as `AI agent framework
integrations tools`, `LangChain integrations tools`, `LlamaIndex tools
integrations`, `AutoGen extensions tools`, `Semantic Kernel plugins`,
`Pydantic AI tools integrations`, `Agno AI tools integrations`, `Haystack
components integrations`, `Mastra AI tools`, and `DSPy tools integrations`.
Open an external framework PR only when Hermes Tweet has a real
framework-native package, component, tool wrapper, graph node, or example that
matches the target contribution docs. Otherwise, add first-party Hermes Tweet
examples and keep the external repo as a revisit target.

Known framework repos to track:

| Framework | GitHub repo | Native route | Current Hermes Tweet action |
| --- | --- | --- | --- |
| LangChain | <https://github.com/langchain-ai/langchain> | Python or JS tool package in the target's integration style | Defer external PR until a tested Hermes Tweet tool adapter exists. |
| LlamaIndex | <https://github.com/run-llama/llama_index> | Reader, tool, or agent integration in the target's package layout | Defer external PR until a tested LlamaIndex adapter exists. |
| AutoGen | <https://github.com/microsoft/autogen> | Extension, tool, or sample agent matching AutoGen docs | Keep as first-party example route until a native extension exists. |
| Semantic Kernel | <https://github.com/microsoft/semantic-kernel> | Plugin or connector matching Semantic Kernel conventions | Keep as first-party example route until a native plugin exists. |
| Pydantic AI | <https://github.com/pydantic/pydantic-ai> | Typed tool function or integration example | Keep as first-party example route unless docs invite external packages. |
| Agno | <https://github.com/agno-agi/agno> | Toolkit or tool adapter | Keep as first-party example route until a native toolkit exists. |
| Haystack | <https://github.com/deepset-ai/haystack> | Component package or integration catalog entry | Best revisit target after a Haystack component package exists. |
| Haystack core integrations | <https://github.com/deepset-ai/haystack-core-integrations> | Community component package | Submit only with a working Hermes Tweet component and target tests. |
| Haystack integrations list | <https://github.com/deepset-ai/haystack-integrations> | Integration list entry | Submit only after a corresponding component package exists. |
| Mastra | <https://github.com/mastra-ai/mastra> | TypeScript tool or workflow integration | Keep as first-party example route until a native tool package exists. |
| DSPy | <https://github.com/stanfordnlp/dspy> | Module or example program | Keep as first-party example route unless docs invite external packages. |
| LangChain4j community | <https://github.com/langchain4j/langchain4j-community> | Java community integration module | Submit only after a Java Hermes Tweet adapter exists. |

Skip framework hits that are archived, app demos, product-owned wrappers,
MCP-only adapters, source mirrors, or repository analyzers. A missing root
license is not a blocker by itself; note it in the research record. An explicit
incompatible license still blocks outreach.

## Tool Choice

- Use `tweet_explore` first when a user asks what Hermes Tweet can do.
- Use `tweet_read` for public or account read routes that the catalog marks as
  read-safe.
- Copied endpoint URLs are fine, but Hermes Tweet matches only catalog-listed
  paths.
- Use `tweet_action` only when the user asks for posting, replies, DMs,
  follows, monitor changes, webhook changes, media changes, extraction jobs, or
  draw actions and actions are explicitly enabled.
- Keep `HERMES_TWEET_ENABLE_ACTIONS=false` for cron, gateway, research,
  monitoring, support triage, and other unattended sessions unless the workflow
  includes an explicit approval step.

## Outreach Copy

Use wording like:

- optional Hermes Agent backend for X/Twitter reads
- managed Hermes Agent X/Twitter toolset
- Hermes Desktop and remote gateway compatible X/Twitter plugin
- read-only by default, with explicit action gating
- complementary to local browser-cookie workflows

Avoid wording that implies Hermes Tweet replaces a target project, fixes a
target bug, bypasses platform rules, or removes the need for user approval on
account actions.
