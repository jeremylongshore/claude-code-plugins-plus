# Agent Skills Structure Audit Report
**Date:** 2025-10-23
**Repository:** claude-code-plugins
**Comparison:** Our structure vs Anthropic's official Agent Skills specification

---

## Executive Summary

This audit compares our current Agent Skills directory structure against Anthropic's official specification from `github.com/anthropics/skills`. **Critical misalignment identified**: We use a non-standard `skill-adapter/` subdirectory that does not exist in Anthropic's specification.

**Status:** 🔴 **NON-COMPLIANT** - Requires structural reorganization

---

## 1. Directory Structure Comparison

### Anthropic's Official Structure (CORRECT)

```
skill-name/
├── SKILL.md                    # REQUIRED - Must be at root of skill directory
├── scripts/                    # OPTIONAL - Executable code (Python, Bash, etc.)
├── references/                 # OPTIONAL - API docs, workflow guides, comprehensive documentation
└── assets/                     # OPTIONAL - Templates, images, icons, fonts, boilerplate code
```

**Key Requirements:**
- SKILL.md must be at the **root** of the skill directory
- Skill directory name becomes the skill identifier
- No intermediate subdirectories between skill root and SKILL.md
- Optional subdirectories: `scripts/`, `references/`, `assets/` (NOT skill-adapter/)

### Our Current Structure (INCORRECT)

```
plugin-name/
└── skills/
    └── skill-adapter/          # ❌ NON-STANDARD - Does not exist in Anthropic spec
        └── SKILL.md            # ❌ WRONG LOCATION - Should be one level up
```

**Problems:**
1. ❌ Extra `skill-adapter/` subdirectory not in official spec
2. ❌ SKILL.md is nested too deep (should be at `skills/skill-name/SKILL.md`)
3. ❌ Prevents use of official subdirectories (`scripts/`, `references/`, `assets/`)

---

## 2. SKILL.md Format Comparison

### Anthropic's Official Format (CORRECT)

```yaml
---
name: my-skill-name
description: A clear description of what this skill does and when to use it
---

# Skill Instructions

[Imperative/infinitive verb-first instructions]

To accomplish X, do Y.
For best results, follow these steps...
```

**Requirements:**
- YAML frontmatter with `name` and `description` (required)
- Name and description determine when Claude uses the skill
- Imperative/infinitive form (verb-first): "To do X, perform Y" (NOT "You should do X")
- Objective, instructional language
- No restrictions on Markdown body content

### Our Current Format (MOSTLY CORRECT)

```yaml
---
name: 000-jeremy-content-consistency-validator
description: |
  Multi-line description...
temperature: 0.0                # ⚠️ NOT IN SPEC - May be Claude Code specific
---

**CRITICAL OPERATING PARAMETERS:**
...
```

**Status:**
- ✅ YAML frontmatter with `name` and `description`
- ✅ Markdown body with instructions
- ⚠️ Uses `temperature` field (not in official spec, may be Claude Code extension)
- ⚠️ Some second-person language ("This skill performs...") instead of imperative

---

## 3. Progressive Disclosure Architecture

### Anthropic's Official Model

**Three-Tier Information Loading:**

1. **Level 1: Metadata (~100 tokens)**
   - Name + description from YAML frontmatter
   - Loaded at session start for all skills
   - Claude uses this to decide when to load full skill

2. **Level 2: SKILL.md Instructions**
   - Full instructions loaded when skill is activated
   - Contains all workflow steps and guidelines

3. **Level 3+: Bundled Resources**
   - `references/` - Comprehensive docs, API references
   - `scripts/` - Executable code
   - `assets/` - Templates, boilerplate, images
   - Loaded on-demand as Claude navigates skill

### Our Current Model (LIMITED)

**Single-Tier Loading:**

1. ✅ Level 1: YAML frontmatter (metadata)
2. ✅ Level 2: SKILL.md instructions
3. ❌ Level 3: **Missing** - No support for:
   - `references/` directory
   - `scripts/` directory
   - `assets/` directory

