# Creating Claude Code Plugins

## Quick Start

### 1. Choose a Template

Templates are in the `templates/` directory:
- `minimal-plugin` - Just plugin.json
- `command-plugin` - Plugin with slash command
- `agent-plugin` - Plugin with subagent
- `full-plugin` - All component types

### 2. Copy Template

```bash
cp -r templates/command-plugin my-plugin
cd my-plugin
```

### 3. Edit plugin.json

```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Clear description of what your plugin does",
  "author": {
    "name": "Your Name",
    "email": "[email protected]"
  },
  "repository": "https://github.com/username/my-plugin",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

### 4. Add Components

#### Slash Command (commands/mycommand.md)

```markdown
---
description: Brief description of command
shortcut: mc
---

# My Command

Detailed instructions for Claude on what this command does.

Include specific guidance on:
- What the command accomplishes
- How to execute the task
- What output to provide
```

#### Subagent (agents/myagent.md)

```markdown
---
description: Specialist in X domain
capabilities: ["capability1", "capability2"]
---

# My Agent

You are a specialized agent for X domain.

## Your Capabilities
- List specific skills
- Define expertise areas

## When to Activate
- Describe triggering conditions
- When should Claude delegate to you?

## Approach
- Outline your methodology
- Specify output format
```

#### Hooks (hooks/hooks.json)

```json
{
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          {
            "type": "command",
            "command": "${CLAUDE_PLUGIN_ROOT}/scripts/process.sh"
          }
        ]
      }
    ]
  }
}
```

### 5. Test Locally

```bash
# Create test marketplace
mkdir -p ~/test-marketplace/.claude-plugin

# Create marketplace.json
cat > ~/test-marketplace/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "test",
  "owner": {"name": "Test"},
  "plugins": [{
    "name": "my-plugin",
    "source": "/full/path/to/my-plugin"
  }]
}
EOF

# Add marketplace
/plugin marketplace add ~/test-marketplace

# Install plugin
/plugin install my-plugin@test

# Test functionality
/mycommand
```

### 6. Debug

```bash
# Run with debug output
claude --debug

# Check plugin loading
/plugin list

# Validate structure
claude plugin validate
```

### 7. Document

Create comprehensive README.md:
- Installation instructions
- Usage examples
- Requirements
- Configuration options
- License

### 8. Distribute

**Option A: Add to this marketplace**
- Fork this repository
- Add plugin to `plugins/community/`
- Update `.claude-plugin/marketplace.json`
- Submit pull request

**Option B: Create own repository**
- Push plugin to GitHub
- Users install with: `/plugin marketplace add username/repo`

## Best Practices

### Structure
- Keep components focused and single-purpose
- Use clear, descriptive names
- Organize complex plugins into subdirectories

### Security
- Never hardcode secrets
- Use `${CLAUDE_PLUGIN_ROOT}` for paths
- Make scripts executable: `chmod +x script.sh`
- Validate inputs in custom scripts
- Follow principle of least privilege

### Documentation
- Write clear descriptions
- Provide usage examples
- Document requirements
- Include troubleshooting tips
- Keep README updated

### Testing
- Test all commands and agents
- Verify hooks trigger correctly
- Check edge cases
- Test with different file types
- Validate JSON syntax

### Versioning
- Use semantic versioning (Major.Minor.Patch)
- Update version in plugin.json for releases
- Document changes in CHANGELOG.md
- Tag releases in git

## Common Issues

**Commands not appearing**:
- Check `commands/` is at root, not in `.claude-plugin/`
- Verify plugin.json is valid JSON
- Run `/plugin list` to see if installed

**Scripts not executing**:
- Make executable: `chmod +x script.sh`
- Use `${CLAUDE_PLUGIN_ROOT}` for paths
- Check script has shebang: `#!/bin/bash`

**Hooks not firing**:
- Verify hooks.json syntax
- Check matcher patterns
- Test with debug mode: `claude --debug`

## Next Steps

- [Plugin structure reference](plugin-structure.md)
- [Security best practices](security-best-practices.md)
- [Testing guide](testing-guide.md)
