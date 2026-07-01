# Contributing to Claude Code Plugins

Thank you for your interest in contributing to the Claude Code Plugins marketplace. With hundreds of plugins and thousands of agent skills, this is a community-driven project and contributions of all sizes are welcome.

> ## 📋 Read the spec before you start
>
> Every plugin and skill in this marketplace is graded against a single
> authoritative specification:
>
> **→ [`000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md`](000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md)** — the **Global Master Standard for Claude Skills** (v3.6.0, schema 3.6.0).
>
> It documents:
>
> - The **8 marketplace-tier required frontmatter fields** (vs Anthropic's 2-field minimum)
> - The **7 required body sections** (`## Overview`, `## Prerequisites`, `## Instructions`, `## Output`, `## Error Handling`, `## Examples`, `## Resources`)
> - The **100-point rubric** the validator scores against
> - Conditional fields (`requires_env`, `requires_tools`, `argument-hint`, etc.)
> - The self-declared config surface (`required_environment_variables`, `metadata.intent-solutions.config`)
> - Source citations for every field — Anthropic's [skills docs](https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview), [Claude Code skills](https://code.claude.com/docs/en/skills), [AgentSkills.io spec](https://agentskills.io/specification), and the [anthropics/skills reference implementation](https://github.com/anthropics/skills).
>
> If your submission deviates from the spec, the validator will flag it and the PR Pre-screen workflow will request changes before a human looks at it. Reading the spec up front saves a round-trip.

## Before You Submit — Read This

Tons of Skills publishes Intent Solutions-grade plugins and skills. That means full-capability, enterprise-ready implementations — validators, tests, docs, license, the works.

### The Intent Solutions standard

At Intent Solutions we ship the full-fledged capability. We don't publish half-implementations, stubs, or "minimum viable" versions. When a contribution lands in this marketplace, it lands as a complete, enterprise-grade artifact: proper frontmatter, tested code, real documentation, a valid license, security-scanned content, and a score above our 100-point rubric threshold.

**That's our side of the contract.** Once a user acquires a plugin or skill from this marketplace, they own it — they can strip it down, fork it, gut it, simplify it, inline it into their own workflow, remove features they don't want, or rewrite it from scratch. That's their prerogative as the consumer.

**But what we _publish_ is the full-capability version.** The validators exist to enforce that bar. If your submission gets flagged, it's not personal — it's the same bar we hold ourselves to internally.

### What this means practically for your PR

- Your `SKILL.md` needs the full frontmatter schema (not just `name` + `description`). See [Adding Skills](#adding-skills) below.
- Your plugin needs a `README.md`, a `LICENSE`, a valid `plugin.json` (allowed fields only), and an entry in `.claude-plugin/marketplace.extended.json`.
- Your code and config can't trip the security scanner — no `rm -rf`, no `eval`, no base64 obfuscation, no hardcoded secrets, no URL shorteners, HTTPS only.
- Your skill needs to score at or above the marketplace threshold on our 100-point rubric (full rubric in the [spec doc](000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md)). Run the same validator CI runs:

  ```bash
  python3 scripts/validate-skills-schema.py --marketplace --verbose plugins/<category>/<name>/
  ```

- If any of this fails in CI, the **PR Pre-screen workflow** ([runbook](000-docs/265-DR-GUID-pr-prescreen-system.md)) will post a structured review on your PR with the exact validator findings + a short Groq-generated summary. A human maintainer follows up after that.

### "But I just want to submit a small skill"

The bar isn't _size_, it's _completeness of what you do ship_. Start from `templates/minimal-plugin/` — even the minimum template passes enterprise validators. A one-command plugin with proper frontmatter, a real README, and a valid license is welcome. A sprawling plugin with placeholder text and bare `Bash` permissions is not.

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

There are two paths. Pick the one that matches how you want to maintain the plugin.

### Path A — Vendor your plugin into this repo (frozen at submission)

Best when you want a one-time submission and don't expect frequent updates.

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

### Path B — Auto-sync from your own repo (your repo stays source of truth)

Best when you maintain the plugin in your own repo and want updates to flow to the marketplace automatically. **This is the recommended path for external/third-party plugins.** Here's our end of the deal, in plain terms:

- **Your repo stays the source of truth.** You keep authoring and maintaining your plugin wherever you already do. You don't fork, vendor, or hand-manage a copy here.
- **We mirror — we don't edit.** By default the sync only _copies_ the files you list into `plugins/<category>/<name>/`. We do not locally rewrite, restructure, or "improve" your content behind your back. Your latest pushes flow to tonsofskills.com on the weekly sync.
- **We never silently overwrite you.** The sync opens an automated PR that a human reviews before anything lands. If anything ever would touch content you curate, the mirror is _frozen_ for your source and skipped entirely (see `curated:` below) — a forced or off-cycle sync cannot revert your work.
- **If we want your plugin at our A-grade bar, we ask first.** Our marketplace holds an enterprise-grade standard (full frontmatter, tested code, real docs). If we'd like your plugin to meet it, we don't quietly patch our mirror and let it drift from yours. We open a friendly **issue on your repo** first ("we featured your plugin and would love to bring its frontmatter to our A-grade bar — open to a PR?"), and if you're up for it we send a **PR that you own and merge** upstream. Once it's merged in your repo, the mirror reflects it naturally. You keep control; your credit is preserved; you decide.

**Steps:**

1. Make sure your plugin in your own repo has at minimum a `SKILL.md` and a `README.md` at a known path.
2. Open a PR against this repo that adds a single entry to [`sources.yaml`](sources.yaml) with the metadata. Example:

   ```yaml
   - name: my-plugin
     description: One-line description
     repo: yourname/your-repo
     source_path: skills/my-plugin # path inside your repo
     target_path: plugins/community/my-plugin
     author:
       name: Your Name
       github: yourname
       email: you@example.com
     license: MIT
     category: community
     verified: true
     include:
       - 'SKILL.md'
       - 'README.md'
       - 'references/**'
     exclude:
       - 'node_modules/**'
       - '.git/**'
   ```

3. After your `sources.yaml` PR merges, the next weekly sync (Mondays 06:00 UTC) pulls your latest content into `plugins/<category>/<name>/` and opens an automated PR. Once that PR merges, your plugin is live on the site.
4. For an immediate first sync (instead of waiting for Monday), a maintainer can trigger the workflow manually via `gh workflow run sync-external.yml`.
5. Every subsequent push you make to your own repo gets picked up by the next weekly sync — no further action on your end.

**What `verified:` and `curated:` mean for you as an author.** These two flags are separate and independent:

- **`verified:`** — a maintainer has vetted your source for quality and trust. This is about the source, not about touching your files.
- **`curated:`** — set only after we've asked you and hardened a local copy of your plugin past what's currently upstream. When `curated: true`, the sync **freezes your mirror**: it does no clone, no overwrite, and no orphan-prune for your source — it only keeps your catalog entry current. This is the guard that guarantees a `--force` or off-schedule sync can never revert curated content. It's an interim state; the intent is always to upstream those improvements back to you (via the issue-then-PR flow above) so your repo and the mirror converge and the freeze is no longer needed.

They're orthogonal on purpose — a plugin can be `curated: true` (we locally hardened it, pending an upstream PR to you) while still `verified: false`, which is an honest way to say "we improved it but haven't formally vetted the source yet."

**Do NOT edit `README.md` by hand to add your plugin.** The README category tables (between the `<!-- AUTO-TOC:START -->` and `<!-- AUTO-TOC:END -->` markers) are auto-generated from `marketplace.extended.json` — your hand-edit will be wiped on the next sync.

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

### Modifying the validator itself

If your PR changes `scripts/validate-skills-schema.py`, the master spec at `000-docs/6767-b-SPEC-DR-STND-claude-skills-standard.md`, or the SKILL.md frontmatter rules in this doc, **read [`000-docs/SCHEMA_CHANGELOG.md`](000-docs/SCHEMA_CHANGELOG.md) first** — the NON-NEGOTIABLES section at the top documents which directions of change are out of bounds without explicit pre-approval (see issue #612 for the postmortem). Bug fixes that bring the validator into spec compliance are fine to apply directly; architectural changes (required-field set, tier model, error vs. warning semantics) need approval before the change lands.

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

1. GitHub runs all 15+ validators (`validate-plugins.yml`). **These required checks are the gate** — your PR is mergeable once they're green.
2. An AI reviewer posts inline comments when it's active on the PR. Treat its findings like any review: address them, or reply if you think it got something wrong and a human will weigh in.
3. A maintainer gets a Slack ping and follows up.
4. Push fixes; the required checks re-run on each push.
5. Once the required checks pass and any review threads are resolved, a maintainer reviews and merges.

The deterministic CI checks — not the AI reviewer — are the authoritative gate; the AI review is advisory.

## PR Process

- The PR template at [`.github/PULL_REQUEST_TEMPLATE.md`](.github/PULL_REQUEST_TEMPLATE.md) pre-fills when you open a pull request. Fill it out completely.
- Include test evidence (validation output, screenshots, or logs as appropriate).
- Reviews are typically completed within 48 hours.
- Address review comments, re-run validation, and push before requesting re-review.

## External Plugin Sync

If you maintain a plugin in your own repository and want it included in the marketplace, see **Path B** under [Adding a Plugin](#adding-a-plugin) above. Quick summary:

- Open a PR adding your plugin's metadata to [`sources.yaml`](sources.yaml).
- The weekly sync (Mondays 06:00 UTC, `.github/workflows/sync-external.yml`) pulls your latest content into `plugins/<category>/<name>/` and opens an automated PR that a human reviews before it lands.
- For an immediate sync after your `sources.yaml` PR merges, a maintainer can trigger the workflow on demand with `gh workflow run sync-external.yml`.

**The contract in one line:** your repo is the source of truth, we mirror your files rather than edit them, we never silently overwrite content you curate (a `curated: true` source is frozen and skipped by the sync), and if we'd like your plugin at our A-grade bar we ask first via a friendly issue and then a PR you own and merge upstream.

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
- Report vulnerabilities via GitHub Security Advisories.
- See [SECURITY.md](SECURITY.md) for the full security policy.

---

Questions? Open a GitHub Discussion or file an issue. We are glad to help.
