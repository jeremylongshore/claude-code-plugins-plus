---
name: 000-jeremy-content-consistency-validator
description: |
  Validate messaging consistency across website, GitHub repos, and local documentation generating read-only discrepancy reports. Use when checking content alignment or finding mixed messaging. Trigger with phrases like "check consistency", "validate documentation", or "audit messaging".
allowed-tools: Read, WebFetch, WebSearch, Grep, Bash(diff:*), Bash(grep:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
tags: [productivity, audit, 000-jeremy]

---
# Content Consistency Validator

## Overview

Checks content for tone, terminology, formatting, and structural consistency across multiple documentation sources (websites, GitHub repos, local docs). Generates read-only discrepancy reports with severity-classified findings and actionable fix suggestions including file paths and line numbers.

## Examples

- **Pre-release audit**: Before tagging a new version, run the validator to catch version mismatches between your README, docs site, and changelog — e.g., the website says v2.1.0 but the GitHub README still references v2.0.0.
- **Post-rebrand check**: After renaming a product or updating terminology (e.g., "plugin" to "extension"), validate that all docs, landing pages, and contributing guides use the new term consistently.
- **Onboarding review**: When a new contributor flags confusing docs, run a consistency check to surface contradictory feature claims, outdated contact info, or missing sections across your documentation sources.

## Prerequisites

- Access to at least two content sources (website, GitHub repo, or local docs directory)
- WebFetch permissions configured for remote URLs (deployed sites, GitHub raw content)
- Local documentation stored in recognizable paths (`docs/`, `claudes-docs/`, `internal/`)

## Instructions

1. **Discover sources** — scan for build directories (`dist/`, `build/`, `public/`, `out/`, `_site/`), GitHub README/CONTRIBUTING files, and local doc folders:
   ```bash
   find . -maxdepth 3 -name "README*" -o -name "CONTRIBUTING*" | head -20
   ls -d docs/ claudes-docs/ internal/ 2>/dev/null
   ```
2. **Extract structured data** from each source: version numbers, feature claims, product names, taglines, contact info, URLs, and technical requirements:
   ```bash
   grep -rn 'v[0-9]\+\.[0-9]\+' docs/ README.md
   grep -rn -i 'features\|capabilities' docs/ README.md
   ```
3. **Verify extraction** — confirm at least 3 data points per source. If a source returns empty, check the Error Handling table before continuing.
4. **Build comparison matrix** pairing each source against every other (website vs GitHub, website vs local docs, GitHub vs local docs):
   ```bash
   diff <(grep -i 'version' README.md) <(grep -i 'version' docs/overview.md)
   ```
5. **Classify discrepancies** by severity:
   - **Critical**: conflicting version numbers, contradictory feature lists, mismatched contact info, broken cross-references
   - **Warning**: inconsistent terminology (e.g., "plugin" vs "extension"), missing information in one source, outdated dates
   - **Informational**: stylistic differences, platform-specific wording, differing detail levels
6. **Apply trust priority**: website (most authoritative) > GitHub (developer-facing) > local docs (internal use).
7. **Generate report** as Markdown with: executive summary, per-pair comparison tables, terminology consistency matrix, and prioritized action items with file paths and line numbers.
8. **Save** to `consistency-reports/YYYY-MM-DD-HH-MM-SS.md`.

## Report Format

```markdown
# Consistency Report — YYYY-MM-DD

## Executive Summary
| Severity | Count |
|----------|-------|
| Critical | 2     |
| Warning  | 5     |
| Info     | 3     |

## Website vs GitHub
| Field        | Website       | GitHub        | Severity |
|-------------|---------------|---------------|----------|
| Version     | v2.1.0        | v2.0.0        | Critical |
| Feature X   | listed        | missing       | Warning  |

## Action Items
1. **Critical** — Update `README.md:14` version from v2.0.0 → v2.1.0
2. **Warning** — Add "Feature X" to `README.md` feature list
```

## Output

The skill produces a timestamped Markdown report saved to `consistency-reports/YYYY-MM-DD-HH-MM-SS.md` containing:
- **Executive summary**: Severity counts (Critical/Warning/Info) at a glance
- **Pair comparison tables**: Field-by-field comparison between each source pair with severity classification
- **Terminology matrix**: Cross-source consistency check for product names, versions, and key terms
- **Prioritized action items**: Specific fixes with file paths and line numbers, ordered by severity

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Website content unreachable | URL returns 4xx/5xx or build dir missing | Verify site is deployed or run local build; check WebFetch permissions |
| GitHub API rate limit | Too many fetches in short window | Pause and retry after reset window; use authenticated requests |
| No documentation directory | Expected paths don't exist | Confirm working directory; specify doc path explicitly |
| Empty content extraction | Client-side rendering not visible to fetch | Use local build output directory instead of live URL |
| Diff command failure | File paths contain special characters | Quote all file paths passed to diff and grep |

## Resources

- Content source discovery logic: `${CLAUDE_SKILL_DIR}/references/how-it-works.md`
- Trust priority and validation timing: `${CLAUDE_SKILL_DIR}/references/best-practices.md`
- Use-case walkthroughs: `${CLAUDE_SKILL_DIR}/references/example-use-cases.md`
