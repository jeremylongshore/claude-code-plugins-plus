---
name: repo-dress
description: |
  Conversational repo creation and governance dressing. Creates a fully dressed,
  validated, released repository with 21 governance files, 6-doc enterprise set,
  CI/CD, and automated quality gate chain. Supports new repos and filling gaps
  in existing repos.
  Trigger with "/repo-dress", "dress this repo", "create new repo", "repo governance".
allowed-tools: 'Read,Write,Edit,Bash(gh:*,git:*,mkdir:*,cp:*,mv:*,ls:*,echo:*,cat:*,sed:*,chmod:*,bd:*,curl:*),Glob,Grep,Skill,Agent'
version: '1.0.0'
author: 'Jeremy Longshore <jeremy@intentsolutions.io>'
license: 'MIT'
tags: ['governance', 'scaffolding', 'repo-setup', 'ci-cd', 'documentation']
---

# Repo Dress — Conversational Repo Creation & Governance

Create a fully dressed, validated, released repository through a 5-question conversation.

## Overview

`/repo-dress` produces a production-ready repository with:

- **21 governance files** (root, GitHub meta, CI/CD)
- **6-doc enterprise planning set** (business case through status)
- **Automated quality gate chain** (beads → doc-filing → validate → gist → sweep → release)
- **Initial v0.1.0 release** cut and published

Complements `/repo-blueprint` (which does code scaffolding). This skill does governance + CI/CD + docs only.

## Usage

### Interactive (default)

```
/repo-dress
```

Starts a 5-question conversation, then builds everything.

### Shortcut (skip interview)

```
/repo-dress freight-tracker "Real-time freight lookup" python intentsolutions public
```

Arguments: `<name> <description> <language> <org> <visibility>`

### Fill-Gaps (existing repos)

```
cd ~/000-projects/existing-repo
/repo-dress --fill-gaps
```

Only adds missing files. Never overwrites existing files.

---

## Instructions

### Phase 0: Parse Arguments & Gather Context

**If arguments are provided (shortcut mode):**
Parse positional arguments: `<name> <description> <language> <org> <visibility>`

**If `--fill-gaps` flag is present:**

- Use current working directory as the project
- Detect existing files to skip
- Infer project name from directory name
- Prompt only for missing context that can't be inferred

**If no arguments (interactive mode):**
Proceed to Phase 1.

### Phase 1: Conversational Drill (5 Questions)

Ask these 5 questions one at a time. Wait for each answer before proceeding.

**Q1: "What's the project name?"**

- Must be kebab-case (e.g., `freight-tracker`)
- Used for: directory name, repo name, all references
- Validate: lowercase, hyphens only, no spaces

**Q2: "One sentence — what does it do?"**

- e.g., "Real-time freight carrier lookup and rate comparison"
- Used for: README description, package.json, doc templates

**Q3: "What language/stack?"**

- Options: `python` | `node` | `ruby` | `go` | `rust` | `generic`
- Used for: .gitignore, CI workflow, editorconfig, dependabot, CONTRIBUTING

**Q4: "Intent Solutions or personal?"**

- Options: `intentsolutions` | `personal`
- Determines:
  - `intentsolutions` → org=`intent-solutions-io`, license=Apache 2.0, email=`jeremy@intentsolutions.io`, security=`security@intentsolutions.io`
  - `personal` → org=`jeremylongshore`, license=MIT, email=`jeremy@jeremylongshore.com`, security=`security@jeremylongshore.com`

**Q5: "Open source or private?"**

- Options: `public` | `private`
- Used for: `gh repo create` visibility flag

### Phase 2: Compute Template Variables

After collecting answers, derive all variables:

