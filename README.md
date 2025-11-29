# Claude Code Plugins

[![Version](https://img.shields.io/badge/version-1.4.1-brightgreen)](CHANGELOG.md)
[![Plugins](https://img.shields.io/badge/plugins-254-blue)](https://github.com/jeremylongshore/claude-code-plugins)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-185%20plugins-orange?logo=sparkles)](CHANGELOG.md)
[![2025 Schema](https://img.shields.io/badge/2025%20Schema-100%25%20Compliant-success?logo=checkmarx)](SKILLS_SCHEMA_2025.md)
[![NEW](https://img.shields.io/badge/NEW-Tool%20Permissions-blueviolet?logo=shield)](SKILL_ACTIVATION_GUIDE.md)
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins?style=social)](https://github.com/jeremylongshore/claude-code-plugins)

**254 production-ready Claude Code plugins for automation, development, and AI workflows.**

🎯 **NEW in v1.4.1:** **Website Accuracy & Enterprise Sponsor** - Corrected plugin counts (now 254), added recognition for Max Mergenthaler @ Nixtla as first Enterprise supporter

**Latest:** [v1.4.1 Release](https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v1.4.1) - Website accuracy improvements, Enterprise sponsor recognition, link fixes

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install devops-automation-pack@claude-code-plugins-plus
```

⚡🪽 **[Buy me a Red Bull](https://buymeacoffee.com/jeremylongshore)** – Give these plugins wings, support ongoing development, and influence the premium plugin roadmap. See our [sponsor page](https://claudecodeplugins.io/sponsor) for tier details.

*Additional support options (like Patreon) may be added later as the ecosystem grows.*

---

## 👥 Enterprise Supporters

🏢 **Grateful to have [Max Mergenthaler](https://github.com/mergenthaler) and [Nixtla](https://www.nixtla.io/) as our first Enterprise supporter!**

Max is CEO & Co-Founder at **Nixtla** (YC S21), building production-grade time-series tools:
- **TimeGPT** - Foundation model for forecasting
- **Nixtlaverse** - Open-source time-series libraries
- **Support Level**: $199/month Enterprise tier

His support helps us prioritize features that matter for real-world AI development.

*Sponsorship reflects support and prioritization on a best-effort basis, not a formal SLA or delivery guarantee.*

---

## 🙏 Contributors

**Huge thanks to our community contributors who make this marketplace better:**

- **[@aledlie](https://github.com/aledlie) (Alyshia Ledlie)** - Fixed 7 critical JSON syntax errors and added production CI/CD patterns from real-world debugging ([#117](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/117), [spotlight](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/118))
- **[@JackReis](https://github.com/JackReis) (Jack Reis)** - Contributed neurodivergent-visual-org plugin with ADHD-friendly Mermaid diagrams and accessibility features ([#106](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/106))
- **[@terrylica](https://github.com/terrylica) (Terry Li)** - Built prettier-markdown-hook with zero-config markdown formatting and comprehensive documentation ([#101](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/101))

**Want to contribute?** See [CONTRIBUTING.md](./CONTRIBUTING.md) or reach out to **jeremy@intentsolutions.io**

---

## Quick Start

**Install a plugin:**
```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install devops-automation-pack@claude-code-plugins-plus
```

> Already using an older install? Run `/plugin marketplace remove claude-code-plugins` and re-add with the command above to switch to the new `claude-code-plugins-plus` slug. Existing plugins keep working either way.

**Browse the catalog:**
Visit **[Claude Code Plugins Marketplace](https://claudecodeplugins.io/)** (CLI slug `claude-code-plugins-plus`) or explore [`plugins/`](./plugins/)

**Learn to build:**
See [Learning Paths](#-learning-paths) for step-by-step guides

---

<details>
  <summary><strong>📚 Essential Documentation</strong> (click to expand)</summary>

  
  | Document | Purpose |
  |----------|---------|
  | **[User Security Guide](./docs/USER_SECURITY_GUIDE.md)** | 🛡️ How to safely evaluate and install plugins |
  | **[Code of Conduct](./CODE_OF_CONDUCT.md)** | Community standards and reporting |
  | **[SECURITY.md](./SECURITY.md)** | Security policy, threat model, vulnerability reporting |
  | **[CHANGELOG.md](./CHANGELOG.md)** | Release history & version updates |
  | **[CONTRIBUTING.md](./CONTRIBUTING.md)** | How to submit plugins |
  | **[Learning Paths](#-learning-paths)** | Structured guides from beginner to expert |

</details>

---

<details>
  <summary><strong>🎓 Learning Paths</strong> (click to expand)</summary>

  
  **New to Claude Code plugins?** Follow structured paths:

  | Path | Duration | Best For |
  |------|----------|----------|
  | 🚀 [Quick Start](./docs/learning-paths/01-quick-start/) | 15 min | Install and use your first plugin |
  | 🛠️ [Plugin Creator](./docs/learning-paths/02-plugin-creator/) | 3 hours | Build your first plugin from scratch |
  | ⚡ [Advanced Developer](./docs/learning-paths/03-advanced-developer/) | 1 day | Create production MCP servers |

  **By Use Case**: [DevOps](./docs/learning-paths/use-cases/devops-engineer.md) • [Security](./docs/learning-paths/use-cases/security-specialist.md) • [AI/ML](./docs/learning-paths/use-cases/ai-ml-developer.md) • [Crypto](./docs/learning-paths/use-cases/crypto-trader.md)

</details>

---

## 🎓 Understanding Agent Skills

**What are Agent Skills?** They're instruction manuals that teach Claude Code **when** and **how** to use your installed plugins automatically.

### How It Works: The 4-Step Flow

```
1. DISCOVERY (Marketplace)
   └─ You browse claudecodeplugins.io
   └─ Find "ansible-playbook-creator"
   └─ Install: /plugin install ansible-playbook-creator@claude-code-plugins-plus

2. INSTALLATION (Files Copied)
   └─ Plugin files copied to your machine
   └─ Including skills/skill-adapter/SKILL.md ← The instruction manual!

3. STARTUP (Claude Learns)
   └─ Claude Code reads SKILL.md frontmatter from ALL installed plugins
   └─ Loads trigger phrases: "ansible playbook", "automate deployment"
   └─ Now Claude knows this plugin exists and when to use it

4. USAGE (Automatic Activation)
   └─ You: "Create an Ansible playbook for Apache"
   └─ Claude: Sees "ansible playbook" trigger → reads full SKILL.md
   └─ Claude: Activates plugin with correct workflow automatically!
```

### Real Example: Before vs After

**WITHOUT Agent Skills:**
```
You: "Create ansible playbook"
Claude: "I have ansible-playbook-creator installed somewhere...
         Let me manually search and figure out how to use it..."
Result: ❌ Plugin sits unused, you have to name it explicitly
```

**WITH Agent Skills:**
```
You: "Create ansible playbook"
Claude: *Recognizes trigger phrase instantly*
        *Reads SKILL.md for workflow*
        "I'll use ansible-playbook-creator for this!"
        *Automatically applies best practices*
Result: ✅ Instant activation, correct usage, zero thinking
```

### What's in a SKILL.md?

Each plugin gets ONE skill file teaching Claude:

```yaml
---
name: Creating Ansible Playbooks
description: |
  Automates Ansible playbook creation. Use when you need to automate
  server configurations or deployments. Trigger with "ansible playbook"
  or "create playbook for [task]".
---

## How It Works
1. Receives user request with infrastructure details
2. Generates production-ready Ansible playbook
3. Includes best practices and security configurations

## When to Use This Skill
- Automate server configuration tasks
- Deploy applications consistently
- Create repeatable infrastructure setups

## Examples
User: "Create ansible playbook to install Apache on Ubuntu"
Skill activates → Generates playbook → Ready to deploy
```

### Key Points

- ✅ **Not creating new plugins** - Adding instruction manuals to existing ones
- ✅ **Automatic activation** - Claude recognizes trigger phrases
- ✅ **Best practices built-in** - Each skill teaches optimal workflows
- ✅ **One skill per plugin** - Comprehensive instruction manual
- ✅ **Only for installed plugins** - Not for discovering new ones

**Status:** Batch-generating Agent Skills for all 229 plugins using Vertex AI. Progress tracked in audit database with full backups.

**Resources:**
- [Internal Guide: How Agent Skills Work →](backups/HOW_AGENT_SKILLS_WORK.md)
- [External Deep Dive: Claude Skills Technical Analysis →](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) - Comprehensive technical breakdown by Lee-Han Chung

---

### Skills Powerkit - First Agent Skills Plugin
**NEW:** The first plugin using Anthropic's Agent Skills feature (launched Oct 16, 2025). Say "create a plugin" or "validate this plugin" and Claude automatically uses these model-invoked capabilities:
- 🛠️ Plugin Creator - Auto-scaffolds plugins
- ✅ Plugin Validator - Auto-validates structure
- 📦 Marketplace Manager - Auto-manages catalog
- 🔍 Plugin Auditor - Auto-audits security
- 🔢 Version Bumper - Auto-handles versions

```bash
/plugin install skills-powerkit@claude-code-plugins-plus
```

### Skill Enhancers - Automation for Claude's Skills
**NEW CATEGORY:** Plugins that extend Claude's built-in Skills (web_search, web_fetch) with automation. Claude searches → Plugin acts.

Example: `web-to-github-issue` - Research → GitHub tickets

[Explore Skill Enhancers →](plugins/skill-enhancers/)

---

## Understanding Plugin Types

This marketplace contains **two types of plugins** that work differently:

### 1. AI Instruction Plugins (98% of marketplace)
- **What they are**: Markdown instructions that guide Claude's behavior
- **How they work**: Tell Claude HOW to perform tasks using its built-in capabilities
- **Examples**: DevOps pack, Security pack, API development tools
- **Count**: 249 plugins
- **No external code execution** - work entirely through Claude's interpretation

### 2. MCP Server Plugins (2% of marketplace)
- **What they are**: TypeScript/JavaScript applications
- **How they work**: Run as separate Node.js processes that Claude can communicate with
- **Examples**: project-health-auditor, conversational-api-debugger, domain-memory-agent
- **Count**: 5 plugins (21 MCP tools total)
- **Actual compiled code** - 13-26KB of executable JavaScript per plugin

---

### 🧠 Agent Skills - A Feature, Not a Type

**185 plugins (73% of marketplace) include Agent Skills** - automatic capabilities that Claude activates based on conversation context.

- **What they are**: SKILL.md files that teach Claude when and how to use the plugin
- **How they work**: Claude reads trigger phrases and activates skills automatically
- **Example**: Say "create a plugin" and Claude uses the Skills Powerkit automatically
- **Invocation**: Automatic - no `/command` needed
- **Launched**: October 16, 2025 by Anthropic

**Skills vs Commands:** Commands require explicit `/command` trigger. Skills activate automatically based on what you're asking for.

**Note:** Plugins can bundle Skills, Commands, Agents, and MCP servers together. Agent Skills are a feature that enhances any plugin type.

---

## 📚 Featured Resources

### Claude Skills Deep Dive - Essential Reading

**[Technical Analysis: How Claude Skills Work →](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/)**

A comprehensive technical breakdown by **Lee-Han Chung** covering:

- **How Skills Activate**: Understanding trigger phrases and automatic invocation
- **Tool Permission System**: Deep dive into `allowed-tools` and security boundaries
- **Architecture Patterns**: Design principles for effective skill-based plugins
- **Best Practices**: Real-world examples and common pitfalls to avoid

This article is the definitive external resource for understanding how Agent Skills work under the hood.

*185 plugins in this marketplace (73%) include Agent Skills based on these principles.*

---

## Example Use Cases

### For Developers

```bash
# Analyze your codebase health
/plugin install project-health-auditor@claude-code-plugins-plus
/analyze /path/to/repo

# Debug API failures
/plugin install conversational-api-debugger@claude-code-plugins-plus
/debug-api

# Build a knowledge base
/plugin install domain-memory-agent@claude-code-plugins-plus

# Never write commit messages again
/plugin install git-commit-smart@claude-code-plugins-plus
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
    "project-health-auditor@claude-code-plugins-plus": true,
    "conversational-api-debugger@claude-code-plugins-plus": true
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

## Documentation

### Getting Started
- [Installation & Usage](docs/getting-started.md) - Install and use plugins
- [Creating Your First Plugin](docs/creating-plugins.md) - Step-by-step tutorial
- [Plugin Reference](docs/plugin-structure.md) - Technical specifications

### Advanced Topics
- [Marketplace Guide](docs/marketplace-guide.md) - Distribute your plugins
- [Security Best Practices](docs/security-best-practices.md) - Secure plugin development
- [MCP Server Status](./MCP-SERVERS-STATUS.md) - MCP plugin configurations

---

## Contributing

We welcome community plugin submissions! This ecosystem thrives on shared knowledge and collaboration.

### Submit Your Plugin

1. **Fork** this repository
2. **Add** your plugin to `plugins/community/your-plugin/`
3. **Update** `.claude-plugin/marketplace.extended.json` with your plugin entry
4. **Run** `pnpm run sync-marketplace` (or `npm run sync-marketplace`) to regenerate `.claude-plugin/marketplace.json`
5. **Submit** a pull request using our plugin submission template

See [CONTRIBUTING.md](CONTRIBUTING.md) for detailed guidelines.

### Plugin Requirements

- Valid `.claude-plugin/plugin.json`
- Comprehensive README.md with examples
- LICENSE file (MIT or Apache-2.0 recommended)
- Tested locally and working
- No hardcoded secrets or credentials
- All scripts executable (`chmod +x`)

---

## Important Notes

### Not on GitHub Marketplace

**Claude Code plugins do NOT use GitHub Marketplace.** They operate in a completely separate ecosystem using JSON-based marketplace catalogs hosted in Git repositories. This repository IS a Claude Code plugin marketplace.

### No Built-in Monetization

**There is currently no monetization mechanism** for Claude Code plugins. All plugins in the ecosystem are free and open-source. See [Monetization Alternatives](docs/monetization-alternatives.md) for external revenue strategies.

### Beta Status

Claude Code plugins are in **public beta** (October 2025). Features and best practices may evolve. This marketplace will stay updated with the latest changes.

---

## Plugin Templates

Start building your own plugin today:

| Template | What's Included | Best For |
|----------|----------------|----------|
| **minimal-plugin** | Just plugin.json & README | Simple utilities |
| **command-plugin** | Slash commands | Custom workflows |
| **agent-plugin** | Specialized AI agent | Domain expertise |
| **full-plugin** | Commands + agents + hooks | Complex automation |

All templates are in the [`templates/`](templates/) directory with complete examples.

---

## Resources

### Official

- [Claude Code Documentation](https://docs.claude.com/en/docs/claude-code/)
- [Plugin Guide](https://docs.claude.com/en/docs/claude-code/plugins)
- [Plugin Reference](https://docs.claude.com/en/docs/claude-code/plugins-reference)
- [Announcement Blog](https://www.anthropic.com/news/claude-code-plugins)
- [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### Community

- [Claude Developers Discord](https://discord.com/invite/6PPFFzqPDZ) - 40,000+ members
- [Report Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)
- [Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)
- [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code) - Curated resources

### Other Marketplaces

- [Dan Ávila's Marketplace](https://github.com/davila7/claude-code-marketplace) - DevOps & productivity
- [Seth Hobson's Agents](https://github.com/wshobson/agents) - 80+ specialized subagents
- [CCPlugins](https://github.com/brennercruvinel/CCPlugins) - Professional commands

---

## Statistics

- **Plugin Packs**: 4 (62 total plugin components)
- **MCP Plugins**: 5 (21 total MCP tools)
- **Production Plugins**: 2 (git-commit-smart, overnight-dev)
- **AI Agency Plugins**: 6 (complete business toolkit)
- **Example Plugins**: 3 (hello-world, formatter, security-agent)
- **Templates**: 4 (minimal, command, agent, full)
- **Total Marketplace Plugins**: 20

---

## Our Mission

To be **THE definitive resource** for Claude Code plugins by:

1. **Educating** - Clear examples showing how plugins work
2. **Curating** - High-quality plugins you can trust
3. **Connecting** - Building a vibrant community of creators
4. **Growing** - Setting standards as the ecosystem evolves

---

## Why This Marketplace?

- **Quality over Quantity** - Every plugin is reviewed and tested
- **Learning-Focused** - Understand how plugins work, don't just use them
- **First-Mover** - Establishing best practices for the ecosystem
- **Community-Driven** - Built by developers, for developers
- **Actively Maintained** - Updated with latest Claude Code features

---

## License

MIT License - See [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- **Anthropic** - For creating Claude Code and the plugin system
- **Community Contributors** - Everyone who submits plugins and improvements
- **Early Adopters** - Users who provide feedback and help us improve

---

## 💬 Community

Join the conversation and connect with other plugin developers and users!

### Discussions
- **[General Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions)** - Community hub for all things plugins
- **[Announcements](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/announcements)** - Stay updated with the latest releases
- **[Ideas](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/ideas)** - Suggest new plugins or features
- **[Q&A](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/q-a)** - Get help from the community
- **[Show and Tell](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/show-and-tell)** - Share what you've built!

### Other Channels
- **[Discord](https://discord.com/invite/6PPFFzqPDZ)** - Claude Code Community (#claude-code channel)
- **[Issues](https://github.com/jeremylongshore/claude-code-plugins/issues)** - Report bugs or request features
- **[Pull Requests](https://github.com/jeremylongshore/claude-code-plugins/pulls)** - Contribute your own plugins

---

## Get Help

- **Questions?** - [Open a discussion](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/q-a)
- **Found a bug?** - [Report an issue](https://github.com/jeremylongshore/claude-code-plugins/issues)
- **Have an idea?** - [Share in Ideas](https://github.com/jeremylongshore/claude-code-plugins/discussions/categories/ideas)
- **Want to chat?** - [Join our Discord](https://discord.com/invite/6PPFFzqPDZ)

---

## Documentation Filing System

This repository uses a structured documentation filing system for all internal project documentation. All documentation files are stored in the **`000-docs/` directory** using a standardized naming convention.

### File Naming Format

```
NNN-CC-ABCD-short-description.ext
```

- **NNN** = Zero-padded sequence number (001-999)
- **CC** = Two-letter category code (PP, AT, DR, RA, etc.)
- **ABCD** = Four-letter document type (PROD, GUID, REPT, etc.)
- **short-description** = 1-4 words, kebab-case

### Examples

```
048-RA-INDX-audit-index.md                   # Audit index report
061-DR-REFF-vertex-ai-gemini-tiers.md       # Reference documentation
086-PP-PLAN-release-v1-2-0.md               # Release plan
```

**Full specification:** See the Document Filing System v3.0 in prompts-intent-solutions master-systems folder

---

<div align="center">

**[Star this repo](https://github.com/jeremylongshore/claude-code-plugins)** if you find it useful!

Made with dedication by the Claude Code community

**[Get Started Now](#quick-start)** | **[Browse Plugins](#all-plugins)** | **[Contribute](#contributing)**

</div>

---

**Status**: Public Beta | **Version**: 1.3.0 | **Last Updated**: November 8, 2025
