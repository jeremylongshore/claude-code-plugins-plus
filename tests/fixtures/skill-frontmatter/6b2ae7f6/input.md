---
name: validate-marketplace
description: |
  Validate a .claude-plugin/marketplace.json catalog file against the
  canonical Anthropic plugin-marketplaces spec. Checks JSON validity,
  required top-level fields (name, owner, plugins array), owner shape
  (object with name), per-plugin entries (required name + source, optional
  description, version, category, keywords array, author), and source-type
  handling (relative path resolves on disk, github shorthand parses, full
  URL form). Optional --deep mode walks every ./plugins/DIR source and
  runs /validate-plugin against each, aggregating findings. Distinct from
  /validate-plugin (which validates ONE plugin) — this skill grades the
  catalog file that lists many. Use for repos that publish a marketplace
  (the canonical case — your repo IS the catalog) or rarer plugins that
  ship their own sub-catalog. Trigger with "/validate-marketplace",
  "validate this marketplace.json", "audit catalog", "check marketplace.json",
  "is my marketplace catalog spec-correct".
allowed-tools: 'Read,Bash(jq:*),Bash(grep:*),Bash(ls:*),Glob,AskUserQuestion,Skill'
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatibility: Designed for Claude Code; requires jq on PATH
tags: [validation, marketplace, plugin-catalog, plugin-quality, claude-code]
user-invocable: true
argument-hint: '[path-to-marketplace.json] [--deep] [--strict]'
---

# Validate Marketplace

