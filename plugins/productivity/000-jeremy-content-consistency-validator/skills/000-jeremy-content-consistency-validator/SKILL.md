---
name: 000-jeremy-content-consistency-validator
description: |
  Validate messaging consistency across website, GitHub repos, and local documentation generating read-only discrepancy reports. Use when checking content alignment or finding mixed messaging. Trigger with phrases like "check consistency", "validate documentation", or "audit messaging".
allowed-tools: Read, WebFetch, WebSearch, Grep, Bash(diff:*), Bash(grep:*)
version: 1.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
compatible-with: claude-code, codex, openclaw
---

# Content Consistency Validator

## Overview

Cross-platform content consistency auditing for organizations maintaining messaging across websites, GitHub repositories, and local documentation. This read-only skill discovers content sources, extracts key messaging elements, and generates severity-graded discrepancy reports -- without modifying any files. Ideal for pre-release audits, rebranding verification, and ongoing documentation hygiene.

## Prerequisites

- Access to at least two content sources (website, GitHub repo, or local docs directory)
- WebFetch permissions configured for remote URLs (deployed sites, GitHub raw content)
- Local documentation stored in recognizable paths (`docs/`, `claudes-docs/`, `internal/`)
- Grep and diff access for comparing extracted content fragments

## Instructions

1. Discover all content sources by scanning for website build directories (e.g., `dist/`, `build/`, `public/`, `out/`, `_site/`), GitHub README/CONTRIBUTING files, and local documentation folders.
2. Extract structured data from each source: version numbers, feature claims, product names, taglines, contact information, URLs, and technical requirements.
3. Build a cross-source comparison matrix pairing each source against every other source (website vs GitHub, website vs local docs, GitHub vs local docs).
4. Classify discrepancies by severity:
   - **Critical**: conflicting version numbers, contradictory feature lists, mismatched contact info, broken cross-references.
   - **Warning**: inconsistent terminology (e.g., "plugin" vs "extension"), missing information in one source, outdated dates.
   - **Informational**: stylistic differences, platform-specific wording, differing detail levels.
5. Apply trust priority when noting conflicts: website (most authoritative) > GitHub (developer-facing) > local docs (internal use).
6. Generate the final Markdown report with executive summary, per-pair comparison tables, a terminology consistency matrix, and prioritized action items with file paths and line numbers.
7. Save the report to `consistency-reports/YYYY-MM-DD-HH-MM-SS.md`.

## Output

- Markdown report containing:
  - Executive summary with discrepancy counts grouped by severity
  - Source-pair comparison sections (website vs GitHub, website vs local docs, GitHub vs local docs)
  - Terminology consistency matrix showing term usage across all sources
  - Prioritized action items with specific file locations, line numbers, and suggested corrections
- Report file saved to `consistency-reports/` with timestamped filename

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Website content unreachable | Deployed URL returns 4xx/5xx or local build directory missing | Verify the site is deployed or run the local build; check WebFetch permissions |
| GitHub API rate limit exceeded | Too many raw content fetches in a short window | Pause and retry after the rate-limit reset window; use authenticated requests |
| No documentation directory found | Expected paths (`docs/`, `claudes-docs/`) do not exist | Confirm correct working directory; specify the documentation path explicitly |
| Empty content extraction | Source page uses client-side rendering not visible to fetch | Use a local build output directory instead of the live URL |
| Diff command failure | File paths contain special characters | Quote all file paths passed to diff and grep commands |

## Examples

**Example 1: Pre-release version audit**
- Scenario: A new version (v2.1.0) ships but internal training docs still reference v2.0.0.
- Action: Run the validator across the website, GitHub README, and `docs/` directory.
- Result: Report flags version mismatch as Critical, listing each file and line where the old version appears.

**Example 2: Feature claim alignment after adding a new capability**
- Scenario: The website announces "AI-powered search" but the GitHub README omits it.
- Action: Validator extracts feature lists from both sources and compares.
- Result: Warning-level discrepancy noting the missing feature mention in the GitHub README with a suggested addition.

**Example 3: Terminology consistency check**
- Scenario: The website uses "plugins" while local docs use "extensions" and GitHub uses "add-ons."
- Action: Validator builds a terminology matrix across all three sources.
- Result: Informational note with a recommendation to standardize on a single term, listing every occurrence.

## Resources

- Content source discovery logic: `{baseDir}/references/how-it-works.md`
- Trust priority and validation timing guidance: `{baseDir}/references/best-practices.md`
- Concrete use-case walkthroughs: `{baseDir}/references/example-use-cases.md`
- YAML 1.2 specification (for config file validation): https://yaml.org/spec/
- GitHub REST API documentation: https://docs.github.com/en/rest
