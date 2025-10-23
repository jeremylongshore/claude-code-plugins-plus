---
name: 000-jeremy-content-consistency-validator
description: |
  Validates messaging consistency across website, GitHub repositories, and local documentation. Generates comprehensive read-only discrepancy reports showing where messaging conflicts or inconsistencies exist. Activates when user mentions "consistency check", "validate documentation", "check for mixed messaging", "audit content consistency", or before updating internal paperwork.
temperature: 0.0
---

**CRITICAL OPERATING PARAMETERS:**
- **Temperature: 0.0** - ZERO creativity. Pure factual analysis only.
- **Read-only** - Report discrepancies, never suggest creative fixes
- **Exact matching** - Report differences precisely as found
- **No interpretation** - Facts only, no opinions

**WORKFLOW MANDATE:**
- Website = OFFICIAL source of truth
- Local docs (SOPs, standards, principles, beliefs) MUST match website
- Report what internal docs are missing compared to published website

## What This Skill Does

This skill performs comprehensive **read-only validation** of messaging consistency across three critical content sources:

1. **Website Content** (ANY HTML site: WordPress, Hugo, Astro, Next.js, static HTML, etc.) - **OFFICIAL SOURCE OF TRUTH**
2. **GitHub Repositories** (README files, technical documentation)
3. **Local Documentation** (SOPs, standards, principles, beliefs, training materials, internal docs, procedures)

**CRITICAL: This skill NEVER makes changes.** It only generates detailed discrepancy reports for human review.

## When This Skill Activates

Trigger this skill when you mention:
- "Check consistency between website and GitHub"
- "Validate documentation consistency"
- "Audit messaging across platforms"
- "Find mixed messaging"
- "Before I update internal docs, check website first"
- "Ensure website matches GitHub"
- "Generate consistency report"

## How It Works

### Phase 1: Source Discovery

1. **Identify Website Sources**
   - Detect and analyze ANY HTML-based website:
     - Static HTML sites (index.html, about.html)
     - Hugo/Astro static site generators
     - Jekyll/GitHub Pages sites
     - WordPress sites (wp-content/)
     - Next.js/React sites (build/, out/, .next/)
     - Vue/Nuxt sites (dist/, .nuxt/)
     - Gatsby sites (public/)
     - 11ty/Eleventy sites (_site/)
     - Docusaurus sites (build/)
     - Any other HTML-based website structure
   - Find marketing pages, landing pages, product descriptions
   - Extract key messaging: taglines, value propositions, feature lists

2. **Identify GitHub Sources**
   - Locate relevant repositories
   - Find README.md, CONTRIBUTING.md, documentation folders
   - Extract: project descriptions, feature claims, installation instructions

3. **Identify Local Documentation**
   - Find internal docs, training materials, SOPs
   - Locate claudes-docs/, docs/, internal/ directories
   - Extract: procedures, guidelines, technical specifications

### Phase 2: Content Extraction

For each source, extract:
- **Core messaging** (mission statements, value propositions)
- **Feature descriptions** (what the product/service does)
- **Version numbers** (software versions, release dates)
- **URLs and links** (external references, documentation links)
- **Contact information** (emails, support channels)
- **Technical specifications** (requirements, dependencies)
- **Terminology** (consistent use of product names, technical terms)

### Phase 3: Consistency Analysis

Compare content across sources and identify:

**🔴 Critical Discrepancies:**
- Conflicting version numbers
- Different feature lists
- Contradictory technical requirements
- Mismatched contact information
- Broken cross-references

**🟡 Warning-Level Issues:**
- Inconsistent terminology (e.g., "plugin" vs "extension")
- Different phrasing of same concept
- Missing information in one source
- Outdated timestamps or dates

**🟢 Informational Notes:**
- Stylistic differences (acceptable)
- Platform-specific variations (expected)
- Different levels of detail (appropriate)

### Phase 4: Generate Discrepancy Report

Create a comprehensive Markdown report with:

```markdown
# Content Consistency Validation Report
Generated: [timestamp]

## Executive Summary
- Total sources analyzed: X
- Critical discrepancies: X
- Warnings: X
- Informational notes: X

## 1. Website vs GitHub Discrepancies

### 🔴 CRITICAL: Version Mismatch
**Website says:** v1.2.0
**GitHub says:** v1.2.1
**Location:**
- Website: /about/index.html:45
- GitHub: README.md:12
**Recommendation:** Update website to reflect v1.2.1

### 🟡 WARNING: Feature Description Inconsistency
**Website says:** "Supports 236 plugins"
**GitHub says:** "Over 230 plugins available"
**Impact:** Potential customer confusion
**Recommendation:** Standardize on exact number

## 2. Website vs Local Docs Discrepancies

### 🔴 CRITICAL: Contact Email Mismatch
**Website says:** support@example.com
**Local docs say:** help@example.com
**Training materials:** Support email is support@example.com
**Recommendation:** Update local docs to support@example.com

## 3. GitHub vs Local Docs Discrepancies

### 🟡 WARNING: Installation Instructions Differ
**GitHub:** "Run npm install"
**Local docs:** "Use pnpm install"
**Impact:** Training may teach wrong commands
**Recommendation:** Synchronize to pnpm install

## 4. Terminology Consistency Issues

| Term Used | Website | GitHub | Local Docs | Recommendation |
|-----------|---------|--------|------------|----------------|
| Plugin/Extension | Plugin | Extension | Plugin | Standardize on "Plugin" |
| Marketplace/Repository | Marketplace | Repository | Marketplace | Standardize on "Marketplace" |

## 5. Action Items (Priority Order)

1. 🔴 Update website version to v1.2.1
2. 🔴 Fix contact email in local docs
3. 🟡 Standardize plugin count messaging
4. 🟡 Align installation instructions
5. 🟢 Standardize terminology usage
```

