---
name: hermes-tweet
description: >-
  Uses Xquik from Hermes Agent for X research, monitoring, and approval-gated actions. Use when the user requests X data or an approved X action. Trigger with "search X", "monitor X", "post tweet", or "X trends".
allowed-tools:
  - tweet_explore
  - tweet_read
  - tweet_action
version: 0.1.6
author: Burak Bayır (@kriptoburak), Xquik
license: MIT
compatibility: Requires Hermes Agent plugin support and Xquik API access.
argument-hint: "[X task, endpoint, or approved action]"
tags:
  - hermes-agent
  - xquik
  - twitter
  - x
  - social-media
  - automation
metadata:
  version: 0.1.6
  author: Xquik
  tags:
    - hermes-agent
    - xquik
    - twitter
    - x
    - social-media
    - automation
required_environment_variables:
  - name: XQUIK_API_KEY
    prompt: Xquik API key
    help: Create an API key at https://dashboard.xquik.com
    required_for: tweet_read, /xstatus, /xtrends, and authenticated Xquik API calls
capabilities:
  shell:
    required: false
    justification: Optional Hermes CLI checks are used only for installation and registry diagnostics.
  network:
    required: true
    justification: Hermes Tweet tools call Xquik API routes for X/Twitter reads and approved actions.
  files:
    required: false
    justification: Normal use does not require local file reads or writes.
  environment:
    required: true
    variables:
      - XQUIK_API_KEY
      - HERMES_TWEET_ENABLE_ACTIONS
      - HERMES_ENABLE_PROJECT_PLUGINS
    justification: Runtime configuration controls authenticated reads, gated actions, and trusted project-local plugin loading.
  mcp:
    required: false
    justification: No MCP server access is required.
  tools:
    - tweet_explore
    - tweet_read
    - tweet_action
---

# Hermes Tweet

## Overview

Hermes Tweet solves X research and automation tasks without direct HTTP fallbacks
or guessed endpoints. It discovers catalog-listed Xquik routes, performs
authenticated reads, and keeps write-like or private operations behind an
explicit environment gate and user approval.

Use the skill for read-first workflows. Enable action tooling only for a named
operation whose endpoint, payload, account, and side effects the user approves.

## When to Use

Use this skill for Hermes Agent sessions that need X/Twitter data or controlled
X actions through the Hermes Tweet plugin.

Use this skill especially for social listening, launch monitoring, support
triage, creator research, brand research, giveaway audits, community audits,
and controlled publishing workflows.

Use `tweet_explore` first when the user asks for a capability, endpoint, route,
or Xquik API surface. Use `tweet_read` only after a read-only endpoint is known.
Use `tweet_action` only after the user requests a write, private read, monitor,
webhook, extraction job, giveaway draw, or media operation that requires action
permissions.

## Prerequisites

- Install and enable the plugin with
  `hermes plugins install Xquik-dev/hermes-tweet --enable`.
- Configure `XQUIK_API_KEY` on the Hermes runtime host for authenticated reads.
  `tweet_explore` remains available without the key or network access.
- Leave `HERMES_TWEET_ENABLE_ACTIONS` unset or false unless the workflow needs
  an approved write-like or private operation.
- For project-local plugins, set `HERMES_ENABLE_PROJECT_PLUGINS=true` only in a
  trusted repository.
- Restart a gateway after environment changes and start a new session. Active
  CLI sessions can use `/reload`.

## Permissions and Capabilities

- Use `tweet_explore`, `tweet_read`, and `tweet_action` only through the enabled
  Hermes Tweet toolset.
- Network access is limited to catalog-listed Xquik API routes reached by those
  tools. Do not create direct HTTP fallbacks.
- Shell access is not part of normal operation. Use Hermes CLI commands only for
  the install and registry checks listed in Testing.
- Local file access is not part of normal operation. Do not write reports,
  credentials, logs, screenshots, or cached API payloads unless the user asks
  for an explicit export workflow.
- Environment access is limited to configuration presence checks for
  `XQUIK_API_KEY`, `HERMES_TWEET_ENABLE_ACTIONS`, and
  `HERMES_ENABLE_PROJECT_PLUGINS`. Never request or echo their values.
- MCP access is not required.

## Instructions

1. Confirm the plugin is enabled with `hermes plugins list` and confirm tool
   registration with `hermes tools list`.
2. Use `tweet_explore` to find the catalog endpoint and method.
3. Use `tweet_read` for public read-only endpoints after the API key is
   configured.
4. Before `tweet_action`, state the exact endpoint, payload, account, reason,
   and expected side effects, then get explicit approval.
5. Verify the tool response. Report policy, authentication, validation, or
   account errors without retrying through alternate routes.

## Decision Rules

- IF the task is endpoint discovery, THEN call `tweet_explore` with a short
  query.
- IF the endpoint method is `GET` and the catalog does not mark it as an
  action, THEN call `tweet_read`.
- IF the endpoint method is not `GET`, or the route touches private account
  state, THEN call `tweet_action` only when actions are enabled and the user has
  approved the operation.
- IF `tweet_action` is unavailable or disabled, THEN explain that action tools
  are intentionally gated by `HERMES_TWEET_ENABLE_ACTIONS=true`.
- IF `XQUIK_API_KEY` is missing, THEN ask the user to set it in the Hermes
  runtime environment without requesting the key value in chat.
- IF Hermes lists the plugin as `not enabled`, THEN tell the user to run
  `hermes plugins enable hermes-tweet` or reinstall with `--enable`.
- IF the plugin is installed as a project-local `.hermes/plugins/` copy, THEN
  remind the user that Hermes requires `HERMES_ENABLE_PROJECT_PLUGINS=true` for
  trusted repositories.
