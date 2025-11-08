---
name: validate-consistency
description: Generate comprehensive read-only discrepancy report comparing messaging consistency across website, GitHub, and local documentation
model: sonnet
temperature: 0.0
---

**CRITICAL INSTRUCTIONS:**
- **Temperature: 0.0** - ZERO creativity. Pure factual analysis only.
- **Read-only** - Report discrepancies, never suggest creative solutions
- **Exact matching** - Report differences precisely as they appear
- **No interpretation** - List facts, not opinions or creative alternatives

# Content Consistency Validation Report Generator

Generate a comprehensive read-only discrepancy report that identifies messaging inconsistencies across:
1. **Website content** (ANY HTML-based website: static HTML, WordPress, Hugo, Astro, Jekyll, Next.js, React, Vue, Gatsby, etc.) - **OFFICIAL SOURCE OF TRUTH**
2. **GitHub repositories** (README, docs, technical documentation)
3. **Local documentation** (SOPs, standards, principles, beliefs, training materials, internal docs, procedures)

**WORKFLOW MANDATE:**
- Website is the OFFICIAL documentation - always the source of truth
- Internal docs (SOPs, standards, principles, beliefs) MUST match website
- Report what's missing/different in local docs compared to published web content
- Zero tolerance for creative interpretation - report exact differences only

## Report Structure

Create a Markdown report with these sections:

### 1. Executive Summary
- Total sources analyzed
- Critical discrepancies count
- Warnings count
- Informational notes count

### 2. Source Inventory
List all content sources discovered:
- Website pages (with URLs)
- GitHub files (with repo paths)
- Local docs (with file paths)

### 3. Critical Discrepancies 🔴
Issues that MUST be fixed:
- Version number conflicts
- Feature list contradictions
- Contact information mismatches
- Technical requirement conflicts
- Broken cross-references

For each:
- Show conflicting content from each source
- Provide exact file locations and line numbers
- Recommend which source is authoritative

### 4. Warnings 🟡
Issues that SHOULD be reviewed:
- Inconsistent terminology
- Different phrasing of same concepts
- Missing information in one source
- Outdated timestamps

For each:
- Compare the variations
- Suggest standardization approach

### 5. Terminology Analysis
Table showing term usage across sources:
| Term | Website | GitHub | Local Docs | Recommendation |
|------|---------|--------|------------|----------------|

### 6. Priority Action Items
Ordered list of fixes:
1. 🔴 Critical issues first
2. 🟡 Warnings second
3. 🟢 Informational last

Each with:
- What to fix
- Where to fix it
- Recommended approach

## Implementation Steps

### Step 1: Discover Sources

Use these patterns to find content:

**Website (detect ANY HTML-based site automatically):**
```bash
# Static HTML sites
find . -name "*.html" -not -path "*/node_modules/*" -not -path "*/.git/*"

# Hugo sites
find . -name "*.md" -path "*/content/*"
find . -name "*.html" -path "*/themes/*" -o -path "*/layouts/*"

# Astro sites
find . -name "*.astro" -o -name "*.md" -path "*/src/pages/*"

# Jekyll/GitHub Pages
find . -name "*.md" -path "*/_posts/*" -o -path "*/_pages/*"
find . -name "*.html" -path "*/_layouts/*" -o -path "*/_includes/*"

# WordPress sites
find . -name "*.php" -path "*/wp-content/themes/*"
find . -name "*.html" -path "*/wp-content/*"

# Next.js/React sites
find . -name "*.tsx" -o -name "*.jsx" -path "*/pages/*" -o -path "*/app/*"
find . -name "*.html" -path "*/out/*" -o -path "*/build/*" -o -path "*/.next/*"

# Vue/Nuxt sites
find . -name "*.vue" -path "*/pages/*" -o -path "*/components/*"
find . -name "*.html" -path "*/dist/*" -o -path "*/.nuxt/*"

# Gatsby sites
find . -name "*.js" -o -name "*.jsx" -path "*/src/pages/*"
find . -name "*.html" -path "*/public/*"

# 11ty/Eleventy sites
find . -name "*.md" -o -name "*.njk" -not -path "*/node_modules/*"
find . -name "*.html" -path "*/_site/*"

# Docusaurus sites
find . -name "*.md" -o -name "*.mdx" -path "*/docs/*" -o -path "*/blog/*"
find . -name "*.html" -path "*/build/*"
```

**GitHub:**
```bash
# Key files
find . -name "README.md" -o -name "CONTRIBUTING.md"
find . -path "*/docs/*.md"
```

**Local Docs:**
```bash
# Documentation directories
find . -path "*/claudes-docs/*.md"
find . -path "*/docs/*.md" -not -path "*/.git/*"
find . -path "*/000-docs/*.md"
```

### Step 2: Extract Key Content

For each source, extract:
- **Version numbers**: Look for `v\d+\.\d+\.\d+`, `version`, `release`
- **Feature claims**: Lists, bullet points, "supports X", "includes Y"
- **Contact info**: Email addresses, support URLs, social media links
- **Technical specs**: Requirements, dependencies, installation steps
- **Terminology**: Product names, technical terms, acronyms

