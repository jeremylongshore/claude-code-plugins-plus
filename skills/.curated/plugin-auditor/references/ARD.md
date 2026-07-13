# ARD: Plugin Auditor

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Plugin Auditor is a read-only inspection skill that scans plugin files against eight audit categories and produces a scored quality report. It operates within the monorepo and references the marketplace catalog for compliance checks.

```
Target Plugin Directory
       ↓
[Plugin Auditor]
  ├── Reads: all plugin files, plugin.json, marketplace.extended.json
  ├── Scans: security patterns, structure, compliance, git state
  └── Produces: scored audit report
       ↓
Audit Report
  ├── Per-category scores (x/10)
  ├── Failed checks with fix commands
  ├── Overall rating (Excellent/Good/Needs Work/Failed)
  └── Prioritized recommendations
```

## Data Flow

1. **Input**: Target plugin path (e.g., `plugins/security/plugin-name/`). May include audit scope (full, security-only, publish-readiness).
2. **Processing**: Confirm plugin directory exists and contains `plugin.json`. Execute eight audit passes sequentially: security scan (secrets, injection, obfuscation), best practices (structure, permissions, dead code), CLAUDE.md compliance (fields, hooks, layout), marketplace compliance (catalog entry, version match), git hygiene (committed artifacts), MCP-specific checks (if applicable), performance indicators, and UX assessment. Score each category 0-10.
3. **Output**: Structured audit report with plugin identification, per-category results (passed checks, failed checks with fix commands, warnings), numeric scores, overall rating, and prioritized recommendations with estimated fix time.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| Eight fixed categories | Security, Best Practices, Compliance, Marketplace, Git, MCP, Performance, UX | Covers the full quality surface; matches the CI pipeline's validation scope |
| Read-only operation | Never modify audited files | Auditors observe; remediation is a separate step with explicit user consent |
| Fix commands in output | Every failure includes a runnable fix | Reduces time-to-fix from "figure out what's wrong" to "run this command" |
| Numeric scoring | 0-10 per category, composite overall | Enables objective comparison across plugins and over time |
| Pattern-based security scan | Regex patterns for secrets, injection, obfuscation | Fast, deterministic, no external service dependency |
| Context-aware filtering | Skip patterns inside code blocks and test directories | Reduces false positives from documentation examples and test fixtures |
| Tiered rating system | Excellent/Good/Needs Work/Failed based on composite score | Clear actionability: Failed blocks publish, Needs Work requires fixes, Good/Excellent are publishable |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Inspect plugin.json, README.md, LICENSE, frontmatter in component files, marketplace.extended.json |
| Grep | Search for security patterns (API keys, secrets, dangerous commands, suspicious URLs) across all plugin files |
| Bash(cmd:*) | Run `jq` for JSON validation, check file permissions, verify git status, list directory contents |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Plugin directory not found | Path does not exist or lacks plugin.json | Report error immediately; suggest listing plugins with `ls plugins/*/` |
| Malformed plugin.json | `jq empty` returns non-zero | Report the parse error location; provide `jq` command to identify the broken line |
| Marketplace entry missing | Plugin name not found in marketplace.extended.json | Score marketplace compliance as 0; provide the fields needed to add the entry |
| Permission errors | File read fails with EACCES | Report which files are inaccessible; suggest `chmod` or ownership change |
| False positive in security scan | Pattern matches documentation or test fixture content | Apply context-aware filtering (skip patterns inside markdown code blocks and test directories) |

## Extension Points

- Custom audit rules: allow plugins to define `.audit-config.yml` for project-specific checks or exclusions
- CI integration: output machine-readable JSON for quality gates in GitHub Actions
- Historical tracking: store audit scores in a database to track quality trends per plugin
- Comparative reports: audit multiple plugins and rank them by overall score
- Severity weighting: allow configuring which categories are blocking vs advisory
- Auto-fix mode: pair with plugin-validator to automatically fix simple issues (permissions, missing fields)
- Community scoring: aggregate audit scores across all marketplace plugins for public quality badges
