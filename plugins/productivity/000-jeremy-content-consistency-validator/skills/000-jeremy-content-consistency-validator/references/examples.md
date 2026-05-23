# Examples

## Example 1: Version Number Audit Across Three Sources

Detect version mismatches between a deployed website, GitHub README, and
internal documentation after a new release.

**Scenario:**

- Website at `tonsofskills.com` claims version 2.1.0
- GitHub README says version 2.0.0
- Internal docs in `docs/release-notes.md` reference version 2.1.0-beta

**Discovery:**

```
Content sources found:
  1. Website: dist/index.html (built site)
  2. GitHub: README.md, CONTRIBUTING.md, CHANGELOG.md
  3. Local docs: docs/release-notes.md, docs/getting-started.md
```

**Report output:**

```markdown
# Content Consistency Report
Generated: 2026-03-17T14:30:00Z

## Executive Summary
- Critical: 1 (version mismatch)
- Warning: 1 (stale beta reference)
- Informational: 0
- Sources scanned: 3

## Critical Findings

### Version Number Mismatch
| Source        | File                    | Line | Version Found |
|---------------|-------------------------|------|---------------|
| Website       | dist/index.html         | 42   | 2.1.0         |
| GitHub        | README.md               | 8    | 2.0.0         |
| Local docs    | docs/release-notes.md   | 3    | 2.1.0-beta    |

**Trust priority:** Website (2.1.0) is authoritative.
**Action:** Update README.md line 8 and docs/release-notes.md line 3 to 2.1.0.

## Warning Findings

### Stale Beta Reference
| Source     | File                  | Line | Content                   |
|------------|-----------------------|------|---------------------------|
| Local docs | docs/release-notes.md | 3    | "Version 2.1.0-beta"      |

**Action:** Remove "-beta" suffix — version 2.1.0 is released.
```

## Example 2: Feature Claim Alignment After New Capability

Detect when a new feature is announced on the website but not mentioned
in developer-facing documentation.

**Scenario:**
The website adds "AI-powered search" to the features list, but the GitHub
README and internal docs do not mention it.

**Report output:**

```markdown
## Warning Findings

### Missing Feature: AI-Powered Search
| Source     | Feature Mentioned | File               | Line |
|------------|-------------------|--------------------|------|
| Website    | Yes               | dist/features.html | 67   |
| GitHub     | No                | README.md          | —    |
| Local docs | No                | docs/features.md   | —    |

**Trust priority:** Website is authoritative — feature exists.
**Action items:**
1. Add "AI-powered search" to README.md features section
2. Add entry to docs/features.md with technical details
3. Update docs/getting-started.md if search setup instructions are needed
```

## Example 3: Terminology Consistency Matrix

Identify inconsistent terminology across content sources where the same
concept uses different names.

**Scenario:**
The project calls its extensions "plugins" on the website, "extensions" in
the GitHub README, and "add-ons" in internal documentation.

**Report output:**

```markdown
## Terminology Consistency Matrix

| Concept           | Website     | GitHub      | Local Docs  | Recommended |
|-------------------|-------------|-------------|-------------|-------------|
| Extensions        | "plugins"   | "extensions"| "add-ons"   | "plugins"   |
| Main page         | "homepage"  | "landing"   | "main page" | "homepage"  |
| Package manager   | "pnpm"     | "pnpm"      | "npm"       | "pnpm"      |
| Install command   | "/install"  | "/install"  | "/add"      | "/install"  |

Occurrences:
  "plugins"    — 14 occurrences across website
  "extensions" — 8 occurrences in README.md, CONTRIBUTING.md
  "add-ons"    — 5 occurrences in docs/architecture.md, docs/developer-guide.md

**Action items (priority order):**
1. Standardize on "plugins" (website is authoritative, highest occurrence count)
2. Replace "extensions" in README.md (lines 12, 34, 56, 78, 91, 103, 115, 128)
3. Replace "add-ons" in docs/architecture.md (lines 22, 45, 67) and
   docs/developer-guide.md (lines 15, 89)
4. Replace "npm" with "pnpm" in docs/getting-started.md (line 23)
5. Replace "/add" with "/install" in docs/quick-reference.md (line 7)
```

