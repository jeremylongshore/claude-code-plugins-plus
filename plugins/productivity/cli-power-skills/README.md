# cli-power-skills

Agentic CLI tool skills for Claude Code. 7 domain-grouped skills covering 26 CLI tools that extend Claude's capabilities beyond its built-in tools.

## Installation

```bash
claude plugins install cli-power-skills
```

First add the marketplace, then install:

```bash
claude plugins marketplace add ykotik/cli-power-skills
claude plugins install cli-power-skills
```

## Prerequisites

These skills assume the CLI tools are already installed. See [INSTALL.md](INSTALL.md) for per-skill and batch install commands (macOS/Homebrew).

## Skills

| Skill | Tools | Trigger |
|-------|-------|---------|
| **data-processing** | jq, yq, gron, miller, xsv, DuckDB | Structured data: CSV, JSON, YAML, TOML, Parquet |
| **security-scanning** | Trivy, ShellCheck, sops | Vulnerabilities, script linting, encrypted secrets |
| **api-testing** | Hurl, httpx | HTTP endpoint testing, URL probing |
| **web-crawling** | Playwright, Puppeteer, Scrapy, Crawlee, Katana | Browser automation, site crawling, scraping |
| **web-research** | newspaper4k, yt-dlp | Article extraction, media download |
| **python-tooling** | uv, Ruff | Python packages, venvs, linting, formatting |
| **ci-automation** | gh, just, act, git-cliff, restic | GitHub workflows, task running, changelogs, backups |

---

## Use Cases

### Analyze and transform data without writing scripts

Query a 2GB CSV with SQL, convert YAML configs to JSON, flatten deeply nested API responses into greppable lines, compute column statistics, or join two datasets — all in single commands that pipe together.

**Tools**: `DuckDB` for SQL on files, `jq` for JSON, `yq` for YAML/TOML/XML, `xsv` for CSV slicing and stats, `miller` for format-aware record transforms, `gron` for grepping nested JSON paths

```
CSV/JSON/YAML/Parquet ──> jq / yq / xsv / mlr ──> DuckDB SQL ──> export
```

### Secure your code before it ships

Scan dependencies for CVEs, check container images for vulnerabilities, lint shell scripts for quoting bugs and unsafe patterns, validate IaC for misconfigurations, and keep secrets encrypted in version control.

**Tools**: `Trivy` for filesystem/container/IaC scanning, `ShellCheck` for shell script analysis, `sops` for encrypting secrets in YAML/JSON

```
code/containers/IaC ──> Trivy scan ──> ShellCheck lint ──> sops encrypt secrets
```

### Test APIs declaratively, not imperatively

Write readable `.hurl` test files with chained requests, variable captures, and built-in assertions — then probe hundreds of URLs for status and metadata in seconds.

**Tools**: `Hurl` for declarative HTTP test suites, `httpx` for concurrent URL probing

```
auth ──> create resource ──> verify ──> assert status + body (all in one .hurl file)
```

### Scrape and crawl the web at any scale

Choose the right tool for the job: full browser automation for JS-rendered pages, headless crawling for link discovery, or production-grade frameworks for large-scale extraction.

**Tools**: `Playwright` / `Puppeteer` for browser automation, `Scrapy` for structured crawling, `Crawlee` for anti-bot resilience, `Katana` for fast URL discovery

```
Katana (discover URLs) ──> Playwright (render JS) ──> Scrapy (extract at scale)
```

### Research the web from your terminal

Extract clean article text from any URL and download video/audio from 1000+ sites with full metadata, format selection, and subtitle support.

**Tools**: `newspaper4k` for article extraction, `yt-dlp` for media download and metadata

```
newspaper4k (extract text) ──> DuckDB (analyze)
yt-dlp (dump metadata) ──> jq / DuckDB (query)
```

### Manage Python projects at Rust speed

Create virtual environments, install packages, run scripts with inline dependencies, lint and format code — all 10-100x faster than traditional Python tooling.

**Tools**: `uv` for package management and venvs, `Ruff` for linting and formatting

```
uv venv ──> uv add deps ──> ruff check --fix ──> ruff format ──> uv run pytest
```

### Automate your CI pipeline locally

Run GitHub Actions in Docker before pushing, define project tasks as recipes, generate changelogs from commits, create releases, and back up before destructive operations.