```
{{PROJECT_NAME}}        = Q1 answer
{{PROJECT_DESCRIPTION}} = Q2 answer
{{LANGUAGE}}            = Q3 answer
{{GITHUB_ORG}}          = "intent-solutions-io" or "jeremylongshore"
{{ORG_NAME}}            = "Intent Solutions" or "Jeremy Longshore"
{{VISIBILITY}}          = "public" or "private"
{{LICENSE_TYPE}}         = "Apache-2.0" or "MIT"
{{YEAR}}                = current year (e.g., 2026)
{{DATE}}                = current date (YYYY-MM-DD)
{{AUTHOR_NAME}}         = "Jeremy Longshore"
{{AUTHOR_EMAIL}}        = org-aware email
{{SECURITY_EMAIL}}      = org-aware security email
{{CONDUCT_EMAIL}}       = org-aware conduct email
```

### Phase 3: Create Repository

**New repo (not `--fill-gaps`):**

```bash
# Create project directory
mkdir -p ~/000-projects/{{PROJECT_NAME}}
cd ~/000-projects/{{PROJECT_NAME}}

# Initialize git
git init

# Create GitHub remote
gh repo create {{GITHUB_ORG}}/{{PROJECT_NAME}} --{{VISIBILITY}} --source=. --push=false
```

**Fill-gaps mode:**

- Use current directory
- Run `ls -la` to detect existing files
- Build a skip-list of files that already exist
- Only create files NOT in the skip-list

### Phase 4: Write Governance Files (21 files)

Read each template from `~/.claude/skills/repo-dress/templates/`, perform variable substitution, and write to the project. In `--fill-gaps` mode, skip files that already exist.

#### Root Governance (12 files)

| #   | Target File          | Template                                                        |
| --- | -------------------- | --------------------------------------------------------------- |
| 1   | `README.md`          | `templates/README.md.tmpl`                                      |
| 2   | `CHANGELOG.md`       | `templates/CHANGELOG.md.tmpl`                                   |
| 3   | `LICENSE`            | `templates/LICENSE-MIT.tmpl` or `templates/LICENSE-APACHE.tmpl` |
| 4   | `CODE_OF_CONDUCT.md` | `templates/CODE_OF_CONDUCT.md.tmpl`                             |
| 5   | `CONTRIBUTING.md`    | `templates/CONTRIBUTING.md.tmpl`                                |
| 6   | `SECURITY.md`        | `templates/SECURITY.md.tmpl`                                    |
| 7   | `SUPPORT.md`         | `templates/SUPPORT.md.tmpl`                                     |
| 8   | `CLAUDE.md`          | `templates/CLAUDE.md.tmpl`                                      |
| 9   | `AGENTS.md`          | `templates/AGENTS.md.tmpl`                                      |
| 10  | `.gitignore`         | `templates/gitignore/{{LANGUAGE}}.tmpl`                         |
| 11  | `.editorconfig`      | `templates/editorconfig.tmpl`                                   |
| 12  | `.gitattributes`     | `templates/gitattributes.tmpl`                                  |

#### GitHub Layer (6 files)

| #   | Target File                                 | Template                                                   |
| --- | ------------------------------------------- | ---------------------------------------------------------- |
| 13  | `.github/FUNDING.yml`                       | `templates/github/FUNDING.yml.tmpl`                        |
| 14  | `.github/CODEOWNERS`                        | `templates/github/CODEOWNERS.tmpl`                         |
| 15  | `.github/PULL_REQUEST_TEMPLATE.md`          | `templates/github/PULL_REQUEST_TEMPLATE.md.tmpl`           |
| 16  | `.github/ISSUE_TEMPLATE/bug_report.md`      | `templates/github/issue-templates/bug_report.md.tmpl`      |
| 17  | `.github/ISSUE_TEMPLATE/feature_request.md` | `templates/github/issue-templates/feature_request.md.tmpl` |
| 18  | `.github/ISSUE_TEMPLATE/config.yml`         | `templates/github/issue-templates/config.yml.tmpl`         |

#### CI/CD (3 files)

