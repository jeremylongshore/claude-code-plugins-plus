# 001-Jeremy Content Consistency Validator

**Read-only validator that generates comprehensive discrepancy reports comparing messaging consistency across your website, GitHub repositories, and local documentation.**

## What It Does

This plugin helps you maintain consistent messaging by:

1. **Scanning** your website, GitHub, and local docs
2. **Comparing** key messaging elements across all sources
3. **Identifying** discrepancies, conflicts, and inconsistencies
4. **Generating** detailed read-only reports for human review
5. **Recommending** specific fixes with file locations and line numbers

**🔒 100% Read-Only** - This plugin NEVER modifies any files. It only generates reports.

## Your Workflow Problem (Solved)

**Problem:** You keep your website up-to-date first, but internal paperwork lags behind, creating mixed messaging.

**Solution:** This plugin validates that website, GitHub, and docs match BEFORE you update internal paperwork.

## Use Cases

### Use Case 1: Pre-Update Validation
**Before updating internal docs, check what changed on the website:**

```bash
/validate-consistency
```

Or naturally:
> "Before I update training materials, check if website matches GitHub"

**Result:** Report showing exactly what needs updating in your docs to match website.

### Use Case 2: Post-Website Update
**After updating website, check what's now inconsistent:**

> "I just updated the pricing page. Check if GitHub and docs are out of sync."

**Result:** List of files that need updating to match new website content.

### Use Case 3: Version Consistency Audit
**Ensure all platforms mention the same version:**

> "Check if all documentation mentions v1.2.1"

**Result:**
```
Version Analysis:
- Website: v1.2.1 ✅
- GitHub: v1.2.0 🔴 (needs update)
- Docs: v1.2.0 🔴 (needs update)
```

## Installation

```bash
# Add marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install plugin
/plugin install 001-jeremy-content-consistency-validator@claude-code-plugins-plus
```

## How to Use

### Method 1: Agent Skill (Automatic)

Just mention your need naturally:

- "Check consistency between website and GitHub"
- "Validate documentation before I update training materials"
- "Find mixed messaging across platforms"
- "Ensure website matches local docs"

**The Agent Skill activates automatically** and generates a report.

### Method 2: Manual Command

Run explicit validation:

```bash
/validate-consistency
```

## What Gets Validated

### 1. Website Content (ALL HTML-Based Sites)
**Automatically detects and validates:**
- Static HTML sites (index.html, about.html)
- Hugo/Astro static site generators
- Jekyll/GitHub Pages sites
- WordPress sites
- Next.js/React applications
- Vue/Nuxt applications
- Gatsby sites
- 11ty/Eleventy sites
- Docusaurus sites
- Any other HTML-based website

**Content validated:**
- Marketing pages
- Product descriptions
- Feature lists
- Pricing information
- Contact details
- Version numbers

### 2. GitHub Repositories
- README.md
- CONTRIBUTING.md
- Documentation files
- Code comments
- Release notes

### 3. Local Documentation
- Internal SOPs
- Training materials
- Technical specifications
- Process documentation
- Knowledge base articles

## Report Format

### Executive Summary
```markdown
# Content Consistency Validation Report
Generated: 2025-10-23 10:45:23

## Summary
- Sources analyzed: 47 files
- 🔴 Critical issues: 3
- 🟡 Warnings: 12
- 🟢 Informational: 8
```

### Critical Discrepancies 🔴
Issues that MUST be fixed:

```markdown
### 🔴 CRITICAL: Version Mismatch

**Website:** v1.2.1 (index.html:45)
**GitHub:** v1.2.0 (README.md:12)
**Docs:** v1.2.0 (training-guide.md:156)

**Impact:** Public-facing version inconsistency

**Recommendation:**
1. Update GitHub README.md line 12 to v1.2.1
2. Update training-guide.md line 156 to v1.2.1

**Priority:** HIGH
```

### Warnings 🟡
Issues that SHOULD be reviewed:

```markdown
### 🟡 WARNING: Feature Count Inconsistency

**Website:** "236 plugins"
**GitHub:** "Over 230 plugins"
**Docs:** "230+ plugins"

**Recommendation:** Standardize on "236 plugins" everywhere
```

### Action Items
Prioritized fix list:

```markdown
## Priority Action Items

1. 🔴 Update GitHub version to v1.2.1
2. 🔴 Fix contact email in local docs
3. 🟡 Standardize plugin count messaging
4. 🟡 Align installation instructions
5. 🟢 Standardize terminology ("plugin" vs "extension")
```

## Report Location

Reports are saved to:
```
consistency-reports/YYYY-MM-DD-HH-MM-SS-full-audit.md
```

Example:
```
consistency-reports/
├── 2025-10-23-10-45-23-full-audit.md
├── 2025-10-22-15-20-12-website-github.md
└── 2025-10-20-09-15-33-docs-sync.md
```

