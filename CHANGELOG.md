# Changelog

All notable changes to the Claude Code Plugins Marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-10-10

### 🔥 MCP Server Plugins Release

This release adds **5 production-ready MCP (Model Context Protocol) plugins** with **21 total MCP tools**, establishing this marketplace as the premier destination for advanced Claude Code plugins.

### Added

#### 🤖 MCP Plugins (5 new plugins, 21 tools)

- **project-health-auditor** - Multi-dimensional code health analysis
  - 4 MCP tools: `list_repo_files`, `file_metrics`, `git_churn`, `map_tests`
  - Cyclomatic complexity analysis with health scores (0-100)
  - Git churn tracking - identifies frequently changing files
  - Test coverage mapping - finds gaps in test coverage
  - TF-IDF based technical debt hot spot identification
  - 24 comprehensive tests (100% passing)
  - `/analyze` command with guided workflow

- **conversational-api-debugger** - REST API debugging with OpenAPI integration
  - 4 MCP tools: `load_openapi`, `ingest_logs`, `explain_failure`, `make_repro`
  - OpenAPI 3.x spec parsing and validation
  - HAR file ingestion from browser DevTools
  - Intelligent failure analysis with severity scoring
  - cURL/HTTPie/fetch reproduction command generation
  - Status code knowledge base (4xx, 5xx explanations)
  - 36 comprehensive tests (100% passing)
  - `/debug-api` command with expert agent

- **domain-memory-agent** - Knowledge base with semantic search
  - 6 MCP tools: `store_document`, `semantic_search`, `summarize`, `list_documents`, `get_document`, `delete_document`
  - TF-IDF semantic search (no external ML dependencies)
  - Extractive summarization with caching
  - Tag-based filtering and organization
  - Full CRUD operations on knowledge base
  - 35+ comprehensive tests (100% passing)
  - Perfect for RAG systems and documentation search

- **design-to-code** - Convert designs to components
  - 3 MCP tools: `parse_figma`, `analyze_screenshot`, `generate_component`
  - Figma JSON export parsing
  - Multi-framework support (React, Svelte, Vue)
  - Built-in accessibility (ARIA labels, semantic HTML, keyboard navigation)
  - Component code generation with TypeScript support
  - Production-ready implementation

- **workflow-orchestrator** - DAG-based workflow automation
  - 4 MCP tools: `create_workflow`, `execute_workflow`, `get_workflow`, `list_workflows`
  - Directed Acyclic Graph (DAG) execution engine
  - Parallel task execution for independent steps
  - Task dependency management and validation
  - Workflow run history tracking
  - Real-time status monitoring
  - Perfect for CI/CD pipelines and ETL workflows

#### 🎨 Additional Plugins

- **overnight-dev** - Autonomous overnight development with TDD enforcement
  - Run Claude autonomously for 6-8 hours overnight
  - Git hooks enforce TDD (pre-commit testing and linting)
  - Conventional commits enforcement
  - Iterative debugging until tests pass
  - Wake up to fully tested features

- **AI Agency Toolkit** (6 plugins)
  - **n8n-workflow-designer** - Design complex n8n workflows with AI
  - **make-scenario-builder** - Create Make.com scenarios
  - **zapier-zap-builder** - Build multi-step Zapier Zaps
  - **discovery-questionnaire** - Generate client discovery questions
  - **sow-generator** - Professional Statements of Work
  - **roi-calculator** - Calculate automation ROI

#### 🏗️ Infrastructure

- **Astro Marketplace Website** (v5.14.4)
  - High-performance static site with Astro + Tailwind CSS 4.x
  - TypeScript content collections with type safety
  - Plugin catalog with search and filtering
  - Category-based organization
  - Installation instructions and examples
  - Automated GitHub Pages deployment

- **pnpm Workspace** - Monorepo management
  - Centralized dependency management
  - Shared TypeScript configuration
  - Build scripts across all plugins
  - Test runner integration

- **GitHub Actions CI/CD**
  - Automated marketplace deployment to GitHub Pages
  - Build verification on push
  - Node.js 22 + pnpm setup

#### 📖 Documentation

- **MCP-SERVERS-STATUS.md** - Complete MCP server configuration reference
  - All 5 server configurations documented
  - Verification commands
  - Testing instructions
  - MCP protocol compliance checklist

- **PHASE-1-COMPLETION-REPORT.md** - Comprehensive Phase 1 summary
  - Detailed plugin metrics
  - Success criteria validation
  - Known limitations
  - Future roadmap

- **RELEASE-PLAN.md** - Complete release plan with Mermaid diagrams
  - Architecture overview
  - Deployment flow
  - Timeline Gantt chart
  - Pre-release checklist
  - Rollback plan

### Changed

- **README.md** - Updated with prominent MCP plugins section
- **Marketplace catalog** - Now includes 16 total plugins (was 12)
- **Statistics** - Updated to reflect 5 MCP plugins with 21 tools

### Infrastructure

