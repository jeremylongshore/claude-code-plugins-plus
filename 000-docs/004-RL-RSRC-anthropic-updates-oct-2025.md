# Anthropic Claude Code Updates Research
**Date:** October 16, 2025
**Research Focus:** Latest plugin updates, Skills feature, and best practices
**Repository:** claude-code-plugins

---

## Executive Summary

Anthropic has made significant updates to Claude Code in October 2025, including:

1. **Claude Code Plugins** - Public beta launched October 9, 2025
2. **Agent Skills** - New feature launched October 16, 2025 (TODAY!)
3. Enhanced best practices for plugin development and team standardization
4. New security considerations with code execution capabilities

**Critical Discovery:** Skills are a NEW, separate feature from Plugins launched just days ago (October 16, 2025). Our repository currently focuses on Plugins but should consider adding Skills support.

---

## 1. Plugin System Updates (October 9, 2025)

### Launch Status
- **Public Beta**: Launched October 9, 2025
- **Ecosystem Growth**: Rapid community adoption with multiple marketplaces emerging
- **Official Support**: Comprehensive documentation at docs.claude.com

### Plugin Structure (Current Best Practices)

```
plugin-name/
├── .claude-plugin/plugin.json    # Required manifest
├── commands/                      # Slash commands (optional)
├── agents/                        # Custom agents (optional)
├── skills/                        # ⚠️ NEW: Agent Skills (optional)
├── hooks/                         # Event handlers (optional)
└── .mcp.json                      # MCP server config (optional)
```

**⚠️ IMPORTANT CHANGE:** Plugins can now include a `skills/` directory for Agent Skills (launched Oct 16, 2025).

### Plugin Manifest Updates

**Required Fields (No changes):**
- `name` - Kebab-case unique identifier
- Located in `.claude-plugin/plugin.json`

**Metadata Fields (Validated):**
```json
{
  "name": "plugin-name",
  "version": "2.1.0",
  "description": "Brief purpose",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://author.com"
  },
  "homepage": "https://plugin-homepage.com",
  "repository": "https://github.com/user/repo",
  "license": "MIT",
  "keywords": ["tag1", "tag2"]
}
```

**Component Path Fields:**
- `commands` - String or array for custom command locations
- `agents` - String or array for agent definitions
- `hooks` - Path to hooks.json or inline config
- `mcpServers` - Path to MCP config or inline config

**Critical Rule:** Custom paths **supplement** default directories, they don't replace them. Default `commands/` and `agents/` directories load automatically.

### Best Practices Updates (2025)

#### 1. CLAUDE.md Project README
**New Recommendation:** Create `CLAUDE.md` at repo root as "project README for agents"

Include:
- Tech stack and versions
- Repository map/structure
- Standard commands (build, test, deploy)
- Test strategy
- Style/lint rules
- Branch/PR etiquette
- "Do not touch" zones
- Security/compliance notes

**Status in Our Repo:** ✅ **IMPLEMENTED** - We have comprehensive CLAUDE.md

#### 2. Workflow Safety
**New Recommendations:**
- Ask Claude to make a plan before coding
- Explicitly tell it not to code until plan is confirmed
- Require small, frequent Git commits and draft PRs
- Never accumulate massive, unreviewable diffs
- Start in read-only mode (Read, Grep)
- Allow writes only after bot understands layout and tests are green

**Status in Our Repo:** ⚠️ **PARTIAL** - Consider adding safety guidelines to plugin templates

#### 3. Checkpoint System
**New Feature:** Claude Code now has automatic checkpoint system
- Saves code state before each change
- Instant rewind via Esc twice or `/rewind` command
- Safety net for rapid iterations

**Status in Our Repo:** N/A - User-facing feature, not plugin development concern

#### 4. Team Standardization
**New Capability:** Repository-level plugin configuration

