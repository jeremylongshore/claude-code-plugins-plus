# Changelog

All notable changes to this project are documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.3.0] - 2026-01-29

### Added
- SessionStart hook for plugin-based persistent mode (replaces UserPromptSubmit hook)
- Persistent state stored in plugin-owned directory; survives plugin updates, removed on uninstall
- Project-scoped persistent mode (`/hyperfocus persistent project`) for per-project configuration
- `/hyperfocus status` command to report current session mode and persistent state
- Capability matrix (plugin vs standalone skill) in README
- Migration guide for upgrading from 0.2.x (cleanup instructions for old settings hooks)
- CI workflow (validate, shellcheck, integration tests)
- `scripts/hyperfocus-state` POSIX shell helper for state management
- `scripts/hyperfocus-hook.sh` SessionStart hook implementation

### Changed
- Single source of truth for rules: `references/core.md`, `references/clean.md`, `references/flow.md`, `references/zen.md`
- Layout flattening: removed duplicate skill copies; unified repo structure
- `/hyperfocus persistent` now uses SessionStart hook instead of modifying settings.json
- README rewritten per spec: install instructions, usage table, persistent mode semantics
- Clean mode description: clarified as "quick answers, PR summaries" (not code reviews; reviews are exempt per boundaries)
- Research claim softened to "informed by cognitive-accessibility research and guidance"

### Fixed
- Plugin manifest now validates with `--strict` (removed `interface` block from `.claude-plugin/plugin.json`)
- Auto-Clarity rule corrected: numbered steps still allowed; only symbol-substitution removed from safety-critical sequences
- Code block lead-in rule clarified (one-line prose, not code comment)

### Removed
- Star prompt (one-time activation popup removed entirely)
- Duplicate skill trees
- `UserPromptSubmit` hook mechanism (replaced by SessionStart)
- `hyperfocus/` and `plugins/` directories (flattened into root structure)
- `hyperfocus-rules.txt` (rules now managed by plugin/skill)

### Technical Details
- State format: line-based key=value (no JSON); version 1, mode ∈ {clean, flow, zen}, enabled ∈ {true, false}
- Precedence: project state > global state; missing/disabled/corrupt state → no injection
- POSIX sh requirement for persistent hooks (macOS, Linux, WSL)
- Standalone `npx skills` installation no longer supports persistence hooks

---

## [0.2.0] - 2024-12-15

### Added
- Zen mode: ultra-condensed output with TL;DR, lists, and tables (no dense prose)
- Persistent mode: auto-activation via hook (experimental UserPromptSubmit mechanism)
- Plugin marketplace support and instructions
- Star prompt on first activation

### Changed
- README overhaul: ADHD-friendly formatting applied to documentation itself
- Enhanced visual hierarchy with badges and comparison tables
- Improved prose structure (short sentences, clear sections, front-loaded points)

### Fixed
- Plugin manifest fixes and category normalization

---

## [0.1.0] - 2024-11-01

### Added
- Initial release: ADHD-friendly output formatting for Claude
- Three modes: Clean, Flow, and Zen
- Session-based activation via `/hyperfocus` command
- Formatting rules for improved cognitive accessibility
- Research-backed principles (chunking, front-loading, visual hierarchy)
- Support for Claude Code, Codex, and GitHub Copilot
- Detailed README with before/after examples

[0.3.0]: https://github.com/nextor2k/hyperfocus/compare/v0.2.0...v0.3.0
[0.2.0]: https://github.com/nextor2k/hyperfocus/compare/v0.1.0...v0.2.0
[0.1.0]: https://github.com/nextor2k/hyperfocus/releases/tag/v0.1.0