## Example 4: Contact Information and URL Audit

Verify that contact details and URLs are consistent and not stale
across all content sources.

**Report output:**

```markdown
## Critical Findings

### Broken Cross-Reference
| Source     | File            | Line | URL                              | Status |
|------------|-----------------|------|----------------------------------|--------|
| GitHub     | CONTRIBUTING.md | 45   | https://tonsofskills.com/legacy  | 404    |
| Local docs | docs/links.md   | 12   | https://old-domain.com/api       | 301    |

### Contact Info Mismatch
| Source     | File          | Line | Email Found              |
|------------|---------------|------|--------------------------|
| Website    | dist/about    | 23   | team@tonsofskills.com    |
| GitHub     | README.md     | 150  | hello@tonsofskills.com   |
| Local docs | docs/support  | 8    | support@intentsolutions.io|

**Trust priority:** Website (team@tonsofskills.com) is authoritative.
**Action items:**
1. Fix broken URL in CONTRIBUTING.md:45 → update to current path
2. Update redirect in docs/links.md:12 → use final destination URL
3. Standardize email to team@tonsofskills.com in all sources
```

## Example 5: Pre-Release Comprehensive Audit

Run a full audit before a major release to catch all inconsistencies at once.

**Command flow:**

```
Step 1: Discover sources
  → Website build: marketplace/dist/ (376 HTML files)
  → GitHub: README.md, CONTRIBUTING.md, CHANGELOG.md, LICENSE
  → Local docs: docs/ directory (12 markdown files)
  → Plugin READMEs: plugins/**/README.md (346 files)

Step 2: Extract structured data
  → Version numbers: 4 distinct values found
  → Feature claims: 28 features mentioned across sources
  → Contact info: 3 email addresses, 2 support URLs
  → Technical requirements: Node.js version, pnpm version, OS support

Step 3: Cross-source comparison
  → 6 source pairs analyzed (website×github, website×docs, etc.)
  → 142 data points compared

Step 4: Classification
  → Critical: 2 (version mismatch, broken URL)
  → Warning: 5 (terminology, missing features, stale dates)
  → Informational: 3 (stylistic differences)
```

**Report saved to:**

```
consistency-reports/2026-03-17-14-30-00.md
```

**Summary table:**

```markdown
## Pre-Release Audit Summary

| Check                    | Status  | Issues |
|--------------------------|---------|--------|
| Version numbers          | FAIL    | 2      |
| Feature claims           | WARNING | 3      |
| Contact information      | FAIL    | 1      |
| URLs and cross-refs      | WARNING | 2      |
| Terminology consistency  | WARNING | 4      |
| Technical requirements   | PASS    | 0      |
| Date references          | WARNING | 1      |

Total: 2 critical, 5 warning, 3 informational
Recommendation: Fix critical items before release. Address warnings in next sprint.
```

## Example 6: Automated CI Integration

Run the validator as part of a CI pipeline to catch consistency drift early.

**GitHub Actions step:**

```yaml
- name: Content Consistency Check
  run: |
    # Run validator in CI mode (exit code 1 on critical findings)
    python scripts/content-consistency-check.py \
      --sources website:marketplace/dist,github:.,docs:docs/ \
      --severity critical \
      --output consistency-reports/ci-report.md

    # Fail the build if critical issues found
    if [ $? -ne 0 ]; then
      echo "::error::Content consistency check found critical issues"
      cat consistency-reports/ci-report.md
      exit 1
    fi
```

**CI output on failure:**

```
::error::Content consistency check found critical issues
Critical: Version mismatch — README.md says 2.0.0, website says 2.1.0
Critical: Broken URL — CONTRIBUTING.md line 45 returns 404
```
