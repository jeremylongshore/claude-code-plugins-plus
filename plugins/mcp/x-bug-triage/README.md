![CI](https://github.com/jeremylongshore/x-bug-triage-plugin/actions/workflows/ci.yml/badge.svg)
![Version](https://img.shields.io/github/v/release/jeremylongshore/x-bug-triage-plugin)

# X Bug Triage Plugin v0.6.0

Closed-loop bug triage pipeline that turns public X/Twitter complaints into filed GitHub issues with human confirmation at every step.

## Quick Start

```bash
bun install
bun run db:migrate
bun test

# In Claude Code terminal:
/x-bug-triage @AnthropicAI --window 24h

# Claude fetches, analyzes, clusters, displays results.
# You interact directly:
> details 1
> file 2
> dismiss 3 noise
> confirm file 2
```

That's it. No Slack, no extra setup — just an X API token and `bun install`.

## Architecture

```
X API v2 → Intake (6) → Normalize → Cluster → Repo Scan (4) → Route (5) → Severity → Terminal → Review (11) → Issue Draft (3) → GitHub Issues
                                                                                          ↳ Slack (optional)
```

1 MCP server (`triage`) with 19 tools, orchestrated by a single SKILL.md playbook:

| Tool Group | Tools | Purpose |
|------------|-------|---------|
| X Intake | 6 | X API v2 ingestion (mentions, search, conversations, quotes) |
| Repo Analysis | 4 | GitHub repo evidence scanning (issues, commits, paths, deploys) |
| Internal Routing | 5 | Ownership lookup with 6-level precedence |
| Issue Draft | 3 | Draft generation with confirmation gate and duplicate check |
| Review | 1 | Deterministic review command parsing |

## Slack (Optional)

If you have the [`claude-code-slack-channel`](https://github.com/jeremylongshore/claude-code-slack-channel) plugin installed, triage results are also delivered to Slack for async team review. Slack is a peer plugin — not bundled, not required.

See [000-docs/004-AT-REFF-slack-review-flow.md](000-docs/004-AT-REFF-slack-review-flow.md) for the optional team workflow.

## Project Structure

```
mcp/triage-server/      # Single MCP server (19 tools: server.ts + lib.ts)
lib/                    # Shared library (types, db, config, audit)
db/                     # SQLite schema and migrations
config/                 # 8 operational config files
skills/x-bug-triage/    # Orchestration skill and policy references
agents/                 # 4 subagent definitions
data/                   # Runtime data (SQLite DB, reports, audit logs)
tests/fixtures/         # Mock API responses for deterministic testing
000-docs/               # Durable project documentation
```

## License

MIT — see [LICENSE](LICENSE).