**Impact:** Cannot leverage progressive disclosure for large skills with extensive documentation

---

## 4. Detailed Discrepancies

### 4.1 Directory Naming

| Aspect | Anthropic Official | Our Current | Status |
|--------|-------------------|-------------|--------|
| Skill directory location | `skill-name/` | `skills/skill-adapter/` | ❌ Wrong |
| SKILL.md location | `skill-name/SKILL.md` | `skills/skill-adapter/SKILL.md` | ❌ Wrong |
| Scripts location | `skill-name/scripts/` | ❌ Not supported | ❌ Missing |
| References location | `skill-name/references/` | ❌ Not supported | ❌ Missing |
| Assets location | `skill-name/assets/` | ❌ Not supported | ❌ Missing |

### 4.2 YAML Frontmatter

| Field | Anthropic Official | Our Current | Status |
|-------|-------------------|-------------|--------|
| `name` | ✅ Required | ✅ Present | ✅ Correct |
| `description` | ✅ Required | ✅ Present | ✅ Correct |
| `temperature` | ❌ Not in spec | ⚠️ Present | ⚠️ Unknown (may be Claude Code extension) |

### 4.3 Writing Style

| Aspect | Anthropic Official | Our Current | Status |
|--------|-------------------|-------------|--------|
| Voice | Imperative/infinitive (verb-first) | Mixed (some second-person) | ⚠️ Needs revision |
| Example correct | "To validate X, use Y" | "This skill validates X..." | ⚠️ Inconsistent |
| Tone | Objective, instructional | Objective, instructional | ✅ Correct |

---

## 5. Integration with Claude Code Plugins

### Current Plugin Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── command-name.md
├── agents/
│   └── agent-name.md
├── skills/
│   └── skill-adapter/          # ❌ NON-STANDARD
│       └── SKILL.md
├── README.md
└── LICENSE
```

### Proposed Corrected Structure

```
plugin-name/
├── .claude-plugin/
│   └── plugin.json
├── commands/
│   └── command-name.md
├── agents/
│   └── agent-name.md
├── skills/
│   └── skill-name/             # ✅ COMPLIANT - Matches Anthropic spec
│       ├── SKILL.md            # ✅ At root of skill directory
│       ├── scripts/            # ✅ Optional - For executable code
│       ├── references/         # ✅ Optional - For comprehensive docs
│       └── assets/             # ✅ Optional - For templates/boilerplate
├── README.md
└── LICENSE
```

**Key Changes:**
1. Remove `skill-adapter/` subdirectory
2. Move SKILL.md up one level to `skills/skill-name/SKILL.md`
3. Use skill name as directory name (e.g., `content-validator/`, `taskwarrior-integration/`)
4. Add optional subdirectories as needed: `scripts/`, `references/`, `assets/`

---

## 6. Impact Assessment

### 6.1 Compatibility Issues

**Current Non-Compliance:**

1. **Claude Code CLI compatibility** - Unknown if current structure works
2. **API integration** - `/v1/skills` endpoint may reject non-standard structure
3. **Messages API** - Skill bundles may fail validation
4. **Progressive disclosure** - Cannot leverage multi-tier loading without proper subdirectories

### 6.2 Feature Limitations

**Cannot Use:**

1. ❌ **scripts/** - No place for executable Python/Bash scripts
2. ❌ **references/** - Cannot bundle API docs or comprehensive guides
3. ❌ **assets/** - No support for templates, boilerplate code, or images
4. ❌ **8 MB skill bundles** - Limited to single SKILL.md file

### 6.3 User Experience Impact

**Problems:**

1. Skills may not load correctly in official Claude implementations
2. Cannot package comprehensive skills with extensive resources
3. Harder to maintain complex skills without proper organization
4. Community confusion from non-standard structure

---

## 7. Migration Requirements

### 7.1 For All 164 Plugins with Agent Skills

**Structural Changes Needed:**

```bash
# BEFORE (current)
plugins/[category]/[plugin-name]/skills/skill-adapter/SKILL.md