| #   | Target File                     | Template                                       |
| --- | ------------------------------- | ---------------------------------------------- |
| 19  | `.github/dependabot.yml`        | `templates/github/dependabot.yml.tmpl`         |
| 20  | `.github/workflows/ci.yml`      | `templates/workflows/ci-{{LANGUAGE}}.yml.tmpl` |
| 21  | `.github/workflows/release.yml` | `templates/workflows/release.yml.tmpl`         |

**Template Substitution Process:**

For each template file:

1. Read the `.tmpl` file content
2. Replace all `{{VARIABLE}}` placeholders with computed values
3. Write to the target path in the project directory
4. If `--fill-gaps` and target exists, skip with message: `  SKIP: {file} (already exists)`

### Phase 5: Seed `000-docs/` with 6-Doc Set

```bash
mkdir -p 000-docs
```

| #   | Target File                                   | Template                                                 |
| --- | --------------------------------------------- | -------------------------------------------------------- |
| 1   | `000-docs/001-PP-BCASE-business-case.md`      | `templates/docs/001-PP-BCASE-business-case.md.tmpl`      |
| 2   | `000-docs/002-PP-PRD-product-requirements.md` | `templates/docs/002-PP-PRD-product-requirements.md.tmpl` |
| 3   | `000-docs/003-AT-ARCH-architecture.md`        | `templates/docs/003-AT-ARCH-architecture.md.tmpl`        |
| 4   | `000-docs/004-PP-UJRN-user-journey.md`        | `templates/docs/004-PP-UJRN-user-journey.md.tmpl`        |
| 5   | `000-docs/005-AT-SPEC-technical-spec.md`      | `templates/docs/005-AT-SPEC-technical-spec.md.tmpl`      |
| 6   | `000-docs/006-OD-STAT-status.md`              | `templates/docs/006-OD-STAT-status.md.tmpl`              |

All use doc-filing v4 naming convention. Placeholders filled from interview answers.

### Phase 6: Initial Commit + Push

```bash
git add -A
git commit -m "feat: initial project setup with full governance"
git push -u origin main
```

In `--fill-gaps` mode:

```bash
git add -A
git commit -m "feat: add missing governance files"
git push
```

### Phase 7: Automated Quality Gate Chain

Run these skills sequentially. Each must complete before the next starts. No prompting between steps — fully autonomous.

**Step 1: Initialize beads**

```
/beads
```

**Step 2: Validate doc-filing structure**

```
/doc-filing
```

**Step 3: Cross-artifact consistency check**

```
/validate-consistency
```

**Step 4: Create project landing gist (Pattern A)**

```
/gist-auditor
```

**Step 5: Repository housekeeping sweep**

```
/repo-sweep
```

**Step 6: Cut initial release**

```
/release
```

Target: v0.1.0

### Phase 8: Report

After all phases complete, output a summary:

```
============================================
{{PROJECT_NAME}} created and dressed
============================================
  Repo:    github.com/{{GITHUB_ORG}}/{{PROJECT_NAME}}
  Files:   21 governance + 6 docs + CI/CD
  Release: v0.1.0
  Gist:    [link from gist-auditor output]

  Governance: complete
  Docs:       6-doc enterprise set seeded
  CI/CD:      lint + test + release automation
  Beads:      initialized

  Next: start building.
============================================
```

---

## Fill-Gaps Detection

When `--fill-gaps` is active:

1. Scan current directory for all 27 expected files (21 governance + 6 docs)
2. Build two lists:
   - **EXISTS**: Files already present (will be skipped)
   - **MISSING**: Files to be created
3. Show the user what will be created:

   ```
   Fill-gaps analysis for existing-repo:
     EXISTS (skip): README.md, LICENSE, .gitignore, ... (14 files)
     MISSING (will create): SUPPORT.md, AGENTS.md, .editorconfig, ... (13 files)

   Proceed? [Y/n]
   ```

4. Only create MISSING files
5. Skip Phase 3 (repo already exists)
6. Adjust commit message: `"feat: add missing governance files"`

---

## Template Variable Reference

