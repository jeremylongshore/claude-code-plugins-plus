# beads-dolt

A Dolt/DoltHub-aware Claude Code plugin for the [beads](https://github.com/gastownhall/beads) (`bd`) task tracker.

It packages, in one plugin:

- **A skill** (`/beads-dolt`) — the beads workflow upgraded to understand bd's Dolt backend: it surfaces the common "my beads aren't visible in DoltHub" root cause (no remote configured), the `bd dolt remote add` + push fix, the JSONL throttle/export model, and the rapid-write-race safe pattern — and dispatches the agents below.
- **Five expert agents** — grounded in a reverse-engineered, source-cited reference of bd's Dolt internals (`references/beads-dolt-internals.md`):
  - `dolt-sync-advisor` — DoltHub remotes, `bd dolt push`/`pull`, backup vs push, federation, drift.
  - `bead-epic-auditor` — subtree/epic-closure audits (which epics have all children closed).
  - `bead-dependency-mapper` — dependency graphs, cycles, critical path (SQL via the Dolt MCP).
  - `bead-recovery-specialist` — rapid-write-race recovery, embedded↔server mode migration, dolt-server incidents.
  - `beads-guru` — general bd/Dolt expertise and the three-layer mirror discipline.
- **A wired Dolt MCP server** (`.mcp.json`) — the official [`dolthub/dolt-mcp`](https://github.com/dolthub/dolt-mcp) server (45 tools) fronting your local `dolt sql-server` over the MySQL protocol, so the SQL-capable agents can query the bead graph directly.

## Built on

This plugin builds on, and credits, two open-source projects:

- **[beads](https://github.com/gastownhall/beads)** — the `bd` task tracker (the data this plugin operates on).
- **[Dolt](https://github.com/dolthub/dolt) / [DoltHub](https://www.dolthub.com)** — the version-controlled SQL database that is bd's backend, and the cloud host that makes a bead graph shareable. The MCP server is [`dolthub/dolt-mcp`](https://github.com/dolthub/dolt-mcp).

## Prerequisites

- [`bd`](https://github.com/gastownhall/beads) ≥ 1.0.4 with a Dolt-backed workspace.
- The Dolt MCP server binary on `PATH`. Install it one of these ways:

  ```bash
  go install github.com/dolthub/dolt-mcp/mcp/cmd/dolt-mcp-server@latest   # native (Go)
  # or
  docker pull dolthub/dolt-mcp:latest                                      # container
  # or grab a release binary from https://github.com/dolthub/dolt-mcp/releases
  ```

## Configuration

The MCP connection is environment-overridable (defaults target the shared `bd dolt --global` server on `:3308`):

| Env var | Default | Notes |
|---|---|---|
| `DOLT_HOST` | `127.0.0.1` | bd's dolt server is loopback-bound. |
| `DOLT_PORT` | `3308` | The shared-server port. For a per-project server, get the port from `bd dolt show`. |
| `DOLT_USER` | `root` | bd's default. |
| `DOLT_DATABASE` | `beads` | Your workspace's database name (see `bd dolt show`). |
| `DOLT_PASSWORD` | _(empty)_ | bd's server is unauthenticated by default. |

## How it was evaluated

This plugin was run end-to-end through the [Intent Eval Platform](https://github.com/jeremylongshore/intent-eval-lab) — deterministic gates → behavioral eval (real model) → kernel-validated Evidence Bundle → ship/no-ship decision. The full evidence and the ship/no-ship decision are recorded in [`DOGFOOD.md`](./DOGFOOD.md); the methodology write-up is the platform's [case study](https://github.com/jeremylongshore/intent-eval-lab/blob/main/000-docs/088-RR-LAND-beads-dolt-external-adopter-convergence-proof-2026-06-20.md). (The eval even surfaced — and we fixed — a bug in the platform's own evidence emitter.)

## License

Apache-2.0. See [LICENSE](./LICENSE).
