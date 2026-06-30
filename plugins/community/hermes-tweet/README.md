# Hermes Tweet

[![CI](https://github.com/Xquik-dev/hermes-tweet/actions/workflows/ci.yml/badge.svg)](https://github.com/Xquik-dev/hermes-tweet/actions/workflows/ci.yml)
[![Docs](https://img.shields.io/badge/docs-README-blue.svg)](https://github.com/Xquik-dev/hermes-tweet#readme)
<a href="https://nothumansearch.ai/site/xquik.com" target="_blank" rel="noopener"><img src="https://nothumansearch.ai/badge/xquik.com.svg" alt="NHS Agentic Readiness Score" height="28"></a>
[![Ask DeepWiki](https://deepwiki.com/badge.svg?url=https%3A%2F%2Fgithub.com%2FXquik-dev%2Fhermes-tweet)](https://deepwiki.com/Xquik-dev/hermes-tweet)
[![PyPI](https://img.shields.io/pypi/v/hermes-tweet.svg)](https://pypi.org/project/hermes-tweet/)
[![piwheels](https://img.shields.io/piwheels/v/hermes-tweet.svg)](https://piwheels.org/project/hermes-tweet/)
[![Python](https://img.shields.io/pypi/pyversions/hermes-tweet.svg)](https://pypi.org/project/hermes-tweet/)
[![PyPI Status](https://img.shields.io/pypi/status/hermes-tweet.svg)](https://pypi.org/project/hermes-tweet/)
[![Wheel](https://img.shields.io/pypi/wheel/hermes-tweet.svg)](https://pypi.org/project/hermes-tweet/#files)
[![Downloads](https://img.shields.io/pypi/dm/hermes-tweet.svg)](https://pypi.org/project/hermes-tweet/)
[![Release](https://img.shields.io/github/v/release/Xquik-dev/hermes-tweet?sort=semver)](https://github.com/Xquik-dev/hermes-tweet/releases)
[![Apify Actor](https://apify.com/actor-badge?actor=xquik/x-tweet-scraper)](https://apify.com/xquik/x-tweet-scraper)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

Native [Hermes Agent](https://github.com/NousResearch/hermes-agent) plugin for
X automation through [Xquik](https://xquik.com).

Hermes Tweet brings X search, account reads, tweet posting, replies, likes,
retweets, follows, DMs, monitors, webhooks, draws, extraction jobs, media, and
trend reads into Hermes as structured tools.

Use it when you need a Hermes Agent Twitter plugin, Hermes X automation, social
media automation for agents, or a native Hermes toolset for X/Twitter.

## Highlights

- Published Python package with a native Hermes plugin entry point.
- Installable from PyPI as `hermes-tweet`.
- 99 agent-callable Xquik endpoints generated from OpenAPI.
- 31 MPP-tagged read endpoints in the bundled catalog.
- Read and action tools are split for least-privilege operation.
- Action endpoints are disabled by default.
- Bundled Hermes skill for agent-facing usage guidance.
- Slash commands for account status and trends.
- Current guidance for Hermes Agent v0.16.0 Desktop, remote gateway, and
  dashboard credential workflows.
- Strict CI with formatting, linting, type checking, tests, coverage, security
  scan, dependency audit, and package build checks.

## Install

Recommended Hermes plugin install:

```bash
hermes plugins install Xquik-dev/hermes-tweet --enable
```

Hermes Agent treats third-party plugins as opt-in. Without `--enable`, the
installer can discover Hermes Tweet, but it may leave the plugin in the
`not enabled` state until you run `hermes plugins enable hermes-tweet` or toggle
it in the interactive `hermes plugins` UI. Use `hermes plugins list` when a
fresh install does not show the `hermes-tweet` toolset.

Hermes will prompt for `XQUIK_API_KEY` during an interactive install and save it
to `~/.hermes/.env`. In non-interactive installs the prompt is skipped; set the
key through the environment or `~/.hermes/.env` before running `tweet_read`.
If you edit `~/.hermes/.env` while Hermes is already running, use `/reload` in
an interactive CLI session, or restart gateway and cron sessions before calling
`tweet_read`.
When `XQUIK_API_KEY` is not configured, Hermes should expose only the no-network
`tweet_explore` tool from this plugin. That is expected safe gating, not an
install failure.

Install the published Python package from PyPI into the Hermes Python
environment:

```bash
uv pip install --python ~/.hermes/hermes-agent/venv/bin/python hermes-tweet
hermes plugins enable hermes-tweet
```

If your Hermes venv includes `pip`, this path is also valid:

```bash
~/.hermes/hermes-agent/venv/bin/python -m pip install hermes-tweet
hermes plugins enable hermes-tweet
```

From a local checkout:

```bash
hermes plugins install file:///absolute/path/to/hermes-tweet --force --enable
```

If you are testing from a project-local `.hermes/plugins/` directory instead of
installing the plugin into `~/.hermes/plugins/` or through the PyPI entry point,
start Hermes with `HERMES_ENABLE_PROJECT_PLUGINS=true` only for trusted
repositories.

Hermes Agent v0.16.0 adds a native desktop app and remote gateway profiles.
For a remote gateway profile, install and enable Hermes Tweet on the remote
Hermes host because that is where plugin code executes and where
`XQUIK_API_KEY` must be available. The desktop app is the chat surface; it
should not receive or store the key unless it is also running the Hermes
runtime locally.

## Python Package

| Field | Value |
| --- | --- |
| PyPI | [`hermes-tweet`](https://pypi.org/project/hermes-tweet/) |
| Official guide | [`github.com/Xquik-dev/hermes-tweet#readme`](https://github.com/Xquik-dev/hermes-tweet#readme) |
| Context7 | [`context7.com/xquik-dev/hermes-tweet`](https://context7.com/xquik-dev/hermes-tweet) |
| piwheels | [`hermes-tweet`](https://piwheels.org/project/hermes-tweet/) |
| Latest release | [`v0.1.6`](https://github.com/Xquik-dev/hermes-tweet/releases/tag/v0.1.6) |
| Supported Python | `>=3.11` |
| Package format | Wheel and source distribution |
| Hermes entry point | `hermes-tweet = hermes_tweet` |
| Entry point group | `hermes_agent.plugins` |
| Included assets | `plugin.yaml`, `catalog_data.json`, bundled Hermes skill, Codex/Claude manifests |
| Claude plugin manifest | [`.claude-plugin/plugin.json`](.claude-plugin/plugin.json) |
| Codex plugin manifest | [`.codex-plugin/plugin.json`](.codex-plugin/plugin.json) |
| Registry skill path | [`skills/hermes-tweet/SKILL.md`](skills/hermes-tweet/SKILL.md) |
| Context7 guide | [`docs/CONTEXT7.md`](docs/CONTEXT7.md) |
| Hermes surface guide | [`docs/HERMES_SURFACES.md`](docs/HERMES_SURFACES.md) |
| Integration patterns | [`docs/INTEGRATION_PATTERNS.md`](docs/INTEGRATION_PATTERNS.md) |
| Submission readiness | [`docs/SUBMISSION_READINESS.md`](docs/SUBMISSION_READINESS.md) |
| Merge enablement | [`docs/MERGE_ENABLEMENT.md`](docs/MERGE_ENABLEMENT.md) |

Hermes Tweet also ships source-native `.codex-plugin` metadata, a root
security policy, a local composer icon, and a HOL Plugin Scanner workflow for
Codex plugin catalogs that require local validation evidence before listing.

## Configure

Create an API key in the Xquik dashboard, then set:

```bash
export XQUIK_API_KEY="xq_..."
```

Optional settings:

```bash
export XQUIK_BASE_URL="https://xquik.com"
export HERMES_TWEET_ENABLE_ACTIONS="false"
```

Action endpoints are disabled unless `HERMES_TWEET_ENABLE_ACTIONS=true`.
If you configure keys through `~/.hermes/.env` during an active Hermes session,
use `/reload` in the interactive CLI, or restart gateway and cron sessions so
they pick up the new values.

## Security Model

Hermes Tweet never accepts credentials through tool arguments. Auth is read from
environment variables and injected by the plugin at request time.

The plugin blocks dashboard-only admin, billing, credit top-up, support-ticket,
API-key, and account re-authentication endpoints from the catalog. Private reads
and write-like endpoints go through `tweet_action`, which is hidden unless
`HERMES_TWEET_ENABLE_ACTIONS=true`.

## Tools

| Tool | Purpose |
| --- | --- |
| `tweet_explore` | Search the bundled Xquik endpoint catalog. No API call. |
| `tweet_read` | Call catalog-listed read-only endpoints. |
| `tweet_action` | Call write-like or private endpoints. Disabled by default. |

Use `tweet_explore` first, then call `tweet_read` or `tweet_action` with a
concrete `/api/v1/...` path.
Copied endpoint URLs are accepted, but Hermes Tweet matches only catalog-listed
paths.

## Hermes Agent Workflows

Hermes Tweet is best used as the X context layer for Hermes Agent workflows that
need current public signal, authenticated account context, or approval-gated
account actions:

| Workflow | Recommended Path |
| --- | --- |
| Social listening | Use `tweet_explore` to find search, user, trend, monitor, or radar routes, then use `tweet_read` for public reads. |
| Launch monitoring | Keep `tweet_action` disabled, schedule Hermes cron sessions around read-only trend, mention, and account checks. |
| Support triage | Read public mentions and user timelines, summarize issues in Hermes, then hand off account-changing responses for explicit approval. |
| Creator or brand research | Combine X search, user profile, follower, media, and trend reads before drafting content or campaign briefs. |
| Giveaway and community audits | Use read routes for tweet, reply, follower, list, draw, and export evidence before any action route. |
| Controlled publishing | Enable `HERMES_TWEET_ENABLE_ACTIONS=true` only in sessions that require posting, DMs, follows, webhooks, monitors, or media changes. |
| Desktop operator sessions | Use Hermes Desktop for interactive review, then keep action calls explicit and approval-gated. |
| Remote gateway teams | Install Hermes Tweet and set `XQUIK_API_KEY` on the remote gateway host, then connect Desktop profiles to that host. |
| Dashboard-administered agents | Use the dashboard for gateway and credential operations, but keep Hermes Tweet secrets in the runtime environment. |

For marketing or user education, position Hermes Tweet as a native Hermes Agent
plugin, not a generic API wrapper: it ships a PyPI entry point, a `plugin.yaml`
manifest with interactive secret prompts, slash commands for quick diagnostics,
and a bundled skill registered through Hermes' plugin skill system.

## Hermes Runtime Fit

Hermes Tweet registers a dedicated `hermes-tweet` plugin toolset. Hermes can
show and manage those tools through its normal `hermes tools` and platform
toolset flows, so teams can keep X automation available only where it belongs.
Current Hermes Agent releases discover third-party plugins but do not execute
them until they are enabled in `plugins.enabled`, through `hermes plugins enable`,
or by installing with `--enable`. This is expected safety behavior for user and
PyPI entry-point plugins.

Hermes Agent v0.16.0 expands the surfaces where the same toolset can appear:
the native Desktop app, remote gateway profiles, the web dashboard, the TUI,
and the CLI can all route work to the enabled runtime. Hermes Tweet does not
need a different plugin entry point for those surfaces. It needs the same
enabled plugin, the same runtime environment, and the same read/action split.

The v0.16.0 Desktop command palette surfaces skills and quick-command slash
commands. Treat `/xstatus` and `/xtrends` as interactive runtime commands for
active CLI, TUI, Desktop, or gateway sessions; keep `hermes -z` for tool-call
smoke tests.

The v0.16.0 dashboard added broader administration and credential-management
surfaces. Those are useful for gateway operations, but Hermes Tweet still reads
`XQUIK_API_KEY` and `HERMES_TWEET_ENABLE_ACTIONS` from the runtime environment.
Do not paste API keys into prompts, issue bodies, PR comments, or tool inputs.

For non-interactive smoke tests and CI-style diagnostics, use
`hermes tools list`; bare `hermes tools` opens the interactive tool UI and
requires a TTY. In current Hermes Agent releases, `hermes tools list` reports plugin toolsets,
not every individual plugin tool name.

Use the read-only path for social listening, trend research, account checks,
giveaway audits, and draft planning. Keep `HERMES_TWEET_ENABLE_ACTIONS=false`
for unattended cron or gateway sessions unless the workflow has an explicit
approval step for posting, DMs, follows, monitor changes, webhook changes, or
other account actions.

Runtime smoke test:

```bash
hermes -z "Use tweet_explore, then read /api/v1/account. Do not call tweet_action." --toolsets hermes-tweet
```

Expected results:

- `tweet_explore` discovers catalog endpoints without using the API key.
- Without `XQUIK_API_KEY`, a non-mutating Hermes probe exposes `tweet_explore`
  only.
- After `XQUIK_API_KEY` is configured and the CLI is reloaded, or the gateway
  or cron process is restarted, `tweet_read` can read `/api/v1/account`.
- `tweet_action` stays hidden or disabled unless `HERMES_TWEET_ENABLE_ACTIONS=true`.
- `/xstatus` and `/xtrends` appear in the Hermes plugin command registry.

Hermes one-shot `hermes -z "/xstatus"` can run as a model prompt, not as the
interactive slash-command dispatcher. Verify slash commands in an active CLI,
TUI, Desktop, or gateway session, or through the plugin registry tests, and use
`hermes -z` for tool-call probes.

If `hermes plugins install` runs without a TTY, Hermes cannot safely prompt for
secrets and will skip API-key storage. This is expected; set `XQUIK_API_KEY`
in the process environment or `~/.hermes/.env`.

## Slash Commands

| Command | Purpose |
| --- | --- |
| `/xstatus` | Show Xquik account, subscription, and usage status. |
| `/xtrends` | Show current X trends. |

## Development

Generate the bundled catalog from Xquik OpenAPI:

```bash
python scripts/build_catalog.py ../xquik/openapi.yaml
```

Run checks:

```bash
uv run --python 3.12 --extra dev ruff format --check .
uv run --python 3.12 --extra dev ruff check .
uv run --python 3.12 --extra dev basedpyright
uv run --python 3.12 --extra dev pytest --cov=hermes_tweet --cov=tests --cov-report=term-missing --cov-fail-under=100
uv run --python 3.12 --extra dev bandit -c pyproject.toml -r hermes_tweet scripts
uv run --python 3.12 --extra dev pip-audit
uv run --python 3.12 --extra dev python -m build
uv run --python 3.12 --extra dev twine check dist/*
```

For a single local quality gate:

```bash
uv run --python 3.12 --extra dev ruff format --check . && \
uv run --python 3.12 --extra dev ruff check . && \
uv run --python 3.12 --extra dev basedpyright && \
uv run --python 3.12 --extra dev pytest --cov=hermes_tweet --cov=tests --cov-report=term-missing --cov-fail-under=100 && \
uv run --python 3.12 --extra dev bandit -c pyproject.toml -r hermes_tweet scripts && \
uv run --python 3.12 --extra dev pip-audit && \
uv run --python 3.12 --extra dev python -m build && \
uv run --python 3.12 --extra dev twine check dist/*
```

## Relationship To TweetClaw

TweetClaw is the OpenClaw-native npm plugin. Hermes Tweet is the Hermes-native
Python plugin. Both use the same Xquik API contract.

## Public Repo Metadata

Recommended GitHub description:

> Native Hermes Agent plugin for X/Twitter automation through Xquik.

Recommended topics:

`hermes-agent`, `hermes-plugin`, `hermes`, `twitter`, `x-api`,
`x-automation`, `xquik`, `tweet`, `automation`, `social-media`,
`social-media-automation`, `ai-agent`, `mcp`, `agent-tools`, `twitter-api`,
`twitter-automation`, `x-twitter`, `social-media-api`, `agent-skill`, `python`