| Variable                  | Source          | Example                            |
| ------------------------- | --------------- | ---------------------------------- |
| `{{PROJECT_NAME}}`        | Q1              | `freight-tracker`                  |
| `{{PROJECT_DESCRIPTION}}` | Q2              | `Real-time freight carrier lookup` |
| `{{LANGUAGE}}`            | Q3              | `python`                           |
| `{{GITHUB_ORG}}`          | Derived from Q4 | `intent-solutions-io`              |
| `{{ORG_NAME}}`            | Derived from Q4 | `Intent Solutions`                 |
| `{{VISIBILITY}}`          | Q5              | `public`                           |
| `{{LICENSE_TYPE}}`        | Derived         | `Apache-2.0` or `MIT`              |
| `{{YEAR}}`                | System          | `2026`                             |
| `{{DATE}}`                | System          | `2026-03-23`                       |
| `{{AUTHOR_NAME}}`         | Constant        | `Jeremy Longshore`                 |
| `{{AUTHOR_EMAIL}}`        | Org-aware       | `jeremy@intentsolutions.io`        |
| `{{SECURITY_EMAIL}}`      | Org-aware       | `security@intentsolutions.io`      |
| `{{CONDUCT_EMAIL}}`       | Org-aware       | `conduct@intentsolutions.io`       |

---

## Language-Specific Behavior

| Aspect          | python                  | node                 | ruby                     | go                    | rust                | generic               |
| --------------- | ----------------------- | -------------------- | ------------------------ | --------------------- | ------------------- | --------------------- |
| `.gitignore`    | venv, **pycache**, .egg | node_modules, dist   | vendor/bundle, .gem      | bin/, vendor/         | target/, Cargo.lock | OS + editor only      |
| CI runner       | `pip install`, `pytest` | `npm ci`, `npm test` | `bundle install`, `rake` | `go build`, `go test` | lint + test stubs   |
| Dependabot      | `pip`                   | `npm`                | `bundler`                | `gomod`               | `cargo`             | `github-actions` only |
| `.editorconfig` | 4-space indent          | 2-space indent       | 2-space indent           | tab indent            | 4-space indent      | 4-space indent        |
| CONTRIBUTING    | pytest, black, ruff     | eslint, prettier     | rubocop, rspec           | gofmt, golint         | cargo fmt, clippy   | generic guidelines    |

---

## Design Decisions

1. **Conversational by default** — `/repo-dress` starts talking. No modes to remember.
2. **5 questions max** — name, description, language, org, visibility. Everything else is opinionated.
3. **Full pipeline auto-runs** — beads → doc-filing → validate → gist → sweep → release. No prompting.
4. **Templates are separate .tmpl files** — not inline. Maintainable and auditable.
5. **Reuses existing canonical content** — CODE_OF_CONDUCT/CONTRIBUTING/SECURITY from project-template, 6-doc from repo-blueprint, release.yml from jeremylongshore.com.
6. **Idempotent** — `--fill-gaps` for existing repos skips what already exists.
7. **No code scaffolding** — governance + CI/CD + docs only. Use `/repo-blueprint` for code structure.

---

## Error Handling

| Error                         | Cause                    | Recovery                                           |
| ----------------------------- | ------------------------ | -------------------------------------------------- |
| `gh: not found`               | GitHub CLI not installed | `brew install gh` or `conda install gh`            |
| Repo already exists on GitHub | Name collision           | Prompt user to choose different name               |
| Permission denied             | Auth issue               | `gh auth login`                                    |
| Template not found            | Missing .tmpl file       | Error with path, suggest reinstall                 |
| Skill chain failure           | Downstream skill error   | Report which skill failed, continue with remaining |

---

## Resources

- Templates: `~/.claude/skills/repo-dress/templates/`
- Governance checklist: `~/.claude/skills/repo-dress/references/governance-checklist.md`
- Doc-filing standard: `~/000-projects/project-template/000-docs/6767-a-DR-STND-document-filing-system-standard-v4.md`
- Project-template canonical: `~/000-projects/project-template/`
