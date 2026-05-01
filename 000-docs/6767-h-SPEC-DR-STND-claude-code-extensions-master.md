# Global Master Standard – Claude Code Extensions (Plugins + Skills) Specification

**Document ID**: 6767-h-SPEC-DR-STND-claude-code-extensions-master
**Version**: 1.0.0
**Status**: AUTHORITATIVE - Single Source of Truth
**Created**: 2025-12-28
**Updated**: 2025-12-28
**Supersedes**: 6767-a (plugins/marketplace), 6767-b (skills), 6767-c (unified enterprise rules)
**Authority**: Intent Solutions (claudecodeplugins.io)

**Audited Against**:
- Claude Code docs: plugins + marketplaces + hooks + skills
- Anthropic Agent Skills docs + best practices
- Anthropic Engineering blog post on skills
- This repository’s enforcement validators and marketplace build pipeline

**Sources**:
- https://code.claude.com/docs/en/plugins-reference
- https://code.claude.com/docs/en/plugin-marketplaces
- https://code.claude.com/docs/en/hooks
- https://code.claude.com/docs/en/settings
- https://code.claude.com/docs/en/skills
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/overview
- https://platform.claude.com/docs/en/agents-and-tools/agent-skills/best-practices
- https://www.anthropic.com/engineering/equipping-agents-for-the-real-world-with-agent-skills
- https://www.claude.com/blog/claude-code-plugins
- https://github.com/anthropics/claude-code
- https://github.com/anthropics/claude-plugins-official
- https://github.com/anthropics/skills

---

## Executive Summary

### What Is a Claude Code Extension?

In practice, “Claude Code extensions” are delivered as **plugins**. A plugin is a container that can bundle:
- **Skills** (auto-invoked workflows)
- **Commands** (slash commands)
- **Agents** (subagents)
- **Hooks** (lifecycle automation)
- **MCP servers** (external tool integrations)

### What Is a Skill?

A skill is a **filesystem-defined capability** described by `skills/<skill-name>/SKILL.md` with YAML frontmatter plus a markdown instruction body. Skills are:
- **Discoverable** by description intent matching
- **Composable** across plugins
- **Context-efficient** via progressive disclosure (`references/` loaded only when needed)

### Non‑Negotiable Invariants (Enterprise Mode)

These are enforced in this repo (see `scripts/validate-skills-schema.py`, `scripts/validate-frontmatter.py`):

1) **`allowed-tools` is a CSV string (NOT a YAML array)**
   - ✅ `allowed-tools: "Read, Write, Grep, Glob"`
   - ❌ `allowed-tools: [Read, Write, Grep]`

2) **`Bash` must be scoped**
   - ✅ `Bash(git:*)`, `Bash(npm:*)`, `Bash(python:*)`
   - ❌ `Bash`

3) **Paths must be portable**
   - ✅ `${CLAUDE_PLUGIN_ROOT}/...` (plugin-root portability)
   - ✅ `{baseDir}/...` (skill-root portability)
   - ❌ absolute paths (`/home/...`, `~/...`)

4) **Progressive disclosure**
   - SKILL.md stays concise; heavy content goes in `references/`
   - Skill body must have required sections and at least one line of real text per section (not just code fences)

---

## 1) Canonical Directory Structure

### 1.1 Plugin Root Anatomy (Repository Standard)

```
plugins/<category>/<plugin-name>/
├── .claude-plugin/
│   └── plugin.json
├── skills/
│   └── <skill-name>/
│       ├── SKILL.md
│       ├── scripts/        (optional)
│       ├── references/     (optional)
│       └── assets/         (optional)
├── commands/               (optional)
├── agents/                 (optional)
├── hooks/                  (optional)
└── README.md               (recommended)
```

**Hard rule**: `.claude-plugin/` contains ONLY `plugin.json`. No commands/skills/scripts inside `.claude-plugin/`.

### 1.2 Skill Folder Anatomy

```
skills/<skill-name>/
├── SKILL.md                 # REQUIRED
├── scripts/                 # OPTIONAL (executed via Bash tool)
├── references/              # OPTIONAL (loaded via Read tool)
└── assets/                  # OPTIONAL (templates; referenced by path)
```

---

## 2) Plugin Manifest: `.claude-plugin/plugin.json`

