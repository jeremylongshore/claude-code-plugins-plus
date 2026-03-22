# Freshie Discovery Run 1 — CSV Export Index

**Run Date:** 2026-03-21 | **Commit:** f0f58cc0 | **Totals:** 22 packs, 349 plugins, 1,426 skills, 4,661 files

---

## Core Entities

| File | Rows | Description |
|------|------|-------------|
| `discovery_runs.csv` | 1 | Run metadata — date, commit hash, aggregate totals |
| `packs.csv` | 22 | Plugin categories (ai-ml, saas-packs, devops, etc.) with plugin/skill/file counts |
| `plugins.csv` | 349 | Every plugin — name, path, pack, readme status, plugin.json field shape |
| `skills.csv` | 1,426 | Every skill — name, path, structure shape (references/scripts/assets dirs) |

## Frontmatter Analysis

| File | Rows | Description |
|------|------|-------------|
| `frontmatter_fields.csv` | 12 | Field-level stats — which YAML fields exist, usage %, unique values, samples |
| `frontmatter_values.csv` | 15,925 | Raw frontmatter key-value pairs for every skill (largest file, 1.6 MB) |
| `frontmatter_shapes.csv` | 10 | Distinct frontmatter key combinations and how many skills use each |

## Content Quality

| File | Rows | Description |
|------|------|-------------|
| `content_signals.csv` | 1,426 | Per-skill quality metrics — line/word count, code blocks, placeholder detection (TODO, YOUR_API_KEY, Step N) |
| `pack_aggregates.csv` | 20 | Aggregate quality metrics rolled up per pack |

## Plugin Structure

| File | Rows | Description |
|------|------|-------------|
| `plugin_companions.csv` | 349 | Per-plugin structure audit — has_readme, has_package_json, has_commands_dir, has_agents_dir |
| `plugin_fields.csv` | 8 | plugin.json field usage stats across all plugins |
| `plugin_values.csv` | 2,411 | Raw plugin.json field values for every plugin |
| `plugin_shapes.csv` | 6 | Distinct plugin.json key combinations |

## File Inventory

| File | Rows | Description |
|------|------|-------------|
| `skill_files.csv` | 4,661 | Every file inside skills/ directories — path, extension, size, parent skill |
| `skill_structure_shapes.csv` | 12 | Distinct directory structures (SKILL.md only vs SKILL.md + references/ + scripts/) |
| `unique_extensions.csv` | 27 | File extension inventory (.md, .ts, .py, .json, etc.) |
| `unique_filenames.csv` | 1,272 | Most common filenames across all skills |
| `unique_subdirs.csv` | 15 | Subdirectory names found in skill dirs (references/, scripts/, assets/) |
| `duplicate_files.csv` | 41 | Files with identical SHA-256 hashes (potential bloat) |

## Compliance & Issues

| File | Rows | Description |
|------|------|-------------|
| `anomalies.csv` | 44 | Structural issues — zero-skills packs, missing dirs, .pyc files, type drift |
| `cross_references.csv` | 301 | Links between skills/plugins — file references, dependencies, shared patterns |
| `validators.csv` | 21 | Validation scripts in the repo — what they check, scoring behavior |
| `validator_checks.csv` | 435 | Individual validation rules across all validators |
| `field_registry.csv` | 72 | Master field registry — every known field, source, type, validation status |

## Infrastructure

| File | Rows | Description |
|------|------|-------------|
| `scripts.csv` | 116 | Shell/Python scripts in the repo — purpose, language, inputs/outputs |
| `ci_workflows.csv` | 15 | GitHub Actions workflows — triggers, jobs, environment variables |
| `docs.csv` | 11,793 | Documentation files scanned with word counts and subjects |
| `root_files.csv` | 30 | Top-level repo files (CLAUDE.md, pnpm-workspace.yaml, etc.) |
| `pack_metadata.csv` | 22 | Per-pack file presence and category indicators |
| `restructure_observations.csv` | 10 | Structural recommendations from the discovery scan |

## NPM Package Analysis

| File | Rows | Description |
|------|------|-------------|
| `npm-packages.csv` | 62 | Published npm packages — versions, downloads, licenses |
| `npm-dist-tags.csv` | 694 | npm dist-tag history for all packages |
| `npm-download-stats.csv` | 51 | Weekly/monthly download counts |
| `npm-version-comparisons.csv` | 128 | Declared vs latest version drift detection |
| `npm-restructure-observations.csv` | 14 | npm-specific structural recommendations |
| `repo-package-sources.csv` | 128 | Where packages are declared (package.json dependencies) |

---

**Note:** JSON equivalents of select tables exist in the parent directory (`../`) for programmatic access.
