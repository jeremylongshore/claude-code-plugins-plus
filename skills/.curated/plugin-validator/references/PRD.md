# PRD: Plugin Validator

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

The CI pipeline for claude-code-plugins runs 10+ validation checks across JSON schemas, frontmatter format, file structure, security patterns, and marketplace catalog consistency. When a check fails in CI, the developer must decode cryptic error messages, identify which file is wrong, figure out the fix, push again, and wait for CI. This feedback loop wastes 10-30 minutes per cycle. Developers need a local pre-commit validator that runs the same checks as CI and provides actionable fix commands.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Plugin Developer | About to commit or push plugin changes | Local validation that catches CI failures before they happen |
| New Contributor | Creating their first plugin and unsure of all requirements | Clear pass/fail report with fix commands for every failure |
| CI Debugger | Investigating why a plugin failed in the pipeline | Same checks as CI with detailed error messages identifying exact files and fields |

## Success Criteria

1. Catch 100% of issues that would fail in CI when run locally
2. Every failed check includes the specific file, line/field, and a runnable fix command
3. Complete validation of a single plugin in under 10 seconds
4. Report format clearly distinguishes blocking failures from non-critical warnings

## Functional Requirements

1. Validate required files exist: `.claude-plugin/plugin.json`, `README.md`, `LICENSE`, and at least one component directory
2. Validate `plugin.json` schema: required fields present, no disallowed fields, semver format, kebab-case name
3. Validate frontmatter in all component files (commands, agents, skills) against their respective schemas
4. Check directory structure matches the expected plugin hierarchy
5. Verify all `.sh` files have execute permissions
6. Run security scans: hardcoded secrets, dangerous commands, suspicious URLs
7. Validate marketplace compliance: entry exists in `marketplace.extended.json` with matching metadata
8. Validate README content: contains installation, usage, and description sections
9. Check hook path variables use `${CLAUDE_PLUGIN_ROOT}` not hardcoded paths
10. Compile results into a structured validation report with pass/fail per check

## Non-Functional Requirements

- Read-only: never modify the validated plugin or catalog files
- Must run without network access (all checks are local)
- Compatible with both individual plugin paths and full-repository scans
- Exit code reflects pass/fail for CI integration (0 = pass, 1 = fail)
- Validation must complete in under 10 seconds for any single plugin
- Error messages must identify the exact file, field, and expected value
- Report format must be consistent for automated parsing

## Dependencies

- Read access to the target plugin directory and `.claude-plugin/marketplace.extended.json`
- `jq` installed for JSON validation
- `grep` and `find` available on PATH for pattern scanning
- `./scripts/validate-all-plugins.sh` available at the repository root (for comparison)

## Out of Scope

- Fixing found issues automatically (validation only; see plugin-auditor for remediation guidance)
- Validating MCP plugin runtime behavior (build and test are separate steps)
- Marketplace search index or route validation (handled by marketplace build pipeline)
- Cross-plugin dependency checking
- Quality scoring beyond pass/fail (see plugin-auditor for scored audits)
- Network-dependent checks (all validation is local)
