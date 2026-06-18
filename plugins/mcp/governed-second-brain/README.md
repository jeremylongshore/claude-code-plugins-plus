<h1 align="center">Governed Second Brain — the plugin</h1>

<p align="center">
  A local-first Claude Code + Cowork plugin: turn <em>your own</em> files into a governed,
  <code>qmd://</code>-cited second brain with a tamper-evident, SHA-256 hash-chained audit trail.<br>
  <strong>Compile, then govern.</strong> Runs in-process — no daemon, no network, no API key for retrieval.
</p>

<p align="center">
  <img src="https://img.shields.io/badge/License-Apache--2.0-10b981?style=flat-square" alt="License: Apache-2.0">
  <img src="https://img.shields.io/badge/local--first-in--process-0ea5e9?style=flat-square" alt="local-first">
  <img src="https://img.shields.io/badge/MCP-stdio-8b5cf6?style=flat-square" alt="MCP stdio">
</p>

---

## 📍 This product lives in two homes

| | Repo | What it is |
|---|---|---|
| **Landing / thesis** | **[intent-solutions-io/governed-second-brain](https://github.com/intent-solutions-io/governed-second-brain)** | The umbrella — *why* this exists, the competitive teardown, the "Compile, Then Govern" thesis, the receipts argument. Start here for the **story**. |
| **The plugin** (you are here) | **[jeremylongshore/governed-second-brain-plugin](https://github.com/jeremylongshore/governed-second-brain-plugin)** | The installable code — the local stdio MCP server + skills. Start here to **run it**. |

It stacks on three engines:

| Engine | Repo | Layer |
|---|---|---|
| **ICO** | [jeremylongshore/intentional-cognition-os](https://github.com/jeremylongshore/intentional-cognition-os) | **Compile** — derive knowledge from a corpus (optional; the only part that egresses) |
| **INTKB** | [jeremylongshore/qmd-team-intent-kb](https://github.com/jeremylongshore/qmd-team-intent-kb) | **Govern** — deterministic dedupe → policy → promote + the hash-chained audit |
| **qmd** | [tobi/qmd](https://github.com/tobi/qmd) | **Retrieve** — on-device search; every hit is a `qmd://` citation |

This plugin **bundles** the compiled INTKB packages, so it runs the govern + retrieve loop fully
in-process — the engines stay independent repos; nothing here forks or privatizes them.

## What it does

Most "AI memory" gives an agent better *recall*. This does two things the category skips: it
**governs** what's allowed to become durable memory (deterministic dedupe / policy / promotion — by
code, not a model), and it ships a **receipt** — a `qmd://` citation plus a SHA-256 hash-chained audit
event — for every write. Runs on your machine; your files never leave it (retrieval is local; the
optional ICO *compile* step is the only thing that egresses, and it's opt-in).

### Tool surface

| Tool | Kind | What it does |
|---|---|---|
| `brain_search` | read | Cited search over your governed memory (`qmd://` receipts), in-process |
| `brain_status` | read | Counts by lifecycle state + category |
| `brain_capture` | write | Capture a fact as a governance **proposal** (to the local spool) |
| `brain_govern` | write | Drain the spool → dedupe → policy → **promote**, with a hash-chained audit receipt — daemon-free |
| `brain_transition` | write | Retire / re-lifecycle a memory (audited) |

Two skills front these: **`/brain`** (cited answers) and **`/brain-save`** (governed capture).

## What the receipt does *not* do

Honesty is the point of a receipt. The chain gives you **tamper-*detection*** — integrity + ordering,
so an edited or reordered record is caught by `verify`. It is **not** tamper-proof: on your own machine
a writer with access can edit an event *and* re-hash the chain forward. Within a single trust boundary
(your machine) that's exactly the integrity guarantee you want; cross-actor non-repudiation needs an
external chain-head anchor (on the roadmap). It is **not** a blockchain and **not** immutable storage.

## Install

One command, two modes:

```bash
# A) zero-egress (default for regulated/client data) — nothing leaves the machine
npx governed-second-brain init <your-folder> --index-only

# B) full compile — ICO derives knowledge (6 passes) before governing; opt-in egress to DeepSeek
DEEPSEEK_API_KEY=… npx governed-second-brain init <your-folder>
```

It builds a governed, `qmd://`-cited, hash-chained-audited brain under `~/.teamkb`, installs the native
dep per-platform, and **auto-registers the MCP server with Claude Code** (`claude mcp add`; `--no-register`
to skip). Full mode runs a loud pre-flight consent (your file text goes to DeepSeek; `--yes` to skip the
prompt). Requires Node 20+, a C/C++ toolchain (for `better-sqlite3`), and `qmd` 2.x on PATH for retrieval.

After it finishes, start a new Claude Code session — the `governed-brain` tools are live. For the
`/brain` and `/brain-save` skills too, `claude plugin install governed-second-brain`.

<details><summary><strong>Build from source</strong> (to hack on the runtime)</summary>

```bash
pnpm -C ../qmd-team-intent-kb build   # the bundle inlines INTKB's compiled packages (sibling checkout, built)
pnpm install && pnpm build            # esbuild → plugin-runtime/governed-brain.cjs
node bin/init.mjs init <your-folder> --index-only
```
</details>

**Coming:** npm provenance + checksums (the `gsb.lock.json` reproducible pin) and
automatic Cowork MCP registration.

## License

Apache-2.0. The umbrella and both engine repos are Apache-2.0; qmd (upstream) is MIT by its author,
[@tobi](https://github.com/tobi).

---

<p align="center">
  Built by <a href="https://github.com/jeremylongshore">Jeremy Longshore</a> ·
  <a href="https://intentsolutions.io/">Intent Solutions</a> ·
  thesis at <a href="https://github.com/intent-solutions-io/governed-second-brain">intent-solutions-io/governed-second-brain</a>
</p>
