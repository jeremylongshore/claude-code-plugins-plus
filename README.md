# Claude Code Plugins 🚀

[![Beta](https://img.shields.io/badge/status-beta-orange)](https://www.anthropic.com/news/claude-code-plugins)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Discord](https://img.shields.io/badge/Discord-Claude%20Developers-5865F2)](https://discord.com/invite/6PPFFzqPDZ)
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins?style=social)](https://github.com/jeremylongshore/claude-code-plugins)

**The comprehensive marketplace and learning hub for Claude Code plugins.**

Discover, learn, and share plugins that supercharge your Claude Code experience. From slash commands to specialized AI agents to production-ready MCP servers, this is THE place to explore what's possible with Claude Code's plugin ecosystem.

---

## 🚀 Quick Start

Get started in 3 commands:

```bash
# 1. Add this marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# 2. Install your first plugin
/plugin install project-health-auditor@claude-code-plugins

# 3. Try it out!
/analyze /path/to/your/repo
```

---

## 💡 What Are Claude Code Plugins?

Claude Code plugins are **lightweight packages** that extend Claude Code's capabilities. Each plugin can contain:

- **🎯 Slash Commands** - Custom shortcuts for frequent operations
- **🤖 Subagents** - Specialized AI agents for specific domains
- **🔌 Hooks** - Automation that triggers on events (file edits, tool usage, etc.)
- **🌐 MCP Servers** - Connections to external tools and data sources (NEW!)

**Released**: October 2025 (Public Beta)
**Official Docs**: https://docs.claude.com/en/docs/claude-code/plugins

---

## 🔥 NEW: MCP Server Plugins

**Production-ready MCP servers with advanced functionality**

### 🏆 Featured MCP Plugins

| Plugin | Description | MCP Tools | Category |
|--------|-------------|-----------|----------|
| **project-health-auditor** ⭐ | Multi-dimensional code health analysis (complexity + churn + tests) | 4 tools | Code Quality |
| **conversational-api-debugger** ⭐ | Debug REST API failures with OpenAPI specs and HTTP logs | 4 tools | Debugging |
| **domain-memory-agent** ⭐ | Knowledge base with TF-IDF semantic search | 6 tools | Productivity |
| **design-to-code** | Convert Figma/screenshots to React/Svelte/Vue components | 3 tools | Design |
| **workflow-orchestrator** | DAG-based workflow automation with parallel execution | 4 tools | Automation |

```bash
# Install MCP plugins
/plugin install project-health-auditor@claude-code-plugins
/plugin install conversational-api-debugger@claude-code-plugins
/plugin install domain-memory-agent@claude-code-plugins
/plugin install design-to-code@claude-code-plugins
/plugin install workflow-orchestrator@claude-code-plugins
```

#### 🎯 What Makes MCP Plugins Special?

- **🔧 21 Total Tools** - Across all 5 MCP servers
- **✅ Production Ready** - Comprehensive testing (95+ tests)
- **📊 Advanced Features** - Semantic search, API debugging, workflow automation
- **🎓 Well Documented** - Complete READMEs with examples
- **🏗️ TypeScript** - Strict mode, full type safety

**[📖 View MCP Server Documentation →](./MCP-SERVERS-STATUS.md)**

---

### 🧠 project-health-auditor

**Identify technical debt hot spots with multi-dimensional analysis**

```bash
/plugin install project-health-auditor@claude-code-plugins
/analyze /path/to/repo  # Comprehensive analysis workflow
```

**What it does**:
- 🔍 **Code Complexity**: Cyclomatic complexity analysis with health scores
- 📊 **Git Churn**: Identifies frequently changing files (hot spots)
- ✅ **Test Coverage**: Maps source files to tests, finds gaps
- 🎯 **Hot Spots**: Finds files with high complexity + high churn + no tests

**MCP Tools**: `list_repo_files`, `file_metrics`, `git_churn`, `map_tests`

---

### 🐛 conversational-api-debugger

**Debug REST API failures using OpenAPI specs and HTTP logs**

```bash
/plugin install conversational-api-debugger@claude-code-plugins
/debug-api  # Guided debugging workflow
```

**What it does**:
- 📄 **OpenAPI Parser**: Load and analyze API specs (JSON/YAML)
- 📝 **HAR Support**: Import browser DevTools HTTP logs
- 💡 **Failure Analysis**: Root cause identification with severity
- 🔧 **cURL Generation**: Create reproducible test commands

**MCP Tools**: `load_openapi`, `ingest_logs`, `explain_failure`, `make_repro`

---

### 🧠 domain-memory-agent

**Knowledge base with TF-IDF semantic search (no ML dependencies)**

```bash
/plugin install domain-memory-agent@claude-code-plugins
```

**What it does**:
- 📚 **Document Storage**: Store documents with tags and metadata
- 🔍 **Semantic Search**: TF-IDF based relevance ranking
- 📝 **Summarization**: Extractive summaries with caching
- 🏷️ **Organization**: Tag-based filtering and categorization

**MCP Tools**: `store_document`, `semantic_search`, `summarize`, `list_documents`, `get_document`, `delete_document`

**Perfect for**: RAG systems, documentation search, knowledge management

---

### 🎨 design-to-code

**Convert Figma designs and screenshots into production-ready code**

```bash
/plugin install design-to-code@claude-code-plugins
```

**What it does**:
- 🎯 **Figma Parsing**: Extract components from Figma JSON exports
- 📸 **Screenshot Analysis**: Analyze UI layouts from images
- ⚛️ **Multi-Framework**: Generate React, Svelte, or Vue components
- ♿ **A11y Built-in**: ARIA labels, semantic HTML, keyboard navigation

**MCP Tools**: `parse_figma`, `analyze_screenshot`, `generate_component`

---

### 🔄 workflow-orchestrator

**DAG-based workflow automation with parallel execution**

```bash
/plugin install workflow-orchestrator@claude-code-plugins
```

**What it does**:
- 📊 **DAG Execution**: Directed Acyclic Graph task dependencies
- ⚡ **Parallel Tasks**: Execute independent tasks concurrently
- 📈 **Run History**: Track all workflow executions
- ✅ **Status Monitoring**: Real-time progress tracking

**MCP Tools**: `create_workflow`, `execute_workflow`, `get_workflow`, `list_workflows`

**Perfect for**: CI/CD pipelines, data ETL, multi-stage deployments

---

## 📦 AI Agency Collection

**Professional tools for AI automation agencies**

Build faster, win more clients, and deliver better projects with our complete AI Agency toolkit:

### Automation Platforms

| Plugin | Description | Why Use It |
|--------|-------------|------------|
| **n8n-workflow-designer** ⭐ | Design complex workflows with loops & branching | Free, powerful, self-hostable |
| **make-scenario-builder** | Create Make.com scenarios visually | 1000+ integrations, great UI |
| **zapier-zap-builder** | Build multi-step Zaps with filters | Easiest platform, 5000+ apps |

### Business Tools

| Plugin | Description | Impact |
|--------|-------------|--------|
| **discovery-questionnaire** | Generate client discovery questions | Better scoping, fewer surprises |
| **sow-generator** | Professional Statements of Work | Win more deals, clear contracts |
| **roi-calculator** | Calculate automation ROI | Compelling proposals, justified pricing |

```bash
# Get the complete AI Agency toolkit
/plugin install n8n-workflow-designer@claude-code-plugins
/plugin install make-scenario-builder@claude-code-plugins
/plugin install zapier-zap-builder@claude-code-plugins
/plugin install discovery-questionnaire@claude-code-plugins
/plugin install sow-generator@claude-code-plugins
/plugin install roi-calculator@claude-code-plugins
```

**[📖 Complete AI Agency Guide →](./plugins/ai-agency)**

---

## 🏆 Production Plugins

| Plugin | Description | Category | Install |
|--------|-------------|----------|---------|
| **git-commit-smart** ⭐ | AI-powered conventional commit messages - production ready! | DevOps | `/plugin install git-commit-smart@claude-code-plugins` |
| **overnight-dev** | Autonomous overnight development with Git hooks enforcing TDD | Productivity | `/plugin install overnight-dev@claude-code-plugins` |

---

## 📚 Example Plugins for Learning

| Plugin | Description | Category | Install |
|--------|-------------|----------|---------|
| **hello-world** | Simple greeting command - perfect for learning! | Example | `/plugin install hello-world@claude-code-plugins` |
| **formatter** | Automatically formats code after edits using hooks | Productivity | `/plugin install formatter@claude-code-plugins` |
| **security-agent** | Expert security agent for vulnerability detection | Security | `/plugin install security-agent@claude-code-plugins` |

---

## 🎓 Example Use Cases

### For Developers

```bash
# Analyze your codebase health
/plugin install project-health-auditor@claude-code-plugins
/analyze /path/to/repo

# Debug API failures
/plugin install conversational-api-debugger@claude-code-plugins
/debug-api

# Build a knowledge base
/plugin install domain-memory-agent@claude-code-plugins

# Never write commit messages again
/plugin install git-commit-smart@claude-code-plugins
/gc
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
    "project-health-auditor@claude-code-plugins": true,
    "conversational-api-debugger@claude-code-plugins": true
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
- [🌐 MCP Server Status](./MCP-SERVERS-STATUS.md) - MCP plugin configurations

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

- **MCP Plugins**: 5 (21 total MCP tools)
- **Production Plugins**: 2 (git-commit-smart, overnight-dev)
- **AI Agency Plugins**: 6 (complete business toolkit)
- **Example Plugins**: 3 (hello-world, formatter, security-agent)
- **Templates**: 4 (minimal, command, agent, full)
- **Total Plugins**: 16 production-ready plugins

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

**[Get Started Now](#-quick-start)** | **[Browse MCP Plugins](#-new-mcp-server-plugins)** | **[Contribute](#-contributing)**

</div>

---

**Status**: Public Beta | **Version**: 1.1.0 | **Last Updated**: October 10, 2025
