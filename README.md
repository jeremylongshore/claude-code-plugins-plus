# Claude Code Plugins

[![Version](https://img.shields.io/badge/version-1.2.4-brightgreen)](CHANGELOG.md)
[![Plugins](https://img.shields.io/badge/plugins-234-blue)](https://github.com/jeremylongshore/claude-code-plugins)
[![Agent Skills](https://img.shields.io/badge/Agent%20Skills-168%20plugins-orange?logo=sparkles)](CHANGELOG.md#123---2025-10-23)
[![Spec Compliant](https://img.shields.io/badge/Anthropic%20Spec-v1.0%20Compliant-success?logo=checkmarx)](https://github.com/anthropics/skills/blob/main/agent_skills_spec.md)
[![NEW](https://img.shields.io/badge/NEW-Agent%20Context%20Manager-blueviolet?logo=sparkles)](plugins/productivity/agent-context-manager/)
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins?style=social)](https://github.com/jeremylongshore/claude-code-plugins)

**234 production-ready Claude Code plugins for automation, development, and AI workflows.**
🎯 **NEW in v1.2.4:** **Excel Analyst Pro** - Professional financial modeling toolkit with auto-invoked Skills and Excel MCP integration!

**Latest:** [v1.2.4 Release](https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v1.2.4) - Excel Analyst Pro plugin for DCF models, LBO analysis, and financial modeling

```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install devops-automation-pack@claude-code-plugins-plus
```

💖 **[Sponsor this project](docs/sponsor/)** - Get early access, premium plugins, and priority support

---

## 🎯 Featured: Excel Analyst Pro

**Professional Financial Modeling with Auto-Invoked Skills**

The new [Excel Analyst Pro](plugins/business-tools/excel-analyst-pro/) plugin brings investment banking-grade financial modeling to Claude Code with automatic Skills activation and Excel MCP integration.

```bash
# Install the plugin
/plugin install excel-analyst-pro@claude-code-plugins-plus

# Build a DCF model with natural language
"Build a 5-year DCF model for a SaaS company with 30% revenue growth"

# Create an LBO analysis
/build-lbo

# Analyze budget variance
/analyze-variance
```

**Four Auto-Invoked Skills:**
- **DCF Modeler**: Build discounted cash flow valuation models
- **LBO Modeler**: Create leveraged buyout analysis with debt schedules
- **Variance Analyzer**: Generate executive variance reports
- **Pivot Wizard**: Create pivot tables with natural language

**Why This Matters:**
- Build complex financial models without remembering formulas
- Investment banking-grade templates and best practices
- Local Excel processing - no cloud upload required
- Perfect timing with Anthropic's Claude for Excel announcement
- Auto-invoked Skills activate automatically when needed
- Comprehensive documentation with real-world examples

[Read the full documentation →](plugins/business-tools/excel-analyst-pro/README.md)

---

## 🆕 What's New in v1.2.3

### 🎯 Agent Context Manager Plugin

**NEW**: Automatic AGENTS.md detection and loading alongside CLAUDE.md

- **Plugin**: [agent-context-manager](plugins/productivity/agent-context-manager/)
- **Category**: Productivity
- **Agent Skills**: 1 (agent-context-loader with 200+ line documentation)
- **Slash Commands**: 1 (/sync-agent-context)
- **Hooks**: 2 (onSessionStart, onDirectoryChange)

**Features**:
- Proactive auto-loading when AGENTS.md is detected
- Directory change hooks with formatted visual feedback
- Manual sync command for permanent CLAUDE.md merge
- Three-layer redundancy system
- Comprehensive documentation (400+ lines)
- 100% Anthropic Agent Skills Spec v1.0 compliant
- Exceeds Anthropic standards for documentation depth

**Updates**:
- Plugin count: 239 → 240
- Agent Skills count: 167 → 168

[Install now →](plugins/productivity/agent-context-manager/)

---

## What's New in v1.2.1

### ✅ Anthropic Official Spec v1.0 Compliance

**All 167 Agent Skills now comply with [Anthropic's official Agent Skills Spec v1.0](https://github.com/anthropics/skills/blob/main/agent_skills_spec.md)** released October 16, 2025.

**What Changed:**
- **Structure migration**: Moved from `skills/skill-adapter/` to `skills/{descriptive-name}/` per Anthropic specification
- **Name format updated**: Title Case → hyphen-case (e.g., "Database Backup Automator" → "database-backup-automator")
- **100% spec compliant**: All SKILL.md files follow official format requirements
- **Forward compatible**: Ensures compatibility with future Claude Code releases
- **No breaking changes**: Skills continue to work exactly as before

**Quality Assessment:**
Our comprehensive internal analysis shows our 167 skills **exceed Anthropic's 17 official examples** in documentation depth, trigger phrase specificity, and workflow detail.

**Automated with:**
- `scripts/migrate-skills.py` - Structure migration tool
- `scripts/fix-skill-names.py` - Batch conversion tool with validation
- 167 skills migrated and validated, 100% success rate

---

## What's New in v1.2.0

### 🎯 Agent Skills Quality Enhancement

**159 high-quality Agent Skills** generated via production-grade AI batch processing with Vertex AI Gemini 2.0 Flash. Achieved 100% success rate at $0 cost with comprehensive documentation.

**Key Achievements:**
- 231 plugins enhanced (98% of marketplace)
- 100% success rate, zero failures
- $0 processing cost (Vertex AI free tier)
- 13 documentation files + 2 blog posts
- Agent Skills 17x larger than Anthropic's examples (3,210 bytes avg vs 500 bytes)

**Technical Deep-Dives:**
- 📖 [Batch Processing Implementation](https://startaitools.com/posts/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/)
- 💼 [Systems Architecture](https://jeremylongshore.com/posts/scaling-ai-systems-production-batch-processing-with-built-in-disaster-recovery/)

### 🧠 How Agent Skills Work

Agent Skills are **automatic capabilities** that Claude activates based on your conversation context - no commands needed!

**File Structure:**
```
your-plugin/
└── skills/
    └── skill-adapter/
        └── SKILL.md       # Agent skill definition
```

**SKILL.md Format (Spec v1.0 Compliant):**
```markdown
---
name: database-backup-automator
description: |
  Automatically handles database backup operations when user mentions
  backup, restore, or data protection needs.
---

## What This Skill Does
Multi-phase database backup workflow with validation...

## When It Activates
- "I need to backup my database"
- "How do I restore from backup?"
- "Set up automated backups"
```

**How It Works in Practice:**

1. **You install a plugin:**
   ```bash
   /plugin install postgres-backup-pro@claude-code-plugins-plus
   ```

2. **You mention your need naturally:**
   > "I need to backup my production PostgreSQL database before the migration"

3. **Claude automatically:**
   - Detects the backup skill is relevant
   - Activates `Database Backup Automator` skill
   - Guides you through: connection → backup → verification → storage
   - No slash commands needed!

4. **You get expert help:**
   - Multi-phase workflows (analysis → execution → validation)
   - Code examples and error handling
   - Best practices built-in
   - Context-aware recommendations

**Key Difference from Commands:**
- **Commands:** You type `/backup-database` explicitly
- **Skills:** Claude recognizes "I need to backup" and helps automatically
- **Result:** More natural, conversational development workflow

**Categories with 100% Agent Skills Coverage:**
- ✅ 27 AI/ML plugins - Model training, data pipelines, MLOps
- ✅ 25 Database plugins - Migrations, optimization, backups
- ✅ 27 Security plugins - Compliance, vulnerability scanning, audits
- ✅ 25 Testing plugins - E2E, integration, load testing
- ✅ 28 DevOps plugins (96.6%) - Infrastructure, CI/CD, deployments
- ✅ 24 Performance plugins (96.0%) - Monitoring, profiling, optimization

**Quality Metrics:**
- Average SKILL.md size: 3,210 bytes (17x larger than Anthropic's 500-byte examples)
- Includes: Multi-phase workflows, code examples, error handling, progressive disclosure
- YAML validation: 99.4% pass rate

[**Read full changelog →**](CHANGELOG.md#120---2025-10-20)

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

[Learn more about Agent Skills →](backups/HOW_AGENT_SKILLS_WORK.md)

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

This marketplace contains **three types of extensions** that work differently:

### 1. AI Instruction Plugins (97% of marketplace)
- **What they are**: Markdown instructions that guide Claude's behavior
- **How they work**: Tell Claude HOW to perform tasks using its built-in capabilities
- **Examples**: DevOps pack, Security pack, API development tools
- **Count**: ~221 plugins
- **No external code execution** - work entirely through Claude's interpretation

### 2. MCP Server Plugins (2% of marketplace)
- **What they are**: TypeScript/JavaScript applications
- **How they work**: Run as separate Node.js processes that Claude can communicate with
- **Examples**: project-health-auditor, conversational-api-debugger, domain-memory-agent
- **Count**: 5 plugins (21 MCP tools total)
- **Actual compiled code** - 13-26KB of executable JavaScript per plugin

### 3. Agent Skills 🆕 (< 1% of marketplace)
- **What they are**: Model-invoked capabilities Claude automatically uses when relevant
- **How they work**: Claude decides when to activate based on conversation context
- **Example**: Skills Powerkit (5 skills: plugin creator, validator, manager, auditor, version bumper)
- **Count**: 1 plugin
- **Invocation**: Automatic - you say "create a plugin" and Claude uses the skill
- **NEW**: Launched October 16, 2025 by Anthropic

**Skills vs Commands:** Commands require explicit `/command` trigger. Skills activate automatically based on what you're asking for.

All three types are **fully functional** but operate through different mechanisms. Plugins can bundle Skills, Commands, Agents, and MCP servers together.

---

## 🎉 v1.0.40 - 227 PLUGINS AVAILABLE!

**The Claude Code Plugin Hub continues to grow!** Now with **227 production-ready plugins** across 15 categories, including the first Skills-based meta-plugin for automated plugin management.

### Plugin Packs (62 AI Instruction Templates)

> **Note**: These packs contain AI instruction templates, not traditional executable code. They enhance Claude's capabilities through detailed guidance and templates.

| Pack | Templates | Description | Type |
|------|-----------|-------------|------|
| **devops-automation-pack** | 25 | Git workflows, CI/CD guidance, Docker best practices, Kubernetes patterns | AI Instructions |
| **security-pro-pack** | 10 | OWASP auditing steps, compliance checklists, threat modeling guides | AI Instructions |
| **fullstack-starter-pack** | 15 | React patterns, API scaffolding, database schema templates | AI Instructions |
| **ai-ml-engineering-pack** | 12 | Prompt optimization, LLM integration patterns, RAG architectures | AI Instructions |

```bash
# Install any pack
/plugin install devops-automation-pack@claude-code-plugins-plus
/plugin install security-pro-pack@claude-code-plugins-plus
/plugin install fullstack-starter-pack@claude-code-plugins-plus
/plugin install ai-ml-engineering-pack@claude-code-plugins-plus
```

---

## All Plugins

### MCP Server Plugins (5 plugins with Executable Code)

> **Real Code**: These plugins contain compiled TypeScript/JavaScript that runs as separate Node.js processes.

| Plugin | Description | Tools | Code Size | Install |
|--------|-------------|-------|-----------|---------|
| **project-health-auditor** | Code health analysis: complexity + churn + tests | 4 | 13KB TS | `/plugin install project-health-auditor@claude-code-plugins-plus` |
| **conversational-api-debugger** | Debug REST APIs with OpenAPI specs and HTTP logs | 4 | 26KB JS | `/plugin install conversational-api-debugger@claude-code-plugins-plus` |
| **domain-memory-agent** | Knowledge base with TF-IDF semantic search | 6 | Compiled | `/plugin install domain-memory-agent@claude-code-plugins-plus` |
| **design-to-code** | Convert Figma/screenshots to React/Svelte/Vue | 3 | Compiled | `/plugin install design-to-code@claude-code-plugins-plus` |
| **workflow-orchestrator** | DAG-based workflow automation | 4 | Compiled | `/plugin install workflow-orchestrator@claude-code-plugins-plus` |

[View MCP Server Documentation →](./MCP-SERVERS-STATUS.md)

### AI Agency Toolkit (6 Template Plugins)

> **Templates**: These provide workflow templates and configuration patterns for Claude to interpret.

| Plugin | Description | Type | Install |
|--------|-------------|------|---------|
| **n8n-workflow-designer** | n8n workflow JSON templates | Templates | `/plugin install n8n-workflow-designer@claude-code-plugins-plus` |
| **make-scenario-builder** | Make.com scenario configurations | Templates | `/plugin install make-scenario-builder@claude-code-plugins-plus` |
| **zapier-zap-builder** | Zapier automation templates | Templates | `/plugin install zapier-zap-builder@claude-code-plugins-plus` |
| **discovery-questionnaire** | Client discovery question sets | Templates | `/plugin install discovery-questionnaire@claude-code-plugins-plus` |
| **sow-generator** | Statement of Work templates | Templates | `/plugin install sow-generator@claude-code-plugins-plus` |
| **roi-calculator** | ROI calculation formulas | Templates | `/plugin install roi-calculator@claude-code-plugins-plus` |

### Production Plugins (2 plugins)

| Plugin | Description | Install |
|--------|-------------|---------|
| **git-commit-smart** | AI-powered conventional commit messages | `/plugin install git-commit-smart@claude-code-plugins-plus` |
| **overnight-dev** | Autonomous overnight development with TDD enforcement | `/plugin install overnight-dev@claude-code-plugins-plus` |

### Example Plugins (3 plugins)

| Plugin | Description | Install |
|--------|-------------|---------|
| **hello-world** | Simple greeting command - perfect for learning | `/plugin install hello-world@claude-code-plugins-plus` |
| **formatter** | Auto-formats code after edits using hooks | `/plugin install formatter@claude-code-plugins-plus` |
| **security-agent** | Expert security agent for vulnerability detection | `/plugin install security-agent@claude-code-plugins-plus` |

---

## What Are Claude Code Plugins?

Claude Code plugins extend Claude's capabilities through two approaches:

### Plugin Components:
- **Slash Commands** - Custom shortcuts that trigger Claude actions or templates
- **Subagents** - Specialized AI instruction sets for specific domains
- **Hooks** - Automation scripts that trigger on events (file edits, tool usage)
- **MCP Servers** - External Node.js applications that provide tools to Claude

### How They Work:
- **AI Instruction Plugins**: Work by providing Claude with detailed guidance, templates, and patterns to follow (majority of plugins)
- **MCP Server Plugins**: Run actual TypeScript/JavaScript code in separate processes that Claude can call (5 plugins)

Both types are valid Claude Code plugins - they just operate through different mechanisms.

**Released**: October 2025 (Public Beta)
**Official Docs**: https://docs.claude.com/en/docs/claude-code/plugins

---

## MCP Plugin Details

### project-health-auditor

**Identify technical debt hot spots with multi-dimensional analysis**

```bash
/plugin install project-health-auditor@claude-code-plugins-plus
/analyze /path/to/repo  # Comprehensive analysis workflow
```

**What it does**:
- Code Complexity: Cyclomatic complexity analysis with health scores
- Git Churn: Identifies frequently changing files (hot spots)
- Test Coverage: Maps source files to tests, finds gaps
- Hot Spots: Finds files with high complexity + high churn + no tests

**MCP Tools**: `list_repo_files`, `file_metrics`, `git_churn`, `map_tests`

---

### conversational-api-debugger

**Debug REST API failures using OpenAPI specs and HTTP logs**

```bash
/plugin install conversational-api-debugger@claude-code-plugins-plus
/debug-api  # Guided debugging workflow
```

**What it does**:
- OpenAPI Parser: Load and analyze API specs (JSON/YAML)
- HAR Support: Import browser DevTools HTTP logs
- Failure Analysis: Root cause identification with severity
- cURL Generation: Create reproducible test commands

**MCP Tools**: `load_openapi`, `ingest_logs`, `explain_failure`, `make_repro`

---

### domain-memory-agent

**Knowledge base with TF-IDF semantic search (no ML dependencies)**

```bash
/plugin install domain-memory-agent@claude-code-plugins-plus
```

**What it does**:
- Document Storage: Store documents with tags and metadata
- Semantic Search: TF-IDF based relevance ranking
- Summarization: Extractive summaries with caching
- Organization: Tag-based filtering and categorization

**MCP Tools**: `store_document`, `semantic_search`, `summarize`, `list_documents`, `get_document`, `delete_document`

**Perfect for**: RAG systems, documentation search, knowledge management

---

### design-to-code

**Convert Figma designs and screenshots into production-ready code**

```bash
/plugin install design-to-code@claude-code-plugins-plus
```

**What it does**:
- Figma Parsing: Extract components from Figma JSON exports
- Screenshot Analysis: Analyze UI layouts from images
- Multi-Framework: Generate React, Svelte, or Vue components
- A11y Built-in: ARIA labels, semantic HTML, keyboard navigation

**MCP Tools**: `parse_figma`, `analyze_screenshot`, `generate_component`

---

### workflow-orchestrator

**DAG-based workflow automation with parallel execution**

```bash
/plugin install workflow-orchestrator@claude-code-plugins-plus
```

**What it does**:
- DAG Execution: Directed Acyclic Graph task dependencies
- Parallel Tasks: Execute independent tasks concurrently
- Run History: Track all workflow executions
- Status Monitoring: Real-time progress tracking

**MCP Tools**: `create_workflow`, `execute_workflow`, `get_workflow`, `list_workflows`

**Perfect for**: CI/CD pipelines, data ETL, multi-stage deployments

---

## Plugin Pack Details

### DevOps Automation Pack (25 plugins)

**Complete DevOps automation suite**

**Component Breakdown**:
- 01-git-workflow: 5 commands
- 02-ci-cd: 5 commands, 1 agent
- 03-docker: 3 commands, 1 agent
- 04-kubernetes: 3 commands, 1 agent
- 05-terraform: 3 commands, 1 agent
- 06-deployment: 1 command, 1 agent

**Total**: 20 commands, 5 agents

**Features**:
- Git workflow automation and branching strategies
- CI/CD pipeline design and optimization
- Docker containerization and optimization
- Kubernetes cluster management and deployment
- Terraform infrastructure as code
- Deployment automation and monitoring

```bash
/plugin install devops-automation-pack@claude-code-plugins-plus
```

---

### Security Pro Pack (10 plugins)

**Professional security toolkit**

**Component Breakdown**:
- 01-core-security: 1 command, 2 agents
- 02-compliance: 1 command, 1 agent
- 03-cryptography: 1 command, 1 agent
- 04-infrastructure-security: 2 commands, 1 agent

**Total**: 5 commands, 5 agents

**Features**:
- OWASP auditing and penetration testing
- HIPAA, PCI DSS, GDPR, SOC 2 compliance checking
- Cryptography audit and key management review
- Threat modeling and container scanning
- API security and infrastructure hardening

```bash
/plugin install security-pro-pack@claude-code-plugins-plus
```

---

### Fullstack Starter Pack (15 plugins)

**Complete fullstack development toolkit**

**Component Breakdown**:
- 01-frontend: 2 commands, 2 agents
- 02-backend: 2 commands, 2 agents
- 03-database: 2 commands, 1 agent
- 04-integration: 3 commands, 1 agent

**Total**: 9 commands, 6 agents

**Features**:
- React components and UI/UX design
- Express/FastAPI scaffolding and API patterns
- PostgreSQL schemas and Prisma ORM
- Authentication setup and environment config
- Full project scaffolding and deployment

**Perfect for**: Bootcamp grads, junior developers, rapid prototyping

```bash
/plugin install fullstack-starter-pack@claude-code-plugins-plus
```

---

### AI/ML Engineering Pack (12 plugins)

**Professional AI/ML engineering toolkit**

**Component Breakdown**:
- 01-prompt-engineering: 1 command, 2 agents
- 02-llm-integration: 1 command, 2 agents
- 03-rag-systems: 1 command, 2 agents
- 04-ai-safety: 1 command, 2 agents

**Total**: 4 commands, 8 agents

**Features**:
- Prompt optimization and A/B testing (30-50% cost reduction)
- Multi-provider LLM integration and model evaluation
- RAG system design and vector database setup (Pinecone, Weaviate)
- AI safety guardrails and fine-tuning preparation
- Production-ready patterns for AI products

**Requirements**: Claude Code CLI, Anthropic or OpenAI API key

```bash
/plugin install ai-ml-engineering-pack@claude-code-plugins-plus
```

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

**Full specification:** See [`000-docs/000-DR-REFF-filing-system-standard-v2.md`](000-docs/000-DR-REFF-filing-system-standard-v2.md)

---

<div align="center">

**[Star this repo](https://github.com/jeremylongshore/claude-code-plugins)** if you find it useful!

Made with dedication by the Claude Code community

**[Get Started Now](#quick-start)** | **[Browse Plugins](#all-plugins)** | **[Contribute](#contributing)**

</div>

---

**Status**: Public Beta | **Version**: 1.2.0 | **Last Updated**: October 20, 2025
