# How It Works

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
