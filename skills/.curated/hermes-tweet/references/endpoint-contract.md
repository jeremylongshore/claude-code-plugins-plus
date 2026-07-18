# Endpoint and Approval Contract

Use this reference when the selected Xquik route or approval boundary is
unclear. The rules apply to CLI, Desktop, dashboard, gateway, scheduled, and
delegated Hermes Agent sessions.

## Tool Matrix

| Tool | API key | Network | Action gate | User approval |
|---|---:|---:|---:|---:|
| `tweet_explore` | No | No | No | No |
| `tweet_read` | Yes | Yes | No | No for public read-only routes |
| `tweet_action` | Yes | Yes | Yes | Yes for the exact operation |

`tweet_explore` reads the bundled catalog. `tweet_read` accepts only
catalog-listed read-only routes. `tweet_action` handles writes, private reads,
monitors, webhooks, extraction jobs, giveaway draws, and media operations.

## Approval Checklist

Before calling `tweet_action`, state and confirm:

1. The catalog-listed endpoint and method.
2. The target account or workflow.
3. The complete payload without credentials.
4. The expected side effects and reason.
5. The user's explicit approval for this operation.

Approval for one operation does not authorize retries, related operations, or
future scheduled runs. Stop after policy, authentication, validation, or
account-state failures.

## Hermes Agent Surfaces

Hermes Tweet uses the same plugin entry point across Desktop, TUI, CLI,
dashboard, and gateway sessions. Install and configure the plugin on the Hermes
runtime host where tools execute. Remote Desktop profiles do not move secrets or
plugin state from the gateway host.

Use active CLI or gateway sessions for `/xstatus` and `/xtrends`. Keep
`HERMES_TWEET_ENABLE_ACTIONS=false` unless the session intentionally permits an
approved account-changing operation.

## Runtime Checks

```bash
hermes plugins list
hermes tools list
```

Confirm that `tweet_explore` remains available without `XQUIK_API_KEY`,
`tweet_read` appears only with the key, and `tweet_action` remains unavailable
unless `HERMES_TWEET_ENABLE_ACTIONS=true` is intentionally configured.

After environment changes, reload an active CLI session. For gateway use, run
`hermes gateway restart`, then start a new session.

## Version History

- Unreleased: Add marketplace metadata, required sections, and reference docs.
- Unreleased: Add capability declarations, risk controls, and release gates.
- 0.1.6: Refresh catalog wording from the current Xquik OpenAPI.
- 0.1.5: Add registry metadata and Hermes runtime guidance.
- 0.1.4: Add public registry frontmatter for skill discovery.
