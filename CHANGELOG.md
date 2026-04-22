# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Security
- **Secret scanning hardened** - Replaced the previous regex-based secret scan
  in `validate-plugins.yml` with a dedicated workflow (`secret-scan.yml`) that
  runs `gitleaks` on every PR and push, plus a weekly `trufflehog` verified-
  credentials scan with Slack alerting. `.gitleaks.toml` adds rules for
  Anthropic, Groq, and Firebase/GCP credential shapes on top of the upstream
  defaults.

### Added
- **External audit response (NLPM, xiaolai)** - Expanded validator and CI
  coverage in response to the NLPM audit (issue #540).
  - `scripts/validate-skills-schema.py` now scans `.claude/agents/` and
    `workspace/**/agents/` in addition to `plugins/`, and flags
    shell-substitution patterns (`$(...)`, backticks, unguarded `${VAR}`) in
    YAML frontmatter values.
  - `.github/workflows/validate-plugins.yml` PR trigger paths extended to
    `scripts/**`, `.claude/**`, and `workspace/**` so changes on those
    surfaces run the full validation suite.
  - Credit to [xiaolai](https://github.com/xiaolai), author of
    [NLPM](https://github.com/xiaolai/nlpm-for-claude), for the audit and
    fix PRs (#535-#539).

## [4.27.0] - 2026-04-21

### Added
- **LangChain Python Skill Pack v1.0** - Complete 33-skill pack for LangChain/LangGraph Python development:
  - Core skills (8): model-inference, embeddings-search, sdk-patterns, reference-architecture, multi-env-setup, debug-bundle, deep-agents, langgraph-basics
  - LangGraph advanced (10): agents, checkpointing, human-in-loop, streaming, subgraphs, middleware-patterns, content-blocks, otel-observability
  - Production patterns (8): performance-tuning, cost-tuning, rate-limits, security-basics, enterprise-rbac
  - DevOps (7): ci-integration, deploy-integration, observability, incident-runbook, local-dev-loop, webhooks-events, upgrade-migration
  - Support skills: common-errors, core-workflow, data-handling, prompt-engineering, eval-harness
  - Average enterprise score: 92.4/100 (A-grade)
  - Reference architecture with pain-catalog documenting 25+ real-world failure modes

### Fixed
- **Gemini PR Review workflow** - Added `workflow_dispatch` trigger for manual review runs on any PR (#546+)
- **npm Publish** - Fixed repository.url for npm provenance compliance (#545)
- **npm Publish** - Fixed SIGPIPE abort in mass-publish enumerate step (#544)

### Changed
- **VERSION file sync** - Corrected VERSION file to match package.json (4.25.0 → 4.26.0)

### Metrics
- Commits since v4.26.0: 4 (1 feature, 3 fixes)
- New skills added: 33 (langchain-py-pack)
- Total skills: 2,882 (+33)
- Enterprise score maintained: 92.4/100 average for new pack

---

## [4.26.0] - 2026-04-20

### Added
- **npm Download Tracking Infrastructure** - Daily stats aggregation (`fetch-npm-stats.mjs`), hero marquee showing top 8 packages with 30-day counts, Slack digest at 1pm Central via #operation-hired webhook (#543)
- **npm Publish Workflows** - Mass publish (`publish-all-packages.yml` with confirmation gate) and incremental publish (`publish-changed-packages.yml` on push to main) for all @intentsolutionsio/* packages (#542)
- **Plugin Package.json Scaffolding** - Generated package.json for 305+ catalog plugins under @intentsolutionsio scope, enabling npm download tracking (#541)
- **README Awesome-List TOC** - Auto-generated table of contents with category counts, enforced by CI via `generate-readme-toc.mjs --check` (#531)
- **agent37.com Partner Integration** - Added to hero partner marquee alongside Nixtla (#532, #533)
- **Ultimate Code Cleanup Plugin** - 11-dimension, 11-agent comprehensive code analysis tool scoring 98/100 A+ enterprise grade
- **Bubble Invest Plugins** - local-tts (voice synthesis), boycott-filter (ethical filtering) from community PR #520
- **Killer Skill of the Week** - web-analytics skill with Umami MCP integration

### Fixed
- **Marquee Symmetry** - Restored translateX(-50%) pattern duplication so agent37 actually renders in seamless loop (#533)
- **Catalog Validation** - Removed phantom entries (tonone, claudebase), normalized 33 plugin author fields to object format
- **SKILL.md Compliance** - Split 13 files exceeding 500-line limit into references/, removed XML tags from frontmatter
- **Cowork Downloads** - Replaced non-existent stripe-pack with clerk-pack
- **CodeQL Finding** - Removed unused tableHeaderDone variable

### Changed
- **Micro-Category Consolidation** - Merged analytics→business-tools, code-quality→testing, finance→business-tools, automation→devops with CLI aliases for backwards compatibility (#530)
- **FS=Catalog Invariant** - Enforced filesystem path matching catalog category via `validate-catalog-invariants.py`
- **SaaS Pack Display** - Individual cards on /cowork page for better discoverability
- **Comprehensive Codebase Cleanup** - 8-parallel-agent refactor addressing code quality across repository

### Metrics
- Commits since v4.25.0: 34 (10 features, 8 fixes, 3 chore)
- Plugins with npm tracking: 305+ (newly scaffolded package.json files)
- Categories consolidated: 4 (analytics, code-quality, finance, automation)
- SaaS packs corrected: 106 → 105 (removed windsurf duplicate)

---

## [4.25.0] - 2026-04-14

### Added
- **Shopify Skill Pack v2.0** - Complete overhaul: 30 → 38 skills, 116 reference files extracted. Added 8 new skills (metafields-metaobjects, functions, storefront-headless, checkout-extensions, theme-performance, graphql-cost-optimizer, b2b-wholesale, ai-toolkit-wrapper). Enterprise score: 81.9 → 93.1/100.
- **Deep Evaluation Engine v1.0** - Intent Solutions 10-dimension skill quality assessment with coaching system and professional tier.
- **CLI Power Skills** - External plugin sync for enhanced CLI automation workflows.
- **CCHub plugin** - Desktop control panel for Claude Code / Codex / Gemini CLI management.
- **Work Diary blog** - Added Apr 6-13 posts to tonsofskills.com/blog.

### Changed
- **Shopify sdk-patterns rewrite** - Removed generic Zod/retry patterns, added codegen-typed operations, bulk operation helpers, and webhook registry.
- **Marketplace data sync** - Updated plugin counts to 430 plugins, 2,838 skills.

### Metrics
- Commits since v4.24.0: 10 (6 features, 2 chores, 2 merges)
- Shopify skills upgraded: 30 → 38 (+8 new)
- Reference files created: 116
- Lines added: +9,950 / -4,893

---

## [4.24.0] - 2026-04-06

### Added
- **SaaS pack skill upgrades** - Upgraded 232 D/F-grade skills to 70+ compliance (C+ or better). Expanded from ~30 lines to 90-150 lines each with Overview, Instructions, Error Handling tables, and product-specific TypeScript examples. Affected packs: appfolio, apple-notes, coreweave, fathom, glean, linktree, lucidchart, mindtickle, openevidence, together.
- **Legal & Compliance collection** - Added to homepage and /collections page with curated legal toolkit plugins.
- **General Legal Assistant plugin** - 12-skill, 5-agent legal toolkit (plugin #417) with contract analysis, compliance checking, and document drafting capabilities.
- **Agent Creator skill** - Added agent-creator skill and agent template to skill-creator plugin.
- **Work Diary blog** - Added Apr 3-5 posts to tonsofskills.com/blog.

### Changed
- **Legal plugin rename** - Renamed legal-assistant → general-legal-assistant for clarity.
- **Freshie inventory cleanup** - Removed 530 stale DB rows (500 legacy skills/, 30 ghost paths). Accurate skill count now 2,834.

### Fixed
- **CI deploy trigger** - Added pnpm-lock.yaml to deploy-firebase workflow trigger paths.
- **Lockfile sync** - Added x-bug-triage to pnpm-lock.yaml, unblocking Firebase deploys.
- **Homepage sponsor** - Restored scrolling marquee for sponsor section under byline.

### Metrics
- Commits since v4.23.0: 11 (5 features, 4 fixes, 1 refactor, 1 chore)
- Skills upgraded: 232 (D/F → C+)
- SaaS packs improved: 10
- Lines added: +21,464 / -5,440

---

## [4.23.0] - 2026-04-04

### Added
- **Skill-creator Anthropic alignment** - Updated to 2026 AgentSkills.io spec and Anthropic best practices
- **Work Diary blog** - Added intentcad-viewer-dwg-fastview-parity post to tonsofskills.com/blog

### Changed
- **Homepage partner banner** - Moved strategic partners section above fold, replaced Agent37 with Nixtla sponsor
- **CLAUDE.md accuracy** - Updated plugin/skill counts to 416/2,574, fixed build pipeline (6 steps), added verify CI job, corrected test file listing

### Fixed
- **YAML frontmatter repairs** - Fixed 1,252 SKILL.md files across the plugin ecosystem:
  - 9 Wondelai skills: double-escaped quotes (`''` → `'`) in block scalars
  - 3 Grammarly pack skills: duplicate frontmatter keys dropping `Bash(curl:*)` access
  - 1,219 skills: removed blank lines before closing `---` delimiters
- **README sponsor badge** - Added Nixtla sponsor badge, updated counts

---

## [4.22.0] - 2026-03-27

### Added
- **Hooks `if` conditional upgrade** - 4 plugins upgraded to use Claude Code v2.1.85 native `if` field for in-process tool filtering, eliminating unnecessary subprocess spawns. (#496)
  - `jeremy-github-actions-gcp` - Replace non-standard `filePattern` with native `if` glob
  - `claude-reflect` - Add `if: "Bash(git commit*)"` to PostToolUse
  - `pm-ai-partner` - Add `if: "Bash(git commit*)|Bash(git push*)"` to PreToolUse
  - `formatter` - Add `if` matching 15 file extensions for Write|Edit
- **x-bug-triage plugin** - External plugin sync with auto-dispatch workflow for all external repos. (#493)
- **OneNote pack rewrite** - All 18 skills rewritten from stubs (61.7) to production quality (91.4/100). (#489)
- **Work Diary blog** - /blog with 100 posts backfilled from startaitools.com, plus March 24-25 daily posts.

### Changed
- **Navigation** - Renamed Blog to Work Diary, replaced Pro nav link with Work Diary link.

### Fixed
- **Hooks schema normalization** - 2 plugins fixed to standard event-keyed format:
  - `prettier-markdown-hook` - Convert non-standard root-level array to standard schema
  - `travel-assistant` - Convert content-based matchers to standard `matcher: ".*"` (scripts handle detection)
- **x-bug-triage catalog** - Convert author field from string to object format.
- **/pro page** - Deactivated with 301 redirect to homepage.

### Metrics
- Commits since v4.21.0: 16 (7 features, 5 fixes, 2 chore)
- Hook plugins upgraded: 6 (4 with `if` conditionals, 2 schema normalizations)
- OneNote skills rewritten: 18
- Contributors: Jeremy Longshore, intentsolutions.io

---

## [4.21.0] - 2026-03-23

### Added
- **oraclecloud-pack rewrite** - All 26 OCI skills rewritten from stubs (61.3) to production quality (92.8/100). Pain-point-driven content covering auth config, capacity errors, IAM policies, SDK memory leaks, Terraform bugs. (#488)
- **navan-pack rewrite** - All 25 Navan skills rewritten to 93.0/100 with Airbyte connector research, real API patterns. (#485, #486, #487)
- **claude-pack hand-written** - Claude API skills at 95.3/100 with real SDK code. (#482)
- **Killer Skill nomination form** - Firebase form for community skill nominations. (#483)
- **105 SaaS packs total** - Notion, Supabase, Sentry packs fully built out (30 skills each). (#391-#480)
- **Universal validator v5.0** - Anthropic schema alignment, 100-point rubric, `--populate-db` for freshie inventory. (#378)
- **Pro tier + benchmarks** - CLI performance benchmark suite, Pro tier landing page. (#381)
- **63 SaaS pack directories** - Generated from marketplace extended metadata. (#380)
- **Infrastructure compliance** - Tags + compatible-with mass migration to 1,412 skills. (#379)
- **Severity1 marketplace plugin** - Severity levels and prompt-improver. (#382)
- **Slack channel plugin** - Added to ecosystem. (#375)

### Changed
- **Performance budget** - Bumped to 40MB gzipped, 1MB largest file, 2800-4000 routes for 414 plugins + 63 SaaS packs.
- **Freshie inventory system** - SQLite CMDB with 50 tables, versioned discovery runs, batch remediation.
- **Gold standard docs** - PRD/ARD/references pattern established for 13 Jeremy plugins.

### Fixed
- **Firebase forms** - Broken killer skill signup fixed. (#374)
- **CI validation** - Python + pyyaml setup for validation-scripts job.
- **Enterprise compliance** - 0 D/F grades after remediation rounds. (#384, #385)
- **Bare except clauses** - Replaced with `except Exception`. (#387)

### Metrics
- Commits since v4.20.0: 124 features, 25 fixes
- Files changed: 5,161 (+large delta)
- SaaS packs: 105 total (42 newly populated)
- Skills: 2,788+ across 414 plugins
- Contributors: Jeremy Longshore, intentsolutions.io

---

## [4.20.0] - 2026-03-20

### Added
- **pr-to-spec MCP plugin** - Convert PRs and local diffs into structured, agent-consumable specs with intent drift detection. 6 MCP tools for agentic coding workflows.
- **claude-memory-kit plugin** - Persistent agent memory system (#370, @seankim-android)
- **prism-scanner plugin** - Added to ecosystem section (#369, @aidongise-cell)
- **Content consistency validator improvements** - Enhanced skill structure validation with skill-review CI (#347, @fernandezbaptiste)

### Changed
- **8 SaaS packs rewritten with production content** - 150+ skills upgraded:
  - MaintainX pack (24 skills) - CMMS API integration
  - Evernote pack (24 skills) - Note management workflows
  - Apollo pack (22 skills) - Sales engagement APIs
  - Clerk pack (22 skills) - Auth/user management
  - Speak pack (9 skills) - Language learning APIs
  - Obsidian pack (10 skills) - Vault plugin development
  - Lokalise pack (23 skills) - Localization workflows
  - Juicebox pack (18 skills) - Community platform APIs
- **Agent spec updated for v2.1.78** - New `effort`, `maxTurns`, `disallowedTools` fields; corrected agent vs skill tool patterns
- **Performance budget** - Bumped to 19.5MB for 346+ plugins

### Fixed
- **Homepage badges** - Removed redundant badges above Killer Skill and Jeremy's Stash headings
- **Skill-review CI** - Removed insecure workflow dispatch, restored Overview + Examples sections
- **HTML attribute sanitization** - Complete quote escaping in discover-skills.mjs
- **Repository URL consistency** - Fixed pr-to-spec → pr-to-prompt mapping
- **Validation script** - Fixed duplicate tuple entry, added anchor skip

### Metrics
- Commits since v4.19.0: 13
- Files changed: 432 (+56,454 lines)
- Contributors: Jeremy Longshore, fernandezbaptiste, aidongise-cell, seankim-android, intentsolutions.io

---

## [4.19.0] - 2026-03-17

### Added
- **box-cloud-filesystem plugin** - Box cloud storage integration with file operations (#368)
- **geepers plugin** - Added to catalog (#367)
- **lumera-agent-memory plugin** - MCP server for persistent agent memory (#367)

### Fixed
- **Content quality audit sweep** - Comprehensive remediation of stub files and boilerplate:
  - Final 3 audit findings resolved (2 stubs + 1 false positive) (#365)
  - Wondelai implementation.md stubs filled with methodology guides (#363)
  - Remaining reference stubs for lokalise, documenso, speak (#364)
  - SaaS packs prose expanded to meet body-substance threshold (#362)
  - 12 misc reference stubs across community/crypto/productivity (#361)
  - 22 devops/saas reference stubs filled (#360)
  - 13 API development reference stubs with real examples (#359)
  - OpenRouter pack: 30 skills replaced boilerplate with unique content (#358)
  - 7 AI/ML reference stubs with real code examples (#357)
  - 24 performance skills: replaced generic boilerplate openings (#356)
  - 21 AI/ML skills: replaced generic boilerplate openings (#355)
  - 4 empty shell skill-enhancers built out with real content (#354)
  - 13 security/packages skills: replaced generic boilerplate (#353)
  - Audit content quality false positives addressed (#352)

### Metrics
- Commits since v4.18.0: 46
- Files changed: 376 (+37,973 / -2,436 lines)
- Contributors: Jeremy Longshore, intentsolutions.io, Ahmed Khaled Mohamed

---

## [4.18.0] - 2026-03-16

### Added
- **navigating-github plugin** - Interactive GitHub setup and learning companion with 6 modes (setup, learn, save, share, understand, fix), adaptive skill assessment, and 9 progressive hands-on lessons
- **mgonto EA skills** - 5 executive assistant skills: action-items-todoist, email-drafting, executive-digest, meeting-prep, todoist-due-drafts
- **Enhanced plugin & skill detail pages** - README section extraction, markdown-to-HTML rendering, FAQ accordions, and improved CTAs
- **Killer Skills spotlight** - Featured hero section on homepage with email signup
- **/github-learn slash command** - User-invocable entry point for navigating-github plugin

### Changed
- **Full facelift Phase 2** - Terminal-Bold redesign across all pages with OKLCH color system
- **Contributor cards redesigned** - Cross-page consistency with new card layout
- **Performance budget bumped** - 16MB for 343+ plugins

### Fixed
- **Mobile UX on /explore** - Card overlap, 480px breakpoint, filter bar improvements
- **Firebase deploy** - Split targets to avoid serviceusage permission error
- **run_eval.py** - Fixed 0% recall for already-installed plugin skills

### Metrics
- Commits since v4.17.0: 27
- Files changed: 41 (+7,331 / -1,665 lines)
- Contributors: Jeremy Longshore, intentsolutions.io

---

## [4.17.0] - 2026-03-11

### Added
- **Intent Solutions skill standard** - Updated all 5 tutorial notebooks to current standard
- **Verified Plugins Program** - Badges, rubric, and /verification page (#326)
- **Blog with changelog posts** - Astro content collections at /blog (#324)
- **Compare Marketplaces page** - SEO landing page at /compare (#323)
- **Light/dark theme toggle** - Across entire marketplace (#329)
- **Doctor --fix flag** - Safe auto-remediation for ccpi doctor (#333)
- **Cross-platform skill headers** - compatible-with field, YAML parser fix (#332)
- **Automated weekly metrics** - GitHub Actions workflow (#330)
- **Wondelai skills pack** - 25 agent skills for business, design & marketing (#303)
- **CONTRIBUTING.md** - Contributor guide with SEO meta tags (#320)

### Fixed
- **4300+ validator warnings reduced to 258** - 94% reduction (#337)
- **130 stub SKILL.md files replaced** - Substantive domain-specific content (#335)
- **Skill counts corrected** - Add windsurf pack, fix cowork claims (#334)
- **Gemini model ID updated** - gemini-2.0-flash-exp → gemini-2.5-flash (#316)
- **Wondelai skills frontmatter** - Added required fields to all 25 skills (#317)
- **SECURITY.md added** - Security policy (#315)

### Changed
- **Validator compliance** - Community page, PDA skill quality upgrade (#336)
- **Playbooks converted** - 11 playbooks to Astro content collections (#325)
- **18 jeremy-owned plugins** - Version bump 1.0.0 → 2.0.0 (#331)
- **Performance budgets** - Bumped for 340+ plugins and dark mode CSS

### Metrics
- Commits since v4.16.0: 33
- Files changed: 2,956 (+272,838 / -215,356 lines)
- Contributors: intentsolutions.io, Jeremy Longshore, Michal Jaskolski, Eugene Aseev

---

## [4.16.0] - 2026-03-07

### Added
- **Domain migration to tonsofskills.com** - Primary domain with Firebase hosting and 301 redirects
- **Homepage dark theme redesign** - Braves Booth-inspired dark theme with modern UI
- **Production E2E tests** - Playwright tests for tonsofskills.com deployment validation
- **Research page** - `/research` with 6 data-driven analysis documents
- **Trading strategy backtester fixes** - 8 quality gaps fixed (#314):
  - Stop-loss and take-profit enforcement
  - Short position support for RSI, MACD, Bollinger, MeanReversion strategies
  - Settings.yaml loading with CLI override support
  - Full test suite with 31 pytest tests

### Fixed
- **Axiom submodule issue** - Converted broken submodule to regular directory, fixing CI on forks
- Mobile horizontal overflow on `/explore` page
- Badge text size and cowork plugin overflow on mobile
- Hidden nav links handling in Playwright tests
- Skills link to cowork page, updated skills page title

### Changed
- CI cron schedules disabled to reduce Actions minutes usage
- Workflow dispatch trigger added to Validate Plugins workflow
- Cowork zip integrity check now works without unzip (Node.js fallback)
- Production E2E job now independent of marketplace-validation

### Reverted
- Chainstack and deAPI plugins temporarily reverted pending review

### Metrics
- Commits since v4.15.0: 50
- Files changed: 183 (+25,792 / -1,584 lines)
- Contributors: Jeremy Longshore, intentsolutions.io, clowreed, Eugene Aseev

---

## [4.15.0] - 2026-02-13

### Added
- Products & Services section on homepage with Agent37 partner integration
- Penetration testing plugin v2.0.0 with 3 real Python security scanners (~4,500 lines):
  - `security_scanner.py` - HTTP headers, SSL/TLS, endpoint probing, CORS analysis
  - `dependency_auditor.py` - npm audit & pip-audit wrapper with unified reporting
  - `code_security_scanner.py` - bandit + 16 regex patterns for static analysis
- Security reference documentation: OWASP Top 10, Security Headers, Remediation Playbook

### Fixed
- Windows Defender false positive in penetration-tester plugin (#300) - removed literal PHP payloads
- Sponsor page pricing tiers replaced with email-for-details contact form
- stored-procedure-generator test functions renamed to avoid pytest collection conflicts
- Homepage product listing prices updated to $10
- Explore page style preservation when filtering search results

### Changed
- Copyrights updated to 2026 across all documentation
- Opus model ID now allowed in skills schema validation
- Schema references synced to 2026 spec

### Metrics
- Commits since v4.14.0: 8
- Files changed: 50+
- New Python code: ~4,500 lines (security scanners)
- New reference docs: 3 (~1,100 lines)

---

## [4.14.0] - 2026-01-31

### Added
- 17 additional SaaS skill packs (408 skills), completing the 42-pack SaaS collection:
  - **apollo-pack**: Sales engagement, sequences, analytics, CRM integration
  - **clerk-pack**: User authentication, session management, organization features
  - **coderabbit-pack**: AI code review, PR automation, code quality analysis
  - **customerio-pack**: Email marketing, customer messaging, campaigns, segments
  - **deepgram-pack**: Speech-to-text, audio transcription, real-time ASR
  - **fireflies-pack**: Meeting transcription, note-taking, conversation intelligence
  - **gamma-pack**: AI presentations, document generation, visual content
  - **granola-pack**: Meeting notes, AI summaries, productivity automation
  - **groq-pack**: LPU inference, ultra-fast AI, Groq Cloud deployment
  - **ideogram-pack**: AI image generation, text rendering, creative design
  - **instantly-pack**: Cold email, outreach automation, lead generation
  - **juicebox-pack**: People search, lead enrichment, contact data
  - **langchain-pack**: LLM orchestration, chains, agents, RAG patterns
  - **linear-pack**: Issue tracking, project management, engineering workflows
  - **lindy-pack**: AI assistants, workflow automation, business processes
  - **posthog-pack**: Product analytics, feature flags, session replay
  - **vastai-pack**: GPU marketplace, cloud compute, ML infrastructure

### Changed
- Updated all skill counts in README.md (739 → 1,537 total skills)
- SaaS pack summary: 42 packs with 1,086 skills total
- Standalone skills: 1,298 (was 500)

### Metrics
- New SaaS skill packs: 17 (408 skills)
- Total SaaS packs: 42 (1,086 skills)
- Total skills: 1,537 (previously 1,027)
- 13 packs with 30 skills, 29 packs with 24 skills

---

## [4.13.0] - 2026-01-26

### Added
- 12 complete SaaS skill packs with real, production-ready content (288 skills total):
  - **databricks-pack**: Delta Lake, MLflow, notebooks, clusters, data engineering workflows
  - **mistral-pack**: Mistral AI inference, embeddings, fine-tuning, production deployment
  - **langfuse-pack**: LLM observability, tracing, prompt management, evaluation metrics
  - **obsidian-pack**: Vault management, plugins, sync, templates, personal knowledge management
  - **documenso-pack**: Document signing, templates, e-signature workflows, compliance
  - **evernote-pack**: Note management, notebooks, tags, search, productivity workflows
  - **guidewire-pack**: InsuranceSuite, PolicyCenter, ClaimCenter, insurance platform integration
  - **lokalise-pack**: Translation management system, localization, i18n automation
  - **maintainx-pack**: Work orders, preventive maintenance, CMMS workflows, asset tracking
  - **openevidence-pack**: Medical AI, clinical decision support, healthcare evidence platform
  - **speak-pack**: AI language learning, speech recognition, pronunciation training, education tech
  - **twinmind-pack**: AI meeting assistant, transcription, summaries, productivity automation
- Each pack follows standard template: S01-S12 (Standard), P13-P18 (Pro), F19-F24 (Flagship)
- All skills include 2026 schema frontmatter with proper tool permissions
- Brand strategy framework plugin integration (#292)

### Changed
- Updated all 2025 schema/spec references to 2026 across documentation
- Improved contributor ordering convention (newest first)
- Marketplace catalog extended with 12 new SaaS packs

### Metrics
- New SaaS skill packs: 12 (288 skills)
- Total skills: 1,027 (previously 739)
- Commits since v4.12.0: 15
- Contributors: Jeremy Longshore (10), Rowan Brooks (4)
- Files changed: 301
- Days since last release: 14

## [4.12.0] - 2026-01-12

### Added
- 5 crypto trading plugins to public repository
- Validator content quality validation checks (#299)

### Fixed
- creating-kubernetes-deployments skill quality (#298)
- automating-database-backups skill quality (#297)
- generating-stored-procedures skill quality (#296)
- All 3 skills improved based on Richard Hightower's quality feedback

### Changed
- Added Richard Hightower as contributor
- Banner text and mobile spacing improvements

## [4.11.0] - 2026-01-18

### Added
- 8 new crypto plugin skills with full PRD/ARD documentation and Python implementations:
  - **Blockchain & On-Chain**: blockchain-explorer-cli, on-chain-analytics, mempool-analyzer, whale-alert-monitor, gas-fee-optimizer
  - **NFT & Tokens**: nft-rarity-analyzer, token-launch-tracker
  - **Infrastructure**: cross-chain-bridge-monitor, wallet-security-auditor
- Firebase Hosting deployment workflow for claudecodeplugins.io
- Firebase Analytics integration with measurement ID tracking
- Google Secret Manager integration for secure Firebase config

### Fixed
- Gemini code review feedback for all new crypto skills:
  - Timezone-naive datetime operations (now UTC)
  - Empty except clauses with explanatory comments
  - Unused import cleanup
  - Config loading from settings.yaml
  - Mock data fallback with explicit --demo flag

### Infrastructure
- GitHub Actions workflow for Firebase Hosting deployment
- Workload Identity Federation for keyless GCP authentication
- All crypto skills follow nixtla enterprise PRD/ARD standard

### Metrics
- New crypto skills: 8 (completing Batch 5 & 6)
- Commits since v4.10.0: 29
- PRs merged: 10
- Total files changed: 221
- Lines changed: +23,839 / -19,891

## [4.10.0] - 2026-01-15

### Added
- 13 new crypto plugin skills with full PRD/ARD documentation and Python implementations:
  - **Market Data & Pricing**: market-price-tracker, market-movers-scanner, crypto-news-aggregator, market-sentiment-analyzer
  - **Portfolio & Tax**: crypto-portfolio-tracker, crypto-tax-calculator
  - **DeFi**: defi-yield-optimizer, liquidity-pool-analyzer, staking-rewards-optimizer, dex-aggregator-router, flash-loan-simulator
  - **Trading & Derivatives**: arbitrage-opportunity-finder, crypto-derivatives-tracker
- Firebase Hosting integration for marketplace website
- Firebase Analytics for download tracking

### Changed
- Updated skill validator compliance for backtester and signal generator skills
- Unified theme colors across all marketplace pages (CSS consolidation)
- Updated .gitignore for firebase cache and skill data files

### Infrastructure
- All crypto skills follow nixtla enterprise PRD/ARD standard
- Each skill includes: SKILL.md, PRD.md, ARD.md, Python scripts, references, config
- Skills use DeFiLlama, CoinGecko, CryptoCompare APIs (free tiers)

### Metrics
- New crypto skills: 13 (with full documentation)
- Commits since v4.9.0: 50
- PRs merged: 8 (crypto skill branches)
- Total files changed: ~200
- Lines added: ~25,000

## [4.9.0] - 2026-01-08

### Added
- 10 new SaaS vendor skill packs (Batch 3): Apollo, Deepgram, Juicebox, Customer.io, LangChain, Lindy, Granola, Gamma, Clerk, Linear
- 240 new skills across Batch 3 vendors (24 skills per pack)
- npm packages for all 30 SaaS packs with download tracking
- Learn pages for all Batch 3 vendors on claudecodeplugins.io

### Changed
- Updated marketplace.extended.json with 10 new pack entries
- Updated vendor-packs.json with Batch 3 vendor metadata
- Updated TRACKER.csv with Batch 3 completion status

### Infrastructure
- All 30 SaaS packs now published to npm (@intentsolutionsio/{vendor}-pack)
- Consistent naming across marketplace and npm registries
- Website deployed with 642 pages including all vendor learn pages

### Metrics
- Total SaaS skill packs: 30 (720 skills)
- Batch 3 packs: 10 (240 skills)
- npm packages published: 30
- Files changed: 305
- Lines added: +72,405

## [4.8.0] - 2026-01-06

### Added
- Marketplace redirects for deleted learning pages
- 14 new vendor skill packs with website pages

### Changed
- Updated learn hub with all vendor icons
- Synced marketplace catalogs

## [4.7.0] - 2026-01-06

### Added
- Progressive Disclosure Architecture (PDA) pattern for all skills
- Intent Solutions 100-point grading system integrated into validator
- 348 reference files for detailed skill content extraction
- `scripts/refactor-skills-pda.py` automation script for skill restructuring

### Changed
- Refactored 98 skills to PDA pattern (SKILL.md files now <150 lines)
- Merged `validate-frontmatter.py` into unified `validate-skills-schema.py` (v3.0)
- Improved average skill score from 88.0/100 (B) to 92.5/100 (A)
- All 957 skills now 100% production ready

### Fixed
- Excel skills quality issues (GitHub Issues #250, #251, #252, #253)
- OpenRouter pack skills grading (8 skills improved from 80 to 95+ points)
- All C/D grade skills elevated to A/B grade
- Kling AI common-errors skill malformed code fences

### Metrics
- Skills validated: 957
- A grade: 897 (93.7%)
- B grade: 60 (6.3%)
- C/D/F grade: 0 (0%)
- Files changed: 2,173
- Lines added: +77,698
- Lines removed: -70,011

## [4.6.0] - 2026-01-05

### Added
- Batch 2 vendor skill databases (217 files)
- Skill databases for 6 published SaaS packs
- Kling AI flagship+ skill pack (30 skills)

### Fixed
- OpenRouter pack skill quality improvements

## [4.5.0] - 2026-01-04

### Added
- External plugin sync infrastructure
- ZCF integration
- 50-vendor SaaS skill packs initiative

### Changed
- Skill quality improvements to 99.9% compliance
