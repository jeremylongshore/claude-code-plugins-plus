# Changelog - Jeremy Plugin Tool

All notable changes to the Jeremy Plugin Tool will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [2.0.0] - 2025-12-22

### 🎉 Major Transformation: skills-powerkit → jeremy-plugin-tool

**Breaking Changes:**
- Renamed plugin from `skills-powerkit` to `jeremy-plugin-tool`
- Removed Marketplace Manager skill (5 skills → 4 skills)
- Changed focus from marketplace management to production-grade plugin creation

### ✨ Added
- **Nixtla-Grade Validator** (`validate_plugin_nixtla.py`) - 805-line production validator
  - Enforces "Use when..." and "Trigger with..." phrases in descriptions
  - Forbids unscoped Bash permissions (requires `Bash(git:*)` patterns)
  - Validates required sections: Overview, Prerequisites, Instructions, Output, Error Handling, Examples, Resources
  - Enforces 500-line body limit with progressive disclosure
  - Validates step-by-step instructions (numbered lists required)
  - Checks token budgets (12K warning, 15K error)
  - Third-person voice enforcement (no "I can" or "You should")
  - Kebab-case name validation
  - Semver version validation
  - Section content validation (non-empty, minimum character counts)

- **Interactive /create-plugin Command** - Guided plugin creation workflow
  - AskUserQuestion integration for plugin type selection
  - 4 plugin types: Commands Only, Agent Only, Skills Only, Full Plugin
  - Purpose description prompting
  - Category selection (12 categories)
  - Automatic nixtla-compliant template generation
  - Built-in validation after creation
  - Marketplace integration

### 🔄 Changed
- **Plugin Creator** - Now generates nixtla-compliant SKILL.md templates
- **Plugin Validator** - Integrated nixtla v2.0 validation logic
- **Plugin Auditor** - Updated to check nixtla quality standards
- **Version Bumper** - Streamlined for 4-skill architecture

### ❌ Removed
- **Marketplace Manager skill** - Focus shifted to plugin quality over marketplace operations
- All marketplace sync operations (handled separately)

### 📊 Quality Improvements
- **Validation Compliance:** 0% → 100% target (nixtla standards)
- **Required Field Coverage:** Basic → Enterprise (Anthropic + Intent Solutions 6767-c)
- **Security:** Unscoped Bash allowed → Forbidden (scoped patterns required)
- **Documentation:** Minimal sections → 8 required sections with content validation
- **Voice Consistency:** Mixed → Third-person only
- **Token Management:** No tracking → Lee Han Chung budget enforcement

### 🐛 Fixes
- Fixed skill descriptions to include trigger phrases
- Fixed Bash permissions to use scoped patterns
- Fixed missing required sections in existing skills
- Fixed reserved word usage ("claude" in descriptions)

### 📚 Documentation
- Renamed README title and description
- Updated all skill counts from 5 to 4
- Renumbered skills (Auditor 4→3, Version Bumper 5→4)
- Added nixtla validation documentation
- Added interactive workflow examples

### 🔧 Technical Details
- **Lines of Code Added:** 805 (validator) + 200 (create-plugin command)
- **Files Changed:** 8 files (plugin.json, README.md, marketplace.extended.json, CHANGELOG.md, validator script, command file)
- **Directory Rename:** `plugins/examples/skills-powerkit/` → `plugins/examples/jeremy-plugin-tool/`
- **Breaking Change Reason:** Complete architectural shift from marketplace management to production-grade plugin creation

### Migration Guide

**For existing skills-powerkit users:**

1. **Uninstall old plugin:**
   ```bash
   /plugin uninstall skills-powerkit@claude-code-plugins-plus
   ```

2. **Install jeremy-plugin-tool:**
   ```bash
   /plugin install jeremy-plugin-tool@claude-code-plugins-plus
   ```

3. **What changed:**
   - Marketplace management commands removed (use separate tools)
   - All 4 skills now enforce nixtla quality standards
   - New interactive /create-plugin workflow available
   - Existing skills work the same but with stricter validation

4. **Update your plugins:**
   - Run nixtla validator on existing plugins
   - Fix any validation errors (see validator output for specifics)
   - Common fixes: Add "Use when/Trigger with" phrases, scope Bash permissions, add required sections

---

## [1.0.0] - 2024-10-16

### Initial Release (as skills-powerkit)
- 5 repository-specific Agent Skills
- Plugin Creator, Validator, Marketplace Manager, Auditor, Version Bumper
- Optimized for claude-code-plugins workflow
- Auto-invoked based on conversation context

---

**Version 2.0.0 represents a complete transformation into a production-grade plugin creation tool with enterprise-quality standards.**