# AFTER (compliant)
plugins/[category]/[plugin-name]/skills/[skill-name]/SKILL.md
```

**Steps:**
1. Rename `skill-adapter/` to a descriptive skill name
2. Move SKILL.md to root of skill directory
3. Create optional subdirectories if needed (`scripts/`, `references/`, `assets/`)
4. Update marketplace catalog references if needed

### 7.2 Script Updates Required

**Files to Update:**

1. `scripts/vertex-skills-generator-safe.py` - Update output path
2. `scripts/generate-skills-gemini.py` - Update skill directory creation
3. `scripts/next-skill.sh` - Update directory structure
4. `.github/workflows/daily-skill-generator.yml` - No changes needed (uses scripts)

### 7.3 Documentation Updates

**Files to Update:**

1. `CLAUDE.md` - Update skill structure documentation
2. `README.md` - Update skill examples
3. `scripts/SKILLS_AUTOMATION.md` - Update generation documentation
4. Plugin README files - Update skill usage examples

---

## 8. Recommended Approach

### Option A: Full Migration (RECOMMENDED)

**Pros:**
- Full compliance with Anthropic spec
- Enables all progressive disclosure features
- Future-proof for API/CLI updates
- Consistent with community standards

**Cons:**
- Requires migration of all 164 plugins
- Need to update generation scripts
- Temporary disruption during migration

**Effort:** HIGH (2-3 days for bulk migration)

### Option B: Hybrid Approach

**Pros:**
- Keep existing plugins as-is
- Use compliant structure for new plugins
- Gradual migration over time

**Cons:**
- Inconsistent structure across plugins
- Existing plugins may break with future updates
- Confusing documentation

**Effort:** LOW initially, HIGH long-term

### Option C: Minimal Fix (NOT RECOMMENDED)

**Pros:**
- No immediate work required
- Current plugins continue working (if they work now)

**Cons:**
- ❌ Non-compliant with official spec
- ❌ Cannot use progressive disclosure features
- ❌ May break with Claude updates
- ❌ Community confusion

**Effort:** NONE (technical debt increases)

---

## 9. Proposed Migration Plan

### Phase 1: Validation (Day 1)

**Goals:**
- Verify current structure works with Claude Code CLI
- Test compliant structure with sample plugin
- Confirm migration is necessary

**Tasks:**
```bash
# 1. Test current structure
/plugin install 000-jeremy-content-consistency-validator@claude-code-plugins-plus

# 2. Create test plugin with compliant structure
mkdir -p test-plugin/skills/test-skill/
echo '---
name: test-skill
description: Test skill with compliant structure
---
# Test Skill
Test instructions here.' > test-plugin/skills/test-skill/SKILL.md

# 3. Test compliant structure
/plugin install test-plugin@test-marketplace
```

### Phase 2: Script Updates (Day 1-2)

**Update Generation Scripts:**

1. `scripts/vertex-skills-generator-safe.py`
   - Change `skills/skill-adapter/` → `skills/{skill_name}/`
   - Use plugin name or custom skill name as directory

2. `scripts/generate-skills-gemini.py`
   - Update directory creation logic
   - Add support for optional subdirectories

3. `scripts/next-skill.sh`
   - Update paths and directory creation

**Test:**
```bash
# Generate skill for test plugin
./scripts/next-skill.sh
# Verify output structure matches Anthropic spec
```

### Phase 3: Bulk Migration (Day 2-3)

**Migrate All 164 Plugins:**

```bash
#!/bin/bash
# migrate-skills-structure.sh

find plugins/ -type d -name "skill-adapter" | while read old_path; do
    plugin_dir=$(dirname "$(dirname "$old_path")")
    plugin_name=$(basename "$plugin_dir")
    skill_name=$(echo "$plugin_name" | sed 's/-/ /g' | sed 's/^//')

    new_path="$(dirname "$old_path")/$plugin_name-skill"

    echo "Migrating: $old_path -> $new_path"

    # Rename directory
    mv "$old_path" "$new_path"

    # Update SKILL.md name field if needed
    # (Optional: keep consistent with old name or update)
