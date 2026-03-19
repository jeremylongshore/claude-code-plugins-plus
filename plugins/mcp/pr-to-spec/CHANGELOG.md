# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.1.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

## [0.8.0] - 2026-03-18

### Added
- **MCP Server** (`servers/pr-spec-analyzer.ts`) — 6-tool Model Context Protocol server exposing `analyze_pr`, `scan_local`, `check_drift`, `set_intent`, `show_intent`, and `analyze_assumptions` via stdio transport
- **Claude Code plugin metadata** (`.claude-plugin/plugin.json`, `.mcp.json`) — enables pr-to-spec as a standalone MCP plugin for Claude Code, Cursor, and Windsurf
- `@modelcontextprotocol/sdk` dependency for MCP protocol compliance
- `--debug` flag for CLI — logs API request URLs, git commands, and timing info to stderr
- `PR_TO_SPEC_DIR` env var — configurable storage directory (default: `.pr-to-spec`)
- Security test suite (`tests/security.test.ts`) — webhook URL validation, custom_command rejection, prototype pollution guard
- API error test suite (`tests/github-errors.test.ts`) — 401, 403, 404, 422, rate limit, large PR truncation
- README: documented all subcommands (`intent`, `check`, `contract`, `graph`, `feedback`)
- README: exit code 4 (`gate_failed`)
- README: troubleshooting section with common errors

### Security
- **Removed `custom_command` contract type** — eliminated command injection vector from arbitrary shell execution. The type is preserved in the schema but always fails with a clear deprecation message.
- **Webhook SSRF prevention** — validates webhook URLs: requires HTTPS, rejects localhost, private IPs (10.x, 172.16-31.x, 192.168.x), and link-local addresses (169.254.x).
- **Reduced GitHub Action permissions** — `contents: write` → `contents: read` (the action only reads PRs and posts comments).
- **Prototype pollution guard** — `--field` extraction blocks `__proto__`, `constructor`, and `prototype` traversal.
- **Secret masking** — webhook URLs are masked in error output to prevent leaking sensitive endpoints.

### Fixed
- **Version sync** — CLI and Action version strings updated from stale `0.6.0` to `0.8.0`
- **API error messages** — GitHub API errors now return user-friendly messages instead of raw Octokit exceptions (401, 403, 404, 422, rate limit)
- **Git error messages** — `scan`/`check` commands now surface clear messages for "not a git repo" and "unknown revision" errors
- **Large PR warning** — warns when GitHub API returns 300 files (the per-page maximum), indicating truncation

### Changed
- 384 tests passing (all existing tests updated for security changes)

## [0.7.0] - 2026-03-17

### Added
- **Intent DAG**: Graph-based intent tracking with spec fragments, decision taxonomy, and propagation engine
- `graph` subcommand — query ancestors/descendants, compute impact, view graph stats
- `contract` subcommand — declarative contract verification (no_new_dependencies, no_file_outside_scope, max_files_changed, no_pattern_in_diff, require_pattern_in_diff, no_new_exports, custom_command)
- `intent approve` / `intent lock` — approval workflow (draft → approved → locked)
- `intent gate` — evaluate gate policy (min_confidence, require_no_stale, require_no_must_ask)
- Graph materialization — gate and contract results become audit trail nodes
- Feedback ingestion — learn from reviews to improve future classifications
- 364 tests (84 new tests for Intent DAG)

### Changed
- Contract evaluator: smarter `no_new_dependencies` detection (lock files vs manifest files)
- Protocol envelope: `gate_failed` status with exit code 4
- `check` subcommand: integrated contract evaluation and gate checks

## [0.6.0] - 2026-03-17

### Changed
- **Renamed**: `pr-to-prompt` → `pr-to-spec`
- **Positioning**: "The flight envelope for agentic coding"

### Added
- `DiffSource` abstraction — works on any diff (local branches, staged changes, GitHub PRs)
- `scan` subcommand — analyze local git changes without GitHub
- `intent` subcommand — declare expected scope, risk ceiling, change type
- `check` subcommand — scan + drift detection against declared intent
- Drift signals: `scope_creep`, `forbidden_touch`, `risk_escalation`, `size_overrun`, `type_mismatch`
- Agent protocol envelope wraps all `--json` output
- Claude Code skill manifest (`.claude/skills/pr-to-spec/SKILL.md`)

### Backwards Compatible
- `pr-to-spec --repo owner/repo --pr 42 --json` still works unchanged

## [0.5.0] - 2026-03-09

### Added
- JSON output format with `--format json` for agent-friendly piping (#7)
- Bash-friendly CLI flags: `--quiet`, `--field <path>`, `--json` shorthand (#8)
- Exit code semantics: 0=success, 1=error, 2=high-risk PR detected (#8)
- `decision_prompt` field in spec for agent-driven review decisions (#12)
- Webhook notifications via `webhook_url` input in GitHub Action (#11)
- Example integrations: `claude-code.md`, `bash-agent.sh`, `github-action-chain.yml` (#10)

### Changed
- README rewritten with agent-first positioning and piping examples (#9)

## [0.4.0] - 2026-03-09

### Added
- Review parsing with `parseReviews()` for aggregated review summaries
- Monorepo detection with `detectMonorepo()` for workspace-aware specs
- Semantic diff analysis with `analyzeSemanticDiff()` for change categorization
- Spec diffing with `diffSpecs()` for comparing spec versions
- Review comments integration in PR data and rendered outputs

## [0.3.0] - 2026-03-09

### Added
- GitHub Marketplace release as official Action
- Action bundle with `@vercel/ncc` for single-file distribution

## [0.2.0] - 2026-03-09

### Added
- AI enhancement with `--ai-enhance` flag (Anthropic/OpenAI support)
- Compact spec output via `compactSpec()` for smaller payloads
- GitHub Action for automated PR spec generation

## [0.1.0] - 2026-03-09

### Added
- Initial release
- Core PR parsing with `generateSpec()`
- Risk classification with severity levels
- YAML and Markdown rendering
- PR comment posting via `--comment` flag
- GitHub API client with Octokit
