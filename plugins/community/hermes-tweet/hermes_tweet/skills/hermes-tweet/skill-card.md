# Hermes Tweet Skill Card

Status: public self-assessment. Not NVIDIA-verified.

Do not present Hermes Tweet as NVIDIA-verified unless the release also includes
a clean SkillSpector scan report, Tier-3 eval data, `BENCHMARK.md`,
`skill.oms.sig`, and signature verification instructions for the exact reviewed
skill directory.

## Owner

- Publisher: Xquik
- Repository: https://github.com/Xquik-dev/hermes-tweet
- License: MIT
- Version: 0.1.6
- Primary skill file: `SKILL.md`

## Use Case

Hermes Tweet helps Hermes Agent users find X/Twitter endpoints, perform
authenticated X/Twitter reads, and run explicitly approved X/Twitter workflow
actions through the bundled Hermes Tweet tools.

Use it for:

- Searching tweets, reading tweet details, replies, and user profiles.
- Preparing action previews for posts, replies, follows, direct messages,
  monitors, webhooks, extraction jobs, media workflows, and giveaway draws.
- Keeping X/Twitter automation inside catalog-listed Xquik API routes.

Do not use it for account connection, re-authentication, billing, credit top-up,
support tickets, or direct HTTP fallback routes.

## Inputs and Configuration

- Required configuration: `XQUIK_API_KEY` must be configured in the runtime
  environment. Never request, echo, log, or store the value.
- Action gate: `HERMES_TWEET_ENABLE_ACTIONS=true` is required before
  write-capable tool calls.
- Project plugin gate: `HERMES_ENABLE_PROJECT_PLUGINS=true` is required for
  trusted local Hermes project plugin loading.
- User input: natural language requests, endpoint choices, and explicit action
  payload approval.

## Capabilities

- Tools: `tweet_explore`, `tweet_read`, `tweet_action`.
- Network: required only through catalog-listed Xquik API routes reached by
  those tools.
- Shell: not required for normal operation. Use Hermes CLI commands only for
  installation and registry diagnostics.
- Files: not required for normal operation. Do not write reports, credentials,
  logs, screenshots, or cached payloads unless the user asks for an explicit
  export workflow.
- MCP: not required.

## Outputs

- Endpoint recommendations from `tweet_explore`.
- Concise summaries of authenticated read results from `tweet_read`.
- Action previews, JSON-like payloads, and post-call summaries for
  user-approved `tweet_action` calls.
- Troubleshooting guidance for missing configuration or disabled action gates.

## Side Effects

- `tweet_explore` has no external side effects.
- `tweet_read` performs authenticated reads.
- `tweet_action` may change account or workflow state only after explicit user
  approval and only when the action gate is enabled.

## Known Risks and Mitigations

- Risk: a broad X/Twitter request may map to a write-capable route.
  Mitigation: start with `tweet_explore`, prefer `tweet_read`, and require a
  user-approved endpoint plus payload before `tweet_action`.
- Risk: secrets may appear in chat or examples.
  Mitigation: ask only for environment configuration, never key values, and
  never put credentials in tool arguments.
- Risk: endpoint guessing may bypass catalog review.
  Mitigation: accept only catalog-listed `/api/v1/...` paths and reject direct
  HTTP fallbacks.
- Risk: automated X/Twitter actions can affect real accounts.
  Mitigation: keep `HERMES_TWEET_ENABLE_ACTIONS=false` by default and summarize
  side effects before any account-changing call.

## Release Trust Gate

Before broad enterprise release or any NVIDIA-verified claim:

1. Run SkillSpector against the complete skill directory.
2. Resolve critical or high findings.
3. Add Tier-3 eval data and `BENCHMARK.md` for the reviewed release.
4. Sign the exact reviewed skill directory and publish `skill.oms.sig`.
5. Verify the published directory with the expected certificate chain.

## References

- `SKILL.md`
- `README.md`
- `after-install.md`
- `SECURITY.md`
