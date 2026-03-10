# Security Policy

## Reporting a Vulnerability

**Do not open a public issue for security vulnerabilities.**

Use [GitHub Private Security Advisories](https://github.com/jeremylongshore/claude-code-plugins/security/advisories/new) to report vulnerabilities privately. Alternatively, email **jeremy@intentsolutions.io**.

We will acknowledge receipt within 24 hours and provide a remediation timeline within 72 hours.

## Scope

This policy covers:

- All plugins and skills in the `plugins/` directory (339 plugins, 1896 skills)
- The `ccpi` CLI tool (`@intentsolutionsio/ccpi` on npm)
- Cowork zip distribution packages
- CI/CD pipelines and GitHub Actions workflows
- The marketplace web application

## How We Protect Users

### Automated Validation

Every plugin submission runs through CI checks before merge:

- **Structure validation** — required files, valid JSON/YAML, script permissions
- **Secret scanning** — detects hardcoded API keys, tokens, credentials
- **Malicious pattern detection** — flags dangerous commands, suspicious URLs, obfuscated code, path traversal attempts
- **Dependency audit** — `npm audit` for MCP server plugins

### Code Review

All changes to `main` require:

- Pull request with passing CI checks
- Branch protection enforced — no direct pushes
- Maintainer review of all plugin code, commands, agents, and scripts

### Distribution Security

Plugin zip packages (cowork downloads) are built with:

- Path traversal rejection — archives cannot reference parent directories or absolute paths
- Sensitive file exclusion — `.env`, credentials, `.git/`, and similar files are stripped at build time
- Symlink prevention — archives do not follow or include symbolic links
- SHA-256 integrity checksums published alongside every package
- CI validation gate — packages are not published unless all checks pass

### Monitoring

- **GitHub Dependabot** — automated PRs for vulnerable dependencies (npm + GitHub Actions)
- **CodeQL** — static analysis on push, PR, and weekly schedule
- **Secret scanning with push protection** — blocks commits containing detected secrets
- **Weekly security audit workflow** — scheduled sweep of the full repository

## Plugin Trust Levels

| Level | Requirements | Recommendation |
|-------|-------------|----------------|
| **Community** | Automated CI passed | Inspect before production use |
| **Verified** | Full review + 2 maintainer approvals + 7-day public review | Safe for production |
| **Featured** | Verified + active maintenance + community adoption | Recommended |

## For Plugin Developers

- Never hardcode secrets — use environment variables
- Pin exact dependency versions in `package.json`
- Document all network calls and permissions in your README
- Run `./scripts/validate-all.sh` before submitting
- See [CONTRIBUTING.md](CONTRIBUTING.md) for the full submission checklist

## Supported Versions

| Version | Supported |
|---------|-----------|
| Latest (`main`) | Yes |
| Previous releases | Best-effort security patches |

---

**Last Updated:** March 2026
