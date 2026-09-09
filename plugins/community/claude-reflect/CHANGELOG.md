# Changelog

All notable changes to claude-reflect will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [3.1.0] - 2026-03-16

### Added
- **Comprehensive CJK support** — Pattern detection now works for Chinese, Japanese, and Korean (#24, thanks @shohu and @yulin0629)
  - 13 CJK correction patterns: Japanese (8), Chinese (3), Korean (2)
  - Full-width `？` and CJK question particles (`嗎吗呢か까`) in false positive filter
  - CJK-aware short message threshold (2 chars for CJK vs 4 for ASCII)
  - Non-correction English phrase filter (`No problem`, `don't worry`, `never mind`, etc.)
- **Per-project queue scoping** — Learnings queue is now stored per-project to prevent cross-contamination (#21, thanks @marcodelpin)
  - Queue files at `~/.claude/projects/<encoded>/learnings-queue.json`
  - Automatic migration from legacy global queue on first access
  - Updated `/view-queue`, `/skip-reflect`, `/reflect` commands

### Fixed
- Windows CI: path encoding tests now platform-agnostic (no longer hardcode Unix paths)

## [3.0.1] - 2026-02-12

### Added
- **`--model` flag** — Control which model is used for semantic analysis during `/reflect` (#16)
  - Default: `sonnet` (cost-effective for classification tasks)
  - Usage: `/reflect --model haiku` for faster/cheaper, `/reflect --model opus` for maximum accuracy
  - Previously defaulted to user's CLI model (often Opus), burning expensive tokens on simple classification

### Changed
- `DEFAULT_MODEL = "sonnet"` in `semantic_detector.py` — all semantic analysis functions (`semantic_analyze`, `validate_tool_error`, `detect_contradictions`) now default to sonnet instead of inheriting the user's CLI model

## [3.0.0] - 2026-02-12

### Added
- **Full Memory Hierarchy Integration** — `/reflect` now supports all 6 Claude Code memory tiers:
  - `.claude/rules/*.md` — Modular rule files with optional YAML `paths:` frontmatter for path-scoping
  - `~/.claude/rules/*.md` — User-level global rule files
  - `CLAUDE.local.md` — Personal, gitignored learnings
  - Auto memory (`~/.claude/projects/<project>/memory/*.md`) — Low-confidence staging area
- **Hierarchy-Aware Routing** — `suggest_claude_file()` now routes by learning type:
  - Guardrails → `.claude/rules/guardrails.md`
  - Model preferences → model-preferences rule file or global CLAUDE.md
  - Low-confidence (0.60-0.74) → auto memory for later promotion
  - Path-scoped rules → matching rule file by `paths:` frontmatter
- **`--organize` command** — Analyze memory hierarchy and suggest reorganization:
  - Detects overgrown files, wrong-tier entries, scattered topics, promotion candidates
  - Presents issues with suggested fixes, applies with user approval
- **Auto Memory Enrichment (Step 1.6)** — During `/reflect`, scans auto memory for promotion candidates and routes low-confidence items to auto memory
- **Cross-Tier Duplicate Detection** — Step 4 now searches all memory tiers (CLAUDE.md, rules, local, auto memory)
- **Rule File Mapping** — Learning type → suggested rule file mapping table in reflect.md
- **New utilities in `reflect_utils.py`**:
  - `_parse_rule_frontmatter()` — Line-based YAML parser for rule frontmatter (no PyYAML dependency)
  - `get_project_folder_name()` — Claude Code folder name encoding
  - `get_auto_memory_path()` — Auto memory directory resolution
  - `read_auto_memory()` — Read all auto memory topic files
  - `suggest_auto_memory_topic()` — Keyword-based topic filename suggestion
  - `read_all_memory_entries()` — Cross-tier entry reader for deduplication
- **New test file** `tests/test_memory_hierarchy.py` with 28 tests covering all new functionality
- Backward-compat tests added to `tests/test_reflect_utils.py`

### Changed
- `find_claude_files()` now discovers `CLAUDE.local.md`, `.claude/rules/*.md`, and `~/.claude/rules/*.md`
- `suggest_claude_file()` accepts optional `learning_type` parameter for smarter routing
- `--targets` display updated with full hierarchy view (rules, local, auto memory)
- Step 7 (Apply Changes) now handles rule files and auto memory destinations

## [2.6.0] - 2026-02-12

### Added
- **Session retention warning** - SessionStart hook warns when `cleanupPeriodDays` is not configured
  - Claude Code deletes sessions after 30 days by default, which affects `/reflect --scan-history` and `/reflect-skills`
  - Self-resolving: warning disappears once user adds `{"cleanupPeriodDays": 99999}` to `~/.claude/settings.json`
  - New `get_cleanup_period_days()` utility in reflect_utils.py
- **README tip #7** - Documents the recommended `cleanupPeriodDays` setting

## [2.5.1] - 2026-02-04

### Fixed
- **False positive filtering** - System content (`<task-notification>`, `<system-reminder>`, session continuations) no longer triggers false pattern matches (#15)
  - Added `should_include_message()` filter before pattern detection
  - Added `MAX_CAPTURE_PROMPT_LENGTH` (500 chars) guard — real corrections are short, system content is long
  - Explicit `remember:` markers bypass length filter
  - Thanks to @DmitryBMsk for the contribution!

### Changed
- Made `_should_include_message` public as `should_include_message()` (backward-compatible alias preserved)
- Test count increased from 141 to 160

## [2.5.0] - 2026-01-25

### Added
- **Session Start Reminder** - New SessionStart hook shows pending learnings when you start a session (#13)
  - Displays up to 5 learnings with confidence scores
  - Reminds to run `/reflect` at the right time
  - Can be disabled via `CLAUDE_REFLECT_REMINDER=false` environment variable
  - Thanks to @xqliu for the contribution!

## [2.4.0] - 2026-01-23

### Added
- **Capture Feedback** - Hooks now output confirmation when learnings are captured (#10)
  - Example: `📝 Learning captured: 'no, use gpt-5.1 not gpt-5' (confidence: 85%)`
  - Claude acknowledges captures in real-time
- **Confidence in /view-queue** - Queue display now shows confidence scores, patterns, and relative timestamps
  - Format: `[0.85] "message preview..." (pattern-name) - 2 days ago`
- **Guardrail Pattern Detection** - New pattern type for "don't do X" constraints
  - Detects: "don't add X unless", "only change what I asked", "stop refactoring unrelated", etc.
  - Higher confidence (0.85-0.90) for constraint-based corrections
  - Routes to new `## Guardrails` section in CLAUDE.md
- **Contradiction Detection** - Semantic analysis to find conflicting CLAUDE.md entries
  - New `detect_contradictions()` function in semantic_detector.py
  - Integrated into `/reflect --dedupe` workflow
  - Resolution options: keep first, keep second, merge, or keep both

### Changed
- `/reflect --dedupe` now checks for contradictions before similarity grouping
- Added `## Guardrails` to standard section headers

## [2.1.1] - 2026-01-06

### Fixed
- **Plugin installation error** - Removed duplicate hooks declaration from plugin.json (#9)
  - The `hooks/hooks.json` file is auto-loaded by Claude Code; explicitly declaring it in manifest caused "Duplicate hooks file detected" error

## [2.1.0] - 2026-01-05

### Added
- **Tool Error Extraction** - Scan session files for repeated tool execution errors and convert to CLAUDE.md guidelines (#7)
  - Extracts connection errors, environment issues, module not found errors
  - Filters out Claude Code guardrails and one-off errors
  - Usage: `/reflect --scan-history --include-tool-errors`
- **Mandatory TodoWrite Tracking** - `/reflect` workflow now uses TodoWrite to track all phases

### Changed
- Improved workflow visibility with real-time progress tracking

## [2.0.0] - 2026-01-04

### Added
- **Windows Support** - Native Python scripts replace bash, no WSL required (#1)
- **Semantic AI Detection** - Multi-language support via `claude -p` (#2, #3)
- **UserPromptSubmit Hook** - Automatic capture now properly registered
- **GitHub Actions CI** - Automated testing on Windows, macOS, Linux (Python 3.8 & 3.11)
- **Comparison Tool** - `scripts/compare_detection.py` for testing detection accuracy
- **90 Unit Tests** - Comprehensive test coverage with mocked Claude CLI calls

### Changed
- Hooks now use Python scripts instead of bash for cross-platform compatibility
- `/reflect` command validates queue items with semantic AI before presenting
- Detection uses hybrid approach: regex patterns (fast, real-time) + semantic AI (accurate, during /reflect)
- Updated documentation (README.md, CLAUDE.md) with new architecture

### Deprecated
- Bash scripts moved to `scripts/legacy/` (still available for reference)

### Fixed
- Hooks failing on Windows due to bash dependency (#1)
- False positives from English-only regex patterns (#2)
- Multi-language corrections not being detected (#3)
- UserPromptSubmit hook not registered in hooks.json

## [1.4.1] - 2025-12-xx

### Fixed
- Critical jq filter bug in distribution files
- Historical scan now ensures matches are always presented to user
- Queue items being ignored during history scan

## [1.4.0] - 2025-12-xx

### Added
- Confidence scoring for learnings (0.60-0.90)
- Positive feedback pattern detection
- AGENTS.md sync support
- Semantic deduplication (`/reflect --dedupe`)

## [1.3.5] - 2025-12-xx

### Changed
- PreCompact hook now informs and backs up instead of blocking

## [1.3.4] - 2025-12-xx

### Fixed
- Restored UserPromptSubmit hook for automatic capture
