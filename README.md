# Claude Code Plugins 🚀

[![Beta](https://img.shields.io/badge/status-beta-orange)](https://www.anthropic.com/news/claude-code-plugins)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/badge/Discord-Claude%20Developers-5865F2)](https://discord.com/invite/6PPFFzqPDZ)
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins?style=social)](https://github.com/jeremylongshore/claude-code-plugins)

**The comprehensive marketplace and learning hub for Claude Code plugins.**

Discover, learn, and share plugins that supercharge your Claude Code experience. From slash commands to specialized AI agents, this is THE place to explore what's possible with Claude Code's plugin ecosystem.

---

## 🚀 Quick Start

Get started in 3 commands:

```bash
# 1. Add this marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# 2. Install your first plugin
/plugin install hello-world@claude-code-plugins

# 3. Try it out!
/hello
```

---

## 💡 What Are Claude Code Plugins?

Claude Code plugins are **lightweight packages** that extend Claude Code's capabilities. Each plugin can contain:

- **🎯 Slash Commands** - Custom shortcuts for frequent operations
- **🤖 Subagents** - Specialized AI agents for specific domains
- **🔌 Hooks** - Automation that triggers on events (file edits, tool usage, etc.)
- **🌐 MCP Servers** - Connections to external tools and data sources

**Released**: October 2025 (Public Beta)
**Official Docs**: https://docs.claude.com/en/docs/claude-code/plugins

---

## 📦 Featured Plugins

| Plugin | Description | Category | Install |
|--------|-------------|----------|---------|
| **hello-world** | Simple greeting command - perfect for learning! | Example | `/plugin install hello-world@claude-code-plugins` |
| **auto-formatter** | Automatically formats code after edits using hooks | Productivity | `/plugin install auto-formatter@claude-code-plugins` |
| **security-reviewer** | Expert security agent for vulnerability detection | Security | `/plugin install security-reviewer@claude-code-plugins` |

### 🎯 What Makes These Plugins Special?

- **✨ Working Examples** - Not just demos, these are fully functional plugins you can use today
- **📚 Educational** - Each plugin teaches different concepts (commands, hooks, agents)
- **🔍 Well-Documented** - Comprehensive READMEs explaining how everything works
- **🛠️ Production-Ready** - Use them as-is or as templates for your own plugins

---

## 🎓 Example Use Cases

### For Developers

```bash
# Auto-format all your code
/plugin install auto-formatter@claude-code-plugins

# Get security reviews on demand
/plugin install security-reviewer@claude-code-plugins
```

### For Teams

Share custom workflows across your organization:

```json
// .claude/settings.json
{
  "extraKnownMarketplaces": {
    "claude-code-plugins": {
      "source": {
        "source": "github",
        "repo": "jeremylongshore/claude-code-plugins"
      }
    }
  },
  "enabledPlugins": {
    "auto-formatter@claude-code-plugins": true,
    "security-reviewer@claude-code-plugins": true
  }
}
```

### For Plugin Creators

Use our templates to build your own plugins:

```bash
# Copy a template
cp -r templates/command-plugin my-awesome-plugin

# Customize and test locally
/plugin marketplace add ./my-test-marketplace
/plugin install my-awesome-plugin@test
```

---

## 📚 Documentation

### Getting Started
- [📖 Installation & Usage](docs/getting-started.md) - Install and use plugins
- [🎨 Creating Your First Plugin](docs/creating-plugins.md) - Step-by-step tutorial
- [📋 Plugin Reference](docs/plugin-structure.md) - Technical specifications

### Advanced Topics
- [🏪 Marketplace Guide](docs/marketplace-guide.md) - Distribute your plugins
- [🔒 Security Best Practices](docs/security-best-practices.md) - Secure plugin development
- [❓ FAQ](docs/monetization-alternatives.md) - Monetization alternatives

---

## 🤝 Contributing

We welcome community plugin submissions! This ecosystem thrives on shared knowledge and collaboration.

### Submit Your Plugin

1. **Fork** this repository
2. **Add** your plugin to `plugins/community/your-plugin/`
3. **Update** `.claude-plugin/marketplace.json` with your plugin entry
4. **Submit** a pull request using our plugin submission template

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Plugin Requirements

- ✅ Valid `.claude-plugin/plugin.json`
- ✅ Comprehensive README.md with examples
- ✅ LICENSE file (MIT or Apache-2.0 recommended)
- ✅ Tested locally and working
- ✅ No hardcoded secrets or credentials
- ✅ All scripts executable (`chmod +x`)

---

## ⚠️ Important Notes

### Not on GitHub Marketplace

**Claude Code plugins do NOT use GitHub Marketplace.** They operate in a completely separate ecosystem using JSON-based marketplace catalogs hosted in Git repositories. This repository IS a Claude Code plugin marketplace.

### No Built-in Monetization

**There is currently no monetization mechanism** for Claude Code plugins. All plugins in the ecosystem are free and open-source. See [Monetization Alternatives](docs/monetization-alternatives.md) for external revenue strategies.

### Beta Status

Claude Code plugins are in **public beta** (October 2025). Features and best practices may evolve. This marketplace will stay updated with the latest changes.

---

## 🌟 Plugin Templates

Start building your own plugin today:

| Template | What's Included | Best For |
|----------|----------------|----------|
| **minimal-plugin** | Just plugin.json & README | Simple utilities |
| **command-plugin** | Slash commands | Custom workflows |
| **agent-plugin** | Specialized AI agent | Domain expertise |
| **full-plugin** | Commands + agents + hooks | Complex automation |

All templates are in the [`templates/`](templates/) directory with complete examples.

---

## 🔗 Resources

### Official

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/)
- [Plugin Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- [Plugin Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference)
- [Announcement Blog](https://www.anthropic.com/news/claude-code-plugins)
- [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### Community

- [💬 Claude Developers Discord](https://discord.com/invite/6PPFFzqPDZ) - 40,000+ members
- [🐛 Report Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)
- [💡 Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- [⭐ Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code) - Curated resources

### Other Marketplaces

- [Dan Ávila's Marketplace](https://github.com/davila7/claude-code-marketplace) - DevOps & productivity
- [Seth Hobson's Agents](https://github.com/wshobson/agents) - 80+ specialized subagents
- [CCPlugins](https://github.com/brennercruvinel/CCPlugins) - Professional commands

---

## 📊 Statistics

- **Example Plugins**: 3 (hello-world, auto-formatter, security-reviewer)
- **Templates**: 4 (minimal, command, agent, full)
- **Documentation Pages**: 6
- **Community Plugins**: Open for submissions!

---

## 🎯 Our Mission

To be **THE definitive resource** for Claude Code plugins by:

1. **📚 Educating** - Clear examples showing how plugins work
2. **🏪 Curating** - High-quality plugins you can trust
3. **🤝 Connecting** - Building a vibrant community of creators
4. **📈 Growing** - Setting standards as the ecosystem evolves

---

## 💪 Why This Marketplace?

- **✨ Quality over Quantity** - Every plugin is reviewed and tested
- **📖 Learning-Focused** - Understand how plugins work, don't just use them
- **🚀 First-Mover** - Establishing best practices for the ecosystem
- **🌍 Community-Driven** - Built by developers, for developers
- **🔄 Actively Maintained** - Updated with latest Claude Code features

---

## 📜 License

MIT License - See [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Anthropic** - For creating Claude Code and the plugin system
- **Community Contributors** - Everyone who submits plugins and improvements
- **Early Adopters** - Users who provide feedback and help us improve

---

## 📞 Get Help

- **💬 Questions?** - [Open a discussion](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- **🐛 Found a bug?** - [Report an issue](https://github.com/jeremylongshore/claude-code-plugins/issues)
- **💡 Have an idea?** - [Join our Discord](https://discord.com/invite/6PPFFzqPDZ)

---

<div align="center">

**[⭐ Star this repo](https://github.com/jeremylongshore/claude-code-plugins)** if you find it useful!

Made with ❤️ by the Claude Code community

**[Get Started Now](#-quick-start)** | **[Browse Plugins](#-featured-plugins)** | **[Contribute](#-contributing)**

</div>

---

**Status**: Public Beta | **Version**: 1.0.0 | **Last Updated**: October 2025
