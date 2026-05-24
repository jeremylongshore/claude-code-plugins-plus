---
title: "Safety Model First: 16-Tool Ops MCP, One Day"
description: "Design a 7-point safety model before writing tools. How server-ops-mcp shipped 16 tools, 40 tests, and v0.1.0 in a single day."
date: "2026-05-22"
tags: ["mcp", "typescript", "claude-code", "devops", "architecture", "ssh", "automation"]
featured: false
---
The Intent Solutions production stack now lives on a single Contabo VPS after [a multi-week migration](/posts/propagation-day-when-the-spec-becomes-the-migration-plan/). Twenty-four containers across five stacks — Braves, Plane, Twenty, Umami, ntfy — sit behind one Caddy reverse proxy. Every day-to-day operational task touches that box: reload Caddy after a host-block edit, restart a stuck container, pull the last 200 lines of a service log, snapshot an instance before a risky change. Doing those by hand from a shell defeats the point of having Claude Code in the loop. Doing them through [a sloppy MCP server](/posts/guidewire-mcp-v0-1-0-foundation-ship/) is how you brick prod from a chat window.

So the question on day one wasn't "what tools do I want?" The question was "what would have to be true of those tools before I let a model fire them at a server I actually depend on?"

The answer became a 7-point safety model, written into the README on the very first commit, before any tool existed. That model — and the host registry that sits behind it — is the whole reason the rest of the work fit in one day.

## The 7-point safety model

The model is what every tool in the catalog has to satisfy before it ships: a hard write denylist, dry-run-by-default for destructive operations, argument validation, key-based SSH only, backup-before-write, validate-before-reload, and capped output. No exceptions, no "we'll add that later."

1. **Write denylist (hard).** `server.file.write` always refuses `/etc/passwd`, `/etc/shadow`, `/etc/sudoers[.d/...]`, `~/.ssh/authorized_keys`, `/boot/`, `/usr/`. Per-host config cannot opt out.
2. **Dry-run by default.** Every destructive tool requires explicit `apply: true` to actually fire. Omitting it returns the command that *would* run.
3. **Argument validation.** Unit names, container names, service names, and paths are regex-validated before they ever reach a shell. `/^[A-Za-z0-9_.@-]+$/` for systemd units, `/^[A-Za-z0-9_.-]+$/` for container names, `/^\/[A-Za-z0-9_./-]+$/` for absolute paths. Shell metacharacters never get the chance.
4. **Key-based SSH only.** The `ssh2` Client opens with `privateKey`. No password fallback, no agent fallback. If the key isn't there, the call fails.
5. **Backup before write.** Real writes do `cp -p <path> <path>.bak` first. Recovery is one SSH command away.
6. **Validate before reload.** `server.caddy.reload` runs `caddy validate` first and refuses to reload if validation fails. A broken Caddyfile cannot leave the building.
7. **Output capped.** `server.exec` defaults to 8 KiB per stream; `server.file.read` to 1 MiB. A runaway log tail can't blow up the context window or the model's reasoning.

The thing to notice: none of these are tool-specific. They're cross-cutting invariants. Designing them first meant every tool I built afterward had a fixed checklist to satisfy, not a fresh argument to relitigate.

A tool author shouldn't be inventing safety policy at 3pm on commit four. By then, the pressure to "just ship this one helper" has won the argument. The 7-point list exists so that argument never starts — every tool either passes all seven gates or doesn't ship.

## The host registry as the access-control boundary

Here's the architectural choice that did the most work: **the tools enforce nothing host-level. The registry does.**

Only hosts in `~/.config/server-ops/hosts.yaml` are reachable. The tools take a `host` parameter, look it up, and refuse if it isn't there. Adding a new host is one YAML edit. Rotating a key is one YAML edit. Restricting which commands `server.exec` may run on a given host is one YAML edit.

```yaml
hosts:
  intentsolutions:
    address: 167.86.106.29
    user: intentsolutions
    key: ~/.ssh/id_ed25519
    port: 22
    allowed_commands:
      - "^docker "
      - "^free"
      - "^df"
    write_allowed_paths:
      - "^/srv/braves/.env$"
      - "^/etc/caddy/Caddyfile$"

  dev-box:
    address: 100.x.x.x
    user: jeremy
    key: ~/.ssh/id_ed25519
    # No allowed_commands -> all commands allowed
    # No write_allowed_paths -> denylist only
```

Two optional per-host regex allowlists do the per-host narrowing:

- `allowed_commands` — `server.exec` only runs commands matching one of these. Omit to permit anything.
- `write_allowed_paths` — `server.file.write` only writes paths matching one of these. The hard write denylist is *always* enforced regardless.

