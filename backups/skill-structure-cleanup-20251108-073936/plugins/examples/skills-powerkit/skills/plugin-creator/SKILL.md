---
name: plugin-creator
description: |
  Automatically creates new Claude Code plugins with proper structure, validation, and marketplace integration when user mentions creating a plugin, new plugin, or plugin from template. Specific to claude-code-plugins repository workflow.
allowed-tools: Write, Read, Grep, Bash
version: 1.0.0
---

# Plugin Creator

## Purpose
Automatically scaffolds new Claude Code plugins with complete directory structure, required files, proper formatting, and marketplace catalog integration - specifically optimized for the claude-code-plugins repository.

## Trigger Keywords
- "create plugin" or "new plugin"
- "plugin from template"
- "scaffold plugin"
- "generate plugin"
- "add new plugin to marketplace"

## Plugin Creation Process

When activated, I will:

1. **Gather Requirements**
   - Plugin name (kebab-case)
   - Category (productivity, security, devops, etc.)
   - Type (commands, agents, skills, MCP, or combination)
   - Description and keywords
   - Author information

2. **Create Directory Structure**
   ```
   plugins/[category]/[plugin-name]/
   ├── .claude-plugin/
   │   └── plugin.json
   ├── README.md
   ├── LICENSE
   └── [commands|agents|skills|hooks|mcp]/
   ```

3. **Generate Required Files**
   - **plugin.json** with proper schema (name, version, description, author)
   - **README.md** with comprehensive documentation
   - **LICENSE** (MIT by default)
   - Component files based on type

4. **Add to Marketplace Catalog**
   - Update `.claude-plugin/marketplace.extended.json`
   - Run `npm run sync-marketplace` automatically
   - Validate catalog schema

5. **Validate Everything**
   - Run `./scripts/validate-all.sh` on new plugin
   - Check JSON syntax with `jq`
   - Verify frontmatter in markdown files
   - Ensure scripts are executable

## Plugin Types Supported

### Commands Plugin
- Creates `commands/` directory
- Generates example command with proper frontmatter
- Includes `/demo-command` example

### Agents Plugin
- Creates `agents/` directory
- Generates example agent with capabilities
- Includes model specification

### Skills Plugin
- Creates `skills/skill-name/` directory
- Generates SKILL.md with proper format
- Includes trigger keywords and allowed-tools

### MCP Plugin
- Creates `src/`, `dist/`, `mcp/` directories
- Generates TypeScript boilerplate
- Includes package.json with MCP SDK
- Adds to pnpm workspace

### Full Plugin
- Combines all types
- Creates complete example structure
- Ready for customization

## File Templates

### plugin.json Template
```json
{
  "name": "plugin-name",
  "version": "1.0.0",
  "description": "Clear description",
  "author": {
    "name": "Author Name",
    "email": "[email protected]"
  },
  "repository": "https://github.com/jeremylongshore/claude-code-plugins",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

### Command Template
```markdown
---
name: command-name
description: What this command does
model: sonnet
---

# Command Title

Instructions for Claude...
```

### Skill Template
```markdown
---
name: Skill Name
description: What it does AND when to use it
allowed-tools: Read, Write, Grep
---

# Skill Name

## Purpose
[What this skill does]

## Trigger Keywords
- keyword1
- keyword2

## Instructions
[Step-by-step for Claude]
```

## Marketplace Integration

I automatically:
1. Add plugin entry to `marketplace.extended.json`
2. Run `npm run sync-marketplace` to update CLI catalog
3. Validate both catalogs with `jq`
4. Check for duplicate names
5. Verify source paths exist

## Validation Steps

After creation:
- ✅ All required files present
- ✅ Valid JSON (plugin.json, catalogs)
- ✅ Proper frontmatter in markdown
- ✅ Scripts executable (`chmod +x`)
- ✅ No duplicate plugin names
- ✅ Category is valid
- ✅ Keywords present

## Repository-Specific Features

**For claude-code-plugins repo:**
- Follows exact directory structure
- Uses correct marketplace slug (`claude-code-plugins-plus`)
- Includes proper LICENSE file
- Adds to correct category folder
- Validates against existing plugins
- Updates version in marketplace

## Output

I provide:
```
✅ Created plugin: plugin-name
📁 Location: plugins/category/plugin-name/
📝 Files created: 8
🔍 Validation: PASSED
📦 Marketplace: UPDATED
✨ Ready to commit!

Next steps:
1. Review files in plugins/category/plugin-name/
2. Customize README.md and component files
3. Run: git add plugins/category/plugin-name/
4. Run: git commit -m "feat: Add plugin-name plugin"
```

## Examples

**User says:** "Create a new security plugin called 'owasp-scanner' with commands"

**I automatically:**
1. Create directory: `plugins/security/owasp-scanner/`
2. Generate plugin.json, README, LICENSE
3. Create `commands/` with example
4. Add to marketplace.extended.json
5. Sync marketplace.json
6. Validate all files
7. Report success

**User says:** "Scaffold a Skills plugin for code review"

**I automatically:**
1. Create directory with `skills/` subdirectories
2. Generate SKILL.md templates
3. Add trigger keywords for code review
4. Add to marketplace
5. Validate and report
