# Agent Skills Structure Visual Comparison

## Anthropic Official Structure ✅

```
skill-name/                          # Skill directory (root)
├── SKILL.md                         # ✅ REQUIRED - At root of skill directory
│   ├── YAML frontmatter             # ✅ name, description
│   └── Markdown instructions        # ✅ Imperative verb-first style
├── scripts/                         # ✅ OPTIONAL - Executable code
│   ├── process.py
│   ├── validate.sh
│   └── helper.js
├── references/                      # ✅ OPTIONAL - Comprehensive documentation
│   ├── api_reference.md
│   ├── workflow_guide.md
│   └── troubleshooting.md
└── assets/                          # ✅ OPTIONAL - Templates, boilerplate, images
    ├── template.json
    ├── boilerplate.py
    └── icon.png
```

**Progressive Disclosure:**
- **Level 1:** Metadata (~100 tokens) - name + description
- **Level 2:** SKILL.md instructions (full workflow)
- **Level 3+:** scripts/, references/, assets/ (loaded on-demand)

---

## Our Current Structure ❌

```
plugin-name/
└── skills/
    └── skill-adapter/               # ❌ NON-STANDARD - Not in Anthropic spec
        └── SKILL.md                 # ❌ WRONG DEPTH - Should be one level up
```

**Problems:**
1. ❌ Extra `skill-adapter/` subdirectory doesn't exist in official spec
2. ❌ SKILL.md is nested too deep (3 levels instead of 2)
3. ❌ Cannot use `scripts/`, `references/`, `assets/` subdirectories
4. ❌ Breaks progressive disclosure architecture

---

## Side-by-Side Comparison

### Anthropic Official (CORRECT)
```
plugins/productivity/my-plugin/
└── skills/
    └── content-validator/           # ✅ Skill name directory
        ├── SKILL.md                 # ✅ At skill root
        ├── scripts/
        │   ├── validate.py
        │   └── report.sh
        ├── references/
        │   └── api_docs.md
        └── assets/
            └── template.json
```

### Our Current (INCORRECT)
```
plugins/productivity/my-plugin/
└── skills/
    └── skill-adapter/               # ❌ Wrong directory name
        └── SKILL.md                 # ❌ Wrong depth
                                     # ❌ No scripts/
                                     # ❌ No references/
                                     # ❌ No assets/
```

---

## Path Depth Analysis

### Correct Path (Anthropic)
```
plugins/                             # Level 0
├── [category]/                      # Level 1
    └── [plugin-name]/               # Level 2
        └── skills/                  # Level 3
            └── [skill-name]/        # Level 4 ✅ SKILL DIRECTORY ROOT
                └── SKILL.md         # Level 5 ✅ CORRECT DEPTH
```

### Our Current Path (WRONG)
```
plugins/                             # Level 0
├── [category]/                      # Level 1
    └── [plugin-name]/               # Level 2
        └── skills/                  # Level 3
            └── skill-adapter/       # Level 4 ❌ EXTRA LEVEL
                └── SKILL.md         # Level 5 ❌ TOO DEEP
```

**Difference:** We have an extra directory level that shouldn't exist

---

## Migration Required

### Before (Current - 164 plugins)
```bash
plugins/productivity/000-jeremy-content-consistency-validator/skills/skill-adapter/SKILL.md
plugins/productivity/001-jeremy-taskwarrior-integration/skills/skill-adapter/SKILL.md
plugins/testing/security-test-scanner/skills/skill-adapter/SKILL.md
# ... 161 more plugins
```

### After (Compliant)
```bash
plugins/productivity/000-jeremy-content-consistency-validator/skills/content-validator/SKILL.md
plugins/productivity/001-jeremy-taskwarrior-integration/skills/taskwarrior/SKILL.md
plugins/testing/security-test-scanner/skills/security-scanner/SKILL.md
# ... 161 more plugins
```

**Changes:**
1. Rename `skill-adapter/` → descriptive skill name
2. SKILL.md stays at same depth (just parent directory renamed)
3. Can now add `scripts/`, `references/`, `assets/` as siblings to SKILL.md