The prod host gets the tight collar. The dev box stays loose because if I brick it, I haven't taken any customer down.

The asymmetry is the point — least privilege per environment, not a blanket policy. A flat policy that treated every host identically would either be too loose for prod or too tight for the dev box. Per-host config lets each environment carry exactly the constraints that match its blast radius. The Caddyfile and the Braves `.env` are the only two files I ever intentionally edit on the prod box; everything else stays read-only. That's enforceable in seven lines of YAML.

### Why not let the tools do ACLs?

Tempting design: bake the allow/deny logic into each tool. Don't. Two reasons.

First, you end up with the same access policy duplicated across `exec`, `file.write`, `systemd.restart`, `docker.restart`, `compose.up/down`, and `caddy.reload`. Drift between those is inevitable, and one drifted tool is the one an attacker (or a confused model) walks through.

Second, the host registry is a much better trust seam. Reviewing one YAML file is a five-minute job. Reviewing seven tool implementations for consistent ACL enforcement is a meeting. The tools stay simple — they just do their one thing, validate their args, and ask the registry "am I allowed here?" The registry owns the answer.

## The shared SSH client pool

The second choice worth calling out: **one `ssh2.Client` per host, shared across exec and SFTP.**

Every tool — `server.exec`, `server.file.read`, `server.file.write` — goes through the same pool. A first call to `host:intentsolutions` opens the TCP connection, authenticates, and caches the client. Every subsequent call against that host reuses it. The pool drops the cached client on `close` or `error` events so the next call reconnects cleanly. On `SIGINT` / `SIGTERM` the server calls `closeAllClients()` to drain on shutdown.

The alternative — opening a fresh SSH session per tool call — would have added a full TCP + TLS + auth roundtrip to every operation. With Claude Code firing a sequence of `exec` then `file.read` then `systemd.restart` calls against the same host, that's three connection setups where one would do. Worse, key-only auth is slow enough that the latency would show up in conversations.

Pooling is one of those "obvious in hindsight" decisions that only stays clean if you commit to it on day one. Retrofit-pooling is a rewrite — every tool that opened its own client now has to learn to ask the pool, and the lifecycle questions (who closes? who reconnects on error? what happens on shutdown?) get answered seven different ways instead of once.

### Why not use ssh-agent?

Using the local SSH agent would have eliminated the need to handle a private key file directly. It would also have made the server's behavior depend on out-of-band ambient state — whether an agent is running, whether the right key is loaded, whether the user remembered to `ssh-add` after a reboot. For a server that needs to be predictable from a long-running Claude Code session, that ambient state is a liability. The `privateKey` path is explicit, reproducible, and the failure mode is loud: missing key, fail immediately.

## The tool catalog

With the safety model and the host registry settled, the actual tools fell out fast. Six commits, 16 tools, 40 unit tests, ~1,950 lines added.

| Tool | What it does | Destructive? |
|---|---|---|
| `server.exec` | Run shell command; capped output, optional allowlist | Configurable |
| `server.file.read` | SFTP read, 1 MiB cap | No |
| `server.file.write` | SFTP write with `<path>.bak` snapshot | Dry-run default + write denylist |
| `server.health` | Snapshot uptime, free, df, sensors, 7d OOM count | No |
| `server.systemd.status` | `systemctl status <unit>` | No |
| `server.systemd.restart` | `sudo systemctl restart <unit>` | Dry-run default |
| `server.caddy.reload` | Validate then reload Caddyfile | Dry-run default; refuses if validate fails |
| `server.docker.ps` | List running containers | No |
| `server.docker.logs` | Tail container logs (default 200 lines) | No |
| `server.docker.restart` | Restart container | Dry-run default |
| `server.compose.up` | `docker compose up -d` in a directory | Dry-run default |
| `server.compose.down` | `docker compose down` | Dry-run default |
| `server.compose.logs` | Tail one service's logs | No |
| `contabo.instance.list` | List Contabo instances | No |
| `contabo.instance.create` | Provision new instance (billed) | Dry-run default |
| `contabo.instance.snapshot` | Snapshot an instance | Dry-run default |

The pattern is uniform: read-only tools just run; destructive tools default to dry-run and only fire with `apply: true`. A dry-run call returns the command that *would* execute, so the model (or the human reading the transcript) can verify before committing.

## The Contabo wrapper has a quirk worth knowing

Contabo's identity server requires *both* OAuth2 `(client_id, client_secret)` *and* legacy `(api_user, api_password)` to mint a bearer token. This is non-standard — most OAuth2 flows want one or the other, not both. The wrapper validates all four env vars are present and surfaces a clean error if any are missing:

```
Missing Contabo credentials: CONTABO_API_USER, CONTABO_API_PASSWORD
```

The token is cached in-process until 30 seconds before expiry. Tests expose `_clearTokenCache()` to reset between cases. `contabo.instance.create` and `contabo.instance.snapshot` default to dry-run for the obvious reason: a create call books real money. Snapshot doesn't bill the same way, but the principle is consistent — if it mutates infrastructure, it asks before firing.

The wrapper is intentionally thin. It's not trying to be a full Contabo SDK. It exposes three operations because those are the three I actually need from a Claude Code session: list what's running, provision a new instance when scaling out, snapshot before doing something risky. Adding more later is cheap; getting the safety defaults right is the part that has to be right on the first commit.

### Why not allowlist commands inside `server.exec` itself?

I went back and forth on this. The case for in-tool allowlists is "defense in depth — even if the registry is wrong, the tool refuses." The case against won, for the same reason the registry owns ACLs in general: every additional enforcement point is another spot where the policy can drift from intent.

The `server.exec` allowlist *is* a regex array — but it lives per-host in `hosts.yaml`, not hardcoded in the tool. The tool itself just asks the registry "is this command allowed on this host?" and refuses if no, runs if yes. One source of truth, reviewable in one place.

## What this buys you

The day's stats are downstream of the design, not the other way around. Six commits, 16 tools, 40 passing unit tests, typecheck + build clean, CI matrix green on Node 20 and 22. v0.1.0 cut and registered in `.mcp.json` by end of day.

That pace is possible because the cross-cutting decisions were nailed before any tool got written. Every tool was a fill-in-the-blanks exercise: validate args, look up host, check allowlist, build command, run with output cap, return dry-run-or-result. No tool needed to argue with the safety model — it just had to satisfy it.

The opposite path — build tools first, retrofit safety after — is how MCP servers end up with five different error paths, three different ACL styles, and the one tool that forgot to cap its output. Designing the invariants before the surface area is what keeps the surface area honest.

There's a second-order benefit: the safety model is the spec. When a future tool gets added — say `server.nginx.reload` or `server.zfs.snapshot` — there's no design meeting. The author reads the 7-point list, picks the matching pattern (validate-before-reload for nginx, dry-run for zfs), drops it into a host's `allowed_commands`, and ships. The cognitive load of "is this safe enough?" got paid down once, on day one.

This matters more for a Model Context Protocol (MCP) server than for ordinary tools because the caller is a model, not a human. A human reading `server.exec` documentation would hesitate before running `rm -rf /srv/braves`. A model that just learned the tool exists will happily fire it if the prompt nudges that way. The guardrails are the layer that doesn't depend on the caller having good judgment.

## Also shipped

- **claude-code-plugins (PRs #762/#763/#764):** CI hardening — eslint + prettier added as blocking gates (first PR of a multi-PR cleanup), human-triggered auto-merge disabled (dependabot bumps still auto-merge), and nine historical AA-AACR audit files from December 2025 committed to the record.
- **intentional-cognition-os:** v0.2 dogfood continued — `paraphrase_robustness` metric landed in `verify.py`, `ask-loop.py` extracted as a standalone helper with `--paraphrases`, `bank.py` schema library plus ADRs 029-032, release v1.2.5, wiki/citation resolution against the workspace cache (closes h99). Continuation of [yesterday's zero-to-five FTS fallback arc](/posts/icos-dogfood-zero-to-five-fts-fallback/).
- **pipelinepilot:** Firebase Cloud Functions standardized on Gen2 Node 20 ESM (`firebase-admin` import fixed), orchestrator wrapper added with sync `query(**kwargs)` and pinned cloudpickle, Python smoke for the Vertex AI Reasoning Engine, beads tracking initialized, `.env` patterns added to `.gitignore`.
- **hybrid-ai-stack + intent-genai-project-template:** Gemini PR-review fixups — flake8 violations cleared, three pre-existing security defects in redact/sanitize/routes closed, mypy + ruff cleanup.

## Related Posts

- [Intent Catalog: Six Phases from Empty Repo to Production Control Plane](/posts/intent-catalog-six-phases-control-plane/) — the sibling shape: empty repo to working control plane in a small number of clean phases.
- [Guidewire MCP v0.1.0: Carrier-Native Server Blueprint](/posts/guidewire-mcp-v0-1-0-foundation-ship/) — another foundation-ship MCP post, same v0.1.0 framing.
- [A v1.0 Is a Gate, Not a Tag](/posts/v1-release-gate-conditional-go/) — release-gate discipline; the same logic that says "design the invariants first" applies to "earn the version number."
