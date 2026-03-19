# Security Policy

## Supported Versions

| Version | Supported          |
|---------|--------------------|
| 0.1.x   | :white_check_mark: |

## Reporting a Vulnerability

If you discover a security vulnerability, please report it responsibly:

1. **Do not** open a public GitHub issue
2. Email: [Create a private security advisory](https://github.com/jeremylongshore/pr-to-prompt/security/advisories/new)
3. Include steps to reproduce and impact assessment

We will respond within 48 hours and aim to release a fix within 7 days for critical issues.

## Security Model

### What pr-to-prompt does

- Reads PR metadata and diffs via the GitHub API (read-only by default)
- Generates structured specs from metadata using deterministic heuristics
- Optionally posts comments to PRs (requires write permission)

### What pr-to-prompt does NOT do

- Execute code from PRs
- Checkout or run untrusted code
- Store credentials beyond the current session
- Send data to third-party services (unless optional AI enhancement is explicitly enabled)

### Threat Model

| Threat | Mitigation |
|--------|------------|
| Malicious PR content in rendered comments | Output is structured text only; no HTML injection possible via GitHub Markdown |
| Token scope escalation | CLI documents minimum required scopes; Action uses default `GITHUB_TOKEN` |
| Supply chain attack via dependencies | Minimal dependency tree; lockfile integrity checked in CI |
| Shell injection via CLI arguments | All inputs validated with Zod; no shell execution of user-provided strings |
| Secrets in logs | Token values are never logged; GitHub Actions masks secrets automatically |

### Required Token Scopes

**CLI (Personal Access Token):**
- Classic: `repo` scope (for private repos) or `public_repo` (for public repos only)
- Fine-grained: `Pull requests: Read` + `Contents: Read`

**GitHub Action:**
- Uses the default `GITHUB_TOKEN` with `pull-requests: write` permission
- No additional secrets required for core functionality

### Dependencies

We keep the dependency tree minimal:
- `@octokit/rest` — GitHub API client (Octokit is GitHub's official library)
- `commander` — CLI argument parsing
- `yaml` — YAML serialization
- `zod` — Schema validation