---

## Feature Comparison

| Feature | Anthropic Spec | Our Current | Status |
|---------|---------------|-------------|--------|
| SKILL.md at skill root | ✅ Required | ❌ Nested too deep | ❌ Non-compliant |
| `scripts/` directory | ✅ Supported | ❌ Not supported | ❌ Missing |
| `references/` directory | ✅ Supported | ❌ Not supported | ❌ Missing |
| `assets/` directory | ✅ Supported | ❌ Not supported | ❌ Missing |
| Progressive disclosure | ✅ 3-tier loading | ❌ Single tier only | ❌ Limited |
| 8 MB skill bundles | ✅ Supported | ❌ Cannot leverage | ❌ Restricted |
| API compatibility | ✅ Full support | ⚠️ Unknown/limited | ⚠️ Risk |

---

## Real-World Example: Content Validator Skill

### Current Structure (NON-COMPLIANT)
```
plugins/productivity/000-jeremy-content-consistency-validator/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── validate-consistency.md
├── skills/
│   └── skill-adapter/                    # ❌ Non-standard name
│       └── SKILL.md                      # ❌ Can't add scripts/references/assets
├── README.md
└── LICENSE
```

### Proposed Compliant Structure
```
plugins/productivity/000-jeremy-content-consistency-validator/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── validate-consistency.md
├── skills/
│   └── content-validator/                # ✅ Descriptive skill name
│       ├── SKILL.md                      # ✅ At skill root
│       ├── scripts/                      # ✅ NEW - Validation scripts
│       │   ├── scan_website.py
│       │   ├── scan_github.py
│       │   └── generate_report.sh
│       ├── references/                   # ✅ NEW - Documentation
│       │   ├── html_frameworks.md
│       │   ├── validation_rules.md
│       │   └── sop_examples.md
│       └── assets/                       # ✅ NEW - Templates
│           ├── report_template.md
│           └── consistency_checklist.json
├── README.md
└── LICENSE
```

**Benefits:**
- ✅ Scripts can be executed by Claude directly
- ✅ References loaded on-demand (saves context)
- ✅ Assets available for report generation
- ✅ Full 8 MB bundle capacity for comprehensive documentation

---

## Quick Reference

### ✅ DO (Anthropic Compliant)
```
skills/
└── my-skill/              # Descriptive skill name
    ├── SKILL.md           # At skill root
    ├── scripts/           # Optional: Executable code
    ├── references/        # Optional: Comprehensive docs
    └── assets/            # Optional: Templates/boilerplate
```

### ❌ DON'T (Our Current - Non-compliant)
```
skills/
└── skill-adapter/         # Generic non-standard name
    └── SKILL.md           # Can't add subdirectories
```

---

## Migration Effort

**Affected Files:** 164 plugins with Agent Skills

**Required Changes per Plugin:**
1. Rename `skills/skill-adapter/` → `skills/[descriptive-name]/`
2. SKILL.md location unchanged (just parent directory renamed)
3. Optionally add `scripts/`, `references/`, `assets/` as needed

**Automation:**
```bash
# Bulk rename script
find plugins/ -type d -name "skill-adapter" | while read path; do
    plugin_name=$(basename "$(dirname "$(dirname "$path")")")
    new_name="${plugin_name}-skill"
    mv "$path" "$(dirname "$path")/$new_name"
done
```

**Estimated Time:**
- Script development: 1 hour
- Testing: 2 hours
- Bulk migration: 30 minutes
- Validation: 1 hour
- **Total: ~5 hours** for all 164 plugins

---

## Recommended Next Steps

1. **Immediate:** Test current structure to see if it even works
2. **Phase 1:** Update generation scripts for future plugins
3. **Phase 2:** Migrate Jeremy's 2 personal plugins as proof-of-concept
4. **Phase 3:** Bulk migrate all 164 plugins
5. **Phase 4:** Update documentation and release v1.3.0

---

**Generated:** 2025-10-23
**Status:** Awaiting user approval for migration