Use grep patterns:
```bash
# Versions
grep -E "v[0-9]+\.[0-9]+\.[0-9]+" file.md

# Email addresses
grep -E "[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}" file.md

# URLs
grep -E "https?://[^\s)]+" file.md

# Feature keywords
grep -iE "(feature|supports|includes|provides)" file.md
```

### Step 3: Compare & Analyze

Build comparison tables:

```markdown
## Version Comparison

| Source | Version | Location | Last Updated |
|--------|---------|----------|--------------|
| Website | v1.2.1 | /about/index.html:45 | 2025-10-23 |
| GitHub | v1.2.0 | README.md:12 | 2025-10-20 |
| Docs | v1.2.0 | 000-docs/082-*.md:8 | 2025-10-18 |

🔴 **CRITICAL**: Website shows v1.2.1 but GitHub/Docs show v1.2.0
```

### Step 4: Generate Report

Save report to:
```
consistency-reports/YYYY-MM-DD-HH-MM-SS-full-audit.md
```

Include timestamp, sources analyzed, and full findings.

### Step 5: Present Summary

Print terminal summary:
```
╔════════════════════════════════════════════════╗
║   Content Consistency Validation Report       ║
║   Generated: 2025-10-23 10:45:23              ║
╠════════════════════════════════════════════════╣
║  Sources Analyzed: 47 files                   ║
║  🔴 Critical Issues: 3                         ║
║  🟡 Warnings: 12                               ║
║  🟢 Informational: 8                           ║
╠════════════════════════════════════════════════╣
║  Report saved to:                              ║
║  consistency-reports/2025-10-23-10-45-23.md   ║
╚════════════════════════════════════════════════╝
```

## Read-Only Operations ONLY

✅ **Allowed:**
- `Read` - Read local files
- `Glob` - Find files by pattern
- `Grep` - Search file contents
- `Bash` (read-only): `cat`, `grep`, `find`, `wc`

❌ **Forbidden:**
- `Write` - NO file modifications
- `Edit` - NO file edits
- `git commit` - NO version control changes
- Any destructive operations

## Example Report Sections

### Critical Discrepancy Example

```markdown
### 🔴 CRITICAL: Plugin Count Mismatch

**Issue:** Different plugin counts across platforms

**Website Says:**
"236 production-ready plugins"
- Location: index.html:89
- Last updated: 2025-10-23

**GitHub Says:**
"Over 230 plugins available"
- Location: README.md:45
- Last updated: 2025-10-20

**Local Docs Say:**
"230+ plugins in marketplace"
- Location: 000-docs/training-guide.md:156
- Last updated: 2025-10-15

**Impact:** Potential customer confusion, inconsistent marketing

**Recommendation:**
1. Standardize on "236 plugins" (most specific)
2. Update GitHub README.md line 45
3. Update training-guide.md line 156
4. Set reminder to update all sources when count changes

**Priority:** HIGH - Public-facing inconsistency
```

### Warning Example

```markdown
### 🟡 WARNING: Terminology Inconsistency

**Issue:** Mixing "plugin" and "extension" terms

**Website:** Consistently uses "plugin" (23 mentions)
**GitHub:** Uses both "plugin" (15x) and "extension" (3x)
**Docs:** Consistently uses "plugin" (45 mentions)

**Analysis:**
- Majority consensus: "plugin"
- GitHub has 3 outliers using "extension"

**Recommendation:**
1. Update GitHub docs to use "plugin" exclusively
2. Add terminology guide to CONTRIBUTING.md
3. Add linter rule to catch "extension" usage

**Priority:** MEDIUM - Internal consistency issue
```

## User Experience

### Interactive Prompts

If scope is unclear, ask:
```
I'll validate content consistency. Please specify:
1. Which sources? (website/github/docs/all)
2. Focus area? (versions/features/contact/all)
3. Report detail? (summary/detailed/comprehensive)
```

### Progress Updates

Show progress:
```
🔍 Scanning website... found 23 pages
🔍 Scanning GitHub... found 15 markdown files
🔍 Scanning local docs... found 9 documentation files

📊 Analyzing version mentions... 15 found
📊 Analyzing feature claims... 34 found
📊 Analyzing contact info... 8 found

✅ Analysis complete. Generating report...
```

### Final Output

```
✅ Consistency Report Complete

📄 Full report: consistency-reports/2025-10-23-10-45-23-full-audit.md

🔴 3 critical issues require immediate attention
🟡 12 warnings should be reviewed soon
🟢 8 informational notes for awareness

Top priority fix:
→ Update version number in GitHub README.md (v1.2.0 → v1.2.1)
```

## Integration Example

```bash
# User runs command
/validate-consistency

# Or asks naturally
"Check if my website matches GitHub docs"
"Validate consistency before I update training materials"
"Find mixed messaging across all platforms"
```

The command/skill automatically:
1. Discovers all relevant sources
2. Extracts key messaging
3. Compares for consistency
4. Generates detailed report
5. Provides actionable recommendations

**Remember: READ-ONLY. Never modify files. Only report discrepancies.**
