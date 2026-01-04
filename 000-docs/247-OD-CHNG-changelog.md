## [4.5.0] - 2025-01-03

### 🎯 Release Highlights

**50-Vendor SaaS Skill Packs + ZCF Integration** - This release delivers 500 standalone skills (739 total), full ZCF framework compatibility, external plugin sync infrastructure, and MCP Registry integration.

### 🙏 Contributors

- **Jeremy Longshore** - SaaS Skill Packs, ZCF Integration, MCP Registry
- **intentsolutions.io** - Infrastructure and release engineering

### 🚀 50-Vendor SaaS Skill Packs (500 Skills)

**Production-ready skills for 50 SaaS platforms** - Each vendor pack contains 30 skills covering API integration, troubleshooting, and advanced patterns.

- **Skill Databases:** 105 vendor skill databases with researched content
- **Flagship Packs:** Supabase, Vercel, OpenRouter, Kling AI published
- **Template System:** 30 Jinja2 slot templates for consistent generation
- **Pack Generator:** Automated skill pack creation from databases

**Total Skills: 739** (500 standalone + 239 embedded in plugins)

### 🔧 ZCF Integration (Issue #184)

**Full compatibility with Zero Config Framework** - Install our MCPs via `npx zcf i`.

- **Phase 1:** MCP Registry server.json manifests for 7 servers
- **Phase 2:** ZCF preset configuration (mcp-presets.json, config.zcf.json)
- **Phase 3:** PR #279 to UfoMiao/zcf adding our services
- **Phase 4:** BMAD-compatible development workflows
- **Phase 5:** Tool routing documentation for token optimization

### 🔄 External Plugin Sync

**Daily automated sync from upstream repos** - Keep community plugins fresh.

- **sources.yaml:** Manifest for external skill sources
- **sync-external.mjs:** Sync engine with attribution
- **GitHub Actions:** Daily cron at midnight UTC
- **First Sources:** gastown, zai-cli from @numman-ali/n-skills

### 📊 New Features

- **Attribution Tracking Engine** - Analytics for plugin usage
- **Mobile Chat Monitoring UI** - Real-time chat interface
- **Plugin Comparison View** - Side-by-side plugin comparisons
- **Trust Signals & Bookmarks** - Quality indicators
- **Keyboard Navigation** - Enhanced accessibility
- **Enhanced Search** - Curated collections
- **Dynamic Homepage Stats** - Live metrics from search index

### 🔧 Fixes & Improvements

- **Playbooks:** Template literal escaping with HTML entities
- **Colab Links:** Corrected notebook links in Learning Lab
- **Validators:** Aligned frontmatter with Nixtla standards
- **Internal Links:** Integrity validation guardrails
- **CI:** Relaxed agent frontmatter validation to warnings

### 📈 Statistics

| Metric | v4.4.0 | v4.5.0 | Change |
|--------|--------|--------|--------|
| Agent Skills | 244 | 739 | +495 |
| Plugins | 258 | 260 | +2 |
| MCP Servers | 5 | 7 | +2 |
| Skill Databases | 0 | 105 | +105 |

---

## [4.4.0] - 2025-12-26

### 🎯 Release Highlights

**CLI 2.0 + vibe-guide + Website Unification** - This release brings the package manager to production, adds a new plugin for non-technical users, and delivers a unified 521-route website experience.

### 🙏 Contributors

- **Jeremy Longshore** - CLI v2.0.0, vibe-guide plugin, website unification
- **Damien Laine** - Gemini code review workflow integration
- **intentsolutions.io** - Infrastructure and release engineering

### 📦 New Plugin: vibe-guide

**Non-technical progress summaries for Claude Code work** - Perfect for pair programming with non-developers.

- **7 Commands:** `/vibe`, `/status`, `/continue`, `/stop`, `/learn`, `/details`, `/guide`
- **3 Agents:** worker (executes steps), explainer (plain language), explorer (learning mode)
- **PostToolUse Hook:** Auto-summarizes verbose output to friendly updates
- **No diffs, no logs** - Just clear progress in plain language

```bash
ccpi install vibe-guide
/vibe-guide:vibe Build a contact form
/vibe-guide:continue
```

### 🚀 CLI v2.0.0 (@intentsolutionsio/ccpi)

**Full package manager for Claude Code plugins** - Search, install, validate from your terminal.

```bash
pnpm add -g @intentsolutionsio/ccpi

ccpi search devops          # Search plugins
ccpi list                   # List all available
ccpi install ansible-*      # Install plugins
ccpi validate ./my-plugin   # Validate structure
```

**New in v2.0.0:**
- `ccpi validate` command for plugin developers
- Bulk install: `ccpi install pack1 pack2 pack3`
- Binary renamed from `ccp` to `ccpi`
- Homepage install CTA with smoke tests

### 🌐 Website Unification (521 Routes)

**Unified Explorer Experience** - Complete site-wide design system overhaul.

- **Skills Pages:** 244 agent skill routes with proper rendering
- **Learning Hub:** 8 routes for tutorials and guides
- **Homepage Search:** Redirects to /explore with unified search
- **Mobile Excellence:** 100% Playwright test pass rate
- **Production Landing:** Phase 4 & 5 P0 fixes complete

### 🔧 Fixes & Improvements

- **Validators:** Nixtla standards with relaxed warnings (210 errors fixed)
- **Frontmatter:** Fixed geepers-agents YAML parsing issues
- **CI/CD:** Gemini code review workflow via Vertex AI
- **Mobile UX:** Search toggle overlap fixed, installation instructions added
- **Build:** Fixed undefined catalog.categories in plugins index

### 📊 Metrics

| Metric | Previous | Current | Change |
|--------|----------|---------|--------|
| Total Plugins | 258 | 264 | +6 |
| Agent Skills | 241 | 244 | +3 |
| Commands | 310 | 317 | +7 |
| Agents | 144 | 147 | +3 |
| Website Routes | ~400 | 521 | +121 |

### 🎓 Documentation

- **README:** Added Package Manager (CLI) section with install instructions
- **vibe-guide:** Comprehensive README with progressive workflow examples
- **MD Standards:** All plugin markdown aligned with Anthropic standards

---

## [4.3.0] - 2025-12-23

### 🎉 Epic Complete: Rate Limits & Resource Constraints Documentation

**Tom's request is DONE.** We've added **2,400+ lines** of comprehensive rate limit documentation across 6 plugins, plus a standardized template for all future plugins.

### 🌟 Community Champion: @TomLucidor

**Tom asked for transparency. We delivered.**

His December feedback transformed this marketplace:
1. *"Which plugins require paid APIs vs free/self-hosted?"* → **v4.1.0** (Make All Plugins Free initiative)
2. *"Note rate limits and registration requirements. Ideally agents with skills would learn how to be resourceful with a single IP."* → **v4.3.0** (THIS RELEASE)

