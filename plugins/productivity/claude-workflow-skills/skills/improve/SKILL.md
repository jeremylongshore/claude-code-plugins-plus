---
name: improve
description: Analyses the current project across code quality, feature gaps, documentation, security, competitive landscape, and monetisation opportunities, then files prioritised GitHub issues. Use when the user says improve this, analyse this project, find improvements, or fill the backlog.
allowed-tools: Read Glob Grep Bash WebSearch WebFetch
disable-model-invocation: true
---

# Improve

Project: !`basename $(git rev-parse --show-toplevel 2>/dev/null) 2>/dev/null || basename $PWD`
Open issues: !`gh issue list --state open --json number --jq 'length' 2>/dev/null || echo "unknown"`
Last tag: !`git describe --tags --abbrev=0 2>/dev/null || echo "none"`
Recent commits: !`git log --oneline -5 2>/dev/null || echo "none"`

Analyses the current project from multiple angles — technical, strategic, and commercial —
then files actionable GitHub issues for every finding.

## Step 0: Pre-flight check

```bash
gh auth status 2>&1 || { echo "ERROR: gh is not authenticated. Run: gh auth login"; exit 1; }
```

## Step 1: Understand the project

Read these files to build context before analysing anything:

- `README.md` — stated purpose, audience, and feature set
- `CLAUDE.md` — current status, decisions, next steps
- Any `.claude-plugin/plugin.json` or manifest files — metadata and versioning

Then inventory all files:

```bash
find . -not -path './.git/*' -type f | sort
```

Read a representative sample of source files to understand the implementation.
Note: what does this project do, who is it for, and what problem does it solve?

## Step 2: Code quality and bugs

Review source files for:

- Logic errors, edge cases, or fragile assumptions
- Anti-patterns or code that will break under realistic conditions
- Inconsistent behaviour between similar components
- Missing error handling at system boundaries (user input, external APIs)
- Unnecessary complexity or premature abstraction
- Hardcoded values that should be configurable

For shell scripts, also check:

```bash
bash -n <script.sh>   # syntax check each script
```

Label findings: `bug` for defects, `enhancement` for quality improvements.

## Step 3: Feature completeness

Based on the project's stated purpose in README.md, identify:

- Features described but not yet implemented
- Obvious gaps a user of this tool would expect
- Incomplete workflows (things that almost work end-to-end but don't)
- Integration opportunities with tools this project already touches

Label findings: `enhancement`.

## Step 4: Documentation

- Is the README sufficient for a new user to get started without help?
- Are there undocumented behaviours or options?
- Are examples present and accurate?
- Is `CLAUDE.md` current with the real project state?
- Are there missing or misleading inline comments in complex code?

Label findings: `documentation`.

## Step 5: Security

Review for:

- Credentials, tokens, or secrets that could be exposed
- Shell injection risks in any scripts that interpolate external input
- Insecure defaults (world-readable files, unvalidated input passed to system calls)
- Dependencies with known vulnerabilities (check if a lock file or manifest is present)
- Over-permissioned tool or API scopes

Label findings: `security`.

## Step 6: Competitive landscape

Search for similar projects, tools, or plugins in the same space:

- What do competing or complementary tools offer that this project doesn't?
- Are there recent developments in the ecosystem (new APIs, new frameworks) this project
  could leverage?
- What are users asking for in issues/discussions on similar projects?

Use WebSearch to research. Focus on actionable gaps, not general observations.

Label findings: `enhancement` or `idea`.

## Step 7: Monetisation and passive income opportunities

Think about realistic ways this project could generate passive income or build leverage:

- Sponsorship hooks (GitHub Sponsors, Open Collective)
- A premium or hosted tier (what would justify a paid version?)
- Consulting or training services this project could anchor
- Marketplace or integration listings (e.g. plugin marketplaces, app directories)
- Companion products (templates, courses, related tools)
- Licensing opportunities

Be concrete — vague suggestions are not useful. If an opportunity is real, describe
exactly what would need to be built or done.

Label findings: `idea`.

## Step 8: File GitHub issues

For each distinct finding across all dimensions, create one GitHub issue:

```bash
gh issue create \
  --title "<category>: <brief description>" \
  --body "$(cat <<'EOF'
## Summary

<one paragraph describing the finding>

## Why it matters

<impact on users, security, revenue, or maintainability>

## Suggested approach

<concrete steps to address this>

## References

<links to competitive examples, docs, or research — if applicable>
EOF
)" \
  --label "<bug|enhancement|documentation|security|idea>"
```

Avoid duplicate issues — check existing open issues first:

```bash
gh issue list --state open --limit 100
```

Note each issue number as you create it.

## Step 9: Summary report

Output a table of all issues filed:

| # | Title | Label | Priority |
|---|-------|-------|----------|
| N | ...   | ...   | High/Med/Low |

Then call out:

- **Top 3 issues to address first** and why
- **Most surprising finding**
- **Highest-leverage opportunity** (best return for effort)
