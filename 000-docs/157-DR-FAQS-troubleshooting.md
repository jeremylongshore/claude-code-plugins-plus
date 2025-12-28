# Troubleshooting Guide

Common issues and solutions for Claude Code Plugins marketplace.

---

## Installation Issues

### WSL2: "Clone succeeded, but checkout failed"

**Problem:** Git clone fails when adding the marketplace on WSL2 with error:
```
Clone succeeded, but checkout failed.
You can inspect what was checked out with 'git status'
and retry with 'git restore --source=HEAD :/'
```

**Cause:** WSL2 uses the Windows filesystem which has a 260-character path length limit (MAX_PATH). The marketplace repository is large (~10,000 files) and some plugin paths exceed this limit.

**Solution 1: Enable Long Path Support (Recommended)**

```bash
# Step 1: Enable long paths in Git globally
git config --global core.longpaths true

# Step 2: Remove the failed clone attempt
rm -rf ~/.claude/plugins/marketplaces/jeremylongshore-claude-code-plugins

# Step 3: Try adding the marketplace again
/plugin marketplace add jeremylongshore/claude-code-plugins
```

**Solution 2: Manual Clone**

```bash
# Step 1: Enable long paths
git config --global core.longpaths true

# Step 2: Clone manually with shallow depth
git clone --depth 1 https://github.com/jeremylongshore/claude-code-plugins.git ~/.claude/plugins/marketplaces/jeremylongshore-claude-code-plugins

# Step 3: Verify in Claude Code
/plugin marketplace list
```

**Verification:**

```bash
/plugin marketplace list
# Should show: claude-code-plugins-plus

/plugin install devops-automation-pack@claude-code-plugins-plus
# Should install successfully
```

---

## Plugin Issues

### Plugin Not Found After Installation

**Problem:** Installed a plugin but can't find its commands or skills.

**Solution:**

```bash
# Verify plugin is installed
/plugin list

# Verify plugin is enabled
# Check ~/.claude/settings.json for plugin in enabledPlugins

# Reload Claude Code
# Exit and restart Claude Code CLI
```

### Permission Denied on Hook Scripts

**Problem:** Plugin hooks fail with "Permission denied" error.

**Solution:**

```bash
# Make all plugin scripts executable
cd ~/.claude/plugins/marketplaces/jeremylongshore-claude-code-plugins
find . -name "*.sh" -type f -exec chmod +x {} \;

# Or for specific plugin
chmod +x plugins/[category]/[plugin-name]/scripts/*.sh
```

---

## MCP Server Issues

### MCP Plugin Build Failures

**Problem:** MCP plugin fails to build with TypeScript errors.

**Solution:**

```bash
# Ensure Node.js 20+ is installed
node --version  # Should be 20.x or higher

# Install dependencies
cd plugins/mcp/[plugin-name]
npm install

# Run type checking
npm run typecheck

# Build the plugin
npm run build
```

### MCP Server Won't Start

**Problem:** MCP server plugin installed but tools not available.

**Solution:**

```bash
# Check if plugin was built
ls plugins/mcp/[plugin-name]/dist/
# Should contain compiled JavaScript files

# Check Claude Code logs
# Look for MCP server startup errors

# Rebuild the plugin
cd plugins/mcp/[plugin-name]
npm run build
```

---

## Marketplace Issues

### Marketplace Not Updating

**Problem:** New plugins or updates not appearing after marketplace update.

**Solution:**

```bash
# Remove and re-add marketplace
/plugin marketplace remove claude-code-plugins-plus
/plugin marketplace add jeremylongshore/claude-code-plugins

# Force git pull in marketplace directory
cd ~/.claude/plugins/marketplaces/jeremylongshore-claude-code-plugins
git pull origin main
```

### Old Marketplace Slug Issues

**Problem:** Using old `claude-code-plugins` slug instead of `claude-code-plugins-plus`.

**Solution:**

```bash
# Remove old marketplace
/plugin marketplace remove claude-code-plugins

# Add with new slug
/plugin marketplace add jeremylongshore/claude-code-plugins

# Update plugin installations
/plugin install [plugin-name]@claude-code-plugins-plus
```

---

## Performance Issues

### Slow Plugin Installation

**Problem:** Plugin installation takes a very long time.

**Cause:** Large repository size (~10,000 files).

**Solution:**

```bash
# Use shallow clone for faster installation
git config --global fetch.depth 1

# Or manually clone with depth limit
git clone --depth 1 https://github.com/jeremylongshore/claude-code-plugins.git ~/.claude/plugins/marketplaces/jeremylongshore-claude-code-plugins
```

---

## Getting Help

If these solutions don't resolve your issue:

1. **Check existing issues:** https://github.com/jeremylongshore/claude-code-plugins/issues
2. **Open a new issue:** Include:
   - Your operating system and version
   - Claude Code version (`/version`)
   - Full error message
   - Steps to reproduce
3. **Contact maintainer:** jeremy@intentsolutions.io

---

**Last Updated:** November 29, 2025
