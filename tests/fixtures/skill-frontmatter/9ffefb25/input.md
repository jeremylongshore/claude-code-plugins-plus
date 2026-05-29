---
name: repo-blueprint
description: |
  Scaffold a complete plugin and skills repository for any business with MCP servers, tier gating, enterprise docs, CI/CD, and inventory tracking. Use when creating a new business-integration repo. Trigger with "/repo-blueprint", "scaffold repo", or "new business repo".
allowed-tools: 'Read,Write,Edit,Glob,Grep,Bash(mkdir:*),Bash(gh:*),Bash(git:*),Bash(ls:*),Bash(bash:*),Bash(chmod:*),Task'
argument-hint: '[business-name]'
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: BUSL-1.1
compatibility: 'Designed for Claude Code; requires git, gh (GitHub CLI), and Python 3.10+ on PATH'
tags: [scaffolding, plugins, skills, mcp, repo-template, intent-solutions]
model: inherit
effort: medium
---

# Repo Blueprint

Scaffold a production-grade plugin + skills repository for any business,
following the SearchCarriers master blueprint pattern. Real working
infrastructure, not stubs.

## Overview

Generates a complete repo with:

- 5-plugin architecture (3 stackable pipeline + 2 standalone)
- 10-14 categorized skills across 4 categories
- MCP servers with tier-gated API access
- 6-doc enterprise planning set per plugin
- CI/CD, validation script, onboarding script
- Inventory CSVs tracking status across the lifecycle

The skill is an **orchestrator**: it delegates reasoning to subagents and
execution to deterministic scripts.

## Prerequisites

- `gh` (GitHub CLI) authenticated — `!`gh auth status | head -1``
- `git` configured with user email
- Python 3.10+ on PATH
- Target directory does not exist (or is empty)

## Instructions

1. **Gather business context** — ask for `business_name`, `business_domain`,
   `entities`, `tiers`, `api_spec`, `output_path`, `github_org`. See
   [references/repo-pattern.md](references/repo-pattern.md) for canonical
   examples.
2. **Design plugin architecture** — delegate to the `plugin-architect` subagent
   via the Task tool. Pass business context. It writes a JSON spec to
   `/tmp/$BIZ_NAME-plugins.json`. See
   [references/plugin-architecture.md](references/plugin-architecture.md).
3. **Design skill categories** — delegate to the `skill-categorizer` subagent
   via the Task tool. Pass business context + the plugin spec from step 2. It
   writes a JSON spec to `/tmp/$BIZ_NAME-skills.json`. See
   [references/skill-categories.md](references/skill-categories.md).
4. **Run scaffold scripts in order** (each one targets `$REPO_PATH`):
   - `bash scripts/scaffold-foundation.sh $REPO_PATH $BIZ_NAME $BIZ_DOMAIN`
   - `bash scripts/scaffold-docs.sh $REPO_PATH`
   - `bash scripts/scaffold-inventory.sh $REPO_PATH`
   - `bash scripts/scaffold-validate.sh $REPO_PATH`
   - `bash scripts/scaffold-ci.sh $REPO_PATH`
   - `bash scripts/scaffold-tests.sh $REPO_PATH`
5. **Materialize plugins** — for each plugin in the architecture spec, write
   its `plugin.json`, copy doc templates from `templates/docs/`, populate the
   inventory CSV row.
6. **Materialize skills** — for each skill in the categorizer spec, write its
   `SKILL.md` with frontmatter and required body sections, populate the
   inventory CSV row.
7. **Run the validator** — `bash $REPO_PATH/scripts/validate.sh --verbose`.
   Fix any errors before continuing.
8. **Review** — delegate to the `repo-blueprint-reviewer` subagent. It writes a
   pass/fail report including unsubstituted-token hunt, secret scan, tier
   gating sanity check.
9. **Initialize git + GitHub** — only after explicit user confirmation:
   `git init`, `gh repo create $GITHUB_ORG/$REPO_NAME --private`, initial
   commit, push.