### 2.1 Required Fields (Enterprise Marketplace)

`plugin.json` is the plugin identity contract:

- `name` (kebab-case, <= 64 chars)
- `version` (SemVer `X.Y.Z`)
- `description` (human description)
- `author` (object with `name` + `email`)
- `license` (SPDX-like string)
- `keywords` (array of strings)

### 2.2 Path Resolution

Inside a plugin, prefer `${CLAUDE_PLUGIN_ROOT}` for paths that need to be portable across installs.

---

## 3) Skill Definition: `skills/<skill-name>/SKILL.md`

### 3.1 YAML Frontmatter (Required)

Frontmatter is a YAML mapping at the top of the file:

```yaml
---
name: my-skill
description: Does X and Y. Use when [scenario]. Trigger with "phrase 1", "phrase 2".
allowed-tools: "Read, Grep, Glob, Bash(git:*), Bash(python:*)"
version: "1.0.0"
author: "Name <email@domain>"
license: "MIT"
---
```

**Rules**:
- `allowed-tools` MUST be a **CSV string**
- `description` MUST include **“Use when …”** and **“Trigger with …”**
- Avoid first/second person in `description` (third-person voice)

### 3.2 Instruction Body (Required Sections)

The validator expects these sections to exist and contain real prose:
- `## Overview`
- `## Prerequisites`
- `## Instructions`
- `## Output`
- `## Error Handling`
- `## Examples`
- `## Resources`

### 3.3 `{baseDir}` and Bundled Files (References/Assets/Scripts)

Within SKILL.md, reference bundled files using `{baseDir}`:
- Scripts: `{baseDir}/scripts/<script>`
- References: `{baseDir}/references/<doc>`
- Assets/templates: `{baseDir}/assets/<file>`

**Semantics**:
- `scripts/` are executed (no token cost until output).
- `references/` are loaded into context on demand (token cost when read).
- `assets/` are path-addressable templates/configs (generally not loaded unless read).

---

## 4) Marketplace & Website (claudecodeplugins.io) Safety Contract

### 4.1 Source of Truth for Published Plugins

In this repo:
- Marketplace source of truth: `.claude-plugin/marketplace.extended.json`
- CLI-compatible catalog: `.claude-plugin/marketplace.json` (generated via `node scripts/sync-marketplace.cjs`)

### 4.2 Skills/Explore Index Generation

Marketplace build performs:
- Skills discovery: `marketplace/scripts/discover-skills.mjs`
- Catalog sync for Explore: `marketplace/scripts/sync-catalog.mjs`
- Unified search index: `marketplace/scripts/generate-unified-search.mjs`
- Static build: `astro build`

### 4.3 Required Website Gates (Zero Warnings Policy)

Run these before claiming “site-safe” changes:

```bash
python scripts/validate-skills-schema.py --fail-on-warn
python scripts/validate-frontmatter.py
corepack pnpm -C marketplace build
node scripts/check-routes.mjs
node scripts/check-official-links.mjs
```

These gates enforce:
- No schema warnings (treat warnings as failures)
- No missing routes for published plugins
- No stale `/explore` links pointing at missing plugin pages

---

## 5) Compliance Checklist (PASS/FAIL)

- [ ] Plugin manifests exist at `.claude-plugin/plugin.json`
- [ ] Skill frontmatter includes `name`, `description`, `allowed-tools`, `version`, `author`, `license`
- [ ] `allowed-tools` is CSV string; no YAML arrays
- [ ] No unscoped `Bash`
- [ ] Skill body includes required sections with real prose
- [ ] All `{baseDir}` references resolve to real files
- [ ] Marketplace build produces catalogs with no orphaned skills
- [ ] `/explore` plugin links map to real `/plugins/<name>/` pages
- [ ] Route + official link gates are green

---

## Appendix A: In-Repo Canonical References

- `000-docs/6767-d-AT-APIS-claude-code-extensions-schema.md` (error codes + schema)
- `000-docs/6767-e-WA-WFLW-extensions-validation-ci-gates.md` (CI gates)
- `000-docs/6767-f-AT-ARCH-plugin-scaffold-diagrams.md` + diagrams
- `000-docs/6767-g-AT-ARCH-skill-scaffold-diagrams.md` + diagrams

