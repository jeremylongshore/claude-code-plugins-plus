# File Templates

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