Via `.claude/settings.json`:
```json
{
  "extraKnownMarketplaces": {
    "marketplace-name": {
      "source": {
        "source": "github",
        "repo": "user/repo"
      }
    }
  },
  "enabledPlugins": {
    "plugin-name@marketplace-name": true
  }
}
```

**Status in Our Repo:** ⚠️ **CONSIDER ADDING** - Could provide example team configuration templates

---

## 2. Agent Skills (MAJOR NEW FEATURE - October 16, 2025)

### What Are Skills?

**Definition:** Skills are modular capabilities that extend Claude's functionality through organized folders containing instructions, scripts, and resources.

**Key Difference from Plugins:**
- **Plugins**: User installs them (distribution mechanism)
- **Skills**: Claude automatically invokes them when relevant (capability mechanism)
- **Relationship**: Plugins can bundle Skills for distribution

### Skills vs Slash Commands

| Feature | Skills | Slash Commands |
|---------|--------|----------------|
| **Invocation** | Model-invoked (Claude decides) | User-invoked (explicitly typed) |
| **Trigger** | Automatic based on context | Manual `/command` |
| **Use Case** | Background capabilities | Explicit workflows |

**Example:**
- Skill: Claude automatically uses "excel-formatter" when you mention spreadsheets
- Command: You type `/format-excel` to explicitly trigger Excel formatting

### Skill Structure

**Required File:** `SKILL.md`

```
skill-name/
├── SKILL.md          # Required: Instructions and frontmatter
├── reference.md      # Optional: Reference documentation
├── examples.md       # Optional: Usage examples
├── scripts/          # Optional: Helper scripts
└── templates/        # Optional: Template files
```

### SKILL.md Format

```yaml
---
name: Skill Name
description: What it does AND when to use it (critical for Claude to recognize)
allowed-tools: Tool1, Tool2, Tool3
---

# Skill Name

## Purpose
[What this skill does]

## Instructions
[Step-by-step guidance for Claude]

## Examples
[Usage scenarios]
```

**Critical Field:** `description` must include:
1. What the skill does (functionality)
2. When to use it (trigger keywords/context)

### Discovery Locations

Skills are automatically discovered from three sources:

1. **Personal Skills:** `~/.claude/skills/` (user-specific)
2. **Project Skills:** `.claude/skills/` (shared via git)
3. **Plugin Skills:** Bundled with installed plugins in `plugins/.../skills/`

### Tool Restrictions

The `allowed-tools` field restricts which tools Claude can use when skill is active:

```yaml
allowed-tools: Read, Grep  # Read-only operations
```

Useful for:
- Security-sensitive workflows
- Read-only analysis tasks
- Preventing accidental writes

### Official Anthropic Skills

Anthropic provides official skills for:
- Creating professional Excel spreadsheets with formulas
- PowerPoint presentations
- Word documents
- Fillable PDFs

**Installation:** Via `anthropics/skills` marketplace

### Security Warning

⚠️ **CRITICAL:** Skills require the Code Execution Tool beta
- Gives Claude access to execute code
- Be mindful about which skills you use
- Stick to trusted sources to keep data safe

---

## 3. Repository Impact Analysis

### Current State of claude-code-plugins Repository

**What We Have:**
- ✅ 226 plugins across 14 categories
- ✅ 221 AI instruction plugins (markdown templates)
- ✅ 5 MCP server plugins (TypeScript/Node.js executables)
- ✅ 4 plugin templates
- ✅ Comprehensive marketplace system
- ✅ CLAUDE.md (updated today)

**What We're Missing:**
- ❌ Skills support (new feature launched Oct 16, 2025)
- ❌ Skill templates
- ❌ Skills directory in plugin templates
- ❌ Skills documentation
- ❌ Example skills
- ❌ Skills vs Plugins comparison in docs

### Skills Integration Opportunities

#### 1. Add Skills Support to Plugin Templates

