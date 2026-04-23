# Contributing to Claude Code Plugins

Thank you for your interest in contributing to the Claude Code Plugins marketplace. With hundreds of plugins and thousands of agent skills, this is a community-driven project and contributions of all sizes are welcome.

## Before You Submit — Read This

Tons of Skills publishes Intent Solutions-grade plugins and skills. That means full-capability, enterprise-ready implementations — validators, tests, docs, license, the works.

### The Intent Solutions standard

At Intent Solutions we ship the full-fledged capability. We don't publish half-implementations, stubs, or "minimum viable" versions. When a contribution lands in this marketplace, it lands as a complete, enterprise-grade artifact: proper frontmatter, tested code, real documentation, a valid license, security-scanned content, and a score above our 100-point rubric threshold.

**That's our side of the contract.** Once a user acquires a plugin or skill from this marketplace, they own it — they can strip it down, fork it, gut it, simplify it, inline it into their own workflow, remove features they don't want, or rewrite it from scratch. That's their prerogative as the consumer.

**But what we *publish* is the full-capability version.** The validators exist to enforce that bar. If your submission gets flagged, it's not personal — it's the same bar we hold ourselves to internally.

### What this means practically for your PR

- Your `SKILL.md` needs the full frontmatter schema (not just `name` + `description`). See [Adding Skills](#adding-skills) below.
- Your plugin needs a `README.md`, a `LICENSE`, a valid `plugin.json` (allowed fields only), and an entry in `.claude-plugin/marketplace.extended.json`.
- Your code and config can't trip the security scanner — no `rm -rf`, no `eval`, no base64 obfuscation, no hardcoded secrets, no URL shorteners, HTTPS only.
- Your skill needs to score at or above the enterprise threshold on our 100-point rubric. Run the same validator CI runs:
  ```bash
  python3 scripts/validate-skills-schema.py --enterprise --verbose plugins/<category>/<name>/
  ```
- If any of this fails in CI, **Gemini 2.5 Pro will post a specific, actionable review** on your PR explaining exactly what's wrong and how to fix it. A human maintainer will follow up if the bot was unclear.

### "But I just want to submit a small skill"

The bar isn't *size*, it's *completeness of what you do ship*. Start from `templates/minimal-plugin/` — even the minimum template passes enterprise validators. A one-command plugin with proper frontmatter, a real README, and a valid license is welcome. A sprawling plugin with placeholder text and bare `Bash` permissions is not.

### Now what

Read the rest of this doc, then run `./scripts/quick-test.sh` locally before you push. That script runs the same validators CI runs — passing it locally means your PR will pass the hard gates.

---

## Quick Start

1. Fork and clone the repository
2. Copy a template from `templates/` (`minimal-plugin`, `command-plugin`, `agent-plugin`, or `full-plugin`)
3. Develop your plugin
4. Run validation: `./scripts/quick-test.sh`
5. Open a PR

## Ways to Contribute

- **New plugins** -- Add tools, workflows, or integrations for Claude Code
- **New skills** -- Create auto-activating SKILL.md files for existing or new plugins
- **Bug fixes** -- Fix issues in existing plugins, the marketplace site, or the CLI
- **Documentation** -- Improve READMEs, guides, or inline documentation
- **Security reports** -- Responsibly disclose vulnerabilities (see Security below)
- **Plugin reviews** -- Test and review open PRs from other contributors

## Adding a Plugin

1. Pick a category from `plugins/` (e.g., `devops`, `productivity`, `api-development`) or propose a new one in your PR.
2. Copy a template:
   ```bash
   cp -r templates/command-plugin plugins/[category]/my-plugin
   ```
3. Edit `.claude-plugin/plugin.json` with the required fields: `name`, `version`, `description`, `author`.
4. Add a `README.md` and optionally a `LICENSE` file (MIT recommended).
5. Add `commands/`, `agents/`, or `skills/` directories as needed.
6. Add an entry to `.claude-plugin/marketplace.extended.json`.
7. Run `pnpm run sync-marketplace` to regenerate the CLI-compatible catalog.
8. Run `./scripts/quick-test.sh` -- this must pass before opening a PR.

Only these fields are allowed in `plugin.json`: `name`, `version`, `description`, `author`, `repository`, `homepage`, `license`, `keywords`. CI rejects anything else.

## Adding Skills

Create a `skills/[skill-name]/SKILL.md` file inside any plugin directory. Use the 2026 Schema frontmatter:

```yaml
---
name: skill-name
description: |
  When to use this skill. Include trigger phrases.
allowed-tools: Read, Write, Edit, Bash(npm:*), Glob
version: 1.0.0
author: Your Name <you@example.com>
---
```

Validate your skills with:

```bash
python3 scripts/validate-skills-schema.py --skills-only
```

## Validation Requirements

CI runs the following checks on every PR:

- **JSON validity and plugin structure** -- All `plugin.json` files must be well-formed with required fields.
- **Catalog sync** -- `marketplace.extended.json` and `marketplace.json` must be in sync. Run `pnpm run sync-marketplace` before committing.
- **Security scan** -- No hardcoded secrets, API keys, or dangerous patterns.
- **Marketplace build and route validation** -- The Astro site must build successfully with all plugin routes resolving.
- **Frontmatter validation** -- Commands, agents, and skills must have valid YAML frontmatter.
- **E2E tests** -- Playwright tests run on chromium, webkit, and mobile viewports.

Run `./scripts/quick-test.sh` locally to catch most issues before pushing.

### What happens when you open the PR

1. GitHub runs all 15+ validators (`validate-plugins.yml`).
2. Gemini 2.5 Pro reviews your code and posts inline comments within ~2–5 minutes.
3. A maintainer gets a Slack ping — we'll follow up if Gemini missed something or was wrong.
4. Push fixes; both the validators and Gemini re-run on each push.
5. Once validators pass and Gemini has no `[Critical]` or `[High]` findings, a maintainer reviews and merges.

The Gemini reviewer reads from a project-specific prompt at `.gemini/commands/gemini-review.toml` — it knows the catalog system, plugin structure, SKILL.md schema, severity classifications, and anti-patterns. If you think it got something wrong, just reply to the review and a human will weigh in.

## PR Process

- The PR template at [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) pre-fills when you open a pull request. Fill it out completely.
- Include test evidence (validation output, screenshots, or logs as appropriate).
- Reviews are typically completed within 48 hours.
- Address review comments, re-run validation, and push before requesting re-review.

## External Plugin Sync

If you maintain a plugin in your own repository and want it included in the marketplace:

- Request addition to `sources.yaml` by opening a PR or issue.
- External plugins are synced daily at midnight UTC via `scripts/sync-external.mjs`.

## Recognition

Every contributor is credited in the project README with contribution type badges. Newest contributors are featured at the **top** of the list.

Contribution types:

- **PLUGIN AUTHOR** -- Created one or more plugins
- **SKILLS CONTRIBUTOR** -- Added skills to existing or new plugins
- **SECURITY REPORTER** -- Responsibly disclosed a vulnerability
- **CODE CONTRIBUTOR** -- Improved infrastructure, CI, CLI, or the marketplace site
- **DOCS CONTRIBUTOR** -- Improved documentation or guides

Outstanding contributions are highlighted in the Contributor Spotlight section. Active contributors may be invited to join as project maintainers.

## Code of Conduct

This project follows a code of conduct to ensure a welcoming environment for all participants. See [Code of Conduct](000-docs/006-BL-POLI-code-of-conduct.md) for details.

## Security

- Never commit secrets, API keys, or credentials. CI will reject PRs that contain them.
- Report vulnerabilities via [GitHub Security Advisories](../../security/advisories).
- See [SECURITY.md](SECURITY.md) for the full security policy.

---

Questions? Open a [GitHub Discussion](../../discussions) or file an issue. We are glad to help.
