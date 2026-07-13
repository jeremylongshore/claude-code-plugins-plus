# ARD: Plugin Validator

> Part of [Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)

## System Context

The Plugin Validator runs the same structural and compliance checks as the CI pipeline, but locally and with actionable fix output. It operates read-only within the monorepo.

```
Target Plugin Directory
       ↓
[Plugin Validator]
  ├── Reads: plugin.json, README.md, LICENSE, frontmatter, marketplace.extended.json
  ├── Checks: structure, schema, frontmatter, permissions, security, marketplace
  └── Produces: validation report
       ↓
Validation Report
  ├── Per-check PASS/FAIL status
  ├── Fix commands for failures
  ├── Warning list for non-critical issues
  └── Overall PASSED/FAILED verdict
```

## Data Flow

1. **Input**: Target plugin path (e.g., `plugins/devops/my-plugin/`). Defaults to current directory if it contains `.claude-plugin/`.
2. **Processing**: Execute 10 validation checks sequentially: file existence, plugin.json schema, frontmatter parsing, directory structure, script permissions, security patterns, marketplace entry, README content, hook variables, and cross-field consistency. Collect pass/fail results with details for each.
3. **Output**: Structured validation report with total pass/fail count (e.g., "8/10 PASSED"), per-check results, fix commands for failures, warnings for non-critical issues, and overall PASSED/FAILED verdict.

## Key Design Decisions

| Decision | Choice | Rationale |
|----------|--------|-----------|
| CI-parity checks | Same validation logic as `validate-all-plugins.sh` | Ensures local validation catches exactly what CI catches; no surprises |
| Fix commands in output | Every failure includes a runnable command | Eliminates guesswork; developer can copy-paste to fix |
| Sequential check execution | Run all checks even if early ones fail | Complete picture in one run; developer fixes all issues at once |
| Read-only operation | Never modify files during validation | Validators should never have side effects; separation of concerns |
| Local-only execution | No network calls required | Works offline, fast, deterministic |
| Structured output format | Consistent report structure with pass/fail indicators | Enables CI parsing and human reading from the same output |
| Allowed-field allowlist | Check plugin.json against explicit field list | Catches extra fields that CI rejects; more reliable than a denylist |

## Tool Usage Pattern

| Tool | Purpose |
|------|---------|
| Read | Parse plugin.json, README.md, LICENSE, component frontmatter, and marketplace.extended.json |
| Grep | Search for security patterns (secrets, dangerous commands), disallowed fields, hardcoded paths |
| Bash(cmd:*) | Run `jq empty` for JSON validation, check file permissions with `ls -la`, verify file existence |

## Error Handling Strategy

| Error Class | Detection | Recovery |
|------------|-----------|----------|
| Plugin directory not found | Target path does not exist | Report immediately with suggestion to check the path; list plugins with `ls plugins/*/` |
| JSON parse error | `jq empty` returns non-zero | Report exact error location from jq output; provide the command to debug |
| Missing frontmatter delimiters | File lacks opening `---` or closing `---` | Report the file path; provide the frontmatter template for the component type |
| Disallowed plugin.json fields | Fields present that are not in the allowed set | List the disallowed fields; provide `jq 'del(.fieldname)'` command to remove each |
| Script not executable | `ls -la` shows no execute bit on `.sh` files | Provide `chmod +x <path>` for each non-executable script |

## Extension Points

- Custom validation rules: allow `.validation-config.yml` for project-specific checks or skip rules
- JSON output mode: emit machine-readable JSON for CI pipeline consumption and quality dashboards
- Batch validation: validate all plugins in a category or the entire repository with a single command
- Severity levels: distinguish critical (blocks publish), warning (should fix), and info (nice to have)
- Watch mode: re-validate on file changes during plugin development
- Pre-commit hook: register as a git pre-commit hook that blocks commits with validation failures
- Diff-mode: validate only files changed in the current git diff for faster iteration