**Update Required Files:**
- `templates/minimal-plugin/` - Add `skills/` directory
- `templates/command-plugin/` - Add `skills/` directory with example
- `templates/agent-plugin/` - Add `skills/` directory with example
- `templates/full-plugin/` - Add comprehensive Skills example

#### 2. Create Skills Examples

**Proposed New Plugins:**
- `examples/skill-based-plugin/` - Plugin that demonstrates Skills
- `skills/excel-processor/` - Example skill for Excel processing
- `skills/code-analyzer/` - Example skill for code analysis
- `skills/test-generator/` - Example skill for test generation

#### 3. Update Documentation

**Files to Update:**
- `CLAUDE.md` - Add Skills section
- `README.md` - Explain Skills vs Plugins
- `docs/plugin-structure.md` - Document `skills/` directory
- `docs/creating-plugins.md` - Add Skills creation guide
- `.claude-plugin/marketplace.extended.json` - Add skills metadata

#### 4. Add Official Anthropic Skills Marketplace

**Consideration:** Add `anthropics/skills` marketplace to documentation as recommended source for official skills.

---

## 4. Best Practices Validation

### Current Repository Compliance

| Best Practice | Status | Notes |
|--------------|--------|-------|
| **CLAUDE.md at root** | ✅ Implemented | Updated today with comprehensive info |
| **Semantic versioning** | ✅ Implemented | All plugins use semver |
| **Comprehensive README** | ✅ Implemented | Every plugin has README |
| **Local testing workflow** | ✅ Documented | Test marketplace pattern in CLAUDE.md |
| **Security scanning** | ✅ Implemented | CI checks for secrets, AWS keys, dangerous patterns |
| **Team configuration** | ⚠️ Partial | Could add example `.claude/settings.json` |
| **Skills support** | ❌ Missing | New feature, needs implementation |
| **Safety guidelines** | ⚠️ Partial | Could add to plugin templates |

### Security Compliance

**Current Security Measures:**
- ✅ CI scans for hardcoded secrets
- ✅ AWS key detection (blocks CI)
- ✅ Private key detection (blocks CI)
- ✅ Dangerous command patterns (`rm -rf /`)
- ✅ Command injection risks (`eval()`)
- ✅ Suspicious URLs detection
- ✅ MCP plugin dependency audit

**New Security Considerations with Skills:**
- ⚠️ Skills can execute code (requires Code Execution Tool)
- ⚠️ Need to warn users about skill sources
- ⚠️ Should add skill security guidelines
- ⚠️ Consider skill vetting process

---

## 5. Recommendations

### Priority 1: Critical Updates (Do Now)

1. **Add Skills Documentation to CLAUDE.md**
   - Explain Skills vs Plugins difference
   - Document `skills/` directory structure
   - Add SKILL.md format specification
   - Include discovery locations

2. **Update README.md with Skills Information**
   - Add Skills section to plugin types
   - Explain model-invoked vs user-invoked
   - Link to official Anthropic skills marketplace

3. **Add Security Warning for Skills**
   - Document code execution capability
   - Warn about trusted sources
   - Add to USER_SECURITY_GUIDE.md

### Priority 2: Repository Enhancements (This Week)

4. **Create Skills Example Plugin**
   - New plugin: `examples/skills-demo/`
   - Demonstrate Skills integration in plugin
   - Include SKILL.md examples
   - Show skill auto-invocation

5. **Update Plugin Templates**
   - Add `skills/` directory to all 4 templates
   - Include example SKILL.md in `full-plugin/`
   - Document Skills in template README files

6. **Add Team Configuration Examples**
   - Create `examples/team-config/` directory
   - Provide sample `.claude/settings.json`
   - Document team standardization workflow

### Priority 3: Extended Features (Next Sprint)

7. **Create Skills Pack**
   - New plugin pack: `skills-starter-pack/`
   - Include 5-10 common skills
   - Document skill creation workflow
   - Provide skill templates

