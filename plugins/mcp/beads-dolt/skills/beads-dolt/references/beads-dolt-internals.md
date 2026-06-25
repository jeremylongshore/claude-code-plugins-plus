# beads + Dolt — where to get the current truth (no frozen snapshot)

This plugin keeps **no baked copy** of beads' or Dolt's internals. A hand-copied
snapshot goes stale the moment upstream ships a release and silently lies in
between. Every agent in this plugin instead **forks into its own context, fetches
the current facts from the sources below, and reports back** — so the answer is
always correct for the *installed* version, never a guess from memory.

This file is only a directory of authoritative sources + the live commands to read
them. It contains **no behavioral claims** on purpose.

## Authority order (higher wins on any conflict)

1. **The installed binary** — current to exactly what's running, by definition:
   - `bd --help`, `bd <cmd> --help` — e.g. `bd dolt --help`, `bd init --help`, `bd backup --help`, `bd config --help`
   - `bd prime` — live AI workflow context
   - `bd dolt show` — this workspace's live database, host, port, mode
   - `bd config list` / `bd config get <key>` — the effective config
   - Live data model — introspect, never assume: `SHOW TABLES`, `information_schema.columns`, `SHOW CREATE TABLE <t>` (via the Dolt MCP)

2. **Official upstream docs** (maintained with the code) — `curl` the raw files or read the site:
   - beads repo: <https://github.com/gastownhall/beads> — `docs/DOLT-BACKEND.md`, `docs/DOLT.md`, `docs/CONFIG.md`, `docs/CLI_REFERENCE.md`, `docs/INTERNALS.md`, `docs/FEDERATION-SETUP.md`
     (raw: `https://raw.githubusercontent.com/gastownhall/beads/main/docs/<FILE>.md`)
   - beads docs site: <https://gastownhall.github.io/beads/>
   - Dolt: <https://docs.dolthub.com> · <https://github.com/dolthub/dolt>
   - Dolt MCP: <https://github.com/dolthub/dolt-mcp>

## How agents use this

Every agent here is told: **do not assert version-specific behavior from memory or
any bundled text.** Fetch it live — run the relevant `bd … --help`, `curl` the
matching official doc, or introspect the live schema — then answer from what you
just read, and name the source. The installed binary is the tie-breaker.