## Validation Workflow Example

**User:** "Before I update my internal training materials, check if my website matches GitHub"

**Skill Actions:**
1. Scans website for core messaging, features, version
2. Scans GitHub README, docs for same information
3. Extracts current training materials content
4. Compares all three sources
5. Generates detailed discrepancy report
6. Highlights critical issues that must be fixed first
7. Provides specific file locations and line numbers

**Output:** Comprehensive report showing exactly what's inconsistent and where to fix it

## Best Practices

### Source Priority (Use This When Conflicts Exist)

**Trust Priority Order:**
1. **Website** - Public-facing, most authoritative
2. **GitHub** - Developer-facing, technical accuracy
3. **Local Docs** - Internal-use, lowest priority for public messaging

**Update Flow:**
Website → GitHub → Local Docs

### When to Run Validation

✅ **Run validation BEFORE:**
- Updating internal documentation
- Creating training materials
- Writing new marketing content
- Publishing blog posts
- Releasing new versions

✅ **Run validation AFTER:**
- Website updates
- GitHub README changes
- Major feature releases
- Rebranding efforts

### What This Skill Does NOT Do

❌ Does NOT automatically fix issues
❌ Does NOT modify any files
❌ Does NOT make content decisions
❌ Does NOT prioritize which version is "correct"
✅ ONLY generates read-only reports for human review

## Integration with Your Workflow

### Scenario: Pre-Update Validation

**You:** "I need to update our internal SOPs. First, validate consistency with the website."

**Skill Response:**
1. Reads current website content
2. Reads current GitHub documentation
3. Reads existing internal SOPs
4. Generates comparison report
5. Shows you exactly what needs updating in SOPs
6. Identifies messaging that website uses but SOPs don't

**Result:** You update SOPs with confidence, knowing they match public messaging

### Scenario: Post-Website Update

**You:** "I just updated the website pricing page. Check if GitHub and docs are now inconsistent."

**Skill Response:**
1. Reads NEW website pricing information
2. Compares to GitHub repository pricing docs
3. Compares to internal sales training materials
4. Flags any discrepancies created by website update
5. Provides checklist of what to update next

**Result:** Prevents mixed messaging cascade

## Technical Implementation

### Read-Only Tools Used

- `Read` - Reads local files (website, docs, SOPs)
- `Glob` - Finds relevant files by pattern
- `Grep` - Searches for specific terms across files
- `WebFetch` - Reads deployed website pages (if needed)
- `Bash` (read-only) - Uses `cat`, `grep`, `find` for analysis

### NO Write Operations

This skill NEVER uses:
- ❌ `Write` tool
- ❌ `Edit` tool
- ❌ `git commit` commands
- ❌ File modification operations

### Output Format

- Markdown report saved to `consistency-reports/YYYY-MM-DD-HH-MM-SS.md`
- Terminal-friendly summary
- Export to JSON for automation (optional)

## Example Use Cases

### Use Case 1: Version Consistency Check

**Trigger:** "Check if all docs mention the same version number"

**Result:**
```
Version Analysis Report
Website: v1.2.1 (5 mentions)
GitHub: v1.2.1 (3 mentions), v1.2.0 (2 mentions) ⚠️
Local Docs: v1.2.0 (8 mentions) 🔴

Action: Update Local Docs to v1.2.1
```

### Use Case 2: Feature Claim Validation

**Trigger:** "Validate that all platforms claim the same features"

**Result:**
```
Feature Consistency Analysis
"236 plugins": Website ✅, GitHub ✅, Docs ❌ (says "230+")
"Agent Skills": Website ✅, GitHub ✅, Docs ✅
"MCP Support": Website ✅, GitHub ✅, Docs ⚠️ (unclear mention)

Action: Update Docs to specify "236 plugins" and clarify MCP support
```

### Use Case 3: Pre-Training Update

**Trigger:** "Before I update training materials, what's changed on the website?"

**Result:**
```
Website Changes Since Last Training Update (Oct 15)
- New feature added: "Skill Enhancers" (not in training)
- Pricing updated: $39/mo → $49/mo (not in training)
- Contact form URL changed (broken link in training)

Suggested Training Updates:
1. Add Skill Enhancers section
2. Update pricing screenshots
3. Fix contact form URL
```

## Integration Points

Works seamlessly with:
- **All HTML-based websites**: Static HTML, Hugo, Astro, Jekyll, WordPress, Next.js, React, Vue, Nuxt, Gatsby, 11ty, Docusaurus, and more
- **GitHub repositories**: README files, documentation, code comments
- **Local markdown documentation**: Internal docs, training materials
- **Internal wikis and knowledge bases**: Confluence, Notion exports, custom wikis
- **Content management systems**: WordPress, Drupal, custom CMS
- **Static site generators**: Hugo, Jekyll, 11ty, Gatsby, Astro, Docusaurus
- **Modern web frameworks**: Next.js, Nuxt, SvelteKit build outputs

## Report Storage

Reports saved to:
```
consistency-reports/
├── 2025-10-23-10-30-45-full-audit.md
├── 2025-10-22-15-20-12-website-github.md
└── 2025-10-20-09-15-33-docs-sync.md
```

## Expected Activation Patterns

**Natural Language Triggers:**
- "Check consistency"
- "Validate documentation"
- "Audit messaging"
- "Find discrepancies"
- "Compare website to GitHub"
- "Before I update X, check Y"
- "What's out of sync?"

**Context-Aware Activation:**
- When user is about to update documentation
- When user asks about version consistency
- When user mentions "mixed messaging"
- When user is preparing training materials