- **Total Plugins**: 16 (5 MCP + 2 production + 6 AI agency + 3 examples)
- **Total MCP Tools**: 21 across 5 MCP servers
- **Test Coverage**: 95+ tests (100% passing)
- **Code Written**: 2,330+ lines of TypeScript
- **Build Status**: 100% success rate

### Metrics

- **MCP Plugins**: 5
- **MCP Tools**: 21
- **Production Plugins**: 2 (git-commit-smart, overnight-dev)
- **AI Agency Plugins**: 6
- **Example Plugins**: 3
- **Templates**: 4
- **Documentation Files**: 11+
- **Tests**: 95+ (100% passing)

### Technology Stack

- **MCP Servers**: Node.js 20+, TypeScript 5.6+, Zod 3.23+
- **Testing**: Vitest 2.1.9 with 80%+ coverage targets
- **Marketplace**: Astro 5.14.4, Tailwind CSS 4.x, TypeScript
- **Build**: pnpm workspace, strict TypeScript mode
- **Deployment**: GitHub Actions, GitHub Pages

### Migration Notes

This release represents a major expansion of the marketplace with production-ready MCP plugins that demonstrate advanced Claude Code capabilities. All plugins are fully tested, documented, and ready for production use.

**Key Achievement**: First comprehensive MCP plugin collection in the Claude Code ecosystem.

---

## [1.0.0] - 2025-10-10

### 🎉 Initial Open-Source Release

**BREAKING CHANGE**: Complete repository restructure from commercial Gumroad model to open-source GitHub marketplace.

### Added

#### 🏆 Production Plugin
- **git-commit-smart** - AI-powered conventional commit message generator
  - Analyzes staged changes and generates contextual commit messages
  - Supports conventional commits standard (feat, fix, docs, etc.)
  - Interactive confirmation workflow
  - Breaking change detection
  - `/gc` shortcut for fast workflow
  - 1,500+ words of comprehensive documentation

#### 📚 Example Plugins (Educational)
- **hello-world** - Basic slash command demonstration
- **formatter** - PostToolUse hooks demonstration
- **security-agent** - Specialized AI subagent demonstration

#### 🎨 Plugin Templates
- **minimal-plugin** - Bare minimum plugin structure
- **command-plugin** - Plugin with slash commands
- **agent-plugin** - Plugin with AI subagent
- **full-plugin** - Complete plugin with commands, agents, and hooks

#### 🔍 Quality Assurance Tools
- `check-frontmatter.py` - Python YAML frontmatter validator
- `validate-all.sh` - Comprehensive plugin validation (JSON, frontmatter, shortcuts, permissions)
- `test-installation.sh` - Plugin installation testing in isolated environment

#### 📖 Documentation
- Comprehensive README.md with installation and usage
- CONTRIBUTING.md with community guidelines
- Detailed plugin development guide
- Security best practices
- Monetization alternatives guide

#### 🤝 GitHub Integration
- GitHub Actions workflow for plugin validation
- Issue templates (plugin submission, bug report)
- Pull request template
- GitHub Sponsors configuration (FUNDING.yml)

### Changed

- **Repository Model**: Pivoted from commercial plugin packs to open-source community marketplace
- **Monetization Strategy**: GitHub Sponsors + consulting/training instead of direct plugin sales
- **Distribution Model**: GitHub-based marketplace catalog (JSON) instead of Gumroad
- **Focus**: Community-driven growth and first-mover advantage

### Removed

- Commercial plugin packs infrastructure (`website/products/`)
- Gumroad sales integration (`website/marketing-site/`)
- Build automation for commercial distribution (`website/scripts/`)
- Internal business reports (`website/000-docs/`)

### Infrastructure

- Marketplace catalog: `.claude-plugin/marketplace.json` with 4 plugins
- Plugin validation CI/CD pipeline
- GitHub Sponsors monetization framework
- Community contribution workflow

### Metrics

- **Production Plugins**: 1 (git-commit-smart)
- **Example Plugins**: 3 (educational)
- **Templates**: 4 (starter templates)
- **Validation Scripts**: 3 (quality assurance)
- **Documentation Pages**: 6+ (comprehensive guides)

### Migration Notes

This release represents a complete pivot from a commercial model to an open-source community marketplace. The restructure was motivated by:

1. **Distribution Reality**: Claude Code plugin marketplace doesn't support commercial sales
2. **Community Value**: Open-source model better serves developer community
3. **First-Mover Advantage**: Launched days after Anthropic's plugin announcement (October 2025)
4. **Sustainable Model**: GitHub Sponsors + consulting provides sustainable revenue

All quality work (validation systems, templates, production plugin) was preserved and migrated to the new structure.

---

## Release Links

- [1.1.0 - 2025-10-10](#110---2025-10-10) - **Latest** - MCP Plugins Release
- [1.0.0 - 2025-10-10](#100---2025-10-10) - Initial Open-Source Release

---

**Repository**: https://github.com/jeremylongshore/claude-code-plugins
**Installation**: `/plugin marketplace add jeremylongshore/claude-code-plugins`
**Flagship Plugin**: `/plugin install git-commit-smart@claude-code-plugins`