## What It Checks

### Version Numbers
- Software versions (v1.2.0)
- Release dates
- Copyright years
- API versions

### Feature Claims
- "Supports X plugins"
- "Includes Y features"
- Technical capabilities
- Performance claims

### Contact Information
- Email addresses
- Support URLs
- Social media links
- Physical addresses

### Technical Specifications
- System requirements
- Dependencies
- Installation steps
- Configuration options

### Terminology
- Product names
- Technical terms
- Acronyms
- Brand terminology

## Source Priority

When conflicts exist, trust this order:

1. **Website** (public-facing, most authoritative)
2. **GitHub** (developer-facing, technical accuracy)
3. **Local Docs** (internal-use, lowest priority)

**Recommended update flow:** Website → GitHub → Local Docs

## Example Scenarios

### Scenario 1: Pre-Training Update

**You:** "Before I update our sales training, check if website pricing changed."

**Plugin Actions:**
1. Reads current website pricing page
2. Reads existing training materials
3. Compares pricing information
4. Shows exactly what changed
5. Provides line-by-line update recommendations

**Result:** You update training with confidence, knowing it matches current website.

### Scenario 2: Post-Website Redesign

**You:** "I redesigned the website. What's now inconsistent with GitHub?"

**Plugin Actions:**
1. Reads new website content
2. Reads GitHub documentation
3. Identifies content that diverged
4. Lists specific files needing updates

**Result:** Checklist of GitHub files to update.

### Scenario 3: Version Release

**You:** "Just released v2.0.0. Validate consistency everywhere."

**Plugin Actions:**
1. Searches all sources for version mentions
2. Identifies sources still showing old version
3. Provides update checklist

**Result:** Complete list of files to update with line numbers.

## Read-Only Guarantee

This plugin uses ONLY read-only operations:

✅ **Allowed:**
- `Read` - Read local files
- `Glob` - Find files by pattern
- `Grep` - Search file contents
- `Bash` (read-only): `cat`, `grep`, `find`, `wc`

❌ **Never Used:**
- `Write` - NO file modifications
- `Edit` - NO file edits
- `git commit` - NO version control changes
- Any destructive operations

**You maintain complete control.** The plugin only reports - you decide what to fix.

## Technical Details

### Sources Discovered Automatically

**Website (ALL HTML-based sites):**
- **Static HTML:** `**/*.html`
- **Hugo:** `content/**/*.md`, `themes/**/*.html`, `layouts/**/*.html`
- **Astro:** `src/pages/**/*.{astro,md}`
- **Jekyll:** `_posts/**/*.md`, `_pages/**/*.md`, `_layouts/**/*.html`
- **WordPress:** `wp-content/themes/**/*.php`, `wp-content/**/*.html`
- **Next.js/React:** `pages/**/*.{tsx,jsx}`, `app/**/*.{tsx,jsx}`, `out/**/*.html`, `build/**/*.html`
- **Vue/Nuxt:** `pages/**/*.vue`, `components/**/*.vue`, `dist/**/*.html`
- **Gatsby:** `src/pages/**/*.{js,jsx}`, `public/**/*.html`
- **11ty/Eleventy:** `**/*.{md,njk}`, `_site/**/*.html`
- **Docusaurus:** `docs/**/*.{md,mdx}`, `blog/**/*.{md,mdx}`, `build/**/*.html`

**GitHub:**
- `README.md`
- `CONTRIBUTING.md`
- `docs/**/*.md`

**Local Docs:**
- `claudes-docs/**/*.md`
- `000-docs/**/*.md`
- `docs/**/*.md`

### Comparison Algorithms

1. **Exact Match:** Finds identical strings across sources
2. **Fuzzy Match:** Detects similar phrasing (90%+ similarity)
3. **Semantic Match:** Identifies same concept, different words
4. **Pattern Match:** Regex-based detection (versions, emails, URLs)

### Performance

- Scans 100+ files in < 10 seconds
- Generates comprehensive report in < 30 seconds
- No external API calls required
- 100% local processing

## Troubleshooting

### "No sources found"
**Solution:** Ensure you're in project root directory with website/docs/GitHub files.

### "Report too large"
**Solution:** Use focused validation:
> "Only check version consistency"

### "Can't find website"
**Solution:** Specify location:
> "Check consistency, website is in ~/startaitools/"

## Contributing

Found an issue or have a suggestion? Open an issue at:
https://github.com/jeremylongshore/claude-code-plugins/issues

## License

MIT License - See LICENSE file for details

## Support

- **Documentation:** This README
- **Issues:** GitHub Issues
- **Email:** jeremy@intentsolutions.io

---

**Built by:** Jeremy Longshore
**Version:** 1.0.0
**Category:** Productivity
**Type:** Read-Only Validator

**Perfect for:** Content managers, documentation teams, technical writers, and anyone maintaining consistency across multiple platforms.
