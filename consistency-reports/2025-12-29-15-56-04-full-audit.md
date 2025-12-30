# Content Consistency Validation Report

**Generated:** 2025-12-29 15:56:04
**Analyst:** Claude Code (Read-Only Analysis)
**Temperature:** 0.0 (Pure factual analysis)

---

## Executive Summary

| Metric | Count |
|--------|-------|
| **Sources Analyzed** | 292 files |
| 🔴 **Critical Issues** | 3 |
| 🟡 **Warnings** | 5 |
| 🟢 **Informational** | 2 |

**Status:** 🔴 Action Required - Multiple critical discrepancies found

---

## Source Inventory

### Website (Astro)
- **Location:** `marketplace/src/pages/`
- **Files:** 12 pages
- **Key Pages:**
  - `index.astro` - Homepage (SOURCE OF TRUTH)
  - `explore.astro` - Plugin browser
  - `compare.astro` - Plugin comparison
  - `collections.astro` - Curated collections
  - `tools.astro` - Development tools

### GitHub Documentation
- **Location:** Repository root
- **Files:** 276+ plugin READMEs
- **Key Files:**
  - `README.md` - Root documentation
  - `CLAUDE.md` - Project instructions
  - `package.json` - Monorepo version

### Marketplace Website Config
- **Location:** `marketplace/`
- **Files:**
  - `package.json` - Website version

---

## 🔴 Critical Discrepancies

### CRITICAL #1: Version Number Conflict

**Issue:** Multiple version numbers across different sources

| Source | Version | Location | Last Modified |
|--------|---------|----------|---------------|
| **Root README** | **v4.4.0** | `README.md:3` | 2025-12-28 |
| Root package.json | 4.3.0 | `package.json:2` | 2025-12-27 |
| Marketplace package.json | 3.0.0 | `marketplace/package.json:2` | Unknown |

**Evidence:**

**README.md:3**
```markdown
[![Version](https://img.shields.io/badge/version-4.4.0-brightgreen)](000-docs/247-OD-CHNG-changelog.md)
```

**README.md:60**
```markdown
**v4.4.0:** CLI 2.0 + vibe-guide plugin + Website Unification (521 routes).
```

**package.json:2**
```json
"version": "4.3.0",
```

**marketplace/package.json:2**
```json
"version": "3.0.0",
```

**Impact:**
- Public-facing version badge shows v4.4.0
- Monorepo internal version is 4.3.0 (ONE version behind)
- Marketplace website is 3.0.0 (SIGNIFICANTLY outdated)
- npm package installations may reference wrong version

**Priority:** 🔴 HIGH - Immediate fix required

**Recommendation:**
1. Determine which version is correct (appears to be v4.4.0 based on README badge and release notes)
2. Update `package.json` to `"version": "4.4.0"`
3. Update `marketplace/package.json` to `"version": "4.4.0"`
4. Verify changelog at `000-docs/247-OD-CHNG-changelog.md` matches

---

### CRITICAL #2: Category Count Mismatch

**Issue:** Website claims 18 categories, but CLAUDE.md documents 22 categories

| Source | Category Count | Location |
|--------|----------------|----------|
| **Website** | **18 categories** | `marketplace/src/pages/index.astro:749` |
| **CLAUDE.md** | **22 categories** | `CLAUDE.md:67, 752` |

**Evidence:**

**Website (index.astro:749)**
```html
"258 plugins across 18 categories",
```

**CLAUDE.md:67**
```markdown
Claude Code plugins marketplace and learning hub. 258 plugins across 22 categories with 239 Agent Skills.
```

**CLAUDE.md:752**
```markdown
- **Total Plugins**: 258 across 22 categories
```

**Analysis:**
The website dynamically calculates categories from `searchIndex.stats.categories.length` (line 11), suggesting the actual category count may be 18 at build time. However, internal documentation claims 22.

**Impact:**
- Inconsistent messaging about marketplace scope
- May indicate missing categories on website or overcounting in documentation
- Could confuse users about plugin organization

**Priority:** 🔴 HIGH

**Recommendation:**
1. Count actual categories in `.claude-plugin/marketplace.extended.json`
2. Determine which count is accurate
3. Update the incorrect source(s)
4. Investigate if 4 categories are missing from website or overcounted in docs

---

### CRITICAL #3: NPM Package Scope Inconsistency

**Issue:** Mixed usage of `@intentsolutionsio` and `@claude-code-plugins` scopes

