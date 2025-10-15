# 🛠️ Plugin Creator Path: Build Your First Plugin

**Goal**: Create, test, and publish a complete Claude Code plugin from scratch.

**Prerequisites**:
- Completed [Quick Start](../01-quick-start/) path
- Basic understanding of markdown and YAML
- Text editor (VS Code recommended)

**Time Required**: 3 hours

**What You'll Build**: A functional plugin with slash commands, hooks, and agents

---

## Table of Contents

1. [Understanding Plugin Anatomy](#step-1-understanding-plugin-anatomy) (30 min)
2. [Create Plugin from Template](#step-2-create-plugin-from-template) (20 min)
3. [Build Slash Commands](#step-3-build-slash-commands) (45 min)
4. [Add Hooks for Automation](#step-4-add-hooks-for-automation) (30 min)
5. [Create AI Agents](#step-5-create-ai-agents) (30 min)
6. [Test Your Plugin](#step-6-test-your-plugin) (20 min)
7. [Publish to Marketplace](#step-7-publish-to-marketplace) (15 min)

---

## Step 1: Understanding Plugin Anatomy (30 min)

### Core Concept

**Claude Code plugins are instructions, not code** (for most plugins). They tell Claude **how** to do things using markdown files.

**Official Docs**: [Plugin Architecture](https://docs.claude.com/en/docs/claude-code/plugins#architecture)

### Required Structure

Every plugin needs this minimal structure:

```
my-plugin/
├── .claude-plugin/
│   └── plugin.json          # Plugin metadata (REQUIRED)
├── README.md                # Documentation (REQUIRED)
├── LICENSE                  # License file (REQUIRED)
└── [components]/            # At least ONE component required
    ├── commands/            # Slash commands (optional)
    ├── agents/              # AI agents (optional)
    ├── hooks/               # Lifecycle hooks (optional)
    └── scripts/             # Shell scripts (optional)
```

### Component Breakdown

**1. plugin.json** - Plugin Metadata
```json
{
  "name": "my-plugin",
  "version": "1.0.0",
  "description": "Clear one-line description",
  "author": {
    "name": "Your Name",
    "email": "your.email@example.com"
  },
  "repository": "https://github.com/username/repo",
  "license": "MIT",
  "keywords": ["keyword1", "keyword2"]
}
```

**2. Slash Commands** (`commands/*.md`)
- Triggered with `/command-name`
- Contain instructions for Claude
- Must have YAML frontmatter

**3. AI Agents** (`agents/*.md`)
- Specialized AI personas
- Domain-specific expertise
- Can be invoked by other commands

**4. Hooks** (`hooks/hooks.json`)
- Event-driven automation
- PostToolUse, PreToolUse, etc.
- Execute scripts or commands

**Official Docs**: [Plugin Components](https://docs.claude.com/en/docs/claude-code/plugins-reference#components)

---

## Step 2: Create Plugin from Template (20 min)

### Use the Minimal Template

```bash
# Clone this repository
git clone https://github.com/jeremylongshore/claude-code-plugins.git
cd claude-code-plugins/templates/minimal-plugin

# Copy to your workspace
cp -r . ~/my-first-plugin/
cd ~/my-first-plugin/
```

### Customize plugin.json

Edit `.claude-plugin/plugin.json`:

```json
{
  "name": "my-first-plugin",
  "version": "1.0.0",
  "description": "My first Claude Code plugin for learning",
  "author": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "repository": "https://github.com/yourusername/my-first-plugin",
  "license": "MIT",
  "keywords": ["learning", "example", "tutorial"]
}
```

**Important**: Plugin name must match directory name!

### Initialize Git Repository

```bash
git init
git add .
git commit -m "Initial plugin structure"
```

**Official Docs**: [Creating Plugins](https://docs.claude.com/en/docs/claude-code/plugins#creating-plugins)

---

## Step 3: Build Slash Commands (45 min)

### Create Your First Command

Create `commands/greet.md`:

```markdown
---
name: greet
description: Greet a user with a personalized message
---

# Greet Command

When the user runs `/greet [name]`, follow these steps:

## Instructions

1. **Extract the name argument**
   - If provided: Use the name
   - If not provided: Ask for the name

2. **Generate personalized greeting**
   - Include the name
   - Add a friendly emoji
   - Include current date/time

3. **Provide helpful next steps**
   - Suggest other commands
   - Link to documentation

## Example Output

```
👋 Hello, [Name]! Welcome to my-first-plugin!

Today is: [Current Date]

Next steps:
- Try /help to see all commands
- Visit our docs: [link]
```

## Error Handling

If no name is provided and user doesn't respond:
- Show friendly error message
- Provide example usage
- Don't fail silently
```

### Command Best Practices

**YAML Frontmatter** (REQUIRED):
```yaml
---
name: command-name          # Used for /command-name
description: One-line desc  # Shows in /help
---
```

**Clear Instructions**:
- Use numbered steps
- Be specific and unambiguous
- Include examples
- Handle errors gracefully

**Test the Command**:
```bash
# Install locally (from within your plugin directory)
/plugin install . --name my-first-plugin@local

# Run the command
/greet Claude
```

**Official Docs**: [Slash Commands Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference#slash-commands)

---

## Step 4: Add Hooks for Automation (30 min)

### What are Hooks?

Hooks automatically run code when events happen:
- **PostToolUse**: After Claude uses a tool
- **PreToolUse**: Before Claude uses a tool
- **OnError**: When errors occur

### Create hooks.json

Create `hooks/hooks.json`:

```json
{
  "hooks": [
    {
      "type": "PostToolUse",
      "toolName": "Write",
      "matcher": ".*\\.md$",
      "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format-markdown.sh",
      "description": "Auto-format markdown files after writing"
    }
  ]
}
```

**Key Fields**:
- `type`: Hook trigger (PostToolUse, PreToolUse, OnError)
- `toolName`: Which tool triggers this (Write, Edit, Bash, etc.)
- `matcher`: Regex pattern to filter files
- `command`: Script to execute
- `${CLAUDE_PLUGIN_ROOT}`: Always use for portable paths!

### Create the Hook Script

Create `scripts/format-markdown.sh`:

```bash
#!/bin/bash
# Auto-format markdown files

FILE="$1"

echo "📝 Formatting markdown: $FILE"

# Add prettier or other formatting logic
# For demo, just echo
echo "✅ Formatted successfully"
```

**Make it executable**:
```bash
chmod +x scripts/format-markdown.sh
```

### Test the Hook

```bash
# Write a markdown file to trigger the hook
# Claude will use Write tool -> Hook runs automatically
```

**Official Docs**: [Hooks Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference#hooks)

---

## Step 5: Create AI Agents (30 min)

### What are Agents?

Agents are specialized AI personas with domain expertise. They help Claude perform complex tasks.

### Create an Expert Agent

Create `agents/expert.md`:

```markdown
---
name: expert
description: Domain expert for my-first-plugin
model: claude-sonnet-4
---

You are an expert in [YOUR DOMAIN].

## Your Expertise

You specialize in:
- [Skill 1]: [Description]
- [Skill 2]: [Description]
- [Skill 3]: [Description]

## Your Approach

When helping users:

1. **Understand the context** first
   - Ask clarifying questions
   - Verify requirements
   - Check constraints

2. **Provide expert guidance**
   - Use industry best practices
   - Cite sources when possible
   - Explain trade-offs

3. **Deliver actionable solutions**
   - Show code examples
   - Provide step-by-step instructions
   - Anticipate edge cases

## Knowledge Base

You have deep knowledge of:
- [Topic 1]
- [Topic 2]
- [Topic 3]

## Response Format

Always structure responses as:
1. Summary (1-2 sentences)
2. Detailed explanation
3. Code examples (if applicable)
4. Next steps or alternatives

## Quality Standards

- Accuracy is critical
- Cite official documentation
- Admit when uncertain
- Provide learning resources
```

### Agent Best Practices

**YAML Frontmatter**:
```yaml
---
name: agent-name
description: What this agent does
model: claude-sonnet-4  # or claude-opus
---
```

**Be Specific**:
- Define clear expertise boundaries
- Set expected behavior
- Include examples
- Define response formats

**Official Docs**: [Agents Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference#agents)

---

## Step 6: Test Your Plugin (20 min)

### Local Testing

```bash
# 1. Install from local directory
cd ~/my-first-plugin
/plugin install . --name my-first-plugin@local

# 2. Verify installation
/plugin list | grep my-first-plugin

# 3. Test commands
/greet Testing

# 4. Check files were created
ls -la ~/.claude/plugins/my-first-plugin/
```

### Validation Checklist

Run these checks:

```bash
# ✅ Validate plugin.json syntax
jq empty .claude-plugin/plugin.json

# ✅ Check all scripts are executable
find scripts/ -name "*.sh" -not -perm -u+x

# ✅ Verify YAML frontmatter
for file in commands/*.md agents/*.md; do
  head -5 "$file" | grep -q "^---$" || echo "Missing frontmatter: $file"
done

# ✅ Test hooks.json syntax
jq empty hooks/hooks.json
```

### Test Marketplace Entry

Create local test marketplace:

```bash
# Create test marketplace
mkdir -p ~/test-marketplace/.claude-plugin

# Create marketplace.json
cat > ~/test-marketplace/.claude-plugin/marketplace.json << 'EOF'
{
  "name": "test",
  "owner": {"name": "Test"},
  "plugins": [{
    "name": "my-first-plugin",
    "source": "/absolute/path/to/my-first-plugin"
  }]
}
EOF

# Add marketplace
/plugin marketplace add ~/test-marketplace

# Install from test marketplace
/plugin install my-first-plugin@test
```

**Official Docs**: [Testing Plugins](https://docs.claude.com/en/docs/claude-code/plugins#testing)

---

## Step 7: Publish to Marketplace (15 min)

### Option 1: Submit to This Marketplace

1. **Fork this repository**
   ```bash
   # On GitHub: Click Fork
   git clone https://github.com/yourusername/claude-code-plugins.git
   ```

2. **Add your plugin**
   ```bash
   cp -r ~/my-first-plugin plugins/community/my-first-plugin/
   ```

3. **Update marketplace catalog**

   Edit `.claude-plugin/marketplace.extended.json`, add:
   ```json
   {
     "name": "my-first-plugin",
     "source": "./plugins/community/my-first-plugin",
     "description": "My first Claude Code plugin",
     "version": "1.0.0",
     "category": "productivity",
     "keywords": ["learning", "example"],
     "author": {
       "name": "Your Name",
       "email": "you@example.com"
     }
   }
   ```

```bash
# Regenerate CLI marketplace.json
pnpm run sync-marketplace  # or: npm run sync-marketplace
```

4. **Submit Pull Request**
   ```bash
   git add .
   git commit -m "feat: add my-first-plugin"
   git push origin main
   # Open PR on GitHub
   ```

### Option 2: Create Your Own Marketplace

```bash
# Create your marketplace repo
mkdir my-marketplace
cd my-marketplace

# Create structure
mkdir -p .claude-plugin plugins

# Create marketplace.json
cat > .claude-plugin/marketplace.json << 'EOF'
{
  "name": "my-marketplace",
  "owner": {
    "name": "Your Name",
    "email": "you@example.com"
  },
  "plugins": [
    {
      "name": "my-first-plugin",
      "source": "./plugins/my-first-plugin",
      "version": "1.0.0"
    }
  ]
}
EOF

# Copy plugin
cp -r ~/my-first-plugin plugins/

# Publish to GitHub
git init
git add .
git commit -m "Initial marketplace"
gh repo create --public --source=. --remote=origin
git push origin main
```

Users install with:
```bash
/plugin marketplace add yourusername/my-marketplace
/plugin install my-first-plugin@my-marketplace
```

**Official Docs**: [Publishing Plugins](https://docs.claude.com/en/docs/claude-code/plugins#publishing)

---

## Congratulations! 🎉

You've successfully:
✅ Understood plugin anatomy
✅ Created a plugin from template
✅ Built slash commands
✅ Added automation hooks
✅ Created AI agents
✅ Tested thoroughly
✅ Published to marketplace

### What's Next?

**Level Up**:
→ [Advanced Developer Path](../03-advanced-developer/) - Build MCP servers with real code

**Get Inspired**:
- Study [security-agent](../../../plugins/examples/security-agent/) - Production example
- Explore [devops-pack](../../../plugins/packages/devops-automation-pack/) - Complex plugin pack
- Browse [crypto plugins](../../../plugins/crypto/) - Real-world implementations

**Join the Community**:
- 💬 [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- 🗨️ [Discord](https://discord.com/invite/6PPFFzqPDZ) (#claude-code)
- 📚 [Official Docs](https://docs.claude.com/en/docs/claude-code/plugins)

---

## Resources

### Official Documentation
- [Plugin Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- [Plugin Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference)
- [CLI Reference](https://docs.claude.com/en/docs/claude-code/cli-reference)

### This Repository
- [Contributing Guide](../../../CONTRIBUTING.md)
- [Example Plugins](../../../plugins/examples/)
- [Plugin Templates](../../../templates/)

### Tools
- [jq](https://stedolan.github.io/jq/) - JSON validation
- [VS Code](https://code.visualstudio.com/) - Recommended editor
- [GitHub CLI](https://cli.github.com/) - Easy publishing

---

**Ready to build production tools?** Continue to [Advanced Developer Path](../03-advanced-developer/)!