**Tools**: `act` for local GH Actions, `just` for task recipes, `git-cliff` for changelogs, `gh` for GitHub API, `restic` for encrypted backups

```
act -j test ──> git-cliff changelog ──> gh release create ──> restic backup
```

---

## Speed and Efficiency vs. Standard Tools

Each skill replaces slower, less capable, or more verbose standard alternatives. The table below shows what each tool replaces and the measured performance advantage.

### Data Processing

| Task | Standard Tool | cli-power-skills Tool | Speed/Efficiency Gain |
|------|--------------|----------------------|----------------------|
| JSON querying and transformation | Python `json` module + script | **jq** | ~5-10x faster (no interpreter startup, single pipeline vs multi-line script) |
| CSV column stats, search, sort | `awk` / `cut` / Python pandas | **xsv** | ~10x faster on large files (Rust, zero-copy CSV parsing, handles quoted fields correctly unlike awk) |
| CSV/JSON record transforms | `awk` with manual parsing | **miller (mlr)** | ~3-5x faster (native format awareness, no manual field splitting or quoting bugs) |
| SQL queries on local files | Load into PostgreSQL/SQLite, then query | **DuckDB** | ~50-100x faster setup (zero config, reads CSV/Parquet/JSON directly, columnar engine on large data) |
| YAML/TOML/XML reading | Custom Python parsers per format | **yq** | ~5x faster (single binary, consistent syntax across formats, no script needed) |
| Exploring unknown JSON structure | Manual inspection / Python pretty-print | **gron** | ~3x faster discovery (greppable paths, instantly find nested keys without knowing structure) |

### Security Scanning

| Task | Standard Tool | cli-power-skills Tool | Speed/Efficiency Gain |
|------|--------------|----------------------|----------------------|
| Dependency vulnerability scanning | `npm audit` + `pip audit` + `bundler-audit` (one per ecosystem) | **Trivy** | ~3x fewer commands (single scan covers all ecosystems, containers, IaC in one pass) |
| Shell script linting | Manual code review | **ShellCheck** | ~20x more issues caught (detects quoting bugs, globbing pitfalls, POSIX portability issues humans miss) |
| Secrets management in repos | Plaintext `.env` files or external vault setup | **sops** | ~10x simpler workflow (encrypts in-place, version-control friendly, no external server needed) |

### API Testing

| Task | Standard Tool | cli-power-skills Tool | Speed/Efficiency Gain |
|------|--------------|----------------------|----------------------|
| Multi-step API test suites | Bash curl scripts with manual assertion parsing | **Hurl** | ~5-10x less code (declarative syntax, built-in assertions, variable capture, no bash scripting) |
| Probing many URLs for status/headers | `curl` in a for loop (sequential) | **httpx** | ~50-100x faster (massively concurrent, structured JSON output, tech detection built in) |

### Web Crawling

| Task | Standard Tool | cli-power-skills Tool | Speed/Efficiency Gain |
|------|--------------|----------------------|----------------------|
| JS-rendered page scraping | Selenium (verbose API, flaky waits) | **Playwright** | ~2-3x less code, ~30% faster execution (auto-wait, multi-browser, better selectors) |
| URL/endpoint discovery | Manual browsing or custom link extraction | **Katana** | ~100x faster (Go binary, recursive, handles JS-rendered links, structured output) |
| Large-scale structured crawling | Hand-rolled request loops + retry logic | **Scrapy** | ~5x faster development (built-in rate limiting, pipelines, persistence, middleware) |
| Sites with anti-bot protection | Manual proxy rotation + header spoofing | **Crawlee** | ~10x simpler setup (anti-blocking built in, proxy rotation, session management) |

### Web Research

| Task | Standard Tool | cli-power-skills Tool | Speed/Efficiency Gain |
|------|--------------|----------------------|----------------------|
| Article text extraction | `curl` + BeautifulSoup manual parsing | **newspaper4k** | ~10x less code (automatic boilerplate removal, metadata extraction, one function call) |
| Video/audio download + metadata | Browser extensions, online converters | **yt-dlp** | ~20x more capable (1000+ sites, format selection, subtitles, metadata, batch download) |

### Python Tooling

