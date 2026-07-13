# PRD: Plugin Auditor

**Version:** 1.0.0
**Author:** Jeremy Longshore <jeremy@intentsolutions.io>
**Status:** Active
**Marketplace:** [tonsofskills.com](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io)
**Portfolio:** [jeremylongshore.com](https://jeremylongshore.com)

---

## Problem Statement

Claude Code plugins can introduce security vulnerabilities (hardcoded secrets, command injection, obfuscated code), violate repository standards (wrong fields in plugin.json, broken marketplace entries, incorrect frontmatter), or carry quality issues (missing tests, dead code, poor documentation). Without systematic auditing, these problems reach the marketplace and erode user trust. Manual reviews are inconsistent and miss patterns that automated scanning would catch.

## Target Users

| User | Context | Primary Need |
|------|---------|-------------|
| Plugin Author | Preparing a plugin for marketplace publication | Security and quality audit before submitting for review |
| Marketplace Maintainer | Reviewing community-submitted plugins | Standardized audit report with scoring to make accept/reject decisions |
| Security Reviewer | Evaluating plugin safety before installation | Security-focused audit covering secrets, injection vectors, and obfuscation |
| Quality Gatekeeper | Assessing plugins for featured status | Elevated quality audit with higher thresholds for documentation and coverage |

## Success Criteria

1. Detect 100% of hardcoded secrets, API keys, and private key headers in plugin files
2. Produce a scored audit report across eight categories with per-category scores out of 10
3. Every failed check includes a specific fix command or action that resolves the issue
4. Audit completes in under 30 seconds for any single plugin

## Functional Requirements

1. Scan all plugin files for hardcoded secrets, API keys, AWS access keys, and private key headers
2. Detect dangerous commands (`rm -rf /`, `eval()`, `exec()`) and command injection vectors
3. Flag suspicious URLs (non-HTTPS, raw IP addresses) and obfuscated code (base64 decode, hex encoding)
4. Validate plugin structure: required files exist, semver format correct, script permissions set
5. Check CLAUDE.md compliance: directory structure, allowed fields in plugin.json, hook path variables
6. Verify marketplace compliance: catalog entry exists with matching name, version, category, and source path
7. Assess git hygiene: no committed node_modules, .env files, large binaries, or merge conflict markers
8. For MCP plugins: validate package.json, TypeScript config, dist/ in .gitignore, and build scripts
9. Generate a scored report with per-category results, overall rating, and prioritized recommendations

## Non-Functional Requirements

- Audit is read-only: never modify the plugin being audited
- Pattern matching must avoid false positives on common test fixtures and documentation examples
- Report format must be consistent across all plugins for comparability
- Each failed check must include a specific, runnable fix command
- Audit must complete within 30 seconds for any single plugin
- Scoring must be deterministic: same plugin state always produces the same scores
- Report must clearly distinguish critical failures from advisory warnings

## Dependencies

- Read access to the target plugin directory and `.claude-plugin/marketplace.extended.json`
- `jq` installed for JSON schema validation
- `grep` and `find` available on PATH for pattern scanning

## Out of Scope

- Automated remediation of found issues (the auditor reports, the author fixes)
- Runtime security testing (executing plugin code in a sandbox)
- Performance benchmarking of MCP server plugins
- Auditing external dependencies for known vulnerabilities (use dedicated tools like `npm audit`)
- Code quality analysis beyond security patterns (logic bugs, performance issues)
- Cross-plugin dependency conflict detection