Schema validator for `.claude-plugin/marketplace.json` catalog files. Reads the catalog and grades it against the [canonical Anthropic plugin-marketplaces spec](https://code.claude.com/docs/en/plugin-marketplaces). Anchors every claim in `references/anthropic-plugin-marketplaces.md` so spec drift is detectable and recoverable.

## Overview

A `marketplace.json` is the catalog file users install via `/plugin marketplace add <slug>`. Two distinct uses:

1. **Repo-as-marketplace** (canonical case) — the repo at the slug IS the catalog. Example: this repo's `.claude-plugin/marketplace.json` lists 427 plugins with their sources/categories/versions.
2. **Plugin-as-marketplace** (rare) — a single plugin can ship its own `marketplace.json` if it distributes additional sub-plugins.

Both forms follow the same schema:

```json
{
  "name": "<catalog-id>",
  "owner": { "name": "<owner-name>", "email": "...", "url": "..." },
  "metadata": {
    "description": "...",
    "version": "...",
    "homepage": "...",
    "pluginRoot": "plugins"
  },
  "plugins": [
    {
      "name": "<plugin-name>",
      "source": "./plugins/devops/my-plugin",
      "description": "...",
      "version": "1.0.0",
      "category": "devops",
      "keywords": ["ci", "lint"],
      "author": { "name": "..." }
    }
  ]
}
```

| Field                                                                 | Required | Notes                                                                         |
| --------------------------------------------------------------------- | -------- | ----------------------------------------------------------------------------- |
| `name` (top-level)                                                    | yes      | Catalog identifier, used in `/plugin marketplace add`                         |
| `owner`                                                               | yes      | Object with `name` (required); optional `email`, `url`                        |
| `plugins[]`                                                           | yes      | Array of plugin entries                                                       |
| `metadata`                                                            | no       | `description`, `version`, `homepage`, `pluginRoot` etc.                       |
| Per-plugin `name`                                                     | yes      | Plugin identifier within catalog                                              |
| Per-plugin `source`                                                   | yes      | Relative path / git URL / github shorthand / full URL / `marketplaceFile` ref |
| Per-plugin `description`, `version`, `category`, `keywords`, `author` | no       | Marketplace polish                                                            |

This skill is distinct from `/validate-plugin`:

- `/validate-plugin` audits **one plugin**'s structure (manifest + skills + agents + ...)
- `/validate-marketplace` audits **the catalog file** that lists many plugins
- Use both: validate the catalog with this skill, then optionally `--deep` to delegate to `/validate-plugin` per entry

## Prerequisites

- `jq` on PATH (every check pipes through `jq`)
- For `--deep` mode: sibling skill `/validate-plugin` available
- The spec snapshot under `references/anthropic-plugin-marketplaces.md` (symlinked from `validate-plugin/references/`)

## Instructions

### Step 1: Resolve target file

Argument forms:

- **Direct file** — `/validate-marketplace /path/to/.claude-plugin/marketplace.json`
- **Repo root** — `/validate-marketplace /path/to/repo/` → look for `.claude-plugin/marketplace.json`
- **Bare directory** — auto-discover

Cache the resolved file as `$MARKETPLACE_FILE` and the directory it lives in as `$REPO_ROOT` (`dirname $(dirname "$MARKETPLACE_FILE")`).

### Step 2: JSON validity + top-level shape

```bash
MARKETPLACE_FILE="<resolved>"

jq empty "$MARKETPLACE_FILE" 2>&1 || { echo "FAIL: malformed JSON"; exit 1; }

# Required top-level
jq '. | {
  has_name: (.name | type == "string" and length > 0),
  has_owner: (.owner | type == "object"),
  has_plugins: (.plugins | type == "array"),
  plugin_count: (.plugins | length)
}' "$MARKETPLACE_FILE"
```

Block on missing `name`, missing `owner`, missing `plugins`, or `plugins` not being an array.

### Step 3: `owner` shape check

```bash
jq '.owner | {
  has_name: (.name | type == "string" and length > 0),
  has_email: (.email | type == "string"),
  has_url: (.url | type == "string")
}' "$MARKETPLACE_FILE"
```

Block on missing `owner.name`. `email` and `url` are optional.

### Step 4: Per-plugin required-field check

```bash
# Find entries missing 'name' or 'source'
jq -r '
  .plugins | to_entries[] |
  select((.value.name == null) or (.value.source == null)) |
  "FAIL plugin[\(.key)]: missing required field(s) — name=\(.value.name // \"<missing>\"), source=\(.value.source // \"<missing>\")"
' "$MARKETPLACE_FILE"

# Count entries
jq '.plugins | length' "$MARKETPLACE_FILE"
```

### Step 5: Per-plugin source resolution

Each `source` string is one of:

- **Relative path** — `./plugins/<category>/<name>` — must resolve to a directory on disk
- **github shorthand** — `<owner>/<repo>` (no scheme), optionally `<owner>/<repo>#<ref>`
- **Git URL** — `https://github.com/<owner>/<repo>.git` or `git@github.com:<owner>/<repo>.git`
- **Full HTTP URL** — `https://...`
- **`marketplaceFile` reference** — pointer to another marketplace.json

Validate per source type:

```bash
REPO_ROOT="$(dirname "$(dirname "$MARKETPLACE_FILE")")"

jq -r '.plugins[] | "\(.name)|\(.source)"' "$MARKETPLACE_FILE" | while IFS='|' read -r name source; do
  case "$source" in
    ./*|../*)
      # Relative path — must resolve on disk
      [ -d "$REPO_ROOT/$source" ] \
        || echo "FAIL $name: source '$source' does not resolve to a directory under $REPO_ROOT"
      ;;
    http://*|https://*)
      # Full URL — accept as-is (cannot verify reachability without network)
      ;;
    git@*:*)
      # SSH git URL — accept as-is
      ;;
    */*)
      # github shorthand: <owner>/<repo> or <owner>/<repo>#<ref>
      echo "$source" | grep -qE '^[A-Za-z0-9_.-]+/[A-Za-z0-9_.-]+(#[A-Za-z0-9_./-]+)?$' \
        || echo "FAIL $name: source '$source' is not a valid github shorthand"
      ;;
    *)
      echo "FAIL $name: source '$source' is not a recognized source type (relative path / github shorthand / URL)"
      ;;
  esac
done
```

### Step 6: `keywords` shape check (when present)

```bash
# keywords must be array of strings
jq -r '.plugins[] | select(.keywords != null and (.keywords | type) != "array") | "FAIL \(.name): keywords must be an array"' "$MARKETPLACE_FILE"
```

### Step 7: Optional `--deep` per-plugin audit

When `--deep` is passed, walk every relative-path entry and delegate to `/validate-plugin`:

```bash
jq -r '.plugins[] | select(.source | startswith("./")) | "\(.name)|\(.source)"' "$MARKETPLACE_FILE" \
| while IFS='|' read -r name source; do
  echo "─── $name ───"
  # Invoke /validate-plugin via the Skill tool with "$REPO_ROOT/$source" as argument
done
```

Aggregate findings into the unified report (Step 8). For 400+ plugin catalogs this is slow — flag the cost up front and confirm before running.

### Step 8: Verdict

```
══════════════════════════════════════════════════════════════════════
  MARKETPLACE CATALOG AUDIT — <file-path>
══════════════════════════════════════════════════════════════════════

  JSON validity:                              PASS
  Top-level shape:                            PASS — name/owner/plugins
  Owner shape:                                PASS — name="<owner>"
  Plugin count:                               <N>

  Per-plugin required fields:
    Entries missing name or source:           <count> (FAIL list below)

  Source resolution:
    Relative paths resolved:                  <X>/<Y>
    github shorthand entries:                 <Z>
    URL entries:                              <W>
    Failed: <name> source='<source>'          <reason>

  Optional polish coverage:
    With description:                         <%>
    With version:                             <%>
    With category:                            <%>
    With keywords:                            <%>

  ──── Deep audit (--deep) ────                [SKIPPED unless --deep]
    <name>:                                   GRADE A / Tier 2 GREEN
    <name>:                                   GRADE D / Tier 2 RED — <issue>

  ──────────────────────────────────────────────────────────────────
  VERDICT: PASS | FAIL — <count> blocking issue(s)
  ──────────────────────────────────────────────────────────────────
```

**Block on**: malformed JSON, missing top-level `name`/`owner`/`plugins`, plugin entries without `name` or `source`, relative-path sources that don't resolve, malformed github shorthand.

**Warn (don't block)**: low optional-polish coverage (e.g. <50% of plugins have descriptions), `keywords` missing on plugins.

**`--strict` mode**: promotes warnings to errors.

## Output

- **Console report** per Step 8 with PASS/FAIL verdict
- **Per-plugin source-resolution table** so authors can spot drift between catalog and on-disk layout
- **Optional `--deep` aggregation** of `/validate-plugin` findings across every entry
- **Spec citations** linking to `references/anthropic-plugin-marketplaces.md` and the live canonical URL

## Error Handling

| Error                                | Recovery                                                                                 |
| ------------------------------------ | ---------------------------------------------------------------------------------------- |
| Target file not found                | Use `Glob` to search for `.claude-plugin/marketplace.json`; ask for clarification        |
| `jq: error (at <path>)`              | Surface jq parse error verbatim with line number                                         |
| Relative path doesn't resolve        | Cite `$REPO_ROOT` resolution; suggest `ls "$REPO_ROOT/$source"` to debug                 |
| GitHub shorthand looks malformed     | Cite `<owner>/<repo>[#<ref>]` pattern from `references/anthropic-plugin-marketplaces.md` |
| `--deep` mode picked up 400+ plugins | Confirm before running; surface ETA (10s × N plugins)                                    |
| `marketplaceFile` reference          | Out of current scope — cite spec, do not auto-resolve                                    |
| `pluginRoot` set in metadata         | Resolve relative paths against `$REPO_ROOT/<pluginRoot>` instead of bare `$REPO_ROOT`    |

## Examples

**Validate this repo's main catalog**:

```
/validate-marketplace ~/000-projects/claude-code-plugins/.claude-plugin/marketplace.json
```

Walks all 427 plugin entries, validates sources resolve, surfaces any drift between catalog declarations and on-disk layout.

**Validate a contributor's catalog before merging their PR**:

```
/validate-marketplace /tmp/external-contributor/their-marketplace/.claude-plugin/marketplace.json
```

**Deep mode (delegates to `/validate-plugin` per entry)**:

```
/validate-marketplace ~/000-projects/claude-code-plugins/.claude-plugin/marketplace.json --deep
```

Slow (~10s/plugin × 427 = ~70 min) — confirm before running. Aggregates Tier 1 grades + Tier 2 verdicts from each plugin into one report.

**Strict mode (low optional-polish coverage becomes a failure)**:

```
/validate-marketplace /path/to/marketplace.json --strict
```

## Resources

### Canonical specs (saved verbatim in `references/`)

- `references/anthropic-plugin-marketplaces.md` — full marketplace.json schema
- `references/anthropic-plugins-reference.md` — referenced for per-plugin source forms

### Live canonical URLs

- [code.claude.com/docs/en/plugin-marketplaces](https://code.claude.com/docs/en/plugin-marketplaces) — marketplace distribution
- [code.claude.com/docs/en/plugins-reference](https://code.claude.com/docs/en/plugins-reference) — plugin manifest schema

### Related skills

- `/validate-plugin` — orchestrator that delegates here for marketplace.json audits + reverse-delegates back when `--deep` walks per entry
- `/validate-skillmd` — sibling SKILL.md grader
- `/validate-mcp` / `/validate-agent` / `/validate-hook` — sibling component validators