| Task | Standard Tool | cli-power-skills Tool | Speed/Efficiency Gain |
|------|--------------|----------------------|----------------------|
| Package installation | `pip install` | **uv pip install** | ~10-100x faster (Rust resolver, parallel downloads, better caching) |
| Virtual environment creation | `python -m venv` | **uv venv** | ~10x faster (Rust, built-in Python version management) |
| Linting (style + errors + imports) | `flake8` + `isort` + `pylint` (3 tools, 3 configs) | **Ruff** | ~10-100x faster (single Rust binary replaces all three, one config file) |
| Code formatting | `black` | **Ruff format** | ~10-30x faster (99.9% Black-compatible, Rust vs Python) |

### CI Automation

| Task | Standard Tool | cli-power-skills Tool | Speed/Efficiency Gain |
|------|--------------|----------------------|----------------------|
| Test GitHub Actions locally | Push and wait for CI (minutes per iteration) | **act** | ~10-50x faster feedback (runs in local Docker, seconds instead of minutes) |
| Project task recipes | `make` (tab-sensitive, cryptic syntax) | **just** | ~2x better DX (no tab sensitivity, built-in arguments, cross-platform, readable syntax) |
| Changelog generation | Manual writing from git log | **git-cliff** | ~100x faster (auto-generated from conventional commits, configurable templates) |
| Encrypted incremental backups | `tar` + `gpg` + manual rotation | **restic** | ~5-10x simpler (deduplication, encryption by default, incremental, JSON status) |

---

## Why CLI Skills Over MCP Tools

MCP (Model Context Protocol) servers are powerful for connecting Claude to external services, but CLI skills are the better choice for local development workflows. Here's why:

### Instant execution, zero overhead
CLI tools run as direct shell commands — there is no server to start, no WebSocket handshake, no JSON-RPC protocol overhead. A `jq` query executes in milliseconds. An MCP server must boot a Node.js/Python process, establish a connection, serialize the request, deserialize the response, and keep a process alive for the session. For the rapid-fire tool usage typical of data processing or CI pipelines, this overhead adds up to seconds per operation.

### Composable Unix pipelines
CLI tools pipe into each other natively: `katana | httpx | jq | duckdb`. Each tool does one thing well and passes structured output to the next. MCP tools are isolated function calls — you cannot pipe the output of one MCP tool directly into another without Claude mediating every step. This means more round-trips, more tokens consumed, and more latency. A 5-stage CLI pipeline runs as a single Bash command; the equivalent MCP workflow requires 5 separate tool calls with Claude parsing and forwarding results between each.

### Full ecosystem access
These skills teach Claude to use 26 battle-tested CLI tools built by dedicated communities (DuckDB, Playwright, Trivy, etc.). MCP servers typically wrap a subset of one tool's functionality behind a simplified API. For example, a Playwright MCP server might expose 10 actions; the CLI skill teaches Claude the full Playwright API including selectors, network interception, multi-browser testing, and PDF generation. You get the complete tool, not an abstraction layer's view of it.

### No process management
MCP servers are long-lived processes that consume memory, can crash, need restarts, and require configuration in `claude_desktop_config.json` or `settings.json`. CLI tools are stateless — they run, produce output, and exit. No zombie processes, no port conflicts, no "MCP server disconnected" errors mid-session.

### Works everywhere, offline
CLI tools work on air-gapped machines, in CI runners, inside Docker containers, and on any OS. MCP servers often depend on specific runtimes (Node.js, Python), network access for installation, and Claude Code's MCP infrastructure. A `trivy fs .` works whether Claude is involved or not — the same command runs in your CI pipeline, your pre-commit hook, or your terminal.

### Debuggable and auditable
When a CLI command fails, the error message is right there in the terminal. You can copy the exact command, run it yourself, and debug it. MCP tool failures are wrapped in protocol layers — the error might be in the server code, the transport, the serialization, or the tool itself. CLI commands are also visible in shell history, making it trivial to audit what Claude did and reproduce it.

---

## Design Principles

- **Agentic** — Claude automatically reaches for tools based on task context
- **Complementary** — extends Claude's capabilities, doesn't replace built-in tools (Grep, Glob, Read)
- **Assume installed** — no install checks; missing tools produce natural shell errors
- **Layered recipes** — single-tool patterns for common tasks, multi-tool pipelines for complex workflows
