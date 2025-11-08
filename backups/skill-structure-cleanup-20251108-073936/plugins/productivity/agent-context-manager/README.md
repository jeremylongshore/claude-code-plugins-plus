# Agent Context Manager

**Automatically load `AGENTS.md` files alongside `CLAUDE.md` for specialized agent-specific instructions.**

[![Version](https://img.shields.io/badge/version-1.0.0-brightgreen)](.)
[![Category](https://img.shields.io/badge/category-productivity-blue)](.)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-enabled-orange?logo=sparkles)](.)
[![Anthropic Spec](https://img.shields.io/badge/Anthropic%20Spec-v1.0%20Compliant-success?logo=checkmarx)](https://github.com/anthropics/skills/blob/main/agent_skills_spec.md)

---

## Problem This Solves

**Before**: Claude Code only reads `CLAUDE.md` automatically. If you want agent-specific instructions separate from general project context, you have to manually manage them or pollute CLAUDE.md with agent-only rules.

**After**: Create `AGENTS.md` in any directory, and Claude Code will **automatically detect and load it** alongside CLAUDE.md, enabling specialized agent behaviors without manual intervention.

---

## Quick Start

### Installation

```bash
/plugin install agent-context-manager@claude-code-plugins-plus
```

### Basic Usage

1. **Create AGENTS.md** in your project root:

```bash
cd /path/to/your/project
nano AGENTS.md
```

2. **Add agent-specific rules**:

```markdown
# AGENTS.md - Agent-Specific Instructions

## Agent Behavior Rules

When working with Agent Skills in this project:

1. **Always use TypeScript strict mode** for all generated code
2. **Never create files** without explicit user permission
3. **Follow naming convention**: use kebab-case for all file names
4. **Auto-commit after changes**: Create git commits automatically

## Specialized Workflows

### Code Generation
- Use templates from `./templates/` directory
- Run ESLint after generating any .ts/.js files
- Add comprehensive JSDoc comments
```

3. **That's it!** Start Claude Code and the plugin will automatically:
   - Detect AGENTS.md
   - Load the content
   - Apply the rules for your session

---

## Features

### ⚡ Automatic Loading (Layer 1: Proactive Skill)

The plugin **automatically** detects and loads AGENTS.md when:

- Starting a new Claude Code session
- Changing directories (via `cd` command)
- Invoking any other agent skill

**User Experience**:
```
📋 Loaded agent-specific context from AGENTS.md

Following specialized agent rules for this session:
- Always use TypeScript strict mode
- Never create files without permission
- Follow kebab-case naming convention
```

**No user action required!**

### 🔔 Directory Change Detection (Layer 2: Hooks)

When you enter a directory with AGENTS.md, you'll see:

```
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
📋 AGENTS.md detected in current directory
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

⚡ Agent Context Manager is active

The agent-context-loader skill will automatically load
agent-specific instructions from AGENTS.md

Location: /path/to/project/AGENTS.md

What happens next:
  1. Claude will read AGENTS.md automatically
  2. Agent-specific rules will be incorporated
  3. Instructions will be active for this session

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
```

### 🔄 Manual Synchronization (Layer 3: Slash Command)

Permanently merge AGENTS.md into CLAUDE.md:

```bash
/sync-agent-context
```

**What it does**:
1. Finds all AGENTS.md files in your project
2. Reads their content
3. Merges into CLAUDE.md under "## Agent-Specific Instructions" section
4. Creates backup: `CLAUDE.md.backup.TIMESTAMP`

**Result**:
```markdown
## Agent-Specific Instructions

### Root Directory Agent Rules (./AGENTS.md)
[Content from ./AGENTS.md]

### Subproject Agent Rules (./packages/app/AGENTS.md)
[Content from ./packages/app/AGENTS.md]
```

---

## Architecture

### Three-Layer Redundancy System

```
Layer 1: Proactive Skill (agent-context-loader)
   ↓
   Automatically invoked when context needed
   ↓
   Reads AGENTS.md using Read tool
   ↓
   Loads into session context

Layer 2: Directory Change Hook (check-agents-md.sh)
   ↓
   Runs on cd, session start
   ↓
   Prints detection message
   ↓
   Reminds Claude to load AGENTS.md

Layer 3: Manual Sync Command (/sync-agent-context)
   ↓
   User explicitly merges AGENTS.md → CLAUDE.md
   ↓
   Permanent solution
   ↓
   AGENTS.md always loaded
```

**Why three layers?**

1. **Layer 1** = Ideal (fully automatic)
2. **Layer 2** = Backup (semi-automatic reminder)
3. **Layer 3** = Fallback (manual permanent merge)

This ensures AGENTS.md is **always** loaded, even if one layer fails.

---

## Usage Examples

### Example 1: Single Project with Agent Rules

**Project Structure**:
```
my-project/
├── CLAUDE.md           # General project context
├── AGENTS.md           # Agent-specific rules
└── src/
    └── index.ts
```

**Workflow**:
```bash
cd my-project
# Plugin automatically detects AGENTS.md
# Claude loads both CLAUDE.md and AGENTS.md
# Agent rules are active for this session
```

### Example 2: Multi-Package Monorepo

**Project Structure**:
```
monorepo/
├── CLAUDE.md
├── AGENTS.md                   # Root-level agent rules
└── packages/
    ├── app/
    │   └── AGENTS.md           # App-specific agent rules
    └── api/
        └── AGENTS.md           # API-specific agent rules
```

**Workflow**:
```bash
# In root: Loads monorepo/AGENTS.md
cd monorepo
# Claude applies root-level agent rules

# In app package: Loads packages/app/AGENTS.md
cd packages/app
# Claude applies app-specific agent rules

# Permanent merge all: /sync-agent-context
# Merges all AGENTS.md files into root CLAUDE.md
```

### Example 3: Manual Loading Fallback

If automatic loading doesn't trigger:

```
User: "load agent context"

Claude: 📋 Checking for AGENTS.md...
        Found: ./AGENTS.md

        Loading agent-specific instructions:
        - Use TypeScript strict mode
        - Never create files without permission
        - Follow kebab-case naming

        ✅ Agent context loaded successfully!
```

---

## Configuration

### Priority and Conflict Resolution

**When both CLAUDE.md and AGENTS.md exist**:

- Both are loaded simultaneously
- AGENTS.md **supplements** CLAUDE.md
- For conflicts: AGENTS.md takes **precedence** for agent workflows

**Example Conflict**:
```markdown
# CLAUDE.md
Use JavaScript for all code

# AGENTS.md
Use TypeScript for agent-generated code
```

**Result**: Agent workflows use TypeScript; manual coding uses JavaScript

### Customizing Agent Rules

**AGENTS.md supports any markdown content**:

```markdown
# AGENTS.md

## File Management Rules
- Always ask permission before creating files
- Use .gitignore for generated files
- Clean up temp files after operations

## Code Quality
- Run linter after generating code
- Add tests for all new functions
- Document all public APIs

## Git Workflow
- Auto-commit after each task completion
- Use conventional commit messages
- Never force push to main

## Project-Specific
- Import shared types from @/types
- Use custom logger from @/utils/logger
- Follow API patterns in docs/api-patterns.md
```

---

## Advanced Usage

### Conditional Agent Rules

```markdown
# AGENTS.md

## Environment-Specific Rules

### Development
- Use verbose logging
- Skip performance optimization
- Generate debug comments

### Production
- Minimize bundle size
- Optimize performance
- Remove all console.log statements
```

### Agent Skill Coordination

```markdown
# AGENTS.md

## Skill-Specific Rules

### When using `code-generator` skill:
- Always generate TypeScript
- Include unit tests
- Add JSDoc comments

### When using `git-automator` skill:
- Create feature branches
- Use conventional commits
- Add Co-Authored-By trailer
```

### Progressive Disclosure

```markdown
# AGENTS.md

## Level 1: Basic Rules (Always Apply)
- Follow coding standards
- Test before committing

## Level 2: Advanced Rules (Experienced Agents)
- Implement performance optimizations
- Add caching strategies

## Level 3: Expert Rules (Complex Tasks)
- Design patterns for scalability
- Architectural considerations
```

---

## Troubleshooting

### Problem: AGENTS.md Not Loading Automatically

**Diagnose**:
```bash
# Check if plugin is installed
/plugin list | grep agent-context-manager

# Check if AGENTS.md exists
ls -la AGENTS.md

# Check file permissions
stat AGENTS.md
```

**Solutions**:
1. **Manual invoke**: Say "load agent context"
2. **Explicit path**: "Read ./AGENTS.md and follow those rules"
3. **Permanent merge**: Run `/sync-agent-context`

### Problem: Conflicting Rules Between CLAUDE.md and AGENTS.md

**Solution**: AGENTS.md takes precedence for agent workflows. If this is undesired:

**Option A**: Remove conflicting rule from AGENTS.md
**Option B**: Add clarification in AGENTS.md:
```markdown
# AGENTS.md

## Priority Note
For rules that conflict with CLAUDE.md, prefer CLAUDE.md unless explicitly marked [OVERRIDE]
```

### Problem: Multiple AGENTS.md Files Not All Loading

**Cause**: Auto-loader only loads from current directory

**Solution**: Use slash command to merge all:
```bash
/sync-agent-context
```

This finds and merges ALL AGENTS.md files in the project.

---

## Best Practices

### DO:
✅ Use AGENTS.md for agent-specific rules only
✅ Keep CLAUDE.md for general project context
✅ Be specific and actionable in agent rules
✅ Test agent behavior after adding new rules
✅ Version control both CLAUDE.md and AGENTS.md

### DON'T:
❌ Duplicate rules between CLAUDE.md and AGENTS.md
❌ Make AGENTS.md too generic (use CLAUDE.md instead)
❌ Forget to run /sync-agent-context after major AGENTS.md updates
❌ Create conflicting rules without clear precedence
❌ Use AGENTS.md for non-agent workflows

---

## Integration with Other Plugins

### Works Great With:

- **Code Generators**: Enforce code style rules
- **Git Automators**: Control commit behavior
- **Testing Frameworks**: Define test requirements
- **Deployment Pipelines**: Specify deployment rules

### Example Integration:

```markdown
# AGENTS.md for use with code-generator plugin

## Code Generation Rules

When using the `code-generator` skill:

1. **Templates**: Use Handlebars templates from ./templates/
2. **Output**: Generate to ./src/generated/
3. **Naming**: Use PascalCase for classes, camelCase for functions
4. **Testing**: Generate .test.ts alongside each generated file
5. **Documentation**: Add JSDoc with @generated tag
```

---

## API Reference

### Proactive Skill: `agent-context-loader`

**Triggers automatically when**:
- Starting new session
- Changing directories
- Invoking other agent skills
- User requests: "load agent context"

**Behavior**:
1. Checks for `./AGENTS.md`
2. Reads file if exists
3. Loads into session context
4. Announces loading to user

### Hook Script: `check-agents-md.sh`

**Runs automatically on**:
- Session start (`onSessionStart`)
- Directory change (`onDirectoryChange`)

**Behavior**:
1. Detects `./AGENTS.md`
2. Prints formatted message
3. Prompts Claude to load content

### Slash Command: `/sync-agent-context`

**User invokes manually**:
```bash
/sync-agent-context
```

**Behavior**:
1. Finds all `AGENTS.md` files (recursive)
2. Reads each file
3. Merges into `CLAUDE.md`
4. Creates backup
5. Reports results

---

## Comparison with Alternatives

### Manual Merging (No Plugin)

**Pros**: Full control
**Cons**: Tedious, error-prone, requires manual updates

### Separate Instructions in CLAUDE.md

**Pros**: Single file
**Cons**: Cluttered, hard to maintain, no separation of concerns

### Agent Context Manager Plugin

**Pros**: Automatic, separate concerns, three-layer redundancy
**Cons**: Requires plugin installation

**Winner**: Agent Context Manager ✅

---

## Compliance

### Anthropic Agent Skills Spec v1.0

✅ **Compliant with all requirements**:
- Skills in `skills/` directory
- SKILL.md at root of skill directory
- Descriptive skill names (agent-context-loader)
- Comprehensive documentation
- Bundled resources (scripts/, commands/)
- Progressive disclosure (3 levels)

### Exceeds Anthropic Standards

🌟 **Enhancements beyond spec**:
- Three-layer redundancy system
- Automated synchronization
- Comprehensive error handling
- Detailed troubleshooting guide
- Integration examples
- Best practices documentation

---

## Changelog

### v1.0.0 (2025-10-23)

**Initial Release**:
- ✅ Proactive skill for auto-loading AGENTS.md
- ✅ Directory change hooks
- ✅ Manual sync slash command
- ✅ Three-layer redundancy architecture
- ✅ Comprehensive documentation
- ✅ Anthropic Spec v1.0 compliant

---

## Contributing

Contributions welcome! This plugin is part of the [Claude Code Plugins Plus](https://github.com/jeremylongshore/claude-code-plugins-plus) collection.

**Ideas for enhancements**:
- Auto-sync on AGENTS.md file change
- Multi-level agent context (project, workspace, global)
- Template generator for AGENTS.md
- Validation of AGENTS.md structure
- Integration with external config files

---

## License

MIT License - See LICENSE file

---

## Support

- **Issues**: [GitHub Issues](https://github.com/jeremylongshore/claude-code-plugins-plus/issues)
- **Discussions**: [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins-plus/discussions)
- **Documentation**: This README + [SKILL.md](skills/agent-context-loader/SKILL.md)

---

## Credits

**Author**: Jeremy Longshore
**Plugin Collection**: Claude Code Plugins Plus
**Spec Compliance**: Anthropic Agent Skills Spec v1.0

🤖 Generated with [Claude Code](https://claude.com/claude-code)

Co-Authored-By: Claude <noreply@anthropic.com>
