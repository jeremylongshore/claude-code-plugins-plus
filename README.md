# Claude Code Skills & Plugins Hub

[![Version](https://img.shields.io/badge/version-4.0.0-brightgreen)](CHANGELOG.md)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-240%20Skills-orange?logo=sparkles)](CHANGELOG.md)
[![Plugins](https://img.shields.io/badge/Total%20Plugins-258-blue)](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)
[![2025 Schema](https://img.shields.io/badge/2025%20Schema-Compliant-success?logo=checkmarx)](tutorials/skills/05-skill-validation.ipynb)
[![Tool Permissions](https://img.shields.io/badge/Tool%20Permissions-Secured-blueviolet?logo=shield)](tutorials/skills/02-skill-anatomy.ipynb)
[![Interactive Tutorials](https://img.shields.io/badge/Tutorials-11%20Notebooks-yellow?logo=jupyter)](tutorials/README.md)
[![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jeremylongshore/claude-code-plugins-plus-skills/blob/main/tutorials/)
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins-plus-skills?style=social)](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)

## 📖 Learning Lab

**Build production agent workflows with empirical verification** - Complete teaching system with guides, diagrams, and working examples.

**[→ Start Here: 5-Minute Introduction](workspace/lab/README.md)** | **[→ Visual Architecture Map](workspace/lab/VISUAL-MAP.md)** | **[→ System Summary](workspace/lab/BUILT-SYSTEM-SUMMARY.md)**

<table>
<tr>
<td width="50%">

**Guides** (90+ pages)
- [Mental Model (5 min)](workspace/lab/GUIDE-00-START-HERE.md)
- [Architecture Deep Dive (15 min)](workspace/lab/GUIDE-01-PATTERN-EXPLAINED.md)
- [Build Your Own (30 min)](workspace/lab/GUIDE-02-BUILDING-YOUR-OWN.md)
- [Debugging Tips (15 min)](workspace/lab/GUIDE-03-DEBUGGING-TIPS.md)
- [**Orchestration Pattern** (60 min)](workspace/lab/ORCHESTRATION-PATTERN.md) ⭐

**Interactive Tutorials** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jeremylongshore/claude-code-plugins-plus-skills/blob/main/tutorials/)
- [Skills Tutorials (5 notebooks)](tutorials/README.md#skills-tutorials-5-notebooks)
- [Plugins Tutorials (4 notebooks)](tutorials/README.md#plugins-tutorials-4-notebooks)
- [Orchestration Tutorials (2 notebooks)](tutorials/README.md#orchestration-tutorials-2-notebooks)

</td>
<td width="50%">

**Reference Implementation**
- [Complete 5-Phase Workflow](workspace/lab/schema-optimization/SKILL.md)
- [Phase Contracts & Agents](workspace/lab/schema-optimization/agents/)
- [Verification Scripts](workspace/lab/schema-optimization/scripts/)
- [Hands-On Exercise](workspace/lab/exercises/exercise-1-run-workflow.md)

</td>
</tr>
</table>

**What you'll learn:** Turn "LLM analyzed my code" into "LLM + script verified with evidence" - The pattern for production-ready agent systems.

---

**240 Agent Skills & 258 Plugins for Claude Code**

**v4.0.0:** Learning Lab with 11 interactive tutorials, 90+ pages of guides, and production workflow patterns.

**Latest:** [v4.0.0 Release](https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v4.0.0)

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install devops-automation-pack@claude-code-plugins-plus
```

⚡🪽 **[Buy me a Red Bull](https://buymeacoffee.com/jeremylongshore)** – Give these plugins wings and support ongoing development.

---

## 🙏 Contributors

**Huge thanks to our community contributors who make this marketplace better:**

- **[@alexfazio](https://github.com/alexfazio) (Alex Fazio)** - 🎓 Shared production agent workflow patterns and validation techniques that inspired the complete Learning Lab system (v4.0.0). His insights on empirical verification transformed how we teach agent development.
- **[@lukeslp](https://github.com/lukeslp) (Lucas Steuber)** - 🎉 **MASSIVE CONTRIBUTION:** Created geepers-agents with **51 specialized agents** for development workflows, deployment, quality audits, research, and game development - the largest single plugin contribution to date! ([#159](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/159))
- **[@beepsoft](https://github.com/beepsoft)** - Provided valuable feedback on skill implementations that inspired comprehensive quality enhancements across the entire plugin ecosystem ([#134](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/134))
- **[@CharlesWiltgen](https://github.com/CharlesWiltgen) (Charles Wiltgen)** - Created Axiom, battle-tested iOS development plugin with 13 production-ready skills for Swift/Xcode debugging and optimization ([#121](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/121))
- **[@aledlie](https://github.com/aledlie) (Alyshia Ledlie)** - Fixed 7 critical JSON syntax errors and added production CI/CD patterns from real-world debugging ([#117](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/117), [spotlight](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/118))
- **[@JackReis](https://github.com/JackReis) (Jack Reis)** - Contributed neurodivergent-visual-org plugin with ADHD-friendly Mermaid diagrams and accessibility features ([#106](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/106))
- **[@terrylica](https://github.com/terrylica) (Terry Li)** - Built prettier-markdown-hook with zero-config markdown formatting and comprehensive documentation ([#101](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/101))
- **[@clickmediapropy](https://github.com/clickmediapropy)** - Reported mobile horizontal scrolling bug, improving website UX ([#120](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/120))

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
Visit **[Claude Code Skills & Plugins Marketplace](https://claudecodeplugins.io/)** (CLI slug `claude-code-plugins-plus`) or explore [`plugins/`](./plugins/)

**Learn to build:**
See [Learning Paths](#-learning-paths) for step-by-step guides

---

## 🚀 Agent Skills - The Future of Claude Automation

**185 production-ready Agent Skills** that activate automatically based on your conversations:

### What are Agent Skills?
Agent Skills are intelligent automation tools that Claude Code can invoke automatically when relevant. Unlike plugins that need manual commands, **Skills detect when they're needed and activate seamlessly**.

### Why Skills Matter More
- **🔍 SEO Advantage:** "Claude Skills" gets 3x more searches than "Claude Plugins"
- **🎯 Auto-Activation:** No need to remember commands - Skills trigger automatically
- **🛡️ Tool Permissions:** Fine-grained control over what each skill can do
- **📈 Future-Proof:** Aligned with Anthropic's 2025 vision for AI agents

### Featured Skills Categories
- **🔧 DevOps Skills:** Automated CI/CD, deployment, monitoring
- **🔒 Security Skills:** Code auditing, vulnerability scanning, compliance
- **📊 Data Skills:** Analysis, visualization, reporting
- **🎨 Frontend Skills:** UI/UX improvements, responsive design, accessibility
- **🧪 Testing Skills:** Automated test generation, coverage analysis
- **📝 Documentation Skills:** Auto-documentation, API specs, tutorials

### Quick Stats
- **185 Skills** equipped across plugins
- **100% Anthropic 2025 Schema** compliant
- **Average skill size:** 3.2KB of intelligent automation
- **Categories covered:** 18 specialized domains

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