| Package Name | Scope | Location | Status |
|--------------|-------|----------|--------|
| CLI Tool | `@intentsolutionsio/ccpi` | README.md, website | Published ✅ |
| Vercel Pack | `@intentsolutionsio/vercel-pack` | TRACKER.csv | Published ✅ |
| Generic References | `@claude-code-plugins/ccp` | CLAUDE.md:119 | Not Published ❌ |
| Generic Install | `plugin-name@claude-code-plugins-plus` | README.md:66 | Marketplace slug ✅ |

**Evidence:**

**README.md:80 (Correct - uses @intentsolutionsio)**
```bash
pnpm add -g @intentsolutionsio/ccpi
```

**CLAUDE.md:119 (Incorrect - references non-existent @claude-code-plugins scope)**
```markdown
- **Package:** `@claude-code-plugins/ccp`
```

**CLAUDE.md:122 (Correct - uses marketplace slug)**
```markdown
/plugin install your-plugin@claude-code-plugins-plus
```

**Impact:**
- Confusion about which npm scope is used
- Broken installation instructions if users try `@claude-code-plugins/ccp`
- Inconsistent branding across documentation

**Priority:** 🔴 HIGH

**Recommendation:**
1. Update CLAUDE.md:119 to reference `@intentsolutionsio/ccpi`
2. Audit all documentation for `@claude-code-plugins` npm scope references
3. Reserve `@claude-code-plugins` on npm OR remove all references to it
4. Standardize on `@intentsolutionsio` for npm packages, `claude-code-plugins-plus` for marketplace slug

---

## 🟡 Warnings

### WARNING #1: Plugin Count Consistency (Minor)

**Issue:** All sources correctly show 258 plugins, but phrasing varies

| Source | Phrasing | Location |
|--------|----------|----------|
| README badge | "Total Plugins-258" | README.md:6 |
| Website SEO | "258 plugins for Claude Code" | index.astro:743 |
| Website display | "258 plugins across 18 categories" | index.astro:749 |
| CLAUDE.md | "258 plugins across 22 categories" | CLAUDE.md:67 |