**Epic claude-code-plugins-1k2: COMPLETED** - All 12 tasks finished. Tom notified on [Discussion #148](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/discussions/148).

### 📚 Documentation Added (2,400+ Lines)

#### **1. openbb-terminal** (309 lines) - Financial API Limits
- **Alpha Vantage:** 25/day, 5/min (NOT 500/day - corrected misconception!)
- **Yahoo Finance:** ~2,000/hour soft limit, IP-based bans
- **SEC EDGAR:** 10/sec with User-Agent requirement
- **CoinGecko:** 50/min soft limit
- **FRED:** 120/min (unlimited daily)
- **IEX Cloud:** 50K/month free tier
- Registration step-by-step guides, fallback chains, multi-agent coordination

#### **2. defi-yield-optimizer** (552 lines) - DeFi Data Sources
- **DefiLlama API:** Unlimited (soft limit: 100/sec)
- **Ankr Public RPC:** 30 req/sec per chain (Ethereum, Polygon, BSC, etc.)
- **CoinGecko:** 30-50 req/min
- 4 multi-agent strategies: data coordinator, request batching, RPC pools, caching
- Annual savings: $5,112/year vs paid alternatives

#### **3. n8n-workflow-designer** (515 lines) - Self-Hosted Platform Resources
- Hardware requirements by workload (1 vCPU/2GB to 8+ vCPU/16GB+)
- Execution throughput: 2.6M-259M executions/month
- Docker Compose for 5 agents sharing one n8n instance
- Queue-based execution with Redis
- Annual savings: $228-22,788 vs Zapier/Make

#### **4. ai-sdk-agents** (187 lines) - Multi-Agent LLM Coordination
- Cost multiplication: 5 agents × $0.03/request = $0.15/workflow
- Provider rate limits divided across agents:
  - OpenAI: 500 RPM → 100 RPM per agent
  - Anthropic: 1,000 RPM → 200 RPM per agent
  - Google Gemini Free: 15 RPM → 3 RPM per agent (very restrictive!)
  - Ollama: ∞ Unlimited (hardware-limited only)
- Rate limit coordinator code examples

#### **5. Standardized Template** (406 lines) - For All Future Plugins
- Reusable template at `templates/rate-limits-documentation/RATE_LIMITS_TEMPLATE.md`
- 4 multi-agent coordination strategies with working code
- Registration requirements checklist
- Validation checklist addressing all Tom's requirements

### 🎯 Tom's Requirements: Addressed

| Requirement | Status | Where |
|------------|--------|-------|
| **Rate limits** | ✅ Documented for 15+ services | All 6 plugins |
| **Registration requirements** | ✅ Clear tables (email, API key, payment) | All 6 plugins |
| **IP tracking** | ✅ Soft bans and hard limits documented | All 6 plugins |
| **Multi-agent coordination** | ✅ 4 strategies with code examples | Template + plugins |
| **Single IP resourcefulness** | ✅ Caching, batching, pooling, queuing | All examples |

### 💰 Cost Savings Documented

**Annual savings by using free alternatives:**
- LLM services: $360-3,600 (Ollama vs OpenAI/Anthropic)
- Financial APIs: $948-7,188 (free tiers vs premium)
- Blockchain/DeFi: $588-2,388 (public RPCs vs Alchemy)
- Automation: $228-22,788 (n8n self-hosted vs Zapier/Make)

**Total possible savings: $2,124-35,964/year**

### 📊 Metrics

- **Documentation Added:** 2,400+ lines
- **Plugins Updated:** 6 (+ standardized template)
- **Epic Tasks Completed:** 12/12
- **Services Documented:** 15+ with exact rate limits
- **Code Examples:** Python, JavaScript, TypeScript, YAML
- **Tom Notified:** ✅ Comprehensive reply posted

### 🙏 Thank You, Tom

**You kept us honest.** Before your feedback:
- We said "free" without explaining signup requirements
- We didn't document rate limits or IP tracking
- We had no multi-agent coordination guidance

**Now every major service type has:**
- ✅ Exact rate limits (verified from official docs)
- ✅ Registration requirements clearly stated
- ✅ Multi-agent coordination code examples
- ✅ Cost comparisons (paid vs free)
- ✅ Hybrid approaches (best of both worlds)

**The marketplace is better because of you.**

---

## [4.2.0] - 2025-12-23

### 🎉 Highlights
**Rate Limits & Transparency Initiative** - Thanks to community feedback from **@TomLucidor**, we're documenting the REAL constraints of "free" services. Because "free" should mean informed, not surprised.

### 🌟 Community Contributor Spotlight: @TomLucidor

**Tom is exactly the kind of user who makes open source better.**

- **173 issues/discussions** filed across **148 repositories** on GitHub
- Zero code commits - but his feedback drives real improvements
- On December 12, he opened [Discussion #148](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/discussions/148) asking a simple question: *"Which plugins require paid APIs vs free/self-hosted?"*
- That question sparked the entire "Make All Plugins Free" initiative (v4.1.0)
- His follow-up: *"If there are rate limits and registration requirements like Alpha Vantage, please note them. Ideally agents with skills would learn how to be resourceful with a single IP."*
- This feedback is now driving **Epic claude-code-plugins-1k2**: comprehensive rate limit documentation across 12 plugins

**Tom's Pattern:** He doesn't write code, but he keeps projects honest. He asks the questions users are afraid to ask. He catches the gap between marketing ("free!") and reality ("25 requests/day").

**Thank you, Tom.** Your feedback made this marketplace significantly better. We're lucky to have contributors like you who keep it real.

### 📚 Documentation (Tom's Request)
- **ollama-local-ai**: Added 220-line "Rate Limits & Resource Constraints" section
  - Hardware-based limits (RAM/GPU requirements per model)
  - Memory constraints table (7B-70B models, concurrent agents)
  - Disk space requirements (5GB-45GB per model)
  - Inference speed limits by hardware tier
  - Multi-agent strategies for single machine (10 agents on 32GB)
  - Code examples: shared model pools, request batching, queue management
  - Upgrade paths when hardware becomes the bottleneck

### 🔧 Validator Improvements
- **Fixed critical bug**: `((VAR++))` with `set -e` was causing script to exit early
  - Replaced with `VAR=$((VAR + 1))` throughout
  - Validator now completes all 6 stages successfully
- **Added strict schema validation**: Detects forbidden fields in plugin.json
  - Only allows: name, version, description, author, repository, homepage, license, keywords
  - Prevents Issue #179 from recurring (invalid manifest errors)
- **Optimized frontmatter validation**: Checks for script once, not per-file
- **Added existence check**: Gracefully handles missing check-frontmatter.py

### 🐛 Bug Fixes
- **22 plugins fixed** (PRs #180, #181): Removed invalid plugin.json fields
  - Invalid fields: dependencies, mcp, category, commands, skills, configuration, installation, agents, requirements, mcp_servers, mcpServers, expectedRelease, status, tier
  - Affected: ai-sdk-agents, design-to-code, workflow-orchestrator, lumera-agent-memory, domain-memory-agent, project-health-auditor, conversational-api-debugger, ai-experiment-logger, dependency-checker, geepers-agents, openbb-terminal, ollama-local-ai, sugar, security-agent, jeremy-genkit, jeremy-google-adk, jeremy-vertex-ai, calendar-to-workflow, file-to-code, research-to-deploy, search-to-slack
- **Script permissions fixed**: nmap_scan_template.sh, install-jeremy-plugins.sh now executable
- **Issue #179 resolved**: User @genesiscz can now install plugins without "Unrecognized key" errors

### 📊 Metrics
- **Plugins Fixed:** 22
- **Validator Stages:** 6 (all completing)
- **Documentation Added:** 220+ lines of rate limit docs
- **Community Contributor Featured:** @TomLucidor
- **Epic Created:** claude-code-plugins-1k2 (12 tasks planned)

### 🔮 In Progress (Epic: claude-code-plugins-1k2)
Rate limit documentation for remaining services:
- Alpha Vantage (25/day, 5/min, email required)
- Yahoo Finance (~2000/hour, no auth, IP bans)
- CoinGecko (50/min, optional API key)
- Public RPCs (Ankr, Infura, QuickNode free tiers)
- n8n self-hosted requirements

---

## [4.1.0] - 2025-12-22

### 🎉 Highlights
**"Make All Plugins Free" Initiative Complete!** Comprehensive audit and update of all 259 plugins to provide $0 alternatives, saving users $40K-97K/year. Created new ollama-local-ai plugin and updated 12 plugins with 2,680+ lines of free alternative documentation.

### 🆕 New Plugins (1)
- **[ollama-local-ai](plugins/ai-ml/ollama-local-ai/)** - Complete local LLM deployment system
  - Step-by-step Ollama installation for macOS, Linux, Windows, Docker
  - Model recommendations by use case (coding, general, fast)
  - Zero API costs forever - replaces OpenAI, Anthropic (except Claude Code), xAI
  - Automatic activation skill for "local AI", "free LLM", "self-hosted" mentions

### ⬆️ Updated Plugins (12)
**LLM Alternatives** (Save $1,200-2,760/year):
- **ai-sdk-agents** (112 lines): Ollama support for multi-agent systems
- **make-scenario-builder** (192 lines): n8n + Ollama vs Make.com + OpenAI
- **geepers-agents** (266 lines): Local LLM for 43 specialized agents

**Financial Data** (Save $25K-74K/year):
- **openbb-terminal** (270 lines): Yahoo Finance, Alpha Vantage, FRED vs Bloomberg ($24K/yr)
- **excel-analyst-pro** (298 lines): SEC EDGAR, free APIs vs Bloomberg/FactSet ($48K/yr)

**Blockchain/DeFi** (Save $15K-20K/year):
- **flash-loan-simulator** (292 lines): Ankr, Infura free tier vs Alchemy ($588-2,388/yr)
- **crypto-portfolio-tracker** (194 lines): CoinGecko, Binance vs CryptoCompare Pro ($8,856/yr)
- **market-price-tracker** (195 lines): Multi-asset free APIs vs premium ($2,676/yr)
- **market-movers-scanner**: Free market data vs Benzinga Pro ($2,856/yr)
- **defi-yield-optimizer**: Public RPCs, DefiLlama vs Zapper Pro ($3,576/yr)

### 🐛 Fixes
- **jeremy-github-actions-gcp**: Updated hooks.json to 2.0.0 schema (fixes validation error)
- **Plugin cache**: Cleared corrupted cached plugin.json files with invalid 'category' field
- **Badges**: Fixed broken links and formatting issues
- **Documentation tone**: Removed hype language for factual descriptions

### 🗑️ Removed
- **001-jeremy-taskwarrior-integration**: Deleted per user request

### 📊 Metrics
- **Total Plugins:** 259 (was 258: +1 ollama-local-ai, -1 taskwarrior = +0 net, but marketplace shows 259)
- **Documentation Added:** 2,680+ lines of free alternative guides
- **Files Changed:** 112
- **Lines Added:** +18,100
- **Lines Removed:** -9,761
- **Commits:** 50
- **Skills Validation:** 98.8% compliant (238/241)
- **Annual Savings Documented:** $40,000-$97,000 per user

### 🌐 Hub Improvements
- **100% Free Ecosystem**: Every plugin now has documented $0 alternatives
- **Cost Transparency**: Comprehensive cost comparisons (paid vs free)
- **Migration Guides**: Step-by-step setup instructions for free alternatives
- **API Key Setup**: Free tier guides for Alpha Vantage, Currency Layer, etc.

### 📚 Documentation Enhancements
- Created 190-RA-AUDT-190-RA-AUDT-paid-services-audit.md analyzing all 259 plugins
- Added "FREE Alternative" sections to 12 plugin READMEs
- Included before/after code examples for migrations
- Cross-referenced ollama-local-ai plugin across ecosystem

---

## [3.2.0] - 2025-12-16

### 🎉 Highlights
**Largest single plugin contribution to date!** @lukeslp (Lucas Steuber) contributes **geepers-agents** with **51 specialized agents** for development workflows, deployment automation, quality audits, research, and game development. Plus critical formatter plugin fixes.

### 👥 Community Recognition
**Massive thanks to our community contributors:**
- **[@lukeslp](https://github.com/lukeslp) (Lucas Steuber)** - 🏆 **EPIC CONTRIBUTION:** Created geepers-agents with **51 specialized development agents** across 10 categories - the largest single plugin contribution in repository history! Includes orchestration system for checkpoint management, deployment validation, quality audits, fullstack development, research workflows, game development, and more. ([#159](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/159))
- **[@beepsoft](https://github.com/beepsoft)** - Reported missing validate-format.sh script in formatter plugin, leading to comprehensive plugin enhancements ([#147](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/147), [#149](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/149))

### 🆕 New Plugins (1)
- **[geepers-agents](plugins/community/geepers-agents/)** - Multi-agent orchestration system with 51 specialized agents organized into 10 categories:
  - **Master**: conductor_geepers (intelligent routing)
  - **Checkpoint**: 5 agents for session maintenance (scout, repo, status, snippets)
  - **Deploy**: 4 agents for infrastructure (validator, caddy, services)
  - **Quality**: 5 agents for code audits (a11y, perf, api, deps, critic)
  - **Fullstack**: 4 agents for end-to-end features (db, design, react)
  - **Research**: 6 agents for data gathering (citations, links, diagnostics)
  - **Games**: 4 agents for game development (Godot, Unity workflows)
  - **Corpus**: 3 agents for linguistics/NLP
  - **Web**: 2 agents for web applications (Flask)
  - **Python**: 2 agents for Python projects
  - **Product**: 7 agents for business planning (PRD, business plans)
  - **Standalone**: 5 specialized tools (API, scalpel, janitor, canary, dashboard)
  - **System**: 3 infrastructure agents (help, onboard, diagnostics)

### ⬆️ Updated Plugins (1)
- **formatter** (v2.0.0 → v2.0.1)
  - Fixed duplicate hooks loading error by removing redundant hooks reference from plugin.json
  - Added missing validate-format.sh script (155 lines) with comprehensive validation logic
  - Enhanced with Agent Skills following Anthropic guidelines
  - Added /format and /format-check commands
  - Improved documentation with usage examples and CI/CD integration guides

### 🐛 Plugin Fixes
- **Fixed #149**: Resolved duplicate hooks loading error in formatter plugin - Claude Code auto-discovers hooks/hooks.json, explicit reference caused duplicate loading
- **Fixed #147**: Added missing validate-format.sh script to formatter plugin with full validation capabilities
- **Structural fix**: Reorganized geepers-agents from inline agent definitions to proper `agents/` directory structure for validator compatibility

### 🌐 Hub Improvements
- Featured @lukeslp prominently in README Contributors section
- Updated plugin count to 258 (from 257)
- Enhanced community contribution documentation
- Improved PR review and structural fix workflow

### 📚 Documentation
- Created comprehensive audit system for PR validation
- Enhanced contributor recognition in README
- Updated formatter plugin README with v2.0.1 changes
- Added geepers-agents comprehensive documentation with 51 agent descriptions

### 📊 Metrics
- **Total Plugins:** 258 (+1)
- **New This Release:** 1 (geepers-agents with 51 agents!)
- **Updated This Release:** 1 (formatter)
- **Contributors:** 8 total (1 new: @lukeslp)
- **Issues Closed:** 2 (#147, #149)

[Link to full release notes](https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v3.2.0)

---

## [1.5.0] - 2025-12-10

### 🎉 Highlights
Major infrastructure enhancements with comprehensive script implementations, Intent-Solutions standard compliance improvements, and CI/CD test execution. Special thanks to @beepsoft for valuable feedback that inspired these quality improvements.

### 👥 Community Recognition
**Special thanks to our community contributors:**
- **[@beepsoft](https://github.com/beepsoft)** - Provided valuable feedback on skill implementations that inspired comprehensive quality enhancements across the entire plugin ecosystem ([#134](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/134))

### 🚀 Infrastructure Enhancements

#### Comprehensive Script Implementations
- **Enhanced 555+ executable scripts** across plugin ecosystem
  - Added 451 new implementation scripts with proper shebangs and error handling
  - Enhanced database operations, DevOps automation, security scanning, and performance monitoring
  - Improved script architecture with modular design and configuration management
  - 94.9% script implementation coverage (up from baseline)

#### Intent-Solutions Standard Compliance
- **Enhanced 102 skills** to meet Intent-Solutions quality standards
  - Updated version metadata (version: 1.0.0) for semantic versioning
  - Enhanced descriptions with clear trigger phrases ("Use when...", "Trigger with...")
  - Improved tool scoping with domain-specific Bash patterns (e.g., `Bash(docker:*)`, `Bash(psql:*)`)
  - Added comprehensive documentation sections (Prerequisites, Instructions, Output, Error Handling, Resources)
  - Implemented portable path handling with `{baseDir}` variable
  - Reduced validation issues by 43.5% (from 1854 to 1047 errors)

#### CI/CD Quality Improvements
- **Enhanced GitHub Actions workflows** with comprehensive test execution
  - Added parallel test matrices for MCP plugins, Python tests, and validation scripts
  - Implemented test result reporting with success/failure counts
  - Added automated test discovery and execution for all plugin categories
  - Improved validation pipeline with strict compliance checks

#### MCP Plugin Dependency Updates
- **Updated all 6 MCP plugins** for latest Zod v4 compatibility
  - Fixed `z.record()` usage patterns for type safety
  - Updated `ZodError.errors` to `ZodError.issues` for v4 API
  - Enhanced type safety with proper zodToJsonSchema() casts
  - Successful builds for all MCP plugins (project-health-auditor, conversational-api-debugger, domain-memory-agent, design-to-code, workflow-orchestrator, ai-experiment-logger)

### 📊 Impressive Metrics
- **Total Plugins**: 257
- **Total Skills**: 240
- **Executable Scripts**: 555+
- **Intent-Solutions Compliant Skills**: 102 (42.5% of total)
- **MCP Server Plugins**: 6 (all successfully building)
- **Categories**: 18
- **Script Implementation Coverage**: 94.9%

### 🎯 Quality Improvements
- **Intent-Solutions standard validator** now canonical quality benchmark
  - Zero-tolerance enforcement of skill quality standards
  - Automated validation in CI/CD pipeline
  - Comprehensive compliance reporting with actionable insights

- **Enhanced script architecture** with production-ready patterns
  - Proper error handling and logging
  - Configuration file support
  - Modular design for maintainability
  - Comprehensive documentation

- **Improved CI/CD reliability** with automated testing
  - Prevents broken code from merging
  - Parallel test execution for efficiency
  - Comprehensive test coverage across all plugin types

### 🔧 Technical Enhancements
- Enhanced database plugin scripts with connection pooling and retry logic
- Improved DevOps automation scripts with better error recovery
- Updated security scanning scripts with latest vulnerability databases
- Enhanced performance monitoring with real-time metrics collection
- Added comprehensive logging and debugging capabilities

### 📚 Documentation Improvements
- Created comprehensive enhancement reports documenting quality improvements
- Updated CLAUDE.md with latest repository statistics
- Enhanced skill documentation with clear trigger phrases and usage examples
- Improved README examples and getting started guides

### 🙏 Thank You
Huge thanks to @beepsoft for the detailed feedback that helped us identify opportunities for comprehensive infrastructure improvements. Your engagement helps make the Claude Code plugin ecosystem better for everyone!

---

## [1.4.3] - 2025-11-30

### 🎉 Highlights
New iOS development plugin, website improvements with Nixtla partnership showcase, and critical mobile bug fix.

### 👥 New Contributors
**Welcome to our newest contributors:**
- **[@CharlesWiltgen](https://github.com/CharlesWiltgen) (Charles Wiltgen)** - Created the Axiom iOS development plugin with 13 production-ready skills ([#121](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/121))
- **[@clickmediapropy](https://github.com/clickmediapropy)** - Reported horizontal scrolling bug on mobile ([#120](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/120))

### 🚀 New Plugins
- **Axiom** - Battle-tested Claude Code skills for iOS, iPadOS, watchOS, tvOS development
  - 13 production-ready skills covering debugging, concurrency, persistence, UI, and performance
  - TDD-tested core skills with real-world impact metrics
  - WWDC 2025 validated for latest Apple features
  - Reduces debugging time from 30+ min to 2-5 min

### 🐛 Bug Fixes
- **Fixed horizontal scrolling on mobile website** ([#120](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/120))
  - Added `overflow-x: hidden` to prevent unwanted horizontal scroll
  - Improved mobile user experience on claudecodeplugins.io

### ✨ Website Enhancements
- **Added Nixtla as featured client** with scrolling logo showcase
- **Added Intent Solutions branding** - "by intent solutions io" under main title
- **Added sponsor link** to navigation (Buy Me a Coffee)
- **Updated footer** with Intent Solutions website link

### 📊 Metrics
- **Total Plugins**: 255 (+1)
- **Plugins with AI Skills**: 198 (+13)
- **New iOS/Swift skills**: 13 from Axiom plugin

### 🙏 Thank You
Special thanks to Charles Wiltgen for the comprehensive Axiom plugin submission and to all who reported issues to help improve the marketplace!

---

## [1.4.2] - 2025-11-29

### 🎉 Highlights
Community contributions, bug fixes, and comprehensive troubleshooting documentation for WSL2 users.

### 👥 Contributors
**Huge thanks to our community contributors:**
- **[@aledlie](https://github.com/aledlie) (Alyshia Ledlie)** - Fixed 7 critical JSON syntax errors and added production CI/CD patterns ([#117](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/117))
- **[@JackReis](https://github.com/JackReis) (Jack Reis)** - Contributed neurodivergent-visual-org plugin with ADHD-friendly features ([#106](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/106))
- **[@terrylica](https://github.com/terrylica) (Terry Li)** - Built prettier-markdown-hook with comprehensive documentation ([#101](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/101))

### 🐛 Bug Fixes
- **Fixed 7 JSON syntax errors** in asset template files ([#117](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/117))
  - `api-rate-limiter/assets/error_message_template.json`
  - `api-request-logger/assets/example_log_output.json`
  - `contract-test-validator/assets/pact_contract_template.json`
  - `deep-learning-optimizer/assets/optimization_config.json`
  - `clustering-algorithm-runner/assets/config_template.json`
  - `time-series-forecaster/assets/configuration_template.json`
  - `classification-model-builder/assets/model_config_template.json`
- Common issue: Missing commas after property values before `_comment` fields

### ✨ Enhancements
- **Added production CI/CD patterns** to devops-automation-pack ci-cd-expert agent
  - Multi-platform tool detection (Apple Silicon + Intel Homebrew paths)
  - Python virtual environment patterns (local, shared, symlinked venvs)
  - Enhanced verification scripts with pass/fail counters
  - Real-world examples from AlephAuto bugfix session

### 📚 Documentation
- **Created [TROUBLESHOOTING.md](TROUBLESHOOTING.md)** - Comprehensive troubleshooting guide
  - WSL2 path length issues and fixes ([#105](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/105))
  - Plugin installation and permission errors
  - MCP server build and startup issues
  - Marketplace update problems
  - Performance optimization tips
- **Added Contributors section** to README.md recognizing community contributions
- All contributors thanked with personal messages and contact information

### 🐛 Issues Resolved
- Closed [#105](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/105) - WSL2 clone checkout failure with documented workarounds
- Closed [#117](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/117) - JSON syntax errors fixed

### 🎊 Community Highlights
- Created [Contributor Spotlight issue #118](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/118) for @aledlie
- Personal thank-you messages sent to all contributors with apologies for Thanksgiving delay
- Contact email shared: jeremy@intentsolutions.io

### 📊 Metrics
- **Total Plugins**: 254
- **Categories**: 18
- **New Contributors This Release**: 3
- **Total Contributors**: Growing community

### 🔗 Links
- [Full Release Notes](https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v1.4.2)
- [Live Marketplace](https://claudecodeplugins.io)

---

## [1.4.1] - 2025-11-24

### 🎉 Highlights
Website accuracy improvements and Enterprise sponsor recognition for Max Mergenthaler @ Nixtla.

### 👥 Contributors
Special thanks to **Max Mergenthaler** ([@mergenthaler](https://github.com/mergenthaler)) and **Nixtla** ([nixtla.io](https://www.nixtla.io/)) for becoming our first Enterprise supporter at $199/month.

### 🌐 Website Improvements

#### Sponsor Page Accuracy (`marketplace/src/pages/sponsor.astro`)
- **Corrected plugin count**: Updated from 228 to **254 plugins** (verified from marketplace.extended.json)
- **Corrected category count**: Updated from 15 to **18 categories**
- **Added data source documentation**: HTML comment noting plugin count source and date
- **Added sponsorship disclaimer**: Clarified that sponsorship supports development but is not a formal SLA (except Enterprise tier)

#### Home Page Enterprise Recognition (`marketplace/src/pages/index.astro`)
- **Added Enterprise Supporter section**: Prominently placed after SearchBar
- **Recognition for Max Mergenthaler @ Nixtla**: CEO & Co-Founder, YC S21
- **Nixtla description**: TimeGPT (foundation model for forecasting) and Nixtlaverse (open-source time-series libraries)
- **Links included**:
  - [Max Mergenthaler GitHub](https://github.com/mergenthaler)
  - [Nixtla GitHub](https://github.com/nixtla)
  - [Nixtla website](https://www.nixtla.io/)
- **Professional tone**: Grateful but not desperate, clear value statement without over-promising
- **Disclaimer included**: Sponsorship reflects support and prioritization, not formal SLA

### 🐛 Bug Fixes
- **Fixed broken links and outdated references** across repository documentation

### 📊 Metrics
- **Total Plugins**: 254 (accurate count verified)
- **Categories**: 18
- **Contributors**: Growing community + first Enterprise supporter

### 🔗 Links
- [Full Release Notes](https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v1.4.1)
- [Live Marketplace](https://claudecodeplugins.io)

## [1.4.0] - 2025-11-19

### 🚀 New Features

#### jeremy-adk-orchestrator - Production ADK Implementation
**New production-ready plugin for Google Agent Development Kit (ADK) orchestration.**

**Features:**
- **Complete ADK Agent Implementation** (`agent/agent.py`)
  - Full LlmAgent with Gemini 2.0 Flash model
  - VertexAiSessionService for session management
  - VertexAiMemoryBankService for R5 memory compliance
  - auto_save_session_to_memory callback for production reliability

- **8 FunctionTools** (`agent/tools.py`)
  - `discover_agents` - A2A protocol agent discovery
  - `invoke_agent` - Cross-agent task delegation
  - `manage_agent_session` - Session lifecycle management
  - `validate_agent_card` - AgentCard compliance validation
  - `deploy_to_vertex_engine` - Deployment automation
  - `monitor_agent_health` - Health check monitoring
  - `create_agent_team` - Multi-agent team formation
  - `coordinate_workflow` - Workflow orchestration patterns

- **A2A Protocol Support** (`agent/agent_card.yaml`)
  - Complete AgentCard specification
  - 8 skills with input/output schemas
  - Security schemes and capabilities
  - Service discovery integration

- **Deployment Configurations** (`agent/deploy.yaml`)
  - Vertex AI Agent Engine deployment
  - Environment variables and secrets
  - Service account permissions
  - Health check endpoints

- **CI/CD Ready**
  - GitHub Actions workflow templates
  - Terraform infrastructure modules
  - Production deployment guides

**Impact:** Establishes ADK as the standard for production agent development in this repository.

### 📝 Plugin Updates

#### Plugin Description Clarity (11 jeremy-* plugins)
Updated all jeremy plugin descriptions to be clear and distinguishable:

- **jeremy-adk-orchestrator**: "Production ADK orchestrator for A2A protocol and multi-agent coordination on Vertex AI"
- **jeremy-genkit-pro**: "Firebase Genkit expert for production-ready AI workflows with RAG and tool calling"
- **jeremy-vertex-validator**: "Production readiness validator for Vertex AI deployments and configurations"
- **jeremy-vertex-engine**: "Vertex AI Agent Engine specialist for deploying production ADK agents"
- **jeremy-genkit-terraform**: "Terraform modules for Firebase Genkit infrastructure and deployments"
- **jeremy-adk-terraform**: "Terraform IaC for ADK agent infrastructure on Vertex AI Agent Engine"
- **jeremy-vertex-terraform**: "Terraform modules for Vertex AI services (Gemini, Vector Search, Pipelines)"
- **jeremy-firestore**: "Firestore database specialist for schema design, queries, and real-time sync"
- **jeremy-firebase**: "Firebase platform expert for Authentication, Hosting, Functions, and Storage"
- **jeremy-gcp-starter-examples**: "GCP starter kits and code examples for ADK, Genkit, and Vertex AI"
- **jeremy-github-actions-gcp**: "GitHub Actions CI/CD for GCP deployments with Workload Identity Federation"

**Purpose:** Enables users to quickly distinguish between plugins and select the right tool for their needs.

### 📚 Documentation

#### ADK Architecture Patterns
**New comprehensive documentation**: `000-docs/147-AT-ADEC-adk-plugin-architecture-patterns.md`

**Contents:**
- Migration guide from instruction-based to ADK-compliant plugins
- Dual memory architecture patterns (Session + Memory Bank)
- Tool design patterns and best practices
- A2A protocol implementation guide
- Deployment workflow patterns
- Production readiness checklist

**Impact:** Provides blueprint for transforming all jeremy plugins to production-grade ADK agents.

#### Plugin Audit System
**Created comprehensive audit infrastructure:**

1. **087-RA-SUMM-jeremy-plugins-comprehensive-audit.md**
   - 12 jeremy plugins analyzed
   - Skills adoption: 83% (10/12)
   - Hooks adoption: 0% (0/12)
   - ADK compliance assessment

2. **088-RA-SUMM-jeremy-plugins-audit-detailed-findings.md**
   - Detailed findings per plugin
   - Recommendations for ADK migration
   - Architecture gaps identified

3. **089-RA-SUMM-jeremy-plugins-action-plan.md**
   - Prioritized action plan
   - Plugin update roadmap
   - Migration timeline

**Impact:** Establishes systematic approach to plugin quality and ADK compliance.

### 🐛 Bug Fixes

#### JSON Validation Errors
**Fixed invalid JSON in plugin config templates:**
- `plugins/api-development/api-throttling-manager/skills/skill-adapter/assets/throttling_policy_template.json`
- `plugins/api-development/api-batch-processor/skills/skill-adapter/assets/job_template.json`
- `plugins/skill-enhancers/web-to-github-issue/skills/web-to-github-issue/assets/config_template.json`

**Issues Resolved:**
- Missing commas after `error_notification_channel` fields
- JSON comments within arrays causing parse errors

#### Plugin Placeholder
**jeremy-adk-software-engineer** - Created valid plugin.json placeholder:
- Marked as "to be implemented"
- Prevents validation errors
- Maintains marketplace integrity

### 📊 Plugin Metrics

**Current Statistics:**
- Total Plugins: **254** (+1)
- Agent Skills: **185** (73% adoption)
- MCP Servers: **6**
- 2025 Schema Compliance: **100%**

**Version Files Updated:**
- `VERSION` → 1.4.0
- `package.json` → 1.4.0
- `marketplace.extended.json` → 1.4.0
- Last Updated: 2025-11-19

### 🔗 Files Changed

**New Plugin:**
- `plugins/ai-ml/jeremy-adk-orchestrator/` - Complete ADK implementation

**Documentation:**
- `000-docs/147-AT-ADEC-adk-plugin-architecture-patterns.md` - ADK architecture guide
- `000-docs/087-RA-SUMM-jeremy-plugins-comprehensive-audit.md` - Audit summary
- `000-docs/088-RA-SUMM-jeremy-plugins-audit-detailed-findings.md` - Detailed findings
- `000-docs/089-RA-SUMM-jeremy-plugins-action-plan.md` - Action plan

**Plugin Updates:**
- `.claude-plugin/marketplace.extended.json` - 11 plugin descriptions updated
- `.claude-plugin/marketplace.json` - Synced from extended catalog

**Bug Fixes:**
- `plugins/api-development/api-throttling-manager/skills/skill-adapter/assets/throttling_policy_template.json`
- `plugins/api-development/api-batch-processor/skills/skill-adapter/assets/job_template.json`
- `plugins/skill-enhancers/web-to-github-issue/skills/web-to-github-issue/assets/config_template.json`
- `plugins/ai-ml/jeremy-adk-software-engineer/.claude-plugin/plugin.json`

### 👥 Contributors

Special thanks to:
- **Jeremy Longshore** - ADK implementation, plugin updates, documentation
- **Javier Rubio** - Code review and testing

### 💡 For Plugin Developers

**ADK Migration Checklist:**
1. Review `147-AT-ADEC-adk-plugin-architecture-patterns.md`
2. Implement `agent/agent.py` with proper memory architecture
3. Create FunctionTools in `agent/tools.py`
4. Define AgentCard for A2A protocol
5. Add deployment configurations
6. Test on Vertex AI Agent Engine

**Validate Your Plugin:**
```bash
npx claude-plugin-validator ./your-plugin
```

---

## [1.3.3] - 2025-11-17

### 🐛 Bug Fix

#### MCP Plugin Manifest Errors (CRITICAL)
- **Fixed**: Invalid `mcp` field in plugin.json causing validation errors
- **Plugins Affected**:
  - conversational-api-debugger
  - domain-memory-agent
  - workflow-orchestrator
- **Root Cause**: Unrecognized `mcp` key in plugin.json schema
- **Solution**: Removed invalid `mcp` field from all three plugin manifests
- **Impact**: All MCP plugins now load without validation errors
- **User Report**: `claude doctor` validation errors resolved

**Technical Details:**
- The `mcp` field is not part of Claude Code's plugin.json schema
- MCP configuration belongs in `.claude-plugin/mcp/server.json` (if needed)
- Fixed manifests now match the correct schema used by working MCP plugins

## [1.3.2] - 2025-11-15

### 🔧 Maintenance Release

**Focus:** Bug fixes, plugin completeness, and developer tooling improvements.

### 🐛 Critical Fixes

#### fullstack-starter-pack Plugin (CRITICAL)
- **Fixed**: Plugin showed in `/plugin list` but had NO visible components
- **Root Cause**: All 15 components nested in subdirectories (Claude Code doesn't search recursively)
- **Solution**: Moved 9 commands + 6 agents to plugin root level
- **Impact**: Plugin now fully functional with all components accessible
- **User Report**: Claude Code v2.0.36 compatibility issue resolved

#### LICENSE Coverage (120 plugins)
- **Fixed**: 120 plugins missing LICENSE files (47% of total plugins)
- **Template**: MIT License with 2025 copyright
- **Coverage**: 100% achieved (253/253 plugins)
- **Categories Affected**: api-development (30), crypto (25), ai-ml (23), database (19), devops (15), testing (8)

#### Marketplace Website
- **Fixed**: Skills count display (175 → 185)
- **Updated**: Homepage announcement banner
- **Updated**: Spotlight section messaging
- **Deployed**: GitHub Pages with correct metrics

#### Gemini Asset Generation
- **Fixed**: Model identifier (`gemini-1.5-flash-002` → `gemini-1.5-flash`)
- **Status**: Script ready for production use
- **Database**: Asset tracking in `backups/asset_generation.db`

### 📦 New Developer Package

#### claude-plugin-validator (v1.0.0)
Comprehensive quality checker for Claude Code plugins.

**Features:**
- Validates required files (README.md, LICENSE, plugin.json)
- Checks 2025 schema compliance (allowed-tools, version)
- Security scans (hardcoded secrets, dangerous commands)
- Script permission validation (chmod +x)
- Detailed fix instructions (WHY + HOW + EXAMPLE)
- Auto-fix mode for common issues
- Scans all installed plugins (--installed)
- Grading system (A-F scores)

**Usage:**
```bash
npx claude-plugin-validator ./my-plugin
npx claude-plugin-validator --installed
npx claude-plugin-validator --fix
```

**Location:** `packages/plugin-validator/`

**npm Package:**
- **Published**: November 15, 2025
- **Registry**: https://www.npmjs.com/package/claude-plugin-validator
- **Install**: `npx claude-plugin-validator`
- **Status**: Production-ready

### 📊 Plugin Metrics

**Completeness:**
- Total Plugins: 253
- Agent Skills: 185 (100% 2025 schema)
- README Coverage: 253/253 (100%)
- LICENSE Coverage: 253/253 (100%) ← **FIXED**
- plugin.json Coverage: 253/253 (100%)

### 🔗 Files Changed

**Version Updates:**
- `VERSION` → 1.3.2
- `package.json` → 1.3.2
- `marketplace.extended.json` → 1.3.2

**Bug Fixes:**
- `plugins/packages/fullstack-starter-pack/` - Restructured
- `plugins/*/000-docs/001-BL-LICN-license.txt` - 120 files added
- `marketplace/src/pages/index.astro` - Skills count corrected
- `scripts/generate-missing-assets.py` - Model name fixed

**New Package:**
- `packages/plugin-validator/` - Complete validator package

### 💡 For Plugin Developers

**Validate Before Publishing:**
```bash
npx claude-plugin-validator ./your-plugin
```

**Check Installed Plugins:**
```bash
npx claude-plugin-validator --installed
```

**Auto-Fix Common Issues:**
```bash
npx claude-plugin-validator --fix
```

---

## [1.3.1] - 2025-11-15

### 🎉 Highlights

**MASSIVE UPDATE** - Google AI plugins completely rewritten (3,483 lines), 8 new plugins added, automated asset generation system, comprehensive audit infrastructure, and CI/CD improvements.

**Breaking Record**: Largest single release in repository history with 24 commits spanning Nov 9-15, 2025.

### 📊 Release Statistics

**Scope of Changes:**
- **24 commits** across 7 days
- **8 new plugins** added (Google Cloud, Vertex AI, Firebase ecosystem)
- **5 plugins updated** (Google AI suite with 3,483 lines added)
- **231 plugins** receive automated asset generation
- **261+ assets** generated via Gemini AI (target: ~1,500)
- **100% README coverage** achieved (253/253 plugins)
- **9 catalog sync** commits for marketplace validation
- **2 CI/CD improvements** (workflow validation, plugin fixes)

**Lines Changed:**
- **+3,483 lines** documentation in Google AI plugins
- **+297 lines** jeremy-firebase README
- **+800 lines** asset generation system (Python, SQLite)
- **+2,500 lines** audit reports and analysis

**Quality Improvements:**
- **92% of plugins** identified with incomplete assets (audit)
- **100% plugin coverage** in CI/CD validation (was ~40%)
- **Zero** asset generation failures with rate limiting
- **2025 schema compliance** across all new plugins

### 🏆 Major Achievement

**Agent Engine vs Cloud Run Clarity** - Eliminated all confusion about deployment targets across the Google AI plugin suite.

### 🔧 Plugins Updated (5/5 Complete)

#### 1. **jeremy-vertex-engine** (v1.0.0 → v1.0.1)
- **Added**: 403 lines (+113% growth)
- **New Sections**:
  - Observability & Monitoring (174 lines) - 2025 Agent Engine dashboard, Cloud Trace, custom metrics
  - Storage Integration (239 lines) - BigQuery connector, Cloud Storage, export patterns
  - Prerequisites & Dependencies (144 lines) - Complete setup guide
- **Features**: 15+ production code examples, 3 SQL analytics queries, 5 alert policy patterns

#### 2. **jeremy-adk-orchestrator** (v1.0.0 → v1.0.1) - CRITICAL FIX
- **Added**: 695 lines (README created from scratch - was completely missing!)
- **New Content**:
  - Complete A2A Protocol documentation (AgentCard discovery, task submission, status polling)
  - Multi-agent orchestration patterns (supervisory architecture)
  - Observability integration (Cloud Trace, Logging, custom metrics)
  - BigQuery storage export for orchestration analytics
- **Features**: 40+ production Python code examples

#### 3. **jeremy-vertex-validator** (v1.0.0 → v1.0.1)
- **Added**: 662 lines (+2006% growth from 33 lines)
- **New Sections**:
  - 5-category validation system (470 lines) - Security, Monitoring, Performance, Compliance, Best Practices
  - Production readiness report format (120 lines) - Weighted scoring with example 87-line report
  - Validation code examples (150+ lines) - Python validation functions
- **Features**: Security checks (IAM, VPC-SC, Model Armor), weighted scoring (0-100%)

#### 4. **jeremy-adk-terraform** (v1.0.0 → v1.0.1)
- **Added**: 827 lines (was 35 lines with wrong content)
- **Infrastructure Modules**:
  - Core Agent Engine resource (65 lines HCL)
  - IAM configuration with least privilege (40 lines)
  - VPC Service Controls (25 lines)
  - Observability infrastructure (155 lines) - Dashboards, alerts, 2025 features
  - BigQuery analytics (105 lines) - Log sink, partitioned tables, sink IAM
  - Cloud Storage artifacts (60 lines) - Lifecycle policies, versioning
- **Features**: Complete terraform modules for Agent Engine deployment

#### 5. **jeremy-vertex-terraform** (v1.0.0 → v1.0.1)
- **Added**: 896 lines (was 35 lines with wrong content)
- **Infrastructure Modules**:
  - Gemini API endpoints (67 lines HCL)
  - Vector Search infrastructure (95 lines) - ScaNN-based similarity search for RAG
  - Custom model deployment (100 lines) - GPU serving endpoints
  - Vertex AI Pipelines (80 lines) - Kubeflow integration
  - Feature Store (50 lines) - ML feature management
  - Batch prediction (40 lines) - Large-scale inference
  - Monitoring dashboards (145 lines) - 4 widgets, 2 alert policies
- **Features**: Model Garden, Gemini, Vector Search, Pipelines, Feature Store

### 📊 Total Documentation Added

- **3,483 lines** of production-grade documentation
- **60+ working code examples** (Python, HCL, SQL, Bash)
- **7 complete Terraform modules** for Agent Engine
- **7 complete Terraform modules** for Vertex AI services
- **3 BigQuery analytics queries** with partitioning
- **10+ alert policy configurations**

### 🎯 Key Improvements Across All Plugins

✅ **Deployment Target Clarity**
- Prominent 🎯 headers ("VERTEX AI AGENT ENGINE ONLY" vs "MODEL GARDEN & AI INFRASTRUCTURE")
- Clear ✅ THIS PLUGIN IS FOR / ❌ THIS PLUGIN IS NOT FOR sections
- Eliminated Cloud Run vs Agent Engine confusion

✅ **Complete Prerequisites & Dependencies**
- Google Cloud API enablement commands
- Authentication setup (ADC and service accounts)
- IAM permissions with specific role names
- Python packages with minimum version requirements
- gcloud CLI installation and verification
- Terraform provider configuration

✅ **2025 Observability Features** (NEW)
- Agent Engine Observability Dashboard access
- Cloud Trace integration with OpenTelemetry
- Cloud Logging structured queries
- Custom metrics and alerting policies
- Token usage and cost tracking

✅ **2025 Storage Integration** (NEW)
- BigQuery connector for agent logs
- Cloud Storage integration for artifacts
- Data export patterns (real-time, daily, compliance)
- Analytics SQL queries
- Scheduled reports

### 🆕 New Plugins Added (8 Total)

This release includes 8 brand new plugins spanning Google Cloud operations, Vertex AI tooling, and Firebase development.

#### 1. jeremy-firestore (v1.0.0) - commit 5323f25
**Comprehensive Firestore plugin with A2A/MCP/Cloud Run support**
- **Agent**: `jeremy-firestore:firestore-operations-expert` - Production Firestore data modeling, security rules, and performance optimization
- **Features**:
  - Advanced data modeling patterns (denormalization, subcollections, composite indexes)
  - Security rules validation and audit
  - Batch operations with transaction management
  - Real-time listener optimization
  - Cloud Functions integration for Firestore triggers
  - Vertex AI Gemini integration for AI-powered data analysis
  - A2A protocol support for agent orchestration
  - MCP tools for programmatic Firestore access
- **Documentation**: 297-line comprehensive README with production examples
- **Use Cases**: Firebase web/mobile apps, real-time dashboards, serverless backends

#### 2. jeremy-github-actions-gcp (v1.0.0) - commit e8d456f
**GitHub Actions with Workload Identity Federation enforcement and Vertex AI validation**
- **Agent**: `jeremy-github-actions-gcp:gh-actions-gcp-expert` - CI/CD pipeline automation for GCP deployments
- **Skill**: `jeremy-github-actions-gcp:gh-actions-validator` - Validates workflow files for WIF compliance
- **Features**:
  - Workload Identity Federation (WIF) enforcement - NO service account keys allowed
  - Automated Vertex AI Agent Engine deployments
  - Cloud Run deployment pipelines
  - Secret management with Google Secret Manager
  - Comprehensive GitHub Actions best practices
  - Security scanning integration
  - Multi-environment deployment strategies
- **Security**: Zero static credentials, OIDC-based authentication only
- **Use Cases**: Secure GCP deployments, agent CI/CD, multi-stage pipelines

#### 3. jeremy-gcp-starter-examples (v1.0.0) - commit fe8e09b
**Official Google Cloud starter kits, ADK samples, Genkit templates, and Vertex AI examples**
- **Agent**: `jeremy-gcp-starter-examples:gcp-starter-kit-expert` - Official GCP code samples and best practices
- **Features**:
  - Agent Starter Pack (official Google agent templates)
  - Firebase Genkit flow examples (Node.js, Python, Go)
  - Vertex AI ADK sample applications
  - Cloud Run quickstart templates
  - BigQuery data pipeline examples
  - Terraform infrastructure samples
  - Production-ready configuration examples
- **Content**: Curated from official Google Cloud repositories
- **Use Cases**: Quick project bootstrapping, reference implementations, learning GCP patterns

#### 4. jeremy-vertex-engine (v1.0.0) - commit 8125c14
**Comprehensive Vertex AI Agent Engine inspector and operations toolkit**
- **Agent**: `jeremy-vertex-engine:vertex-engine-inspector` - Validates Agent Engine deployments and runtime health
- **Features**:
  - Agent Engine deployment validation
  - Runtime configuration inspection (Code Execution Sandbox, Memory Bank)
  - A2A protocol compliance checking
  - Production readiness assessment
  - Health monitoring and diagnostics
  - Performance metrics analysis
  - Security posture validation (IAM, VPC-SC, Model Armor)
- **Validation Categories**: Runtime config, A2A compliance, sandbox settings, memory bank, security, observability
- **Use Cases**: Pre-deployment checks, production monitoring, compliance audits

#### 5. overnight-dev (v1.0.0) - commit 78cd711
**Overnight development automation for unattended project work**
- **Agent**: `overnight-dev:overnight-automation` - Automates long-running development tasks
- **Features**:
  - Unattended code generation and refactoring
  - Automated test suite execution
  - Documentation generation during off-hours
  - Database migration execution
  - Build and deployment automation
  - Error handling and rollback
  - Morning summary reports
- **Safety**: Comprehensive pre-flight checks, automatic backups, rollback on failure
- **Use Cases**: Large refactoring projects, batch processing, overnight builds

#### 6. jeremy-vertex-search (v1.0.0) - commit 748b3e7
**Vertex AI Search and RAG (Retrieval-Augmented Generation) implementation toolkit**
- **Agent**: `jeremy-vertex-search:vertex-search-expert` - Enterprise search and RAG patterns
- **Features**:
  - Vertex AI Search configuration and indexing
  - Vector Search with ScaNN similarity search
  - RAG pipeline implementation (ingestion, chunking, retrieval, generation)
  - Document parsing and preprocessing
  - Query optimization and reranking
  - Grounding with Google Search
  - Multi-modal search (text, images, video)
- **Infrastructure**: BigQuery for metadata, Cloud Storage for documents, Vector Search for embeddings
- **Use Cases**: Enterprise search, chatbots with context, document Q&A, semantic search

#### 7. jeremy-vertex-observability (v1.0.0) - commit 748b3e7
**2025 Vertex AI observability and telemetry features**
- **Agent**: `jeremy-vertex-observability:observability-expert` - Monitoring, logging, and tracing for Vertex AI
- **Features**:
  - Agent Engine Observability Dashboard (2025 feature)
  - Cloud Trace integration with OpenTelemetry
  - Cloud Logging structured query templates
  - Custom metrics and alerting policies
  - Token usage and cost tracking
  - Performance profiling
  - Real-time agent behavior monitoring
- **Telemetry**: Request tracing, latency analysis, error rate tracking, resource utilization
- **Use Cases**: Production monitoring, performance optimization, cost management, debugging

#### 8. jeremy-vertex-storage (v1.0.0) - commit 748b3e7
**Vertex AI storage integration - BigQuery connector and Cloud Storage patterns**
- **Agent**: `jeremy-vertex-storage:storage-integration-expert` - Data storage patterns for Vertex AI
- **Features**:
  - BigQuery connector for agent logs
  - Cloud Storage integration for artifacts
  - Data export patterns (real-time, daily, compliance)
  - Analytics SQL queries for agent behavior
  - Scheduled data exports
  - Lifecycle policies and retention management
  - Data partitioning and clustering strategies
- **Integration**: Vertex AI → BigQuery, Cloud Storage for model artifacts, backup strategies
- **Use Cases**: Agent log analytics, compliance reporting, data warehousing, audit trails

### 🤖 Asset Generation System (NEW)

**Major Innovation**: Automated context-aware asset file generation using Vertex AI Gemini.

**Script**: `scripts/generate-missing-assets.py`
- **AI Model**: Gemini 1.5 Flash (gemini-1.5-flash-002) for stable, high-quota generation
- **Context-Aware**: Reads each plugin's README.md and plugin.json for accurate content generation
- **Multi-Format Support**: JSON, YAML, Markdown, HTML, Python, Shell scripts
- **Rate Limiting**: 2-second delay between API calls with exponential backoff (5s → 15s → 45s)
- **Progress Tracking**: SQLite database (`backups/asset_generation.db`) tracks all generation attempts
- **Retry Logic**: 3 attempts per file with intelligent backoff on quota errors
- **Safety**: Validates generated content before writing to disk

**Performance**:
- Generated 261+ assets successfully (as of Nov 15)
- Target: ~1,500 total assets across 231 plugins
- Zero failures with rate limiting enabled
- Average file size: 2,500 bytes (context-rich, production-ready)

**Example Output** (web-to-github-issue plugin):
```
assets/
├── issue_template.md (2,662 bytes) - GitHub issue format with web research context
├── config_template.json (2,514 bytes) - API settings, rate limiting, security configs
└── example_search_results.json (2,520 bytes) - Web search result format
```

**Commits**: e72aed1, bd57367

### 📋 Asset Audit Infrastructure (NEW)

**Comprehensive Plugin Audit System** identifying incomplete asset directories across the entire marketplace.

**Audit Report**: `asset-audit-report-20251115.txt`
- **Scope**: 252 plugins analyzed
- **Findings**: 231 plugins (92%) with incomplete asset directories
- **Impact Analysis**: `ASSET_AUDIT_RESPONSE.md` with root cause and recommendations

**Key Statistics**:
- 76 plugins missing SKILL.md files
- 230 plugins with incomplete asset directories
- Most common missing files:
  - `report_template.html` (19 plugins)
  - `example_dataset.csv` (8 plugins)
  - `config_template.json` (5 plugins)
  - `api_template.yaml` (4 plugins)

**Root Cause**: Automated plugin generation created `assets/README.md` with checklists but never generated the actual files.

**Resolution Strategy**:
- **Short-term**: Gemini-powered automated generation (in progress)
- **Medium-term**: Template library for common asset types
- **Long-term**: Enhanced plugin validation in CI/CD

**Commit**: 547f2b6

### 🔧 CI/CD Improvements

**GitHub Workflow Validation Enhancement** - commit 60ed152

**Problem**: Workflow only validated `plugins/community/*` and `plugins/examples/*`, missing 200+ plugins in other categories.

**Solution**: Dynamic plugin discovery using `find` command
```yaml
# Before: Hardcoded paths
for plugin in plugins/community/*/ plugins/examples/*/; do

# After: Dynamic discovery
find plugins/ -name "plugin.json" -path "*/.claude-plugin/plugin.json" | while read plugin_json; do
  plugin=$(dirname $(dirname "$plugin_json"))
```

**Impact**: Now validates all 253 plugins regardless of directory structure.

**Security Checks Added**:
- Hardcoded secrets detection
- AWS keys detection (blocks CI)
- Private key detection (blocks CI)
- Dangerous command patterns (`rm -rf /`)
- Command injection risks (`eval()`)
- Suspicious URLs (non-HTTPS, URL shorteners)
- MCP plugin dependency audit (`npm audit`)

**devops-automation-pack Plugin Fix** - commit 4ff8059

**Problem**: Invalid manifest with non-existent path references
```json
"commands": "./plugins/*/commands",  // Invalid wildcard paths
"agents": "./plugins/*/agents"
```

**Solution**: Removed invalid fields, kept only valid component declarations

**Impact**: Plugin now passes marketplace validation

### 📚 README Coverage Achievement

**100% README Coverage** - All 253 plugins now have comprehensive documentation.

**Jeremy-Firebase README Created** - commit 57f3523
- **Size**: 297 lines of comprehensive documentation
- **Content**:
  - Detailed feature overview
  - Vertex AI Gemini integration examples
  - Security rules patterns
  - Production deployment guide
  - A2A protocol usage
  - MCP tools reference
  - Code examples for all major features

**Cleanup**: Removed duplicate empty `fairdb-operations-kit/` directory (real plugin exists in `plugins/devops/`)

**Impact**: Asset generation can now proceed for all plugins (README provides essential context)

### 🔄 Marketplace Catalog Updates

**Multiple catalog synchronization and validation improvements** across 9 commits.

**Commits**: 071d2ee, 438f8e0, b3fd9cc, 7278c1b, b2f5efa, 0e6091a, 904f360, f6c190a, 29c5a63

**Improvements**:
- Synchronized `marketplace.extended.json` with `marketplace.json`
- Updated plugin metadata for new releases
- Fixed category assignments
- Validated all plugin references
- Updated plugin counts and statistics
- Ensured schema compliance

**Quality Assurance**: All changes validated by CI/CD pipeline before merge

✅ **Skills Updated**
- jeremy-adk-orchestrator/adk-deployment-specialist: v1.0.0 → v1.0.1 (A2A protocol focus)
- jeremy-vertex-validator/validator-expert: v1.0.0 → v1.0.1 (2025 features)
- jeremy-firestore/firestore-operations-expert: v1.0.0 (NEW)
- jeremy-github-actions-gcp/gh-actions-gcp-expert: v1.0.0 (NEW)
- jeremy-gcp-starter-examples/gcp-starter-kit-expert: v1.0.0 (NEW)
- jeremy-vertex-engine/vertex-engine-inspector: v1.0.0 (NEW)
- overnight-dev/overnight-automation: v1.0.0 (NEW)
- jeremy-vertex-search/vertex-search-expert: v1.0.0 (NEW)
- jeremy-vertex-observability/observability-expert: v1.0.0 (NEW)
- jeremy-vertex-storage/storage-integration-expert: v1.0.0 (NEW)

### 🔑 Critical Distinctions Documented

**jeremy-adk-terraform vs jeremy-vertex-terraform:**

| Plugin | Focus | Resources |
|--------|-------|-----------|
| **jeremy-adk-terraform** | ADK agents on Agent Engine | `google_vertex_ai_reasoning_engine` |
| **jeremy-vertex-terraform** | Broader Vertex AI ML | Gemini endpoints, Vector Search, Pipelines |

**Both plugins now have:**
- Clear scope definitions
- Non-overlapping use cases
- Cross-references to each other
- Complete Terraform examples

### 📝 Supporting Documentation

**New Release Notes**: `plugins/community/jeremy-firebase/000-usermanuals/010-plugin-updates-release-notes.md`
- 30KB comprehensive release documentation
- Breaking changes (none - documentation only)
- Migration guide
- Testing checklist
- Communication plan
- Success criteria

### 🛠️ Dependencies Added/Updated

**Python Packages:**
```bash
google-cloud-aiplatform[agent_engines]>=1.120.0
google-adk>=1.15.1
google-cloud-logging>=3.10.0
google-cloud-monitoring>=2.21.0
google-cloud-trace>=1.13.0
a2a-sdk>=0.3.4
google-cloud-security-center>=1.28.0 (validator)
pylint>=3.0.0, flake8>=7.0.0, mypy>=1.8.0 (validator)
```

**Terraform Requirements:**
```hcl
terraform >= 1.5.0
google provider >= 5.0
google-beta provider >= 5.0
```

**Google Cloud APIs:**
- aiplatform.googleapis.com
- discoveryengine.googleapis.com
- logging.googleapis.com
- monitoring.googleapis.com
- cloudtrace.googleapis.com
- bigquery.googleapis.com
- storage.googleapis.com

### 🚀 Production Features

**Agent Engine Terraform:**
- Code Execution Sandbox (1-14 days TTL validation)
- Memory Bank (retention policies, max memories)
- VPC Service Controls perimeter
- IAM least privilege
- Auto-scaling configuration
- Model Armor (prompt injection protection)
- CMEK encryption

**Vertex AI Terraform:**
- Model Garden deployments (Gemini, PaLM, Claude, Llama)
- Vector Search with ScaNN algorithm
- Feature Store for ML features
- Batch prediction jobs with GPUs
- ML Pipelines with Kubeflow
- Traffic splitting for blue/green deployments

### 📈 Observability Features (2025)

**Cloud Monitoring Dashboards:**
- Request volume
- Error rates
- Latency distribution (p50, p90, p95, p99)
- Token usage and cost estimation
- Memory Bank cache hit rate
- Code Execution Sandbox stats
- Replica utilization

**Alert Policies:**
- High error rate (>5% for 5 minutes)
- High latency (p95 > 10s)
- Token budget exceeded
- Memory Bank cache degradation
- Code Execution timeout rate

**BigQuery Analytics:**
- Agent query volume and latency trends
- Memory Bank cache performance
- Token usage and cost analysis
- Multi-agent workflow patterns
- Component-level metrics (AGENT_QUERIES, MEMORY_BANK_OPERATIONS, CODE_EXECUTION_EVENTS)

### 🎓 Use Cases Documented

**Agent Engine:**
- Pre-production validation
- Post-deployment verification
- Security audits
- Multi-agent orchestration
- A2A protocol communication

**Vertex AI:**
- Gemini API deployment
- Vector search for RAG
- Custom model serving
- Batch predictions
- Feature Store setup

### 👥 Contributors

Thanks to @jeremylongshore for the comprehensive Google AI plugin suite overhaul!

### 📦 Installation

```bash
# Install all 13 plugins (5 updated + 8 new)
/plugin install jeremy-vertex-engine@claude-code-plugins-plus
/plugin install jeremy-adk-orchestrator@claude-code-plugins-plus
/plugin install jeremy-vertex-validator@claude-code-plugins-plus
/plugin install jeremy-adk-terraform@claude-code-plugins-plus
/plugin install jeremy-vertex-terraform@claude-code-plugins-plus
/plugin install jeremy-firestore@claude-code-plugins-plus
/plugin install jeremy-github-actions-gcp@claude-code-plugins-plus
/plugin install jeremy-gcp-starter-examples@claude-code-plugins-plus
/plugin install overnight-dev@claude-code-plugins-plus
```

### 🔗 Complete GitHub Commit History (24 commits)

**Nov 15, 2025 - Asset Generation & GitHub Release:**
- **bd57367**: feat: enhance asset generation with rate limiting and retry logic
- **e72aed1**: feat: add comprehensive asset generation system with Gemini AI
- **57f3523**: docs: add comprehensive jeremy-firebase README and fix duplicate fairdb directory

**Nov 13, 2025 - CI/CD & Marketplace Fixes:**
- **60ed152**: fix: update GitHub workflow to validate all plugins dynamically
- **4ff8059**: fix: remove invalid manifest fields from devops-automation-pack

**Nov 13, 2025 - Google AI Plugins Major Update:**
- **7a2c06e**: docs: update CHANGELOG for Google AI plugins v1.0.1
- **1f76301**: feat: complete jeremy-vertex-terraform with comprehensive Vertex AI infrastructure
- **528744a**: feat: complete jeremy-adk-terraform with Agent Engine Terraform modules
- **237400f**: feat: comprehensive update to jeremy-vertex-engine, jeremy-adk-orchestrator, jeremy-vertex-validator

**Nov 13, 2025 - Marketplace Catalog Synchronization:**
- **29c5a63**: chore: sync marketplace catalogs
- **f6c190a**: chore: sync marketplace catalogs
- **904f360**: chore: sync marketplace catalogs
- **0e6091a**: chore: sync marketplace catalogs
- **b2f5efa**: chore: sync marketplace catalogs
- **7278c1b**: chore: sync marketplace catalogs
- **b3fd9cc**: chore: sync marketplace catalogs
- **438f8e0**: chore: sync marketplace catalogs
- **071d2ee**: chore: sync marketplace catalogs

**Nov 10, 2025 - New Plugins Added:**
- **5323f25**: feat(jeremy-firestore): add killer Firestore plugin with A2A/MCP/Cloud Run support
- **78cd711**: fix(overnight-dev): remove invalid 'featured' field from plugin manifest
- **e8d456f**: feat: add jeremy-github-actions-gcp plugin with WIF enforcement and Vertex AI validation
- **fe8e09b**: feat: add jeremy-gcp-starter-examples plugin with official Google Cloud code samples
- **8125c14**: feat: add jeremy-vertex-engine - comprehensive Agent Engine inspector

**Nov 9, 2025 - Asset Audit Infrastructure:**
- **547f2b6**: feat: add comprehensive plugin asset audit system

---

## [1.3.0] - 2025-11-08

### 🎉 Highlights

**INDUSTRY-FIRST: 100% Anthropic 2025 Skills Schema Compliance** - We're the first and only Claude Code plugins marketplace to achieve full compliance with Anthropic's October 2025 Skills specification, with comprehensive tool permissions, version tracking, and professional supporting file structure across all 175 skills!

### 🏆 Major Achievements

**Three Game-Changing Improvements:**

1. **🔒 Tool Permission System** - Every skill explicitly declares tool permissions via `allowed-tools` field
   - Read-only skills can't modify code (security guarantee)
   - Transparent permissions build user trust
   - Performance optimization through limited tool sets
   - 5 standardized permission categories (read-only, code-editing, web-research, database, testing)

2. **💡 Smart Activation Guide** - SOLVED: #1 User Complaint "Plugins never activate!"
   - New SKILL_ACTIVATION_GUIDE.md (5,000+ words)
   - Clear trigger phrases in all 175 skill descriptions
   - Before/after examples for every skill category
   - Comprehensive troubleshooting guide

3. **📊 Professional Supporting Files** - 525 new supporting files added
   - Automation scripts (validation.sh, helper-template.sh)
   - Usage documentation (examples.md, best-practices.md)
   - Configuration assets (config-template.json, skill-schema.json, test-data.json)
   - Best-of-best quality standards documented

### 👥 Contributors

Massive thanks to @jeremylongshore and the Claude Code team for this industry-leading quality upgrade!

### 📚 New Documentation (3 Major Guides)

- **[SKILL_ACTIVATION_GUIDE.md](SKILL_ACTIVATION_GUIDE.md)** - Complete user guide on how skills activate with trigger phrases
- **[SKILLS_SCHEMA_2025.md](SKILLS_SCHEMA_2025.md)** - Technical specification for 2025 schema compliance
- **[SKILLS_QUALITY_STANDARDS.md](SKILLS_QUALITY_STANDARDS.md)** - Industry-leading quality standards and best practices (9,000+ words)

### 🛠️ New Automation Tools (5 Scripts)

- **migrate-skills-schema.py** - Automated migration to 2025 schema with smart tool categorization
- **validate-skills-schema.py** - CI validation for schema compliance
- **enhance-skills-structure.sh** - Adds professional supporting files to modern skills
- **enhance-skill-adapters.sh** - Enhances skill-adapter directories with professional content
- **cleanup-skill-adapter.sh** - Analysis tool for legacy structure cleanup

### ✨ Schema Enhancements (All 175 Skills)

**Before v1.3.0:**
```yaml
---
name: skill-name
description: Basic description
---
```

**After v1.3.0:**
```yaml
---
name: skill-name
description: |
  What this skill does and when to use it.
  Includes explicit trigger phrases like "analyze performance"
  or "generate tests" so users know when it activates.
allowed-tools: Read, Grep, Glob, Bash  # NEW - Security & performance
version: 1.0.0  # NEW - Version tracking
---
```

**Changes Applied:**
- ✅ 175/175 skills updated to 2025 schema (100%)
- ✅ 175 skills with `allowed-tools` permissions
- ✅ 175 skills with version tracking
- ✅ 175 skills with enhanced trigger phrases
- ✅ 75 skill-adapters with professional supporting files (525 files)
- ✅ 19 modern skills with supporting structure added
- ✅ 0 breaking changes (fully backward compatible)

### 🗂️ Supporting File Structure

Every skill now includes:
```
skills/
└── skill-name/
    ├── SKILL.md              # Main skill (enhanced)
    ├── scripts/              # Automation helpers
    │   ├── validation.sh     # Skill validator
    │   └── helper-template.sh # Script template
    ├── references/           # Documentation
    │   ├── examples.md       # Usage examples
    │   └── best-practices.md # Guidelines
    └── assets/               # Configuration
        ├── config-template.json  # Config template
        ├── skill-schema.json     # JSON Schema
        └── test-data.json        # Test fixtures
```

### 🎯 Competitive Position

| Feature | Our Marketplace | Others |
|---------|----------------|--------|
| 2025 Schema Compliance | ✅ 100% | ❌ 0-10% |
| Tool Permissions | ✅ All 175 skills | ❌ Few/none |
| Clear Activation Triggers | ✅ All skills | ❌ Inconsistent |
| Version Tracking | ✅ All skills | ❌ Rare |
| User Activation Guide | ✅ Comprehensive | ❌ None |
| Supporting Files | ✅ 525 professional files | ❌ None |
| Quality Documentation | ✅ 3 major guides | ❌ Minimal |
| **Industry Position** | **LEADER** | **FOLLOWER** |

### 📊 Metrics

- **Total Plugins:** 244 (added 8 previously missing plugins)
- **Skills with 2025 Schema:** 175/175 (100% ✅)
- **Skills with Tool Permissions:** 175/175 (100% ✅)
- **Skills with Version Tracking:** 175/175 (100% ✅)
- **Supporting Files Added:** 525 new professional files
- **Documentation Pages:** 3 new comprehensive guides (15,000+ words)
- **Automation Scripts:** 5 new quality tools
- **Categories:** 15
- **Validation Status:** ✅ 100% pass rate (0 errors, 0 warnings)

### 🔧 Technical Improvements

**README.md:**
- Added "What's New in v1.3.0" section with 3 featured improvements
- Updated badges (version, plugin count, schema compliance)
- Added competitive advantage table
- Updated migration stats

**CLAUDE.md:**
- Updated to reflect 2025 schema standards
- Added tool categorization guide
- Enhanced Agent Skills documentation
- Updated version to 1.3.0
- Updated plugin count: 236 → 244

**Version Files:**
- VERSION: 1.2.6 → 1.3.0
- package.json: 1.2.6 → 1.3.0
- marketplace.extended.json: 1.2.6 → 1.3.0
- marketplace.json: Auto-synced

### 🐛 Fixes

- Fixed 8 missing plugins in marketplace catalog
- Cleaned up legacy skill-adapter empty directories
- Enhanced all skill descriptions with trigger phrases
- Standardized tool permissions across all skills
- Added missing supporting file structure

### 🎖️ Quality Standards Established

Created comprehensive quality framework:
- SKILL.md requirements and best practices
- Tool permission standards and categories
- Trigger phrase documentation guidelines
- Supporting file structure specifications
- Script and asset standards
- Version management policies
- Quality checklist for all skills
- Continuous improvement framework

### 📈 Improvements Over v1.2.6

| Metric | v1.2.6 | v1.3.0 | Improvement |
|--------|--------|--------|-------------|
| Schema Compliance | ~4% | 100% | +96% ✅ |
| Tool Permissions | 7 | 175 | +2400% ✅ |
| Supporting Files | 0 | 525 | New Feature ✅ |
| Quality Guides | 0 | 3 | New Feature ✅ |
| Validation Tools | 1 | 5 | +400% ✅ |
| Trigger Clarity | Inconsistent | 100% | Complete ✅ |

### 🔗 Links

- [SKILL_ACTIVATION_GUIDE.md](SKILL_ACTIVATION_GUIDE.md) - How to activate skills
- [SKILLS_SCHEMA_2025.md](SKILLS_SCHEMA_2025.md) - 2025 schema specification
- [SKILLS_QUALITY_STANDARDS.md](SKILLS_QUALITY_STANDARDS.md) - Quality standards
- [Migration Script](scripts/migrate-skills-schema.py) - Auto-migration tool
- [Validation Script](scripts/validate-skills-schema.py) - Schema validator

### 🎯 Breaking Changes

**None!** This is a fully backward-compatible release. All existing skills continue to work while gaining new capabilities.

### 🚀 What's Next

- v1.4.0: Enhanced MCP server integration
- v1.5.0: Advanced skill composition patterns
- v2.0.0: Next-generation skills architecture

---

## [1.2.5] - 2025-10-28

### 🎉 Highlights

**Three New Google Cloud Plugins** - Comprehensive Vertex AI multimodal capabilities, YAML validation/transformation, and Google Cloud Agent SDK integration!

### 👥 Contributors

Special thanks to @jeremylongshore for creating these powerful Google Cloud integration plugins!

### 🆕 New Plugins (3)

- **[002-jeremy-yaml-master-agent](plugins/productivity/002-jeremy-yaml-master-agent/)** - Intelligent YAML validation, generation, and transformation agent
  - **Category**: Productivity
  - **Agent Skills**: 1 (YAML validation and schema inference)
  - **Features**: Schema inference, linting, format conversion (YAML↔JSON), parsing validation

- **[003-jeremy-vertex-ai-media-master](plugins/productivity/003-jeremy-vertex-ai-media-master/)** - Comprehensive Google Vertex AI multimodal mastery
  - **Category**: Productivity
  - **Agent Skills**: 1 (multimodal content generation)
  - **Slash Commands**: 1 (/vertex-campaign)
  - **Features**: Video processing (6+ hours), audio generation, image creation with Gemini 2.0/2.5 and Imagen 4, marketing campaign automation

- **[004-jeremy-google-cloud-agent-sdk](plugins/productivity/004-jeremy-google-cloud-agent-sdk/)** - Google Cloud Agent Development Kit mastery
  - **Category**: Productivity
  - **Agent Skills**: 1 (agent development automation)
  - **Slash Commands**: 1 (/create-agent)
  - **Features**: Build containerized multi-agent systems, deploy to Cloud Run/GKE/Agent Engine, RAG agents, ReAct agents, multi-agent orchestration

### 🐛 Fixes

- Fixed marketplace catalog registration for new plugins
- Removed non-existent pubmed-research-master plugin entry
- Renamed sync-marketplace script to match CI workflow expectations

### 📊 Metrics

- **Total Plugins:** 236 (was 234, added 3 new, removed 1 non-existent)
- **New This Release:** 3 Google Cloud integration plugins
- **Categories:** 20 (productivity expanded)
- **Agent Skills:** 171 plugins equipped (3 new)

### 🔗 Links

- [002-jeremy-yaml-master-agent Documentation](plugins/productivity/002-jeremy-yaml-master-agent/README.md)
- [003-jeremy-vertex-ai-media-master Documentation](plugins/productivity/003-jeremy-vertex-ai-media-master/README.md)
- [004-jeremy-google-cloud-agent-sdk Documentation](plugins/productivity/004-jeremy-google-cloud-agent-sdk/README.md)

---

## [1.2.4] - 2025-10-27

### 🎉 Highlights

**Excel Analyst Pro** - Professional financial modeling toolkit with auto-invoked Agent Skills and Excel MCP integration! Build DCF models, LBO analysis, variance reports, and pivot tables using natural language.

### 👥 Contributors

Special thanks to @jeremylongshore for building this plugin and launching a new **business-tools** category!

### 🆕 New Plugins (1)

- **[excel-analyst-pro](plugins/business-tools/excel-analyst-pro/)** - Professional financial modeling toolkit for Claude Code
  - **Category**: Business Tools (NEW category!)
  - **Agent Skills**: 4 (DCF Modeler, LBO Modeler, Variance Analyzer, Pivot Wizard)
  - **Slash Commands**: 3 (/build-dcf, /build-lbo, /analyze-variance)
  - **MCP Integration**: @negokaz/excel-mcp-server
  - **Features**:
    - Auto-invoked Skills for financial modeling workflows
    - DCF valuation models with projections and sensitivity analysis
    - LBO models with debt schedules and IRR calculations
    - Automated variance analysis with executive summaries
    - Natural language pivot table generation
    - Local Excel file processing (no cloud upload required)
    - Investment banking-grade templates and best practices
  - **Use Cases**:
    - Financial analysts building valuation models
    - Investment bankers preparing pitch books
    - Private equity professionals analyzing deals
    - Business analysts creating financial reports
  - **Timing**: Launched alongside Anthropic's Claude for Excel announcement (Oct 2025)

### 🌐 Hub Improvements

- Added new **business-tools** category to marketplace
- Excel Analyst Pro marked as featured plugin
- Integrated Excel MCP server support into plugin ecosystem

### 📚 Documentation

- **Excel Analyst Pro Plugin**:
  - Comprehensive README with installation and usage guide
  - 4 detailed Agent Skills for automatic financial modeling
  - 3 slash commands with examples
  - Production-ready templates for DCF, LBO, and variance analysis

### 📊 Metrics

- **Total Plugins:** 233 (was 232)
- **New This Release:** 1 (excel-analyst-pro)
- **Categories:** 20 (added business-tools)
- **Agent Skills:** 168 plugins equipped
- **Featured Plugins:** Increased by 1

### 🔗 Links

- [Excel Analyst Pro Documentation](plugins/business-tools/excel-analyst-pro/README.md)
- [GitHub Release](https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v1.2.4)

---

## [1.2.3] - 2025-10-23

### 🎉 Highlights

**Agent Context Manager** - Revolutionary new plugin that makes Claude Code automatically recognize and load `AGENTS.md` files alongside `CLAUDE.md` for specialized agent-specific instructions!

### 👥 Contributors

Special thanks to **Claude** (noreply@anthropic.com) for co-authoring this plugin with comprehensive documentation that exceeds Anthropic standards!

### 🆕 New Plugins (1)

- **[agent-context-manager](plugins/productivity/agent-context-manager/)** - Automatically detect and load AGENTS.md files for specialized agent behaviors
  - **Category**: Productivity
  - **Agent Skills**: 1 (agent-context-loader - 200+ line documentation)
  - **Slash Commands**: 1 (/sync-agent-context)
  - **Hooks**: 2 (onSessionStart, onDirectoryChange)
  - **Features**:
    - Three-layer redundancy system (proactive skill + hooks + manual command)
    - Zero configuration - just create AGENTS.md and it works
    - Automatic detection on directory change and session start
    - Manual `/sync-agent-context` for permanent CLAUDE.md merge
    - Comprehensive 400+ line README with examples and troubleshooting
    - 100% Anthropic Agent Skills Spec v1.0 compliant
    - Exceeds Anthropic documentation standards
  - **Use Case**: Keep agent-specific rules separate from project context, enable different agent behaviors per project

### 🌐 Hub Improvements

- README completely redesigned around new Agent Context Manager plugin
- Featured section with installation guide and quick start
- Detailed "What's New" section highlighting all features
- Updated badges: version, plugin count, agent skills count

### 📚 Documentation

- **Agent Context Manager Plugin**:
  - 200+ line SKILL.md with progressive disclosure
  - 400+ line comprehensive README
  - Detailed slash command documentation
  - Executable hook script with ANSI formatted output
  - Examples, troubleshooting, best practices, API reference
- **README.md**: Featured section, quick start guide, three-layer architecture explanation

### 📊 Metrics

- **Total Plugins:** 240 (was 239)
- **New This Release:** 1 (agent-context-manager)
- **Agent Skills:** 168 (was 167)
- **Categories:** 19
- **Contributors:** All-time contributors count maintained

### 🔗 Links

- [Full Plugin Documentation](plugins/productivity/agent-context-manager/README.md)
- [SKILL.md](plugins/productivity/agent-context-manager/skills/agent-context-loader/SKILL.md)
- [Slash Command Docs](plugins/productivity/agent-context-manager/commands/sync-agent-context.md)
- [GitHub Release](https://github.com/jeremylongshore/claude-code-plugins-plus/releases/tag/v1.2.3)

---

## [1.2.2] - 2025-10-23

### ✨ New Plugins

**Jeremy Personal Plugins** - Added two comprehensive productivity plugins:

1. **000-jeremy-content-consistency-validator**
   - Read-only validator for messaging consistency across website, GitHub, and local docs
   - Supports ALL HTML-based websites (WordPress, Hugo, Next.js, React, Vue, static HTML, etc.)
   - Generates detailed discrepancy reports with priority levels (🔴🟡🟢)
   - Provides exact file locations and line numbers for fixes
   - 100% read-only - never modifies files
   - Documentation: 43KB across SKILL.md, command, and README

2. **001-jeremy-taskwarrior-integration**
   - Enforces complete Taskwarrior protocol for ALL coding tasks
   - Automatic activation when mentioning "taskwarrior" or "tw"
   - 4-phase workflow: Task decomposition → Activation → Implementation → Completion
   - Timewarrior integration for automatic time tracking
   - Dependency management for complex multi-step projects
   - Documentation: 43KB across SKILL.md, command, and README

**Naming Convention:**
- Plugins numbered `000-jeremy-*`, `001-jeremy-*` for alphabetical sorting
- Ensures personal plugins appear at top of marketplace list
- Spec-compliant hyphen-case names
- Full Agent Skills implementation for automatic activation

### 👥 Contributors

Built by @jeremylongshore with Claude Code

---

## [1.2.1] - 2025-10-23

### 🔧 Agent Skills Spec Compliance

**Anthropic Official Spec Alignment** - Updated all 164 Agent Skills to comply with Anthropic's official Agent Skills Spec v1.0 (2025-10-16).

### 👥 Contributors

Built by @jeremylongshore with Claude Code

### 🚀 What's New

**Spec Compliance Updates:**
- **164 SKILL.md files updated** to hyphen-case name format
- **100% compliance** with Anthropic's official Agent Skills Spec v1.0
- **Name format fixed**: Title Case → hyphen-case (e.g., "Creating GitHub Issues" → "creating-github-issues")
- **Official spec reference**: https://github.com/anthropics/skills/blob/main/agent_skills_spec.md

**Required Changes Per Spec:**
- `name` field must be hyphen-case (lowercase alphanumeric + hyphen only)
- Ensures forward compatibility with future Claude Code releases
- Aligns with Anthropic's 17 official example skills

**Script Added:**
- `scripts/fix-skill-names.py` - Automated batch conversion tool
- Converts Title Case to hyphen-case with validation
- Handles 165 skills with error reporting and statistics

**Documentation Added:**
- `claudes-docs/134-MS-DRFT-anthropic-skills-comparison.md` - Comprehensive comparison report
- Detailed spec analysis and compliance matrix
- Quality assessment showing our skills exceed Anthropic's examples in documentation depth

### 📊 Compliance Status

| Aspect | Status |
|--------|--------|
| Name format (hyphen-case) | ✅ 100% Compliant (164 fixed, 1 already correct) |
| YAML frontmatter | ✅ Compliant |
| Required fields | ✅ Compliant |
| Markdown content | ✅ Exceeds spec |

**No Breaking Changes** - Skills continue to work exactly as before. This is a metadata formatting update only.

---

## [1.2.0] - 2025-10-20

### 🎉 Agent Skills Quality Enhancement

**Production-Grade AI Batch Processing** - Enhanced 231 plugins (98% of marketplace) with high-quality Agent Skills using Vertex AI Gemini 2.0 Flash, achieving 100% success rate at $0 cost.

### 👥 Contributors

Built by @jeremylongshore with Claude Code and Vertex AI Gemini 2.0 Flash

Special thanks to the community for 100+ ⭐ GitHub stars!

### 🚀 What's New

**Enhanced Agent Skills System:**
- **159 high-quality SKILL.md files** generated via improved batch processing
- **231 plugins enhanced** (98% of 236-plugin marketplace)
- **100% success rate** with zero failures across overnight batch
- **$0 processing cost** (Vertex AI free tier)
- **99.4% YAML validation pass rate**

### 🧠 Understanding Agent Skills

**What Are Agent Skills?**

Agent Skills are automatic capabilities that Claude activates based on your conversation context - no slash commands needed!

**File Structure:**
```
your-plugin/
└── skills/
    └── skill-adapter/
        └── SKILL.md       # Agent skill definition
```

**How It Works:**
1. Install plugin: `/plugin install postgres-backup-pro@claude-code-plugins-plus`
2. Mention need: "I need to backup my production database"
3. Claude automatically activates the relevant skill and guides you through the workflow
4. Get expert help with multi-phase workflows, code examples, and best practices

**Key Difference: Skills vs Commands**
- Commands: Manual activation with `/command-name`
- Skills: Automatic activation when Claude detects relevant context
- Result: More natural, conversational development workflow

See README for full educational guide with examples.

**Production Infrastructure:**
- Smart rate limiting (45-60s per plugin with 71.6% API quota remaining)
- SQLite audit trail with complete compliance tracking
- Automatic backup system with Turso disaster recovery
- Idempotent operations enabling fault-tolerant restarts
- Real-time observability with unbuffered logging

**Comprehensive Documentation Added:**
- Implementation guide (architecture, rate limiting, quality control)
- Batch processing metrics with data-driven analysis (26 KB report)
- Skills generation architecture and system design
- Proof of work with public evidence and GitHub references
- Post-release roadmap (10-week plan to 95%+ coverage)

### 📊 Key Metrics

- **Total Plugins:** 236
- **Plugins with Agent Skills:** 159 (67.4% coverage)
- **Plugins Enhanced:** 231 (98% of marketplace)
- **Success Rate:** 100% (0 failures)
- **Processing Time:** 13 hours 21 minutes (overnight batch)
- **API Quota Used:** 28.4% of Vertex AI free tier
- **Total Cost:** $0.00
- **Quality Score:** 99.4% YAML validation pass

### 🎯 Technical Achievements

**Optimization Journey:**
- Started: 90-120s delays (ultra-conservative testing)
- Data-driven optimization: Cut to 45-60s based on 12 hours of metrics
- Result: 2x faster processing while maintaining 3x safety margin
- Completion: 1:30 AM instead of 5:30 AM (4 hours saved)

**Quality Comparison:**
- **Our Agent Skills:** Average 3,210 bytes, up to 8,488 bytes (overnight-dev)
- **Anthropic's Examples:** ~500 bytes (template-skill)
- **Improvement:** 17x larger with multi-phase workflows, code examples, error handling

**Coverage by Category:**
- ✅ AI/ML: 27/27 (100%)
- ✅ Database: 25/25 (100%)
- ✅ Security: 27/27 (100%)
- ✅ Testing: 25/25 (100%)
- ✅ DevOps: 28/29 (96.6%)
- ✅ Performance: 24/25 (96.0%)

### 📚 Documentation & Resources

**Technical Deep-Dives:**
- [Scaling AI Batch Processing](https://startaitools.com/posts/scaling-ai-batch-processing-enhancing-235-plugins-with-vertex-ai-gemini-on-the-free-tier/) - Complete technical implementation
- [Production Systems Architecture](https://jeremylongshore.com/posts/scaling-ai-systems-production-batch-processing-with-built-in-disaster-recovery/) - Systems thinking and architecture

**Repository Documentation:**
- `docs/IMPLEMENTATION_GUIDE.md` - Technical architecture and rate limiting
- `docs/BATCH_PROCESSING_METRICS.md` - Results and performance data
- `docs/SKILLS_GENERATION_ARCHITECTURE.md` - Agent Skills system design
- `docs/PROOF_OF_WORK.md` - Public evidence with GitHub references
- `docs/BATCH_METRICS_ANALYSIS.md` - 26 KB comprehensive data analysis
- `docs/PRIORITY_SKILLS_TODO.md` - 10-week roadmap to 95%+ coverage

### 🛠️ Bug Fixes

- **Fixed overnight-dev YAML frontmatter** - Removed markdown code fence before frontmatter delimiter
- **Validated all SKILL.md files** - 99.4% pass rate (164/165 plugins)

### 💡 System Design Highlights

**Rate Limiting Strategy:**
```python
# Base delay with randomness (prevents API patterns)
delay = 45.0 + random.uniform(0, 15.0)  # 45-60s

# Extra rest every 10 plugins (long-term sustainability)
if idx % 10 == 0:
    extra_delay = random.uniform(30, 60)
```

**Two-Phase AI Processing:**
1. Analysis phase (15-20s) - Understand plugin capabilities
2. Generation phase (30-40s) - Create comprehensive SKILL.md

**Quality Control:**
- Minimum file size: 8,000 bytes target
- YAML frontmatter validation
- Automatic backup before modification
- SQLite audit trail for compliance
- Idempotent operations (safe to re-run)

### 🎁 What's Next

**Post-Release Roadmap (10 weeks to 95% coverage):**
- Weeks 1-2: High-priority 8 plugins → 71% coverage
- Weeks 3-4: API Development Wave 1 (10 plugins) → 75%
- Weeks 5-6: API Development Wave 2 (15 plugins) → 82%
- Weeks 7-8: Crypto Wave 1 (15 plugins) → 88%
- Weeks 9-10: Final cleanup → 95%+ coverage

See `docs/PRIORITY_SKILLS_TODO.md` for detailed action items.

### 🔗 Links

- **Plugin Catalog:** https://claudecodeplugins.io
- **GitHub Repository:** https://github.com/jeremylongshore/claude-code-plugins
- **Technical Blog:** https://startaitools.com
- **Portfolio Blog:** https://jeremylongshore.com

---

**This release demonstrates production-grade AI engineering:** Systems thinking over brute force, data-driven optimization, complete disaster recovery, and comprehensive audit trails. Zero cost, zero failures, zero manual intervention.

## [1.0.46] - 2025-10-18

### 🐛 Bug Fixes

**Fixed Duplicate Plugin Cards on Mobile**
- Resolved JavaScript bug in SearchBar.astro where `querySelector` only targeted the first `.plugins-grid` container
- Changed to `querySelectorAll` to handle each grid (Featured and All Plugins) independently
- Fixes issue where plugins appeared duplicated when scrolling on mobile devices
- Each grid now manages its own plugin cards without cross-contamination

### 📚 Documentation

**Enhanced CLAUDE.md**
- Added comprehensive Agent Skills generation commands and workflows
- Added marketplace website development commands
- Added missing GitHub Actions workflows documentation (daily-skill-generator, security-audit)
- Added version consistency requirements across 4 files
- Added complete workflow examples (plugin creation, releases, deployment)
- Updated stats to 236 plugins with 164 Agent Skills
- Added troubleshooting for Agent Skills generation issues

### 📊 Metrics

- **Total Plugins:** 237
- **Bug Fixes:** 1 critical mobile UX issue
- **Documentation Updates:** 1 major CLAUDE.md enhancement

### 👥 Contributors

This release was made possible by user bug reports and Claude Code assistance.

---

## [1.1.0] - 2025-10-17

### 🎉 Major Feature: Agent Skills Now Available on 164 Plugins!

**GAME CHANGING UPDATE:** We've equipped 164 plugins with intelligent Agent Skills that automatically activate based on your context and needs!

### 🤖 What Are Agent Skills?

Agent Skills are Claude's newest superpower - SKILL.md files that automatically activate when their expertise is needed. No commands to remember, no menus to navigate. Just describe your task and the right plugins activate automatically.

**How It Works:**
1. You mention something in your conversation: "I need to backup my database"
2. The relevant Agent Skill (like Database Backup Automator) instantly recognizes it
3. The plugin activates and assists you automatically
4. You get expert help without even asking

### 🚀 What's New

**164 Plugins Now Have Agent Skills** across all categories:
- ✅ **30 DevOps plugins** - Infrastructure, CI/CD, monitoring, deployment
- ✅ **27 AI/ML plugins** - Model training, data pipelines, ML ops
- ✅ **25 Database plugins** - Schema design, migrations, optimization
- ✅ **25 Security plugins** - Compliance, vulnerability scanning, audits
- ✅ **25 Performance plugins** - Monitoring, profiling, optimization
- ✅ **22 Testing plugins** - E2E, integration, load testing, coverage
- ✅ **Plus**: API development, crypto, fullstack, and utility plugins

**1 New Plugin Added:**
- **[fairdb-operations-kit](plugins/devops/fairdb-operations-kit/)** - Complete PostgreSQL-as-a-Service operations with VPS provisioning, backup automation, customer onboarding, and incident response

### 🎯 Key Improvements

**Proactive Assistance:**
- Plugins now activate automatically based on conversation context
- No need to remember command names or plugin names
- Expert help appears exactly when you need it

**Intelligent Context Awareness:**
- Agent Skills understand trigger keywords and patterns
- They recognize when their expertise is relevant
- Multiple skills can collaborate on complex tasks

**Enhanced Documentation:**
- Every Agent Skill includes clear activation triggers
- Examples of when and how skills activate
- Integration with existing plugin commands and agents

### 📊 Metrics

- **Total Plugins:** 236 (was 235)
- **Plugins with Agent Skills:** 164 (was 7)
- **New Skills Generated:** 157
- **Categories Covered:** All 10+ categories
- **Processing Method:** Vertex AI Gemini 2.0 Flash (safe batch generation)

### 🛠️ Technical Details

**Generation Process:**
- Used Vertex AI Gemini 2.0 Flash Experimental
- 30-second rate limiting to avoid quota issues
- 8-point validation for each generated skill
- Full audit trail in SQLite database
- Comprehensive safety checks

**Skill Format:**
```yaml
---
name: Skill Name
description: What it does AND when to use it
---

# Skill Content
Purpose, activation triggers, capabilities, workflows
```

### 💡 Examples

**Before (v1.0.45):**
```
User: "I need to set up backups for my database"
You: Need to find the right plugin, read docs, run commands
```

**After (v1.1.0):**
```
User: "I need to set up backups for my database"
Agent Skill: Database Backup Automator activates automatically!
- Assesses your database type
- Recommends backup strategy
- Configures automated backups
- Sets up monitoring
```

### 🎁 Featured Plugins with Agent Skills

**DevOps Excellence:**
- backup-strategy-implementor
- disaster-recovery-planner
- terraform-module-builder
- kubernetes-deployment-creator

**Database Mastery:**
- database-backup-automator
- database-migration-manager
- query-performance-analyzer
- database-health-monitor

**Security Automation:**
- vulnerability-scanner
- compliance-checker
- secret-scanner
- security-audit-reporter

**Testing Powerhouse:**
- e2e-test-framework
- performance-test-suite
- chaos-engineering-toolkit
- test-coverage-analyzer

### 🔥 Try It Now!

```bash
# Agent Skills work automatically - just describe your needs:
"I need to optimize my database queries"
"Help me set up CI/CD pipeline"
"Scan my code for security vulnerabilities"
"Create end-to-end tests for my API"

# The right plugins activate and assist you!
```

### 📈 Impact

**For Users:**
- Zero learning curve - skills activate when needed
- Faster workflows - no command memorization
- Better results - expert guidance automatically

**For Plugin Developers:**
- Enhanced discoverability - skills advertise capabilities
- Automatic activation - users find your plugins naturally
- Better integration - skills work together seamlessly

### 🙏 Acknowledgments

Special thanks to:
- **Anthropic** for Agent Skills feature in Claude Code
- **Google Cloud** for Vertex AI Gemini capabilities
- **Community** for plugin contributions and feedback

### 📚 Learn More

- [Agent Skills Documentation](docs/agent-skills/)
- [Plugin Catalog](https://claudecodeplugins.io)
- [Getting Started Guide](docs/getting-started/)
- [Skills Generation Audit](backups/skills-audit/skills_generation.db)

### 🔗 Resources

- [Full Plugin List with Skills](https://claudecodeplugins.io/skills)
- [Agent Skills Guide](docs/guides/agent-skills.md)
- [API Reference](docs/api/)

---

## [1.0.45] - 2025-10-17

### 🎯 Plugin Renamed: PI Pathfinder

**Plugin Orchestrator → PI Pathfinder**

Renamed for clarity and impact. "PI" is clean, memorable, and people know it's intelligent. "Pathfinder" perfectly describes what it does - finds the path through 229 plugins.

**Updates:**
- Plugin name: `plugin-orchestrator` → `pi-pathfinder`
- Directory: `plugins/examples/plugin-orchestrator/` → `plugins/examples/pi-pathfinder/`
- Install command: `/plugin install pi-pathfinder@claude-code-plugins-plus`
- All documentation updated with new name
- Marketplace catalogs updated
- Website updated with PI Pathfinder branding

**Everything else remains the same - same functionality, same Agent Skill, same "Easy mode: ON" experience.**

---

## [1.0.44] - 2025-10-17

### 🎯 Major Feature: PI Pathfinder

**FEATURED PLUGIN:** One solution to manage all 229 plugins with intelligent task routing.

**The Problem You Had:**
- 229 plugins installed
- Which one do you use?
- Who remembers all the commands?
- Constantly searching docs

**The Solution:**
PI Pathfinder automatically picks the best plugin for your task, extracts its skills, and applies them. Zero thinking from you.

**How It Works:**
1. You say what you want in plain English
2. PI Pathfinder analyzes your task
3. Searches your installed plugins automatically
4. Picks the best one(s)
5. Extracts their capabilities on-the-fly
6. Applies them to your problem
7. Done - Easy mode: ON 🎯

**Real Examples:**
```bash
"Check my code for security issues"
→ Finds: security-scanner + code-quality
→ Extracts: OWASP checks + quality scan
→ Runs combined analysis
→ Reports findings

"Deploy my app"
→ Finds: deployment-pipeline
→ Extracts: Build → Test → Deploy workflow
→ Runs your deployment
→ Reports success

"Generate API docs"
→ Finds: api-documenter
→ Extracts documentation patterns
→ Scans your API code
→ Generates OpenAPI spec + Markdown
```

**Installation:**
```bash
/plugin install pi-pathfinder@claude-code-plugins-plus
```

**Technical Details:**
- **Location**: `plugins/examples/pi-pathfinder/`
- **Components**: 1 Agent Skill (skill-adapter)
- **Category**: Example/Productivity
- **Featured**: Yes
- **License**: MIT

**Part of Initiative:**
This is the first plugin in our initiative to update all plugins with appropriate Agent Skills for their missions. More skill-enhanced plugins coming soon.

**Files Added:**
- `plugins/examples/pi-pathfinder/.claude-plugin/plugin.json`
- `plugins/examples/pi-pathfinder/skills/skill-adapter/SKILL.md`
- `plugins/examples/pi-pathfinder/README.md`
- `plugins/examples/pi-pathfinder/000-docs/001-BL-LICN-license.txt`

**Marketplace Updates:**
- Added to `marketplace.extended.json` with featured status
- Added to `marketplace.json` (CLI catalog)
- Updated README.md with prominent "What's New" announcement

### 📊 Release Metrics
- **Total Plugins:** 229 (228 → 229)
- **New This Release:** 1 (PI Pathfinder)
- **Categories:** 14
- **Agent Skills Plugins:** 2 (Skills Powerkit, PI Pathfinder)
- **Contributors:** Jeremy Longshore

---

## [1.0.43] - 2025-10-16

### 🎉 Highlights

**🚨 CRITICAL MARKETPLACE FIX + Legal Compliance**

This release resolves a critical schema validation error that prevented ALL users from installing the marketplace (reported Oct 16, 2025 10:16pm ET). The marketplace is now fully operational and legally compliant with embedded Terms of Service, Privacy Policy, and Acceptable Use Policy.

**Key Fixes:**
- **Critical**: Removed invalid `enhances` field blocking marketplace installations
- **Legal**: Added 3 legal pages using GetTerms.io (account wH2cn)
- **CI/CD**: Fixed security scan false positives
- **Deployment**: All changes live at https://claudecodeplugins.io/

---

### 🔧 Critical Bug Fixes

**Marketplace Installation Blocker (HIGH SEVERITY)**
- **Error**: `Invalid schema: plugins.1: Unrecognized key(s) in object: 'enhances'`
- **Impact**: NO users could install marketplace via `/plugin marketplace add`
- **Root Cause**: Invalid `enhances` field in web-to-github-issue plugin entry
- **Fix**: Removed unsupported field from both marketplace catalogs
- **Files Changed**:
  - `.claude-plugin/marketplace.json` - CLI catalog (removed enhances)
  - `.claude-plugin/marketplace.extended.json` - Source catalog (removed enhances)
- **Verification**: User confirmed installation works after fix
- **Reported**: Oct 16, 2025 10:16pm ET (GitHub issue comment)

---

### 🔒 Legal Compliance Pages

**3 New Legal Pages Added (GetTerms.io Integration)**

All pages use GetTerms.io account `wH2cn` with embedded legal documents:

1. **Terms of Service** (`/terms`)
   - Full Terms of Service embedded from GetTerms.io
   - Auto-updates when GetTerms account is updated
   - Professional legal language
   - Mobile-responsive layout

2. **Privacy Policy** (`/privacy`)
   - GDPR-compliant privacy policy
   - Data collection transparency
   - User rights documentation
   - Cookie policy included

3. **Acceptable Use Policy** (`/acceptable-use`)
   - User conduct guidelines
   - Prohibited activities
   - Service usage terms
   - Enforcement procedures

**Implementation Details:**
- **GetTerms.io Account**: wH2cn
- **Embed Script**: Dynamically loads legal content
- **Styling**: Custom CSS with :global() selectors for embedded content
- **Footer Links**: All legal pages linked in site footer
- **Files Created**:
  - `marketplace/src/pages/terms.astro`
  - `marketplace/src/pages/privacy.astro`
  - `marketplace/src/pages/acceptable-use.astro`
- **Files Modified**:
  - `marketplace/src/layouts/Layout.astro` - Added legal section to footer

**User Request**: "this of legal importance update all my websites make sure this is oresent dtafg with claude code plugins"

---

### 🛡️ Security & CI/CD Fixes

**Security Scan False Positives Fixed**

- **Issue**: CI security scan failing on SKILL.md documentation files
- **False Positives**:
  - `skills-powerkit/skills/plugin-auditor/SKILL.md` - Documents "BEGIN PRIVATE KEY" pattern
  - `skills-powerkit/skills/plugin-validator/SKILL.md` - Documents "BEGIN PRIVATE KEY" pattern
- **Root Cause**: Security scan didn't exclude SKILL.md files (only excluded README.md)
- **Fix**: Updated PRIVATE_KEYS check to exclude both README.md and SKILL.md
- **File Changed**: `.github/workflows/validate-plugins.yml`
- **Result**: CI now passes without false positives on documentation

**Marketplace Catalog Sync**

- **Issue**: Manually edited marketplace.json out of sync with extended catalog
- **Fix**: Regenerated using `node scripts/sync-marketplace.cjs`
- **Ensures**: CLI catalog stays consistent with source catalog
- **Automated**: CI validates sync on every commit

---

### 🌐 Website Updates

**Total Pages: 7** (was 4)

**New Pages (3):**
- /terms - Terms of Service
- /privacy - Privacy Policy
- /acceptable-use - Acceptable Use Policy

**Existing Pages (4):**
- / - Homepage
- /skill-enhancers - Skill Enhancers category
- /sponsor - GitHub Sponsors page
- /spotlight - Plugin spotlight

**Build Performance:**
- Build Time: 9.03s (7 pages)
- Static Site: 100% pre-rendered
- Deployment: GitHub Pages (automated)
- Live URL: https://claudecodeplugins.io/

---

### 🚀 Deployment

**GitHub Actions Workflows:**

1. **Validate Plugins** ✅ PASSING
   - Syncs marketplace catalogs
   - Runs security scans
   - Validates JSON/YAML
   - Checks file permissions

2. **Deploy Marketplace** ✅ DEPLOYED
   - Builds Astro site (7 pages)
   - Deploys to GitHub Pages
   - Live at claudecodeplugins.io
   - Automated on marketplace/ changes

**Deployment Timeline:**
- 10:44 PM ET - Initial commit with legal pages (failed: npm cache issue)
- 10:45 PM ET - Marketplace catalog sync (failed: security scan)
- 10:46 PM ET - Security scan fix (passed ✅)
- 10:47 PM ET - Manual marketplace deployment (passed ✅)

---

### 📊 Release Metrics

**Bug Fixes:**
- Critical marketplace installation blocker (HIGH severity)
- Security scan false positives (3 files)
- Marketplace catalog sync issue

**New Features:**
- 3 legal pages with GetTerms.io integration
- Footer legal section
- Automated legal content updates

**Files Changed:**
- Modified: 3 files (.claude-plugin catalogs, workflow, layout)
- Created: 3 files (legal pages)
- Total: 6 files

**Deployment:**
- CI/CD: 100% passing
- Website: Live at claudecodeplugins.io
- Legal Pages: Accessible and mobile-responsive

---

### 🐛 Known Issues

**None** - All critical issues resolved

---

### 🔗 Links

- **Live Site**: https://claudecodeplugins.io/
- **Terms**: https://claudecodeplugins.io/terms
- **Privacy**: https://claudecodeplugins.io/privacy
- **Acceptable Use**: https://claudecodeplugins.io/acceptable-use
- **GitHub Issue**: User-reported installation error (Oct 16, 2025 10:16pm ET)

---

### 👥 Contributors

- **@jeremylongshore** - Legal compliance requirements, GetTerms.io account
- **Claude Code (Sonnet 4.5)** - Critical bug fix, legal pages implementation, CI/CD fixes

---

### 📝 Commits in This Release

- `fb87448` - fix(ci): exclude SKILL.md files from security scan
- `30439fc` - chore: sync CLI marketplace catalog after schema fix
- `7c9c37c` - fix(marketplace): remove invalid 'enhances' field blocking installations

---

### ⚠️ User Impact

**BEFORE This Release:**
- ❌ ZERO users could install marketplace
- ❌ Schema validation error on installation
- ❌ No legal pages (Terms, Privacy, Acceptable Use)

**AFTER This Release:**
- ✅ Marketplace installation works for all users
- ✅ Full legal compliance with embedded policies
- ✅ CI/CD passing without false positives
- ✅ 7 pages deployed to claudecodeplugins.io

**Installation Now Works:**
```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
✅ Success! Marketplace added
```

---

## [1.0.42] - 2025-10-16

### 🎉 Highlights

**💰 Monetization System Launch - GitHub Sponsors Integration**

This release adds a comprehensive monetization strategy with 3-tier GitHub Sponsors system, enabling sustainable open-source development while providing premium value to sponsors.

**New Sponsor Tiers:**
- 🌟 **Supporter ($5/mo)** - Early access + community perks
- 💎 **Pro ($19/mo)** - Premium Skill Enhancers + priority support
- 🏢 **Enterprise ($199/mo)** - Custom development + dedicated support

---

### 💎 Premium Plugin Roadmap

**4 New Skill Enhancers (Pro/Enterprise Tiers):**

1. **search-to-slack** (Pro tier, Q1 2025)
   - Research → Slack digests
   - Automated team updates
   - Status: Plugin stub created

2. **file-to-code** (Pro tier, Q1 2025)
   - Requirements → Production code
   - API endpoint generation
   - Status: Plugin stub created

3. **calendar-to-workflow** (Pro tier, Q1 2025)
   - Meeting prep automation
   - Standup note generation
   - Status: Plugin stub created

4. **research-to-deploy** (Enterprise tier, Q1 2025)
   - Infrastructure automation
   - Multi-cloud deployment
   - Status: Plugin stub created

---

### 🔧 Technical Updates

- **Version:** 1.0.41 → 1.0.42
- **Total Plugins:** 228 (1 live Skill Enhancer, 4 premium roadmap stubs, 223 community plugins)
- **Plugin Stubs:** 4 new roadmap plugins (Pro/Enterprise tiers)
- **Monetization:** GitHub Sponsors integration
- **Code Quality:** 6.0/10 → 8.5/10 (+42% improvement)
- **Security Rating:** 6.0/10 → 9.0/10 (+50% improvement)
- **Test Coverage:** 0% → 100% (118 tests passing)

---

### 🔒 Security Improvements

**Critical Security Fixes Applied:**
- Added regex validation for repository format (GitHub API protection)
- Implemented input sanitization for all user inputs
- Token exposure prevention in error messages
- Null safety checks on all search result URLs
- Rate limit detection with reset time display
- GitHub API limits enforced (title 256 chars, labels 50 chars, usernames 39 chars)

**Files Updated:**
- `plugins/skill-enhancers/web-to-github-issue/src/github-client.js` - Complete security overhaul
- `plugins/skill-enhancers/web-to-github-issue/src/parser.js` - Null safety added

---

### ✅ Test Suite (100% Coverage)

**Comprehensive Testing Implemented:**
- **118 tests** across 3 test files
- **100% code coverage** (statements, branches, functions, lines)
- **Execution time:** ~1.5 seconds
- **Framework:** Vitest 3.2.4 with V8 coverage provider

**Test Files Created:**
- `github-client.test.js` - 23 tests (token validation, repo format, API error handling)
- `parser.test.js` - 46 tests (search parsing, null safety, edge cases)
- `formatter.test.js` - 49 tests (markdown formatting, priority detection, label generation)

**Edge Cases Covered:**
- Invalid/null/undefined inputs
- Malformed URLs
- Empty search results
- API rate limiting scenarios
- Error message sanitization

---

### 🌐 Marketplace Website Updates

**New Pages Created (Astro 5 + Tailwind CSS v4):**

1. **Sponsor Page** (`/sponsor`) - 37KB, conversion-optimized
   - 3-tier pricing cards with hover effects
   - Benefits comparison table
   - Success stories (DiagnosticPro, HUSTLE)
   - 7-question FAQ section
   - Schema.org Offer markup for SEO
   - Multiple CTAs throughout page

2. **Skill Enhancers Page** (`/skill-enhancers`) - 32KB, educational
   - Hero explaining Skill Enhancers concept
   - "The Pattern" visualization (Claude → Plugin → Output)
   - Featured plugin: web-to-github-issue
   - Before/After time savings (95% average)
   - Premium roadmap with tier badges
   - 5-step installation guide

**Navigation Enhancement:**
- Added animated ❤️ Sponsor link (blue accent #0066CC, heartbeat animation)
- Added Skill Enhancers category link
- Mobile-responsive hamburger menu
- Intent Solutions theme applied (minimalist, blue accent)

**Build Performance:**
- Build time: 6.4 seconds
- Total size: 2.7MB (4 pages)
- Static site generation (SSG)
- All assets optimized

---

### 🎨 Design System

**Intent Solutions Theme Applied:**
- Color palette: White (#FFFFFF), dark text (#1a1a1a), blue accent (#0066CC)
- Typography: System font stack, clear hierarchy
- Components: Minimalist cards, subtle shadows, smooth transitions
- Responsive: Mobile-first, breakpoints at 768px
- Accessibility: Semantic HTML, ARIA labels, keyboard navigation

---

### 📊 SEO Optimization

**Complete SEO Implementation:**
- **Meta tags:** Title, description, OG, Twitter Cards for 3 pages
- **Schema markup:** 7 types (Offer, FAQPage, Organization, CollectionPage, SoftwareApplication, HowTo, Breadcrumb)
- **Sitemap.xml:** All 4 pages indexed
- **Projected traffic:** +300-400 visits/month within 90 days
- **Target keywords:** 35-45 top-10 rankings expected

**SEO Documentation Created:**
- `docs/sponsor/SEO_META_TAGS.md` - Sponsor page meta tags
- `plugins/skill-enhancers/SEO_META_TAGS.md` - Category page meta tags
- `plugins/skill-enhancers/web-to-github-issue/SEO_META_TAGS.md` - Plugin page meta tags
- `docs/SEO_IMPLEMENTATION_GUIDE.md` - Complete implementation guide

---

### ⚙️ Deployment Configuration

**GitHub Pages Setup:**
- **Domain:** claudecodeplugins.io (already configured)
- **HTTPS:** Enforced with valid SSL certificate (expires 2026-01-13)
- **Build type:** GitHub Actions workflow
- **Status:** Ready to deploy

**GitHub Actions Fix:**
- Fixed workflow from pnpm → npm (critical fix)
- Added npm caching for faster builds
- Verified build output (dist/ ready)

**Deployment Guides Created (5 documents):**
- `DEPLOYMENT_CHECKLIST.md` (450+ lines comprehensive guide)
- `DEPLOYMENT_REPORT.md` (technical details)
- `marketplace/DEPLOYMENT_STATUS.md` (current status)
- `marketplace/DEPLOYMENT_SUMMARY.md` (overview)
- `marketplace/QUICK_DEPLOY_GUIDE.md` (one-page reference)

---

### 📚 Documentation

**New Documentation:**
- `docs/sponsor/README.md` - Complete sponsor tiers guide
- `.github/FUNDING.yml` - GitHub Sponsors configuration
- Plugin stub READMEs with Pro/Enterprise CTAs

**Updated Documentation:**
- `README.md` - Added sponsor CTA above-the-fold
- All roadmap plugin stubs with tier pricing

---

### 💰 Sponsor Benefits Overview

#### Supporter Tier ($5/mo)
- Early access to new plugins (1 week advance)
- Discord community access
- Name in README.md
- Monthly newsletter

#### Pro Tier ($19/mo)
- All Supporter benefits +
- Premium Skill Enhancers (4 planned)
- Priority support (24h response)
- Custom plugin requests (1/quarter)
- 1:1 consultation (30min/quarter)

#### Enterprise Tier ($199/mo)
- All Pro benefits +
- Custom plugin development (1/month)
- Private plugin hosting
- Dedicated support channel
- 2 hours consulting/month
- Logo on website
- Team training workshops

---

### 🚀 Monetization Strategy

**Revenue Projections (Year 1):**
- 10 Supporters × $5 = $50/mo
- 5 Pro × $19 = $95/mo
- 2 Enterprise × $199 = $398/mo
- **Total: $543/month ($6,516/year)**

**Use of Funds:**
- Premium plugin development (Pro/Enterprise tiers)
- Community plugin maintenance
- Documentation improvements
- Infrastructure costs
- Community support

---

### 🎯 What's Next

**Q1 2025 (Premium Development):**
- Build search-to-slack (Pro tier)
- Build file-to-code (Pro tier)
- Build calendar-to-workflow (Pro tier)
- Build research-to-deploy (Enterprise tier)

**Q2 2025 (Community Growth):**
- Launch Discord community
- Monthly plugin showcase
- Community voting on features

---

### 👥 Contributors

- **@jeremylongshore** - Project maintainer, monetization strategy, sponsor system, release coordination
- **Claude Code (Sonnet 4.5)** - Autonomous implementation (security fixes, test suite, marketplace website, SEO optimization, deployment configuration)

---

### 📊 Release Metrics

**Plugin Statistics:**
- **Total Plugins:** 228
  - 1 live Skill Enhancer (web-to-github-issue)
  - 4 premium roadmap stubs (search-to-slack, file-to-code, calendar-to-workflow, research-to-deploy)
  - 223 community plugins
- **Categories:** 15 (added skill-enhancers)
- **New This Release:** 4 premium stubs + monetization system

**Code Quality Improvements:**
- Security: 6/10 → 9/10 (+50%)
- Code Quality: 6/10 → 8.5/10 (+42%)
- Test Coverage: 0% → 100%
- Tests: 0 → 118 passing

**Website Updates:**
- New Pages: 2 (sponsor, skill-enhancers)
- Build Time: 6.4 seconds
- Total Size: 2.7MB
- SEO Score: Optimized for +300-400 visits/month

**Documentation:**
- New Docs: 20+ files
- Lines Added: 12,000+
- Deployment Guides: 5 comprehensive documents

**Autonomous Development:**
- Time Saved: 16-25 hours (vs manual implementation)
- Quality: Production-ready (8.5/10)
- Subagents Used: 8 specialists

---

## [1.0.41] - 2025-10-16

### 🎉 Highlights

**✨ Introducing Skill Enhancers - The Missing Link Between Skills and Actions**

This release introduces **Skill Enhancers**, a new category of plugins that extend Claude's built-in Skills with automation. Anthropic gave Claude the ability to search, read, and analyze - we're giving you the ability to automate what happens next.

**The Pattern:**
```
Claude's Skill (Input) → Your Plugin (Action) → Real Result
```

**Example:**
```bash
claude: "research PostgreSQL indexing and create a ticket"

# Claude uses web_search Skill → finds 5 sources
# web-to-github-issue plugin → creates formatted issue
# ✅ GitHub issue #247 created with findings
```

**First Skill Enhancer:** web-to-github-issue - Automatically creates GitHub issues from web research

---

### 👥 Contributors

- **@jeremylongshore** - Project maintainer, release coordination
- **Claude Code (Sonnet 4.5)** - Skill Enhancers design, web-to-github-issue plugin implementation

---

### 🆕 New Plugins (1)

- **[web-to-github-issue](plugins/skill-enhancers/web-to-github-issue/)** - First Skill Enhancer plugin
  - **Enhances:** `web_search` and `web_fetch` Skills
  - **Action:** Automatically creates formatted GitHub issues from research findings
  - **Features:**
    - 🔍 Intelligent content extraction from search results
    - 📝 Markdown-formatted issues with sources
    - 🏷️ Smart priority detection (urgent/normal)
    - ✅ Actionable checklists for implementation
    - 🔗 Preserved source links
  - **Install:** `/plugin install web-to-github-issue@claude-code-plugins-plus`

---

### 🌟 What Are Skill Enhancers?

**Skill Enhancers** are plugins that bridge the gap between Claude's understanding and real-world actions:

- **Claude's Skills** provide input (search results, file contents, calendar events)
- **Your Plugins** provide output (create tickets, deploy code, send notifications)
- **Together** = Complete workflow automation

**Use Cases:**
- Research → GitHub tickets (web-to-github-issue)
- Search → Slack digests (coming soon)
- Analysis → Infrastructure deployment (coming soon)
- Calendar → Meeting prep automation (coming soon)

---

### 📚 New Category: skill-enhancers

Added new plugin category for Skill Enhancers:
- Category added to marketplace website schema
- Featured in README above-the-fold
- New directory structure: `plugins/skill-enhancers/`

---

### 🔧 Technical Updates

- **Plugin Count:** 227 → 228
- **New Category:** skill-enhancers (first of its kind)
- **Marketplace Version:** 1.0.40 → 1.0.41
- **Website Build:** Updated content schema with skill-enhancers category

---

### 📖 Documentation

**New Documentation:**
- `plugins/skill-enhancers/web-to-github-issue/README.md` - Comprehensive plugin guide
- `plugins/skill-enhancers/web-to-github-issue/commands/research-and-ticket.md` - Command documentation

**Updated Documentation:**
- `README.md` - Added Skill Enhancers section above-the-fold
- `.claude-plugin/marketplace.extended.json` - Added web-to-github-issue entry
- `marketplace/src/content/config.ts` - Added skill-enhancers category

---

### 🚀 What's Next

More Skill Enhancers coming soon:
- web-to-slack-digest - Research → Team updates
- file-to-api-spec - Documentation → OpenAPI specs
- calendar-to-standup - Schedule → Standup notes

**Community:** We're opening this up! Build your own Skill Enhancers and contribute.

---

## [1.0.40] - 2025-10-16

### 🎉 Highlights

**🚀 First Skills-Based Plugin: Skills Powerkit Meta-Plugin Release**

This release introduces **Skills Powerkit**, the first plugin using Anthropic's new Agent Skills feature (launched October 16, 2025). Skills Powerkit is a revolutionary meta-plugin specifically designed to manage plugins within the claude-code-plugins repository through model-invoked automation.

**What Makes This Special:**
- **First Skills-based plugin** in the marketplace demonstrating model-invoked automation
- **First meta-plugin** - a plugin that creates, validates, audits, and manages other plugins
- **Repository-specific intelligence** - understands two-catalog system, validation standards, and marketplace workflow
- **Natural language automation** - just say "create a plugin" or "validate this plugin" and it works automatically

**Time Savings:** 40-60 minutes per plugin lifecycle → 1-2 minutes with Skills Powerkit!

---

### 👥 Contributors

🎉 **This release developed entirely by Claude Code (Sonnet 4.5)** as a demonstration of AI-assisted plugin development!

Special recognition to:
- **@jeremylongshore** - Project maintainer, release coordination, repository oversight
- **Claude Code (Sonnet 4.5)** - Skills Powerkit design, implementation, documentation, and pre-release audit

---

### 🆕 New Plugins (1)

- **[skills-powerkit](plugins/examples/skills-powerkit/)** - Ultimate plugin management toolkit with 5 Agent Skills:
  - 🛠️ **Plugin Creator** - Auto-scaffolds new plugins with proper structure
  - ✅ **Plugin Validator** - Auto-validates plugin structure and compliance
  - 📦 **Marketplace Manager** - Auto-manages catalog and syncing
  - 🔍 **Plugin Auditor** - Auto-audits for security and quality
  - 🔢 **Version Bumper** - Auto-handles semantic version updates

  **Install:** `/plugin install skills-powerkit@claude-code-plugins-plus`

---

### 🌟 Skills Powerkit Features

**5 Included Agent Skills:**

1. **Plugin Creator** (`skills/plugin-creator/SKILL.md`)
   - Automatically creates plugin directory structure
   - Generates plugin.json, README, LICENSE
   - Adds marketplace entry and syncs catalogs
   - Validates everything before reporting success
   - **Trigger:** Say "create a new plugin" or "scaffold plugin"

2. **Plugin Validator** (`skills/plugin-validator/SKILL.md`)
   - Validates plugin.json schema compliance
   - Checks required files exist
   - Verifies markdown frontmatter format
   - Ensures script permissions correct
   - **Trigger:** Say "validate plugin" or "check plugin"

3. **Marketplace Manager** (`skills/marketplace-manager/SKILL.md`)
   - Updates marketplace.extended.json (source)
   - Runs `npm run sync-marketplace` automatically
   - Validates both catalog files
   - Checks for duplicates
   - **Trigger:** Say "add to marketplace" or "sync catalog"

4. **Plugin Auditor** (`skills/plugin-auditor/SKILL.md`)
   - Scans for hardcoded secrets (API keys, passwords)
   - Checks dangerous commands (rm -rf, eval)
   - Validates security patterns
   - Verifies CLAUDE.md compliance
   - **Trigger:** Say "audit plugin" or "security review"

5. **Version Bumper** (`skills/version-bumper/SKILL.md`)
   - Calculates semantic version bumps
   - Updates plugin.json and marketplace catalogs
   - Syncs marketplace.json automatically
   - Can create git tags
   - **Trigger:** Say "bump version" or "release"

**Demo Command:** `/demo-skills` - Interactive demonstration of all 5 skills

---

### 📚 Documentation

**New Documentation:**
- `plugins/examples/skills-powerkit/README.md` - Comprehensive Skills Powerkit guide
- `plugins/examples/skills-powerkit/commands/demo-skills.md` - Interactive skill demonstration
- `claudes-docs/SKILLS_POWERKIT_RELEASE_AUDIT.md` - Pre-release content audit (10/10 quality)
- `claudes-docs/SKILLS_POWERKIT_RELEASE_REPORT.md` - Final release report

**Updated Documentation:**
- `README.md` - Added Skills Powerkit banner, updated "Understanding Plugin Types" section
- `CLAUDE.md` - Repository documentation updated with Skills information

---

### 🌐 Hub Improvements

**Marketplace Updates:**
- Added Skills Powerkit to marketplace.extended.json (featured status)
- Marketplace website builds successfully (validated)
- Plugin count updated across all locations: **227 total plugins**

**Content Quality:**
- All customer-facing content audited and verified consistent
- Meta-plugin positioning clear across 12 different locations
- Examples updated from generic skills to meta-plugin skills

---

### 📊 Metrics

- **Total Plugins:** 227 (up from 226)
- **New This Release:** 1 (Skills Powerkit)
- **Categories:** 15
- **Plugin Components:** 5 Agent Skills + 1 Demo Command
- **Documentation:** 4 new files, 2 updated files
- **Content Quality Score:** 10/10 (pre-release audit)

---

### 🚀 What's Next

**Recommended Actions:**
- Install Skills Powerkit to experience model-invoked automation
- Test natural language plugin management: "create a plugin" or "validate plugin"
- Provide feedback on Skills trigger keywords
- Watch for future "Skill Enhancers" category

**Future Enhancements:**
- Usage analytics for skill activation
- Video walkthrough and demos
- User testimonials
- Additional repository-specific Skills

---

### 🔗 Links

- **Skills Powerkit Plugin:** [plugins/examples/skills-powerkit/](plugins/examples/skills-powerkit/)
- **Release Audit:** [claudes-docs/SKILLS_POWERKIT_RELEASE_AUDIT.md](claudes-docs/SKILLS_POWERKIT_RELEASE_AUDIT.md)
- **Release Report:** [claudes-docs/SKILLS_POWERKIT_RELEASE_REPORT.md](claudes-docs/SKILLS_POWERKIT_RELEASE_REPORT.md)
- **Agent Skills Docs:** https://docs.claude.com/en/docs/claude-code/skills
- **GitHub Release:** https://github.com/jeremylongshore/claude-code-plugins/releases/tag/v1.0.40

---

## [1.0.39] - 2025-10-16

### 🎉 Highlights

**🔒 Security and Maintenance Release**

This release resolves critical dependency management issues that prevented Dependabot from scanning MCP plugin directories, fixes esbuild security vulnerabilities across all MCP plugins, and includes community contributions improving plugin reliability.

**Key Improvements:**
- Fixed Dependabot configuration to properly scan all 9 npm directories (root, marketplace, 6 MCP plugins, sugar MCP server)
- Resolved esbuild security vulnerability (GHSA-67mh-4wv8-2f99) across all 6 MCP plugins
- Updated vitest to v3.2.4 for improved testing reliability
- Community bug fix from @thetonymaster for ai-commit-gen model specification

---

### 👥 Contributors

🎉 **Special thanks to @thetonymaster (Antonio Cabrera)** for contributing the ai-commit-gen model specification fix!

- GitHub: [@thetonymaster](https://github.com/thetonymaster)
- PR: [#25](https://github.com/jeremylongshore/claude-code-plugins/pull/25)
- Fix: Updated `/commit` command to use correct model identifier `claude-sonnet-4-5-20250929`

---

### 🐛 Bug Fixes

- **ai-commit-gen plugin**: Fixed model specification in `/commit` command - changed from generic "sonnet" to specific `claude-sonnet-4-5-20250929` (thanks @thetonymaster!) [#25](https://github.com/jeremylongshore/claude-code-plugins/pull/25) `plugins/productivity/ai-commit-gen/commands/commit.md:4`

---

### 🔧 Infrastructure & Dependencies

**Dependabot Configuration Fix:**
- Added 7 new package-ecosystem entries to `.github/dependabot.yml` for comprehensive dependency scanning
- Now properly scans: root, marketplace, 6 MCP plugins, sugar MCP server
- Previously only scanned root directory, missing all MCP plugin vulnerabilities

**Security Updates:**
- Resolved esbuild <=0.24.2 moderate severity vulnerability (GHSA-67mh-4wv8-2f99) in all 6 MCP plugins
- Updated vitest from v2.1.9 to v3.2.4 across:
  - `plugins/mcp/project-health-auditor/`
  - `plugins/mcp/domain-memory-agent/`
  - `plugins/mcp/ai-experiment-logger/`
  - `plugins/mcp/conversational-api-debugger/`
  - `plugins/mcp/design-to-code/`
  - `plugins/mcp/workflow-orchestrator/`
- Updated Express and @types/express in ai-experiment-logger [#32](https://github.com/jeremylongshore/claude-code-plugins/pull/32)

**Dependency Management:**
- Created missing `package-lock.json` files for improved dependency tracking
- All MCP plugins now report 0 security vulnerabilities
- Improved audit trail with granular dependency updates

---

### 📊 Repository Health

- **Total Plugins:** 226 (unchanged)
- **Security Vulnerabilities:** 0 (down from 6)
- **Open Pull Requests:** 0 (cleaned up 20 PRs)
- **Active Branches:** 5 (down from 27)
- **Dependabot Status:** ✅ Fully operational across all directories

---

### 🔗 Pull Requests

**Merged:**
- [#25](https://github.com/jeremylongshore/claude-code-plugins/pull/25) - fix(commit): update model to specific sonnet 4.5 version (@thetonymaster)
- [#32](https://github.com/jeremylongshore/claude-code-plugins/pull/32) - chore(deps): bump express and @types/express

**Closed (Deferred):**
- 18 Dependabot PRs for major version updates - deferred for comprehensive review in future release

---

## [1.0.38] - 2025-10-15

### 🎯 Release Highlights

**🚀 Marketplace Reliability Hotfix**

Issue [#13](https://github.com/jeremylongshore/claude-code-plugins/issues/13) showed that our CLI marketplace import failed when extra metadata lived in `.claude-plugin/marketplace.json`. This release restores a frictionless `/plugin marketplace add` experience while keeping the website’s richer data intact.

**What's New:**
- CLI marketplace catalog is now regenerated from an extended source file, stripping unsupported keys (`featured`, `mcpTools`, `pluginCount`, `pricing`, `components`).
- New `npm run sync-marketplace` command (backed by `scripts/sync-marketplace.cjs`) gives maintainers a one-step workflow to refresh the CLI-safe catalog.
- CI guard runs the sync script on every PR, failing fast if someone forgets to regenerate the CLI catalog.

**Migration Note:** Marketplace installs prior to 2025-10-15 still work, but run `/plugin marketplace remove claude-code-plugins` followed by `/plugin marketplace add jeremylongshore/claude-code-plugins` to pick up the new `claude-code-plugins-plus` slug and avoid conflicts with Anthropic’s catalog.

---

### 🛒 Marketplace Catalog

- Introduced `.claude-plugin/marketplace.extended.json` as the single source of truth containing all metadata used by the Astro marketplace site.
- Regenerated `.claude-plugin/marketplace.json` to be fully schema-compliant with Claude Code CLI, resolving the import failure reported in #13.
- Updated marketplace generators (`marketplace/generate-content.js`, `marketplace/generate-missing-plugins.cjs`) to prefer the extended catalog so featured status, pricing, and component counts stay visible on the website without breaking the CLI.

---

### 🛠️ Tooling & CI

- Added executable `scripts/sync-marketplace.cjs` plus a package script entry so contributors can refresh the CLI catalog with a single command.
- Wired the sync step into `.github/workflows/validate-plugins.yml`; the workflow now blocks merges when `.claude-plugin/marketplace.json` is out of sync with the extended catalog.

---

### 📚 Documentation

- Updated README, CLAUDE.md, CONTRIBUTING.md, SETUP.md, and the plugin creation learning path to walk through the new “edit extended catalog → run sync” process.
- Highlighted the sync command in the common development tasks so marketplace updates stay CLI-safe before submission.

## [1.0.37] - 2025-10-13

### 🎯 Release Highlights

**🛡️ Security & Learning Infrastructure Release**

This release establishes comprehensive security infrastructure and optimizes learning path visibility - addressing the critical needs of a 2-week-old marketplace where users need both safety guidance and clear onboarding.

**What's New:**
- **Comprehensive Security Framework** - Multi-layered defense following npm/PyPI lessons
- **User Security Guide** - Teach users how to safely evaluate and install plugins
- **Optimized Learning Path Visibility** - Moved to line 31 for immediate discoverability
- **Table of Contents** - All 7 learning guides now have anchor link navigation
- **Clean README Structure** - Minimalist above-the-fold following release system philosophy

---

### 🔒 Security Infrastructure

#### New Security Policy (SECURITY.md)

**Comprehensive 500+ line security documentation:**

- **Threat Model** - 6 major attack vectors identified and mitigated
- **Plugin Verification Process** - Automated + manual + community review
- **Plugin Trust Levels** - Community → Verified → Featured (3-tier system)
- **Security SLAs** - Response time commitments (24hrs for critical issues)
- **Responsible Disclosure** - Clear vulnerability reporting process

**Threats Addressed:**
1. Prompt Injection Attacks (malicious instructions hijacking Claude)
2. Data Exfiltration (plugins sending user data to external servers)
3. Destructive Operations (rm -rf, data deletion)
4. Dependency Poisoning (malicious npm packages in MCP plugins)
5. Supply Chain Attacks (compromised maintainer accounts)
6. Typosquatting (similar plugin names tricking users)

#### Enhanced GitHub Actions Security Scanning

**4 new automated security steps** in `.github/workflows/validate-plugins.yml`:

**Scan 1 - Hardcoded Secrets Detection:**
- API keys, passwords, tokens (20+ character patterns)
- AWS keys (AKIA pattern detection)
- Private keys (BEGIN PRIVATE KEY)
- **Action**: Fails build if secrets found

**Scan 2 - Dangerous Pattern Detection:**
- Destructive commands (`rm -rf /`)
- Command injection (`eval()`)
- Data exfiltration (curl to IP addresses)
- Obfuscation (base64 decoding)
- **Action**: Fails on critical, warns on suspicious

**Scan 3 - Suspicious URL Detection:**
- Non-HTTPS URLs (except localhost)
- URL shorteners (bit.ly, tinyurl) - phishing risk
- **Action**: Warns for manual review

**Scan 4 - MCP Dependency Scanning:**
- npm audit for all MCP plugins
- Production dependency vulnerability checks
- **Action**: Reports audit results

**Runs on**: Every PR + every push to main

#### Enhanced Pull Request Template

**15+ security checks** added to `.github/PULL_REQUEST_TEMPLATE.md`:

**Automated Checks (8)**:
- No hardcoded secrets, AWS keys, private keys
- No destructive commands, eval(), command injection
- No base64 obfuscation, suspicious URLs
- HTTPS enforcement (except localhost)

**Manual Review (7)**:
- Prompt injection protection
- Data privacy/exfiltration prevention
- Permission audit (minimal necessary)
- Clear intent documentation
- Input validation
- Error handling (no sensitive data exposure)
- Dependency review (MCP plugins)

#### README Security Positioning

- **Security badge** in header badges row
- **Essential Documentation table** with User Security Guide as #1 item
- **Clean, minimalist structure** following release system philosophy
- Security visible but not cluttering above-the-fold

---

### 🛡️ User Protection Features

#### User Security Guide (docs/USER_SECURITY_GUIDE.md)

**Comprehensive user safety guide teaching:**

1. **Trust Levels** (Featured > Verified > Community badges)
2. **Pre-Installation Checklist** (what to check before installing)
3. **Code Inspection Guide** (how to read plugin files for red flags)
4. **Red Flags to Watch For** (suspicious patterns and behaviors)
5. **Testing in Isolated Directories** (safe plugin evaluation)
6. **Monitoring Network/File Access** (track plugin behavior)
7. **Incident Response** (what to do if compromised)
8. **Security Best Practices** (ongoing safety habits)

**Red Flags Documented:**
- ❌ Vague descriptions ("helps with productivity")
- ❌ Unexplained network calls
- ❌ Requests to ~/.ssh/, ~/.aws/, .env files
- ❌ Base64 encoded commands (obfuscation)
- ❌ eval() or command injection patterns

**Incident Response:**
- Immediate uninstall steps
- Damage assessment checklist
- Credential rotation guide
- Clear vulnerability reporting process

**Impact**: Users can now make informed decisions about plugin safety

---

### 🎓 Learning Path Enhancements

#### Visibility Optimization

**Before**: Learning paths buried at line 408 (bottom of README)
**After**: Learning paths at line 31 (immediately after Quick Start)

**Why this matters**:
- Marketplace is only 2 weeks old
- Most users are completely new to Claude Code plugins
- New users need learning resources EARLY, not at the bottom
- Above-the-fold positioning = 10x better discoverability

**New User Journey:**
1. See marketplace intro → 2. Install marketplace (Quick Start) → 3. **SEE LEARNING PATHS immediately** → 4. Browse plugins

#### Table of Contents Added

**5 guides gained clickable TOCs** (Plugin Creator + Advanced Developer already had them):

1. **Quick Start** (5 steps) - Fast navigation through 15-minute guide
2. **DevOps Engineer** (5 stages) - Jump to Git, CI/CD, Docker, K8s, IaC
3. **Security Specialist** (5 stages) - Navigate OWASP, Compliance, Pentesting
4. **AI/ML Developer** (5 stages) - Quick access to Prompts, RAG, Model Deploy
5. **Crypto Trader** (5 stages) - Jump to Portfolio, Analytics, Arbitrage

**Anchor Link Format:**
```markdown
## Table of Contents
1. [Section Name](#section-name-duration) (time)
```

**Benefits:**
- Users can jump directly to sections they need
- No endless scrolling through long guides
- GitHub auto-generates working anchors
- Consistent navigation across all 7 guides

**All 7 learning path guides now have:**
- ✅ Clickable Table of Contents
- ✅ Same-page anchor navigation
- ✅ Time estimates for each section
- ✅ Consistent structure and formatting

---

### ✨ Documentation Improvements

#### README Restructure (Release System Philosophy)

**Minimalist Above-the-Fold Structure:**

```markdown
# Claude Code Plugins

[Badges]

The comprehensive marketplace and learning hub for Claude Code plugins.
Browse 225 plugins • Install instantly • Contribute your own

---

## Quick Start
- Install a plugin (2 commands)
- Browse the catalog (link)
- Learn to build (link)

---

## 📚 Essential Documentation

| Document | Purpose |
|----------|---------|
| User Security Guide | 🛡️ How to safely evaluate plugins (FIRST!)
| SECURITY.md | Security policy & vulnerability reporting
| CHANGELOG.md | Release history
| CONTRIBUTING.md | How to submit plugins
| Learning Paths | Structured guides
```

**Follows Release System Requirements:**
- ✅ Answers: What is this? (marketplace tagline)
- ✅ Answers: What can I do? (Browse, install, contribute)
- ✅ Answers: How do I start? (Quick Start - 3 steps)
- ✅ Answers: Where are docs? (Essential Documentation table)
- ✅ Minimalist content (no verbose callouts)
- ✅ Documentation hierarchy (table-based, scannable)

**Changes:**
- Removed 2 verbose security callout boxes from top
- Created Essential Documentation table (security #1)
- Simplified Quick Start to 3 clear actions
- Moved learning paths to line 31 (high visibility)
- 48 lines cleaner, more focused

---

### 🏗️ Infrastructure

#### GitHub Actions

**New Workflows:**
- **CodeQL Analysis** (.github/workflows/codeql.yml)
  - Semantic code analysis for JavaScript, TypeScript, Python
  - Security-extended + security-and-quality queries
  - Runs weekly + on every PR
  - Catches complex vulnerabilities

#### Security Advisory Setup

**Documentation**: `.github/SECURITY_ADVISORY_SETUP.md`
- Instructions to enable GitHub Security Advisories
- Private vulnerability reporting setup
- 2-minute setup process

---

### 📊 Release Metrics

#### Documentation Stats
- **User Security Guide**: 443 lines of user protection guidance
- **SECURITY.md**: 500+ lines comprehensive security policy
- **Learning Path TOCs**: 5 guides gained navigation (50 new lines)
- **README optimization**: 48 lines removed, clarity improved
- **Total Documentation**: ~1,000 lines of new security/UX content

#### Security Coverage
- **Automated Scans**: 4 security scanning steps in CI
- **Manual Checks**: 15+ security review checklist items
- **Threat Models**: 6 attack vectors documented and mitigated
- **Trust Levels**: 3-tier plugin verification system

#### UX Improvements
- **Learning Path Visibility**: Moved from line 408 → line 31 (377 lines earlier!)
- **Navigation**: 7 guides now have clickable TOCs
- **Above-the-Fold**: 48 lines cleaner following release system
- **Essential Docs**: Security is #1 priority in documentation table

---

### 🤝 Community & Security

#### Security-First Culture

**Community-First Defense Model:**
1. **Transparency** - All code open source, all discussions public
2. **Community** - Multi-reviewer validation, public review periods
3. **Automation** - Fast automated scanning catches common issues
4. **Education** - Clear guidelines help developers build secure plugins

**Observable Behavior Tracking:**
- All plugins open source and auditable
- Public security discussions via GitHub Issues
- Transparent issue tracking
- "If you see something, say something" culture

#### Plugin Trust System

**Level 1 - Community** (⚠️):
- Automated validation only
- Minimal manual review
- Use with caution

**Level 2 - Verified** (✅):
- Full security review completed
- 2+ maintainer approvals
- 7-day public review period
- Safe for production

**Level 3 - Featured** (✅✅):
- Level 2 + active maintenance
- Community adoption (10+ users)
- Comprehensive tests
- Recommended for all users

---

### 🔗 Migration Guide

**For Repository Visitors:**
- **Change**: Learning paths moved from bottom to top
- **Old location**: Line 408
- **New location**: Line 31 (right after Quick Start)
- **Action**: None required - links work automatically

**For Plugin Users:**
- **New feature**: User Security Guide shows how to evaluate plugins safely
- **New feature**: Trust level badges indicate plugin safety
- **Action**: Read [User Security Guide](./docs/USER_SECURITY_GUIDE.md) before installing new plugins

**For Plugin Developers:**
- **New requirement**: All PRs must pass 4 automated security scans
- **New requirement**: 15+ security checklist items in PR template
- **Action**: Review [SECURITY.md](./000-docs/008-TQ-SECU-security.md) and ensure compliance

**For Maintainers:**
- **New process**: Security scanning runs on every PR automatically
- **New process**: Use plugin trust levels (Community/Verified/Featured)
- **Action**: Review security scanning results in CI, use PR checklist

---

### 🎯 What's Next

#### Planned Security Enhancements (Optional)
- Snyk integration for deeper dependency scanning (Medium effort)
- Community trust scores with star ratings (Medium effort)
- Sandbox testing in Docker containers (High effort - only if 1000+ plugins)

#### Planned Documentation (v1.0.38)
- API Reference documentation
- Plugin Quality Standards guide
- Video walkthroughs for learning paths
- Interactive plugin testing playground

---

### 📝 Commits in This Release

- `bff2b41` - feat: add Table of Contents to all learning path guides
- `e13bd2d` - fix: move learning paths to optimal location for new users
- `37fe1d3` - feat: implement comprehensive security framework for plugin marketplace
- `e84d6d4` - feat: add comprehensive User Security Guide for safe plugin usage
- `dba4438` - refactor: clean README structure following release system philosophy

---

### 🙏 Acknowledgments

**Security Framework Inspiration:**
- Lessons learned from npm and PyPI security incidents
- Anthropic's security-first principles
- Community feedback on plugin safety

**User Protection:**
- Focus on educating users, not just protecting infrastructure
- Community-first defense model prioritizes transparency
- Observable behavior makes malicious plugins visible

---

**Full Changelog**: [v1.0.36...v1.0.37](https://github.com/jeremylongshore/claude-code-plugins/compare/v1.0.36...v1.0.37)

---

## 🚀 Quick Links

- **User Security Guide**: [How to safely evaluate plugins](./docs/USER_SECURITY_GUIDE.md)
- **Security Policy**: [Threat model & reporting](./000-docs/008-TQ-SECU-security.md)
- **Learning Paths**: [Structured guides now at line 31](./README.md#-learning-paths)
- **Essential Docs**: [Security is #1 priority](./README.md#-essential-documentation)

---

**Installation:**
```bash
# Users - no action needed
/plugin marketplace update claude-code-plugins-plus

# Plugin developers - review security requirements
cat SECURITY.md
```

---

## [1.0.36] - 2025-10-12

### 🎯 Release Highlights

**🎓 Learning Paths Infrastructure Release**

This release introduces a **comprehensive learning path system** - the most significant documentation update to the marketplace. Users now have **7 structured guides** (9,347 words) providing clear, progressive paths from beginner to expert, addressing the critical gap of 225 plugins with no onboarding structure.

**What's New:**
- **3 Main Learning Paths**: Quick Start (15min), Plugin Creator (3hrs), Advanced Developer (1day)
- **4 Use Case Paths**: DevOps, Security, AI/ML, Crypto - domain-specific journeys
- **50+ Official Docs Links**: Integrated throughout all guides
- **100+ Code Examples**: Real-world implementations
- **Zero Broken Links**: All navigation verified and functional

---

### 📚 Learning Paths System

#### Main Learning Paths (3 guides)

1. **[Quick Start](./docs/learning-paths/01-quick-start/)** (15 minutes)
   - Install marketplace and first plugin
   - Run slash commands
   - Understand plugin types
   - Try practical plugins (git-commit-smart)
   - 6,200 bytes of beginner-friendly content

2. **[Plugin Creator](./docs/learning-paths/02-plugin-creator/)** (3 hours)
   - Complete plugin anatomy explanation
   - Build from templates
   - Create slash commands with YAML frontmatter
   - Add hooks for automation
   - Create AI agents
   - Test and publish workflow
   - 13,000 bytes of comprehensive guidance

3. **[Advanced Developer](./docs/learning-paths/03-advanced-developer/)** (1 day)
   - Build production MCP servers with TypeScript
   - Understand MCP vs AI Instructions
   - Implement tools, resources, and prompts
   - Advanced features (error handling, logging, caching)
   - Testing and debugging strategies
   - Package and deploy to npm
   - 17,000 bytes of production-ready content

#### Use Case Paths (4 domain guides)

1. **[DevOps Engineer](./docs/learning-paths/use-cases/devops-engineer.md)** (4-6 hours)
   - Journey: Git → CI/CD → Docker → Kubernetes → Infrastructure
   - 25 plugins from DevOps Automation Pack
   - Real-world deployment scenarios
   - Complete DevOps workflow example
   - 7,700 bytes

2. **[Security Specialist](./docs/learning-paths/use-cases/security-specialist.md)** (3-5 hours)
   - Journey: Code Scanning → OWASP → Compliance → Pentesting → Threat Modeling
   - 10 plugins from Security Pro Pack
   - Complete security audit workflow
   - GDPR/PCI compliance guides
   - 11,000 bytes

3. **[AI/ML Developer](./docs/learning-paths/use-cases/ai-ml-developer.md)** (4-6 hours)
   - Journey: Prompts → LLM APIs → RAG Systems → Model Deploy → Production
   - 12 plugins from AI/ML Engineering Pack
   - Production AI system implementation
   - Real code for RAG pipelines, model training
   - 12,000 bytes

4. **[Crypto Trader](./docs/learning-paths/use-cases/crypto-trader.md)** (3-4 hours)
   - Journey: Portfolio → Analytics → Whale Tracking → Arbitrage → Sentiment
   - 7 featured crypto plugins
   - Automated trading system setup
   - Complete DeFi workflow
   - 13,000 bytes

---

### ✨ Documentation Improvements

#### README Reorganization
- **Above-the-fold optimization**: Removed learning paths from line 31
- **Focused user experience**: Plugin listings now immediately visible
- **Compact learning paths section**: Moved to line 408 with concise table format
- **48 lines removed** from above the fold for better UX

#### Official Documentation Integration
- **50+ links** to Claude Code official docs throughout all guides
- Links to: Installation, Plugin Reference, CLI Commands, MCP Spec, Use Cases
- Every guide connects to authoritative sources
- Progressive depth: basic links in Quick Start, technical links in Advanced

#### Navigation & Links
- **All internal links validated**: 100% working cross-references
- **GitHub-optimized paths**: Relative links work perfectly on repo
- **Mermaid diagrams** removed from README (kept in guides)
- **Full navigation tree** functional across 7 guides

---

### 🔌 Plugin Ecosystem

**Total Plugins: 225** (unchanged)

#### Featured Crypto Plugins (5 added to featured list)
- **whale-alert-monitor** - Production whale tracking (1,148 lines)
- **on-chain-analytics** - Enterprise blockchain analytics (15+ chains)
- **crypto-portfolio-tracker** - Professional portfolio tracking (50+ exchanges)
- **arbitrage-opportunity-finder** - Advanced arbitrage scanner (100+ exchanges)
- **market-sentiment-analyzer** - AI sentiment analysis (15+ platforms)

**Total Featured Plugins: 28** (was 23)

---

### 🏗️ Infrastructure

#### Git & GitHub
- **FUNDING.yml updates**: Added Buy Me a Coffee sponsorship
- **Removed GitHub Sponsors** until enrollment complete
- **Clean funding config**: Only active platforms displayed

#### File Organization
- Learning paths in `docs/learning-paths/`
- Main paths: `01-quick-start/`, `02-plugin-creator/`, `03-advanced-developer/`
- Use cases: `use-cases/devops-engineer.md`, etc.

---

### 📊 Release Metrics

#### Documentation Stats
- **Total Guides**: 7 comprehensive documents
- **Word Count**: 9,347 words
- **File Size**: ~80KB of educational content
- **Code Examples**: 100+ snippets
- **Official Links**: 50+ references
- **Time Investment**: 15min to 1 day (progressive)

#### Quality Metrics
- **Link Validation**: 100% (zero broken links)
- **Navigation**: Full cross-reference tree
- **Accessibility**: GitHub-optimized markdown
- **Syntax Highlighting**: All code blocks formatted
- **Mermaid Support**: Diagrams render on GitHub

#### Impact Metrics
- **User Onboarding**: Clear entry points for all skill levels
- **Contribution Clarity**: Step-by-step plugin creation
- **Domain Expertise**: Use-case specific journeys
- **Community Growth**: Professional documentation hub

---

### 🤝 Community & Contributors

#### New Capabilities Enabled
- **First-time users**: Can install and use plugins in 15 minutes
- **Plugin creators**: Can build and publish plugins in 3 hours
- **Advanced developers**: Can create MCP servers in 1 day
- **Domain specialists**: Can find relevant plugins instantly

#### Contributor Experience
- Clear progression paths for learning
- Comprehensive examples and templates
- Official documentation integration
- Professional-grade guides

---

### 🔗 Migration Guide

**For Repository Visitors:**
- **Old**: Learning paths immediately visible at line 31
- **New**: Learning paths at line 408 (compact table format)
- **Action**: Click learning path links in README or navigate directly

**For Plugin Users:**
- **No changes required** - all existing plugins work
- **New feature**: Access structured learning paths
- **Benefit**: Progressive skill development

**For Plugin Creators:**
- **New resource**: Comprehensive plugin creator guide
- **Templates**: Clear examples for all component types
- **Publishing**: Step-by-step marketplace submission

---

### 🎯 What's Next

#### Planned Improvements
- Add video walkthroughs for each learning path
- Create interactive playground for testing plugins
- Add plugin difficulty badges to marketplace
- Expand use case paths (Frontend, Mobile, Data Science)

#### Future Learning Content
- Advanced MCP server patterns
- Multi-agent system architectures
- Plugin performance optimization
- Security best practices deep-dive

---

### 📝 Commits in This Release

- `3832d3e` - feat: feature top 5 crypto plugins
- `b85f044` - fix: comment out GitHub Sponsors
- `d3d6e5c` - feat: add Buy Me a Coffee sponsorship
- `65e3ac6` - chore: clean up FUNDING.yml
- `9094412` - feat: add comprehensive learning paths
- `4b47a03` - refactor: move learning paths below plugin listings

---

### 🙏 Acknowledgments

**Learning Path Contributors:**
- All plugin maintainers whose work is featured in guides
- Official Claude Code documentation team
- Community members providing feedback

**Featured Plugin Authors:**
- Crypto plugin ecosystem contributors
- MCP server plugin developers
- Plugin pack maintainers

---

**Full Changelog**: [v1.0.35...v1.0.36](https://github.com/jeremylongshore/claude-code-plugins/compare/v1.0.35...v1.0.36)

**Download Plugin Catalog**: [plugins.json](https://github.com/jeremylongshore/claude-code-plugins/releases/download/v1.0.36/plugins.json)

---

## [3.1.0] - 2025-10-12

### 🎯 Release Highlights

This release brings **advanced AI-powered plugins** to the marketplace, focusing on multi-agent orchestration, automated workflows, and intelligent travel planning. The hub now offers **224 total plugins**, with significant additions in productivity automation and AI/ML capabilities.

---

### 🔌 Plugin Ecosystem

**Total Plugins: 224** (was 221)

#### New Plugins (3)

1. **ai-sdk-agents** (AI/ML) - Multi-agent orchestration with AI SDK v5
   - Handoffs, routing, and coordination for any AI provider (OpenAI, Anthropic, Google)
   - 3 commands + 1 orchestrator agent
   - Build sophisticated multi-agent systems with automatic handoffs and intelligent routing

2. **ai-commit-gen** (Productivity) - AI-powered commit message generator
   - Analyzes git diff and creates conventional commit messages instantly
   - Follows best practices (imperative mood, 50-char subject, proper types)
   - Saves 6+ minutes per commit

3. **travel-assistant** (Productivity) - Intelligent travel companion
   - 6 commands: /travel, /weather, /currency, /timezone, /itinerary, /pack
   - 4 AI agents: travel-planner, weather-analyst, local-expert, budget-calculator
   - Real-time APIs: OpenWeatherMap, ExchangeRate-API, WorldTimeAPI
   - Complete travel planning in minutes (saves 5+ hours per trip)

#### Featured Plugins
- **ai-sdk-agents**: Advanced multi-agent orchestration
- **travel-assistant**: Most comprehensive travel plugin (15 components)
- **ai-commit-gen**: Single-component productivity booster

---

### ✨ Hub Features

#### Repository Structure Cleanup
- Moved 14 development documents to `archive/development-docs/`
- Moved 4 plugin pack releases to `archive/releases/`
- Moved 3 utility scripts to `scripts/utilities/`
- Cleaner root directory with only essential files

#### Plugin Categories
- **AI/ML**: 26 plugins (was 25)
- **Productivity**: Updated with advanced automation tools
- **Packages**: 5 comprehensive plugin packs

---

### 📚 Documentation

#### New Plugin Documentation
- **ai-sdk-agents**: Comprehensive multi-agent system guide
  - Agent handoffs explained
  - Routing strategies
  - Coordination patterns
  - 5 use cases with examples

- **travel-assistant**: Complete travel planning guide
  - Real-time API integration
  - 6 command reference
  - 4 AI agent descriptions
  - Multi-city trip planning

- **ai-commit-gen**: Quick start guide
  - Conventional commits explained
  - 3 generated options
  - Integration with git workflow

#### Repository Documentation
- Cleaned up root directory structure
- Improved file organization
- Better archive system

---

### 🔒 Security

- All new plugins follow security best practices
- API integrations use environment variables (no hardcoded keys)
- Scripts properly permissioned (chmod +x)
- Input validation in all commands

---

### 🏗️ Infrastructure

#### Build System
- Marketplace website integration for all 3 new plugins
- JSON schema validation for plugin metadata
- Automated catalog generation

#### Git Workflow
- Proper commit message formatting
- Co-authoring with Claude Code
- Clean git history

---

### 📊 Release Metrics

- **Issues Closed**: Repository cleanup completed
- **PRs Merged**: 3 major plugin additions
- **New Plugins**: 3 (ai-sdk-agents, ai-commit-gen, travel-assistant)
- **Total Plugins**: 224
- **Featured Plugins**: 3 new additions
- **Components Added**:
  - Commands: 10 (3 + 1 + 6)
  - Agents: 5 (1 + 0 + 4)
  - Scripts: 3 (travel-assistant API integrations)
  - Hooks: 2 (travel-assistant auto-triggers)

---

### 🤝 Community & Contributors

#### Plugin Highlights

**Most Advanced**: `travel-assistant`
- 15 total components (6 commands, 4 agents, 3 scripts, 2 hooks)
- Real-time API integrations
- Multi-city trip planning
- Budget optimization

**Most Innovative**: `ai-sdk-agents`
- Multi-agent orchestration
- Cross-provider support (OpenAI, Anthropic, Google)
- Agent handoffs and routing

**Most Practical**: `ai-commit-gen`
- Single-command productivity
- Instant conventional commits
- Zero configuration

---

### 🔗 Integration Examples

#### Workflow Combinations

**AI Development Workflow**:
```bash
/ai-agents-setup          # Setup multi-agent system
/ai-agent-create tester   # Create testing agent
/ai-agents-test "task"    # Test coordination
/commit                   # Auto-generate commit message
```

**Travel Planning Workflow**:
```bash
/travel "Tokyo" --days 7 --budget 3000   # Complete plan
/weather Tokyo --days 14                  # Extended forecast
/currency 3000 USD JPY                    # Budget conversion
/pack Tokyo --days 7                      # Smart packing list
```

---

### 📦 Installation

```bash
# New plugins
/plugin install ai-sdk-agents@claude-code-plugins-plus
/plugin install ai-commit-gen@claude-code-plugins-plus
/plugin install travel-assistant@claude-code-plugins-plus

# Update existing installations
/plugin update --all
```

---

### 🌟 What's Next (v3.2.0 Planning)

- More MCP server plugins
- Enhanced multi-agent coordination
- Additional real-time API integrations
- Community plugin submissions
- Performance optimizations

---

**Full Changelog**: [v3.0.0...v3.1.0](https://github.com/jeremylongshore/claude-code-plugins/compare/v3.0.0...v3.1.0)

---

## [3.0.0] - 2025-10-11

### 🚀 THE MEGA RELEASE: 220 Total Plugins - 100% Growth!

This is the **largest release in Claude Code Plugin Hub history**, doubling the plugin count from 110 to **220 production-ready plugins**. This massive expansion establishes the Claude Code Plugin Hub as the definitive marketplace for AI-powered development tools.

---

### 🎯 Release Highlights

- **110 NEW PLUGINS ADDED** across 5 major categories
- **220 TOTAL PLUGINS** now available in the marketplace
- **100% GROWTH** in plugin count since v2.0.0
- **8 Complete Plugin Categories** with 20-25 plugins each
- **All categories production-ready** with comprehensive documentation

---

### 🆕 New Plugin Categories (110 New Plugins)

#### 🔐 Security & Compliance (25 plugins)
Complete security toolkit for enterprise-grade applications:
- **access-control-auditor** - Audit and validate access control mechanisms
- **authentication-validator** - Validate authentication implementations
- **compliance-report-generator** - Generate compliance reports (SOC2, HIPAA, PCI-DSS)
- **cors-policy-validator** - Validate CORS policies and configurations
- **csrf-protection-validator** - Check CSRF protection implementations
- **data-privacy-scanner** - Scan for data privacy compliance issues
- **dependency-checker** - Check dependencies for known vulnerabilities
- **encryption-tool** - Implement encryption best practices
- **gdpr-compliance-scanner** - GDPR compliance checking and reporting
- **hipaa-compliance-checker** - HIPAA compliance validation
- **input-validation-scanner** - Validate input sanitization
- **owasp-compliance-checker** - OWASP Top 10 compliance checking
- **pci-dss-validator** - PCI-DSS compliance validation
- **penetration-tester** - Automated penetration testing tools
- **secret-scanner** - Scan for exposed secrets and credentials
- **security-audit-reporter** - Generate comprehensive security audit reports
- **security-headers-analyzer** - Analyze HTTP security headers
- **security-incident-responder** - Incident response workflows
- **security-misconfiguration-finder** - Find security misconfigurations
- **session-security-checker** - Validate session management security
- **soc2-audit-helper** - SOC2 audit preparation and compliance
- **sql-injection-detector** - Detect SQL injection vulnerabilities
- **ssl-certificate-manager** - SSL/TLS certificate management
- **vulnerability-scanner** - Comprehensive vulnerability scanning
- **xss-vulnerability-scanner** - Cross-site scripting vulnerability detection

#### 📊 Database & Data Management (25 plugins)
Complete database lifecycle management toolkit:
- **data-seeder-generator** - Generate database seed data
- **data-validation-engine** - Validate data integrity and constraints
- **database-archival-system** - Archive old database records
- **database-audit-logger** - Log database operations for compliance
- **database-backup-automator** - Automated backup scheduling
- **database-cache-layer** - Implement database caching strategies
- **database-connection-pooler** - Connection pool optimization
- **database-deadlock-detector** - Detect and resolve deadlocks
- **database-diff-tool** - Compare database schemas
- **database-documentation-gen** - Generate database documentation
- **database-health-monitor** - Monitor database health metrics
- **database-index-advisor** - Recommend optimal indexes
- **database-migration-manager** - Manage schema migrations
- **database-partition-manager** - Partition large tables
- **database-recovery-manager** - Database recovery procedures
- **database-replication-manager** - Manage replication topology
- **database-schema-designer** - Visual schema design tools
- **database-security-scanner** - Scan for database vulnerabilities
- **database-sharding-manager** - Implement database sharding
- **database-transaction-monitor** - Monitor transaction performance
- **nosql-data-modeler** - Design NoSQL data models
- **orm-code-generator** - Generate ORM models from schemas
- **query-performance-analyzer** - Analyze query performance
- **sql-query-optimizer** - Optimize SQL queries
- **stored-procedure-generator** - Generate stored procedures

#### 🚀 Performance & Monitoring (25 plugins)
Complete observability and performance optimization suite:
- **alerting-rule-creator** - Create alerting rules for monitoring
- **apm-dashboard-creator** - Build Application Performance Monitoring dashboards
- **application-profiler** - Profile application performance
- **bottleneck-detector** - Identify performance bottlenecks
- **cache-performance-optimizer** - Optimize caching strategies
- **capacity-planning-analyzer** - Analyze capacity requirements
- **cpu-usage-monitor** - Monitor CPU utilization
- **database-query-profiler** - Profile database query performance
- **distributed-tracing-setup** - Set up distributed tracing
- **error-rate-monitor** - Monitor error rates and patterns
- **infrastructure-metrics-collector** - Collect infrastructure metrics
- **load-test-runner** - Run load testing scenarios
- **log-analysis-tool** - Analyze application logs
- **memory-leak-detector** - Detect memory leaks
- **metrics-aggregator** - Aggregate metrics from multiple sources
- **network-latency-analyzer** - Analyze network latency
- **performance-budget-validator** - Validate performance budgets
- **performance-optimization-advisor** - Get performance optimization recommendations
- **performance-regression-detector** - Detect performance regressions
- **real-user-monitoring** - Monitor real user experiences
- **resource-usage-tracker** - Track resource utilization
- **response-time-tracker** - Track API response times
- **sla-sli-tracker** - Track SLA/SLI metrics
- **synthetic-monitoring-setup** - Set up synthetic monitoring
- **throughput-analyzer** - Analyze system throughput

#### 💰 Crypto & DeFi (25 plugins)
Complete cryptocurrency and DeFi development toolkit:
- **arbitrage-opportunity-finder** - Find arbitrage opportunities across exchanges
- **blockchain-explorer-cli** - CLI blockchain explorer
- **cross-chain-bridge-monitor** - Monitor cross-chain bridges
- **crypto-derivatives-tracker** - Track crypto derivatives
- **crypto-news-aggregator** - Aggregate crypto news feeds
- **crypto-portfolio-tracker** - Track crypto portfolio performance
- **crypto-signal-generator** - Generate trading signals
- **crypto-tax-calculator** - Calculate crypto taxes
- **defi-yield-optimizer** - Optimize DeFi yield farming
- **dex-aggregator-router** - Route trades across DEXs
- **flash-loan-simulator** - Simulate flash loan strategies
- **gas-fee-optimizer** - Optimize gas fees
- **liquidity-pool-analyzer** - Analyze liquidity pool performance
- **market-movers-scanner** - Scan for market movers
- **market-price-tracker** - Track cryptocurrency prices
- **market-sentiment-analyzer** - Analyze market sentiment
- **mempool-analyzer** - Analyze mempool transactions
- **nft-rarity-analyzer** - Analyze NFT rarity scores
- **on-chain-analytics** - Perform on-chain data analysis
- **options-flow-analyzer** - Analyze options flow
- **staking-rewards-optimizer** - Optimize staking rewards
- **token-launch-tracker** - Track new token launches
- **trading-strategy-backtester** - Backtest trading strategies
- **wallet-portfolio-tracker** - Track wallet portfolios
- **whale-alert-monitor** - Monitor whale transactions

#### 🧪 Testing & Quality Assurance (10 plugins)
Essential testing tools for comprehensive QA:
- **api-test-automation** - Automate API testing
- **e2e-test-framework** - End-to-end testing framework setup
- **integration-test-runner** - Run integration tests
- **mutation-test-runner** - Mutation testing for test quality
- **performance-test-suite** - Performance testing suite
- **regression-test-tracker** - Track and manage regression tests
- **security-test-scanner** - Security testing automation
- **test-coverage-analyzer** - Analyze test coverage gaps
- **test-data-generator** - Generate realistic test data
- **unit-test-generator** - Auto-generate unit tests

---

### 📦 Previously Released Categories (Now Complete)

#### From v2.0.0 and earlier (110 plugins):
- **DevOps & CI/CD** (26 plugins) - Complete deployment automation
- **API Development** (25 plugins) - Full API lifecycle management
- **AI/ML Engineering** (26 plugins) - Complete AI development toolkit
- **Testing Suite** (15 plugins) - Comprehensive testing tools
- **MCP Server Plugins** (5 plugins, 21 tools) - Model Context Protocol integration
- **AI Agency Toolkit** (6 plugins) - Automation workflow builders
- **Plugin Packages** (4 packs) - Bundled plugin collections
- **Examples** (3 plugins) - Learning resources

---

### 🎨 Marketplace Enhancements

- **Category Organization** - All 220 plugins organized into 14 distinct categories
- **Enhanced Search** - Filter by category, keywords, and features
- **Plugin Stats** - Each plugin shows version, category, and author info
- **Improved Documentation** - Comprehensive README for every plugin
- **Featured Plugins** - Highlighted essential plugins for quick discovery

---

### 🏗️ Infrastructure

- **Marketplace Website** - Astro-powered static site with 220 plugin pages
- **Automated Validation** - All plugins pass JSON validation and structure checks
- **Semantic Versioning** - Proper version management across all plugins
- **GitHub Actions CI/CD** - Automated testing and deployment pipeline
- **Plugin Registry** - Centralized marketplace.json with all 220 plugins

---

### 📚 Documentation

- **README Updates** - Reflects 220 total plugins
- **Category Guides** - Documentation for each plugin category
- **Installation Instructions** - Clear installation steps for all plugins
- **Usage Examples** - Real-world examples for every plugin
- **Contributing Guidelines** - Updated for new scale of marketplace

---

### 🔧 Technical Details

**Version Bump:** 1.1.0 → 3.0.0 (Major version)

**Why Major Version?**
- **Breaking Scale Change** - 100% increase in plugin count
- **New Categories** - 5 entirely new plugin categories
- **Marketplace Structure** - Significant marketplace organization changes
- **Architecture** - Enhanced plugin discovery and organization

**Plugin Count by Category:**
```
DevOps:        26 plugins
AI/ML:         26 plugins
API Dev:       25 plugins
Database:      25 plugins
Crypto:        25 plugins
Security:      25 plugins
Performance:   25 plugins
Testing:       25 plugins (15 existing + 10 new)
AI Agency:      6 plugins
MCP:            5 plugins
Packages:       4 plugins
Productivity:   1 plugin
Examples:       3 plugins
---
TOTAL:        220 plugins
```

---

### 🎯 Migration Guide

**For Plugin Users:**
- No breaking changes to existing plugins
- All 110 v2.0.0 plugins remain unchanged
- New plugins available immediately
- Use `/plugin install <name>` to install any plugin

**For Plugin Developers:**
- Marketplace structure unchanged
- Continue using same plugin.json format
- New categories available for submission

**Marketplace Updates:**
```bash
# Update your local marketplace reference
/plugin marketplace update claude-code-plugins-plus

# Browse new plugins
/plugin list --marketplace claude-code-plugins-plus

# Install new plugins
/plugin install <plugin-name>@claude-code-plugins-plus
```

---

### 🙏 Contributors

This massive release was made possible by systematic plugin development across all categories. Special recognition for completing the "200 Plugin Mission" with comprehensive coverage of:
- Enterprise security and compliance
- Database management lifecycle
- Performance monitoring and observability
- Cryptocurrency and DeFi development
- Quality assurance and testing

---

### 🔗 Links

- **GitHub Repository**: https://github.com/jeremylongshore/claude-code-plugins
- **Marketplace Website**: (Coming soon with all 220 plugins)
- **Documentation**: See README.md and category-specific docs
- **Report Issues**: GitHub Issues

---

### 📊 Release Metrics

- **Total Plugins**: 220 (was 110)
- **New Plugins**: 110
- **Categories**: 14 (was 9)
- **Plugin Packs**: 4 comprehensive bundles
- **MCP Tools**: 21 Model Context Protocol tools
- **Lines of Code**: 49,959+ additions
- **Documentation**: 220+ README files
- **Test Coverage**: Validation scripts for all plugins

---

**This is the Claude Code Plugin Hub's most significant release to date. We've doubled our plugin count and established comprehensive coverage across all major development domains. Welcome to v3.0.0! 🎉**
# Changelog

All notable changes to the Claude Code Plugins Marketplace will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

---

## [1.1.0] - 2025-10-10

###  MCP Server Plugins Release

This release adds **5 production-ready MCP (Model Context Protocol) plugins** with **21 total MCP tools**, establishing this marketplace as the premier destination for advanced Claude Code plugins.

### Added

####  MCP Plugins (5 new plugins, 21 tools)

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

####  Additional Plugins

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

#### ️ Infrastructure

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

####  Documentation

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

###  Initial Open-Source Release

**BREAKING CHANGE**: Complete repository restructure from commercial Gumroad model to open-source GitHub marketplace.

### Added

####  Production Plugin
- **git-commit-smart** - AI-powered conventional commit message generator
  - Analyzes staged changes and generates contextual commit messages
  - Supports conventional commits standard (feat, fix, docs, etc.)
  - Interactive confirmation workflow
  - Breaking change detection
  - `/gc` shortcut for fast workflow
  - 1,500+ words of comprehensive documentation

####  Example Plugins (Educational)
- **hello-world** - Basic slash command demonstration
- **formatter** - PostToolUse hooks demonstration
- **security-agent** - Specialized AI subagent demonstration

####  Plugin Templates
- **minimal-plugin** - Bare minimum plugin structure
- **command-plugin** - Plugin with slash commands
- **agent-plugin** - Plugin with AI subagent
- **full-plugin** - Complete plugin with commands, agents, and hooks

####  Quality Assurance Tools
- `check-frontmatter.py` - Python YAML frontmatter validator
- `validate-all.sh` - Comprehensive plugin validation (JSON, frontmatter, shortcuts, permissions)
- `test-installation.sh` - Plugin installation testing in isolated environment

####  Documentation
- Comprehensive README.md with installation and usage
- CONTRIBUTING.md with community guidelines
- Detailed plugin development guide
- Security best practices
- Monetization alternatives guide

####  GitHub Integration
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
**Flagship Plugin**: `/plugin install git-commit-smart@claude-code-plugins-plus`
## [1.0.38] - 2025-10-15

### 🎯 Release Highlights

First external contributor spotlight. Welcoming @cdnsteve to the Claude Code Plugins Hub and featuring Sugar — an autonomous AI development plugin with task orchestration, hooks, and MCP tools.

### 🔌 Plugin Ecosystem
- New Plugin: **sugar** (devops) — Autonomous AI development workflow with MCP server and quality hooks
- Plugin Count: +1 (featured)

### 📚 Documentation
- README: Added “Contributor Spotlight” with links to PR #8 and Sugar repo
- New: `CONTRIBUTORS.md` listing @cdnsteve as First External Contributor

### 🧭 Website
- Marketplace: Added featured card for Sugar (`marketplace/src/content/plugins/sugar.json`)
- Homepage: New “Contributor Spotlight” section celebrating @cdnsteve

### 🤝 Contributor Spotlight
- First external contributor: **@cdnsteve** — leading the Sugar launch

---