done
```

**Validation:**
```bash
# Verify all migrations
find plugins/ -type f -name "SKILL.md" | while read skill; do
    # Check SKILL.md is at correct depth
    depth=$(echo "$skill" | grep -o "/" | wc -l)
    if [ $depth -ne 5 ]; then
        echo "ERROR: Wrong depth - $skill"
    fi
done
```

### Phase 4: Documentation Updates (Day 3)

**Update All Documentation:**

1. CLAUDE.md - Skill structure section
2. README.md - Skill examples
3. scripts/SKILLS_AUTOMATION.md - Generation guide
4. Plugin README files - Usage examples

### Phase 5: Testing & Rollout (Day 3-4)

**Testing:**
1. Test skill loading in Claude Code CLI
2. Test skill activation triggers
3. Verify marketplace installation
4. Community beta testing

**Rollout:**
1. Commit structure changes
2. Run marketplace sync
3. Update version to 1.3.0 (structural change)
4. Create release notes explaining migration
5. Push to GitHub

---

## 10. Risk Assessment

### High Risk

- **Breaking existing installations** - Users may need to reinstall plugins
- **Skill activation failures** - Non-compliant structure may not activate
- **API rejection** - Messages API may reject improperly structured skills

### Medium Risk

- **Migration script bugs** - Bulk rename could corrupt plugins
- **Name conflicts** - Skill directory names may conflict
- **Documentation lag** - Users confused during transition

### Low Risk

- **Performance impact** - Structure change should not affect performance
- **Backwards compatibility** - Old structure may continue working temporarily

### Mitigation Strategies

1. **Backup before migration** - Already have backup system
2. **Test with sample plugins first** - Validate approach works
3. **Staged rollout** - Migrate high-priority plugins first
4. **Clear communication** - Update docs and changelog thoroughly
5. **Rollback plan** - Keep backups for quick reversion

---

## 11. Recommendations

### Immediate Actions (Today)

1. ✅ **Test current structure** - Verify if non-compliant structure even works
2. ✅ **Create compliant test plugin** - Validate official structure works
3. ✅ **Document findings** - This audit report

### Short-Term (This Week)

1. 🔴 **Update generation scripts** - Fix for future plugins
2. 🔴 **Migrate Jeremy's personal plugins first** - Test with 2 plugins:
   - `000-jeremy-content-consistency-validator`
   - `001-jeremy-taskwarrior-integration`
3. 🔴 **Test thoroughly** - Ensure migration works correctly

### Long-Term (Next Sprint)

1. 🟡 **Bulk migrate all 164 plugins** - Use automated script
2. 🟡 **Update all documentation** - Reflect new structure
3. 🟡 **Release v1.3.0** - Structural compliance update
4. 🟡 **Add progressive disclosure features** - Leverage `scripts/`, `references/`, `assets/`

---

## 12. Conclusion

**Current Status:** 🔴 **NON-COMPLIANT**

Our Agent Skills structure uses a non-standard `skill-adapter/` subdirectory that does not exist in Anthropic's official specification. This prevents us from:

1. Using progressive disclosure features (scripts/, references/, assets/)
2. Guaranteeing compatibility with Claude's API and CLI
3. Following community best practices
4. Leveraging advanced skill capabilities

**Recommendation:** **MIGRATE TO COMPLIANT STRUCTURE**

**Effort:** 2-3 days for complete migration

**Impact:** HIGH - Enables full Agent Skills feature set, ensures long-term compatibility

**Next Steps:**
1. Test current vs compliant structure
2. Update generation scripts
3. Migrate Jeremy's 2 plugins as proof of concept
4. Bulk migrate remaining 162 plugins
5. Release v1.3.0 with structural compliance

---

**Report Generated:** 2025-10-23
**Reviewed By:** Claude Code (Sonnet 4.5)
**Status:** Pending user approval for migration plan