## Output

A new directory at `$REPO_PATH` containing:

```
$REPO_NAME/
├── plugins/                  # 5 plugins, each with plugin.json + 6 docs
├── skills/                   # 4 categories × 3-4 skills each (10-14 total)
├── scripts/                  # validate.sh, setup-dev.sh
├── tests/                    # conftest.py, test_plugins.py, test_skills.py
├── inventory/                # plugins_inventory.csv, skills_inventory.csv
├── templates/docs/           # 6 enterprise doc templates per-plugin
├── .github/                  # workflows/ci.yml + 2 issue templates
├── pyproject.toml, README.md, CLAUDE.md, LICENSE, VERSION, CHANGELOG.md
```

Plus a markdown review report at `$REPO_PATH/REVIEW.md` with PASS or FAIL verdict.

See [references/directory-structure.md](references/directory-structure.md)
for the full per-plugin and per-skill layout.

## Examples

### Example 1 — Freight carrier research

```
/repo-blueprint searchcarriers
  Domain:   motor carrier research (FMCSA data, 4M+ companies)
  API:      https://api.searchcarriers.com/v2 (API key auth)
  Tiers:    Free, Basic, Pro, Pro+, SMB, Enterprise
  Entities: carriers, inspections, insurance, authority, equipment
```

Result: `searchcarriers/` repo with 5 plugins (input/analysis/output/
monitoring/integration), 12 skills across the 4 categories, full enterprise
docs, CI green, validation script passes.

### Example 2 — Fleet telematics

```
/repo-blueprint fleetpulse
  Domain:   fleet telematics and vehicle tracking
  API:      https://api.fleetpulse.io/v1 (OAuth2)
  Tiers:    Starter, Pro, Business, Enterprise
  Entities: vehicles, drivers, trips, geofences, alerts
```

Categories renamed to fit domain: `vehicle-tracking/`, `fleet-health/`,
`driver-safety/`, `operations/`. 11 skills total.

### Example 3 — Logistics marketplace

```
/repo-blueprint loadboard
  Domain:   freight load matching and broker tools
  API:      https://api.loadboard.com/v3 (JWT auth)
  Tiers:    Free, Professional, Agency, Enterprise
  Entities: loads, lanes, carriers, quotes, shipments
```

Pipeline: load-discovery → carrier-vetting → pricing → operations. 13 skills
total, with `carrier-vetting/` skills calling tools from both the input and
analysis plugins.

## Error Handling

| Error                        | Cause                      | Action                                                    |
| ---------------------------- | -------------------------- | --------------------------------------------------------- |
| `gh: command not found`      | GitHub CLI missing         | Skip step 9, surface install hint                         |
| Directory not empty          | Repo path collision        | Ask: overwrite, merge, or abort                           |
| Invalid `business_name`      | Spaces or special chars    | Convert to kebab-case automatically                       |
| Missing API details          | User skipped questions     | Use sentinel values, flag the inventory row for follow-up |
| `validate.sh` exits non-zero | Generated repo has defects | Surface errors and re-run after fix                       |
| Subagent unreachable         | `Task` tool unavailable    | Inline the design step with explicit prompts              |

## Resources

- [references/repo-pattern.md](references/repo-pattern.md) — master blueprint pattern
- [references/plugin-architecture.md](references/plugin-architecture.md) — 5-plugin spec
- [references/skill-categories.md](references/skill-categories.md) — 4-category taxonomy
- [references/directory-structure.md](references/directory-structure.md) — full tree
- [references/ci-cd-spec.md](references/ci-cd-spec.md) — workflow + issue templates
- [references/validation-rules.md](references/validation-rules.md) — full validator ruleset
- `agents/plugin-architect.md` — subagent for step 2
- `agents/skill-categorizer.md` — subagent for step 3
- `agents/repo-blueprint-reviewer.md` — subagent for step 8
- `assets/templates/` — file templates used by scaffold scripts
