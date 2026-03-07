# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