8. **Enhanced Security Scanning**
   - Add CI check for `allowed-tools` in SKILL.md
   - Validate skill descriptions for clarity
   - Check for code execution warnings in README

9. **Skills Marketplace Section**
   - Add skills filter to marketplace website
   - Distinguish skills-enabled plugins
   - Add skill count to plugin metadata

### Priority 4: Long-term Strategy (Future)

10. **Official Anthropic Skills Integration**
    - Document how to use `anthropics/skills` marketplace
    - Create integration guide
    - Test official skills with our plugins

11. **Skills Best Practices Guide**
    - Document skill authoring patterns
    - Provide skill testing strategies
    - Share team deployment approaches

12. **Skills vs Plugins Decision Tree**
    - Help developers choose between skills and commands
    - Document when to use each approach
    - Provide conversion guides

---

## 6. Plugin Schema Updates

### Current plugin.json Schema

**No changes required** - Current schema is fully compatible:

```json
{
  "name": "plugin-name",
  "version": "2.1.0",
  "description": "Brief purpose",
  "author": {
    "name": "Author Name",
    "email": "author@example.com",
    "url": "https://author.com"
  },
  "homepage": "https://plugin-homepage.com",
  "repository": "https://github.com/user/repo",
  "license": "MIT",
  "keywords": ["tag1", "tag2"]
}
```

**Optional Enhancement:** Consider adding skills-specific metadata:

```json
{
  "name": "plugin-name",
  "version": "2.1.0",
  "skills": {
    "included": ["skill-1", "skill-2"],
    "count": 2,
    "requiresCodeExecution": true
  }
}
```

---

## 7. Validation & Testing

### Updated Pre-commit Checklist

Add to existing checklist:

```bash
# 6. Validate Skills (if present):
if [ -d "skills/" ]; then
  # Check for SKILL.md in each skill directory
  find skills/*/SKILL.md -type f

  # Validate SKILL.md frontmatter
  python3 scripts/check-frontmatter.py skills/*/SKILL.md

  # Check for allowed-tools field
  grep -r "allowed-tools:" skills/
fi
```

### New CI Workflow Checks

Consider adding to `.github/workflows/validate-plugins.yml`:

```yaml
- name: Validate Skills
  run: |
    echo "Validating Agent Skills..."
    for skill_dir in plugins/*/skills/*/; do
      if [ -d "$skill_dir" ]; then
        echo "Checking $skill_dir"

        # Verify SKILL.md exists
        if [ ! -f "$skill_dir/SKILL.md" ]; then
          echo "Missing SKILL.md in $skill_dir"
          exit 1
        fi

        # Validate YAML frontmatter
        python3 scripts/check-frontmatter.py "$skill_dir/SKILL.md"
      fi
    done
```

---

## 8. Breaking Changes & Compatibility

### Good News: No Breaking Changes

✅ **Full backward compatibility** - All existing plugins continue to work:
- Existing plugin structure unchanged
- Current plugin.json schema valid
- Commands and agents work as before
- MCP plugins unaffected

### Additive Changes Only

✅ **Skills are purely additive:**
- Optional `skills/` directory
- No required changes to existing plugins
- Gradual adoption possible
- Users opt-in to Skills feature

### Migration Path

For plugin authors who want to add Skills:

1. **Add `skills/` directory** to plugin root
2. **Create skill subdirectories** with SKILL.md
3. **Update README** to mention Skills support
4. **Bump minor version** (e.g., 1.2.0 → 1.3.0)
5. **Test locally** with `/plugin install`

No changes required for existing plugin users.

---

## 9. Competitive Analysis

### Other Marketplaces

Checked other known Claude Code plugin marketplaces:

1. **Dan Ávila's Marketplace** (`davila7/claude-code-marketplace`)
   - No Skills support yet (as of Oct 16, 2025)
   - Focus: DevOps & productivity

2. **Seth Hobson's Agents** (`wshobson/agents`)
   - 80+ specialized subagents
   - No Skills support yet