- IF the task is unattended, scheduled, gateway-driven, or cron-driven, THEN
  prefer `tweet_read` and keep `tweet_action` disabled unless the workflow has a
  clear approval step.
- IF the user is in Hermes Desktop with a remote gateway profile, THEN remind
  them that Hermes Tweet must be installed, enabled, and configured on the
  remote Hermes host where plugin tools execute.
- IF the user uses the Hermes dashboard for gateway administration or
  credentials, THEN keep Hermes Tweet secrets in the runtime environment and do
  not ask for key values in chat.

## Safety

- Never ask for or reveal API keys, signing keys, passwords, cookies, or TOTP secrets.
- Never pass credentials in tool arguments.
- Use only catalog-listed `/api/v1/...` endpoints.
- Copied endpoint URLs are accepted only when they resolve to catalog-listed paths.
- Do not use account connection, re-authentication, API key, billing, credit top-up, or support-ticket endpoints.
- For posting, deleting, following, DMs, profile changes, monitors, webhooks, extraction jobs, and draws, summarize the action before calling `tweet_action`.

## Known Risks and Mitigations

- Risk: A broad X/Twitter request may map to a write-capable route.
  Mitigation: Start with `tweet_explore`, prefer `tweet_read`, and require a
  user-approved endpoint plus payload before `tweet_action`.
- Risk: Secrets may be pasted into chat or examples.
  Mitigation: Ask only for environment configuration, never for key values, and
  never put credentials in tool arguments.
- Risk: Endpoint guessing may bypass catalog review.
  Mitigation: Accept only catalog-listed `/api/v1/...` paths and reject direct
  HTTP fallbacks.
- Risk: Automated X/Twitter actions can affect real accounts.
  Mitigation: Keep `HERMES_TWEET_ENABLE_ACTIONS=false` by default and summarize
  side effects before any account-changing call.

## Output

- Output type: endpoint selection, API-result summaries, action previews, and
  troubleshooting guidance.
- Output format: concise Markdown for humans and JSON-like tool payloads for
  Hermes Tweet calls.
- Side effects: `tweet_explore` has no external side effects, `tweet_read`
  performs authenticated reads, and `tweet_action` may change account or
  workflow state only after explicit approval.

## Error Handling

Use the narrowest recovery step that preserves the read-first and action-gated
contract:

- Missing tool: confirm the plugin is enabled, then run `hermes tools list`.
- Missing API key: configure `XQUIK_API_KEY` on the runtime host without pasting
  its value into chat, then run `/reload` in an active CLI session or run
  `hermes gateway restart` and start a new gateway session.
- Unknown endpoint: call `tweet_explore` again. Never guess paths or create a
  direct HTTP fallback.
- Disabled action: keep the action blocked unless the user requested it and
  `HERMES_TWEET_ENABLE_ACTIONS=true` is intentionally configured.
- Policy, authentication, validation, or account error: return the sanitized
  failure and corrective step. Do not retry through another route.
- Missing slash command: verify it in an active Hermes session or plugin
  registry test rather than treating prompt text as registration proof.
- Secret in input: stop and ask the user to rotate it before continuing.

## Examples

**Example: Search tweets**

```json
{"query":"tweet search","method":"GET"}
```

Then call:

```json
{"path":"/api/v1/x/tweets/search","query":{"q":"AI agents","limit":25}}
```

**Example: Inspect trends**

Run `/xtrends` in an active Hermes session. Use `tweet_explore` when the task
needs a catalog endpoint or structured response instead of the slash command.

**Example: Post a tweet**

```json
{"query":"post tweet","include_actions":true}
```

Then call `tweet_action` with:

```json
{"path":"/api/v1/x/tweets","method":"POST","body":{"account":"@example","text":"Hello from Hermes Tweet"},"reason":"Post the user-approved tweet."}
```

## Testing

After installing or upgrading the plugin in Hermes Agent:

1. Run `hermes plugins enable hermes-tweet` unless the install used `--enable`.
2. Run `hermes plugins list` and confirm the plugin is `enabled`.
3. Run `hermes tools list` and confirm the `hermes-tweet` toolset is enabled.
4. Confirm `tweet_explore` is available without `XQUIK_API_KEY`.
5. Confirm `tweet_read` appears only when `XQUIK_API_KEY` is configured.
6. Confirm `tweet_action` stays hidden or disabled unless `HERMES_TWEET_ENABLE_ACTIONS=true`.

Useful CLI checks:

```bash
hermes plugins enable hermes-tweet
hermes tools list
```

## Release Trust Gate

Before presenting this skill as NVIDIA-verified or ready for broad enterprise
deployment:

1. Run SkillSpector against the complete skill directory and resolve critical or
   high findings.
2. Complete `skill-card.md` with owner, license, use case, deployment
   geography, risks, references, output shape, and release version.
3. Include Tier-3 eval data and `BENCHMARK.md` for the reviewed release.
4. Sign the exact reviewed skill directory and publish `skill.oms.sig`.
5. Verify the published directory with the expected certificate chain.

Do not claim NVIDIA verification when those release artifacts are absent.

## Resources

- [Endpoint and approval contract](references/endpoint-contract.md)
- [Skill card](skill-card.md)
- [Hermes Tweet repository](https://github.com/Xquik-dev/hermes-tweet)
- [Hermes Agent plugin guide](https://github.com/NousResearch/hermes-agent/blob/main/website/docs/user-guide/features/plugins.md)
- [Xquik Hermes Tweet guide](https://docs.xquik.com/guides/hermes-tweet)
