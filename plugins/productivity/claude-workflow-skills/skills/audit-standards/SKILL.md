---
name: audit-standards
description: Audits the current project against the development standards defined in ~/.claude/CLAUDE.md. Documents non-compliant findings as GitHub issues and writes a prioritised fix plan to the project CLAUDE.md. Use when the user says audit against settings, audit standards, check standards compliance, or audit this project.
allowed-tools: Read Glob Grep Bash
disable-model-invocation: true
---

# Audit Standards

Project: !`basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || basename $PWD`
Branch: !`git branch --show-current 2>/dev/null || echo "unknown"`

Audits the current project against the personal development standards loaded from `~/.claude/CLAUDE.md`.
Generates actionable GitHub issues and a prioritised fix plan.

The development standards from the user's global `~/.claude/CLAUDE.md` are already loaded into context.
The key principles to audit against are:

1. **Codify, Don't Document** — manual steps should be executable scripts
2. **Bash Script UX with pfb** — terminal output uses pfb with correct visual hierarchy
3. **Markdown Standards** — all markdown passes markdownlint with zero warnings
4. **Professional Documentation Tone** — formal docs are objective, not personal
5. **Version Control Everything** — correct files committed, secrets excluded
6. **Fail Fast, Pivot Early** — (process principle, skip for static audit)
7. **Behavioral Integrity** — (process principle, skip for static audit)

## Step 0: Pre-flight check

```bash
gh auth status 2>&1 || { echo "ERROR: gh is not authenticated. Run: gh auth login"; exit 1; }
```

## Step 1: Inventory the project

```bash
find . -not -path './.git/*' -type f | sort
```

Also read:

- `README.md` — documentation tone and completeness
- `CLAUDE.md` — project AI context file exists and is current
- Any `.env`, `.env.template`, `.gitignore` — secrets handling
- Any `*.sh` files — bash scripting standards
- Any `*.md` files — markdown quality

## Step 2: Audit each principle

### Principle 1 — Codify, Don't Document

- Does the README describe manual steps that should instead be scripts?
- Do bash scripts use `#!/usr/bin/env bash` shebang?
- Do scripts have Google-Style header docs (name, description, author, version, usage, dependencies)?
- Do functions have `@param`, `@return`, `@example` doc comments?
- Is author attribution derived from `git config user.name`/`git config user.email`?
- Are scripts idempotent (safe to run multiple times)?

Run: `grep -rn "#!/" --include="*.sh" .` to find all scripts.

### Principle 2 — Bash Script UX with pfb

For each `.sh` file:

- Is pfb used for terminal output (not plain `echo` for status messages)?
- Are emojis passed as a parameter, not embedded in the message string?
- Are log levels (`pfb info/success/warn/error`) used for single-line status only?
- Is visual hierarchy consistent (heading → subheading, not mixed)?

Run: `grep -rn "pfb\|echo" --include="*.sh" .` and compare usage patterns.

### Principle 3 — Markdown Standards

Check for a `.markdownlint.json` at the repo root:

```bash
cat .markdownlint.json 2>/dev/null || echo "MISSING"
```

Run markdownlint if available:

```bash
markdownlint '**/*.md' 2>&1 | head -50
```

Check:

- Blank lines around headings, lists, code blocks, tables
- Code blocks specify a language (no bare triple-backtick fences)
- Prose lines ≤ 120 characters
- URLs wrapped in `<>` or link syntax
- Consistent list numbering (1. 2. 3.)
- YAML frontmatter description fields are single unbroken lines

### Principle 4 — Professional Documentation Tone

Read `README.md` and any formal docs. Flag:

- Second-person language ("you", "your") in formal technical docs (README intro, architecture sections)
- Conversational phrasing in formal sections
- User-specific references that should be generic

Note: READMEs and tutorials may use "you" in instructional sections — this is acceptable.

### Principle 5 — Version Control Everything

```bash
cat .gitignore 2>/dev/null || echo "MISSING .gitignore"
ls .env* 2>/dev/null
```

Check:

- `.gitignore` exists and excludes `.env`, secrets, build artifacts, IDE files
- `.env.template` exists if the project requires environment configuration
- No `.env` with real values present
- AI context files (`CLAUDE*.md`, `AGENTS*.md`, `GEMINI*.md`) are gitignored and symlinked

#### AI context file check

Find all AI context files in the project (excluding `.git`):

```bash
find . -not -path './.git/*' \( -name 'CLAUDE*.md' -o -name 'AGENTS*.md' -o -name 'GEMINI*.md' \) | sort
```

For each file found, verify two things:

1. **Gitignored** — the pattern appears in `.gitignore`:

   ```bash
   git check-ignore -v <file>
   ```

2. **Symlink** — the file is a symbolic link (pointing to the private `ai-context` repo), not a regular tracked file:

   ```bash
   [ -L "<file>" ] && echo "SYMLINK" || echo "REGULAR FILE — should be a symlink"
   ```

A finding is raised for any AI context file that is **not** gitignored OR is **not** a symlink. The expected
pattern is: file is listed in `.gitignore`, stored in the private `ai-context` repo, and symlinked back into
the project directory so local AI tooling finds it normally (see `extract-ai-context.sh` in that repo).

## Step 3: Generate GitHub issues

First, fetch all open issues to avoid creating duplicates:

```bash
gh issue list --state open --limit 100 --json title --jq '.[].title'
```

For each finding, check whether an open issue with a matching title already exists. If one does,
skip it. Only create an issue if no existing open issue covers the same finding.

For each distinct finding with no existing open issue, create a GitHub issue:

```bash
gh issue create \
  --title "<principle>: <brief description of violation>" \
  --body "$(cat <<'EOF'
## Principle

<which standard this relates to>

## Finding

<description of the non-compliance>

## Expected

<what the standard requires>

## Current state

<what was found in the project>

## Suggested fix

<concrete change to make>
EOF
)" \
  --label "enhancement"
```

Use `--label "bug"` for missing required files or broken standards; `--label "enhancement"` for
improvements and style compliance.

Note each issue number as you go.

## Step 4: Write prioritised fix plan to CLAUDE.md

Append or update a section in the project `CLAUDE.md` under the heading
`## Standards Audit — <today's date>`:

```markdown
## Standards Audit — YYYY-MM-DD

Issues generated from `/audit-standards` review against ~/.claude/CLAUDE.md.
Suggested fix order:

### Group 1 — Correctness (fix first)

- #N: <title>
- #N: <title>

### Group 2 — Standards Compliance

- #N: <title>
- #N: <title>

### Group 3 — Quality Improvements

- #N: <title>
- #N: <title>
```

Order: missing required files first, then standards violations, then style improvements.

## Step 5: Report summary

Output a brief summary:

- Total issues created (with links)
- Which principle had the most findings
- Top-priority fix
- Link to the CLAUDE.md section added