3. **CCPlugins** (`brennercruvinel/CCPlugins`)
   - Professional commands
   - No Skills support yet

**Opportunity:** We can be **first marketplace with Skills support** by implementing quickly.

---

## 10. Documentation Updates Needed

### Files Requiring Updates

1. **CLAUDE.md** (high priority)
   - Add "Agent Skills" section
   - Explain Skills vs Plugins vs Commands
   - Document `skills/` directory structure
   - Add SKILL.md format specification

2. **README.md** (high priority)
   - Update "Understanding Plugin Types" section
   - Add Skills as third type
   - Update plugin count if we add examples

3. **docs/plugin-structure.md** (high priority)
   - Document `skills/` directory
   - Add SKILL.md format details
   - Include discovery locations

4. **docs/creating-plugins.md** (medium priority)
   - Add "Creating Skills" section
   - Skill authoring best practices
   - Testing skills locally

5. **USER_SECURITY_GUIDE.md** (high priority - security)
   - Add Skills security warning
   - Explain code execution capability
   - Recommend trusted sources only

6. **MCP-SERVERS-STATUS.md** (low priority)
   - Note: MCP servers and Skills are separate
   - Clarify relationship if needed

7. **.claude-plugin/marketplace.extended.json** (medium priority)
   - Consider adding skills metadata fields
   - Track skills-enabled plugins

---

## 11. Key Takeaways

### What's New in October 2025

1. **Plugins** - Public beta (Oct 9) with growing ecosystem
2. **Skills** - Brand new feature (Oct 16) - launched TODAY!
3. **Team Standardization** - Repository-level plugin configuration
4. **Safety Features** - Checkpoint system, rewind capability
5. **Best Practices** - CLAUDE.md project READMEs, workflow safety

### What We Should Do

**Immediate Actions:**
1. ✅ Update CLAUDE.md with Skills information
2. ✅ Update README.md with Skills section
3. ✅ Add security warning about code execution
4. Create Skills example plugin
5. Update plugin templates with `skills/` directory

**Strategic Advantage:**
- Be first marketplace with Skills support
- Position as cutting-edge, up-to-date resource
- Attract Skills-interested developers

**Compatibility:**
- No breaking changes required
- All existing plugins work as-is
- Gradual adoption path

---

## 12. Action Items Summary

### This Week

- [ ] Update CLAUDE.md with Skills documentation
- [ ] Update README.md with Skills vs Plugins explanation
- [ ] Add Skills security warning to USER_SECURITY_GUIDE.md
- [ ] Create `examples/skills-demo/` plugin
- [ ] Update all 4 plugin templates with `skills/` directory

### Next Week

- [ ] Create `skills-starter-pack/` plugin pack
- [ ] Add Skills validation to CI workflow
- [ ] Update marketplace website with Skills filter
- [ ] Create Skills authoring guide

### This Month

- [ ] Add team configuration examples
- [ ] Document official Anthropic skills integration
- [ ] Create Skills vs Plugins decision tree
- [ ] Test and document Skills best practices

---

## 13. References

### Official Documentation
- **Plugins Guide:** https://docs.claude.com/en/docs/claude-code/plugins
- **Plugins Reference:** https://docs.claude.com/en/docs/claude-code/plugins-reference
- **Skills Documentation:** https://docs.claude.com/en/docs/claude-code/skills
- **Skills Announcement:** https://www.anthropic.com/news/skills
- **Best Practices:** https://www.anthropic.com/engineering/claude-code-best-practices

### Community Resources
- **Discord:** https://discord.com/invite/6PPFFzqPDZ (#claude-code channel)
- **GitHub Discussions:** https://github.com/jeremylongshore/claude-code-plugins/discussions

---

**Research Completed:** October 16, 2025
**Next Review:** October 23, 2025 (1 week after Skills launch)
**Priority:** HIGH - Skills feature launched today, first-mover advantage available