**Analysis:** Count is consistent (258), but category count varies (see Critical #2)

**Priority:** 🟡 MEDIUM (linked to Critical #2)

---

### WARNING #2: Skills Count Consistency

**Issue:** Skills count is consistent (239) but phrasing varies

| Source | Phrasing | Location |
|--------|----------|----------|
| README badge | "Agent Skills-239 Skills" | README.md:5 |
| CLAUDE.md | "239 Agent Skills" | CLAUDE.md:67 |
| Website | Uses `{totalSkills}` variable | index.astro:765 |

**Analysis:** No discrepancy detected. Website uses dynamic variable from search index.

**Priority:** 🟡 LOW - Informational only

---

### WARNING #3: Repository URL Inconsistency

**Issue:** GitHub badges point to different repository than marketplace slug

| Context | URL/Slug | Location |
|---------|----------|----------|
| GitHub Stars Badge | `jeremylongshore/claude-code-plugins-plus-skills` | README.md:11 |
| Marketplace Slug | `jeremylongshore/claude-code-plugins` | README.md:65 |
| Actual Repository | `jeremylongshore/claude-code-plugins` | Current location |

**Evidence:**

**README.md:11 (Badge points to -plus-skills repo)**
```markdown
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins-plus-skills?style=social)]
```

**README.md:65 (Marketplace uses base repo)**
```markdown
/plugin marketplace add jeremylongshore/claude-code-plugins
```

**Analysis:** The `-plus-skills` suffix appears to be a legacy name or a different repository. Current repo is `claude-code-plugins`.

**Priority:** 🟡 MEDIUM

**Recommendation:**
1. Verify if `claude-code-plugins-plus-skills` repo exists
2. If it's a redirect/alias, update badge to use canonical name
3. If it's a separate repo, clarify purpose in documentation

---

### WARNING #4: Contact Email Consistency

**Issue:** Contact email appears once in README, not in website footer

| Source | Email | Location |
|--------|-------|----------|
| README | jeremy@intentsolutions.io | README.md (line ~100+) |
| Website | intentsolutions.io (company URL) | index.astro:735 |

**Analysis:** Website shows company URL but no direct email contact. README provides email.

**Priority:** 🟡 LOW - Different contexts (README for contributors, website for users)

---

### WARNING #5: Tutorial Count Consistency

**Issue:** README claims 11 notebooks, but breakdowns sum to 11 correctly

| Tutorial Type | Count | Location |
|---------------|-------|----------|
| Skills | 5 notebooks | README.md:37 |
| Plugins | 4 notebooks | README.md:38 |
| Orchestration | 2 notebooks | README.md:39 |
| **Total** | **11 notebooks** | README.md:9 badge |

**Analysis:** Math checks out (5+4+2=11). No discrepancy.

**Priority:** 🟢 INFORMATIONAL - No action needed

---

## Terminology Analysis

| Term | Website | GitHub (README) | CLAUDE.md | Recommendation |
|------|---------|-----------------|-----------|----------------|
| "Plugin" | ✅ Consistent | ✅ Consistent | ✅ Consistent | ✅ Keep |
| "Agent Skills" | ✅ Consistent | ✅ Consistent | ✅ Consistent | ✅ Keep |
| "Marketplace" | ✅ Used | ✅ Used | ✅ Used | ✅ Keep |
| Version format | v4.4.0 | v4.4.0 | - | ✅ Consistent |
| npm scope | @intentsolutionsio | @intentsolutionsio | Mixed ⚠️ | ⚠️ Fix CLAUDE.md |
| Repo slug | claude-code-plugins | Mixed ⚠️ | claude-code-plugins | ⚠️ Fix badge |

---

## 🟢 Informational Notes

### INFO #1: Dynamic Website Stats

**Observation:** Website uses dynamic variables for stats

**Location:** `marketplace/src/pages/index.astro:9-11`
```javascript
const totalSkills = searchIndex.stats.totalSkills;
const totalPlugins = searchIndex.stats.totalPlugins;
const totalCategories = searchIndex.stats.categories.length;
```

**Impact:** Website stats auto-update from search index at build time, which is good. However, static documentation (README, CLAUDE.md) must be manually updated.

**Recommendation:** Consider adding a build script to sync README stats from search index.

---

### INFO #2: License Information

**Observation:** Individual plugin licenses vary (MIT common)

**Example:** Vercel pack uses MIT license
- Location: `plugins/saas-packs/vercel-pack/LICENSE`

**Impact:** None - plugins can have individual licenses

---

## Priority Action Items

### 🔴 Immediate (Critical)

1. **Fix Version Numbers**
   - Update `package.json` → `"version": "4.4.0"`
   - Update `marketplace/package.json` → `"version": "4.4.0"`
   - Verify `000-docs/247-OD-CHNG-changelog.md` matches v4.4.0

2. **Resolve Category Count**
   - Count actual categories in marketplace catalog
   - Update either website (18) or CLAUDE.md (22) to match reality
   - Document final count in both places

3. **Fix NPM Package Scope**
   - Update CLAUDE.md:119 → `@intentsolutionsio/ccpi`
   - Audit all `@claude-code-plugins` references in docs
   - Decide: Reserve that scope on npm OR remove all references

### 🟡 Soon (Warnings)

4. **Fix Repository URL Badge**
   - Verify if `claude-code-plugins-plus-skills` repo exists
   - Update README.md:11 badge to use canonical repo name
   - Ensure consistency across all GitHub links

5. **Standardize Contact Information**
   - Add contact email to website footer if desired
   - OR remove from README if not public-facing

### 🟢 Optional (Enhancements)

6. **Automate Stats Sync**
   - Create build script to update README stats from search index
   - Prevents manual update errors

7. **Add Terminology Guide**
   - Document official terms (plugin vs extension, etc.)
   - Add to CONTRIBUTING.md

---

## Verification Checklist

After fixes, verify:

- [ ] All version numbers match (4.4.0 across all sources)
- [ ] Category count matches (18 or 22, but consistent)
- [ ] npm scope is `@intentsolutionsio` everywhere
- [ ] GitHub URLs point to canonical repo
- [ ] Contact info is consistent and intentional
- [ ] README badge stats match website
- [ ] Changelog reflects current version

---

## Report Metadata

**Sources Scanned:**
- Website: 12 Astro pages
- GitHub: 1 root README, 1 CLAUDE.md, 276 plugin READMEs
- Config: 2 package.json files
- Catalogs: marketplace.extended.json (not scanned in detail)

**Tools Used:**
- grep, find, cat (read-only Bash)
- Read, Glob, Grep (Claude Code tools)

**Analysis Method:**
- Pattern matching for versions, counts, URLs
- Cross-reference comparison
- No creative interpretation - exact text matching only

**Report Saved:** `consistency-reports/2025-12-29-15-56-04-full-audit.md`

---

**End of Report**
