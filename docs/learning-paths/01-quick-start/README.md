# 🚀 Quick Start: Your First Plugin in 15 Minutes

**Goal**: Install the marketplace, run your first plugin, and understand the basics.

**Prerequisites**:
- Claude Code CLI installed ([Installation Guide](https://docs.claude.com/en/docs/claude-code/installation))
- Basic command line knowledge

**Time Required**: 15 minutes

---

## Table of Contents

1. [Add the Marketplace](#step-1-add-the-marketplace-2-minutes) (2 min)
2. [Install Your First Plugin](#step-2-install-your-first-plugin-3-minutes) (3 min)
3. [Use Your First Command](#step-3-use-your-first-command-2-minutes) (2 min)
4. [Try a Practical Plugin](#step-4-try-a-practical-plugin-5-minutes) (5 min)
5. [Explore Plugin Packs](#step-5-explore-plugin-packs-3-minutes) (3 min)

---

## Step 1: Add the Marketplace (2 minutes)

First, add this plugin marketplace to Claude Code:

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

**What just happened?**
- Claude Code connected to this GitHub repository
- You can now access 225+ plugins instantly
- The marketplace catalog is cached locally

**Official Docs**: [Plugin Marketplace Guide](https://docs.claude.com/en/docs/claude-code/plugins#marketplace)

---

## Step 2: Install Your First Plugin (3 minutes)

Let's start with the simplest plugin - `hello-world`:

```bash
/plugin install hello-world@claude-code-plugins-plus
```

**What's happening?**
- Claude Code downloads the plugin files
- Installs to `~/.claude/plugins/hello-world/`
- Registers the `/hello` slash command

**Verify Installation**:
```bash
/plugin list
# You should see: hello-world@claude-code-plugins-plus
```

---

## Step 3: Use Your First Command (2 minutes)

Try the hello command:

```bash
/hello
```

**Expected Output**:
```
👋 Hello from the hello-world plugin!

This is a basic example plugin demonstrating:
✅ Slash commands
✅ YAML frontmatter
✅ Plugin structure

Next steps:
- Try /hello World
- View source: ~/.claude/plugins/hello-world/
- Read the README
```

**Try with arguments**:
```bash
/hello Claude Code
# Output: 👋 Hello, Claude Code!
```

**Official Docs**: [Slash Commands Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference#slash-commands)

---

## Step 4: Try a Practical Plugin (5 minutes)

Now install a production-ready plugin:

```bash
/plugin install git-commit-smart@claude-code-plugins-plus
```

**Use it to create a smart commit**:

1. Make some changes to a project
2. Run: `/commit-smart`
3. Claude will:
   - Analyze your git diff
   - Generate a semantic commit message
   - Follow conventional commits format
   - Create the commit with co-authorship

**Example Output**:
```bash
feat: add learning paths documentation

Added comprehensive learning paths for new users:
- Quick start guide (15 min)
- Plugin creator path (3 hrs)
- Advanced developer path (1 day)

🤖 Generated with Claude Code
Co-Authored-By: Claude <noreply@anthropic.com>
```

---

## Step 5: Explore Plugin Packs (3 minutes)

Install a complete plugin pack for your domain:

### For DevOps Engineers:
```bash
/plugin install devops-automation-pack@claude-code-plugins-plus
```

This gives you 25 plugins:
- Git workflow automation
- CI/CD pipeline templates
- Docker optimization guides
- Kubernetes deployment patterns
- Infrastructure as Code helpers

### For Security Professionals:
```bash
/plugin install security-pro-pack@claude-code-plugins-plus
```

This gives you 10 plugins:
- OWASP compliance checking
- Security audit workflows
- Penetration testing guides
- Threat modeling templates

**View all available packs**:
```bash
/plugin search pack
```

**Official Docs**: [Plugin Packs](https://docs.claude.com/en/docs/claude-code/plugins#plugin-packs)

---

## Understanding What You Just Installed

### Plugin Types

**1. AI Instruction Plugins** (hello-world, git-commit-smart, packs)
- Markdown instructions that guide Claude's behavior
- No external code execution
- Work through Claude's interpretation

**2. MCP Server Plugins** (advanced, covered in Advanced path)
- Real Node.js applications
- Run as separate processes
- Provide tools Claude can use

**Official Docs**: [Plugin Architecture](https://docs.claude.com/en/docs/claude-code/plugins#architecture)

---

## Common Commands Reference

```bash
# List installed plugins
/plugin list

# Search marketplace
/plugin search <keyword>

# Update a plugin
/plugin update <plugin-name>

# Remove a plugin
/plugin uninstall <plugin-name>

# View plugin info
/plugin info <plugin-name>
```

**Official Docs**: [CLI Commands Reference](https://docs.claude.com/en/docs/claude-code/cli-reference)

---

## Troubleshooting

### Plugin not found?
```bash
# Refresh marketplace cache
/plugin marketplace update claude-code-plugins-plus
```

### Command not working?
```bash
# Verify plugin is installed
/plugin list | grep <plugin-name>

# Check plugin files exist
ls -la ~/.claude/plugins/<plugin-name>/
```

### Need help?
- 📚 [Official Documentation](https://docs.claude.com/en/docs/claude-code/plugins)
- 💬 [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- 🗨️ [Discord Community](https://discord.com/invite/6PPFFzqPDZ) (#claude-code channel)

---

## What's Next?

You've successfully:
✅ Added the marketplace
✅ Installed plugins
✅ Run slash commands
✅ Understand plugin types

### Continue Learning:

**Want to build your own plugins?**
→ [Plugin Creator Path](../02-plugin-creator/) (3 hours)

**Want to build production MCP servers?**
→ [Advanced Developer Path](../03-advanced-developer/) (1 day)

**Have a specific use case?**
→ [Use Case Paths](../use-cases/) (domain-specific)

**Just want to use more plugins?**
→ [Browse the Marketplace](https://jeremylongshore.github.io/claude-code-plugins/)

---

## Quick Wins - Try These Next

```bash
# Improve code formatting
/plugin install formatter@claude-code-plugins-plus
# Use: Automatically formats code on tool use

# Professional commits
/plugin install git-commit-smart@claude-code-plugins-plus
# Use: /commit-smart

# Overnight development automation
/plugin install overnight-dev@claude-code-plugins-plus
# Use: /overnight-setup

# Project health analysis
/plugin install project-health-auditor@claude-code-plugins-plus
# Use: Analyze code complexity and health
```

---

**Congratulations!** 🎉 You're now a Claude Code plugin user. Continue to the [Plugin Creator Path](../02-plugin-creator/) to build your own!

**Official Resources**:
- 📖 [Plugin Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- 🔧 [Plugin Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference)
- 💡 [Examples Repository](https://github.com/anthropics/claude-code-examples)
