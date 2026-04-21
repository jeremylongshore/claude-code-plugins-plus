# Tons of Skills — Claude Code Plugins Marketplace

[![CLI](https://img.shields.io/badge/CLI-ccpi-blueviolet?logo=npm)](https://www.npmjs.com/package/@intentsolutionsio/ccpi)
[![Plugins](https://img.shields.io/badge/plugins-423-blue)](https://tonsofskills.com/explore)
[![Skills](https://img.shields.io/badge/skills-2%2C849-green)](https://tonsofskills.com/skills)
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins-plus-skills?style=social)](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)
[![Sponsor: Nixtla](https://img.shields.io/badge/Sponsor-nixtla.io-ff6b35)](https://nixtla.io)
[![Buy me a monster](https://img.shields.io/badge/Buy%20me%20a-Monster-FFDD00?logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/jeremylongshore)

423 plugins, 2,849 skills, 177 agents, 16 community contributors — validated and ready to install.

```bash
pnpm add -g @intentsolutionsio/ccpi    # Install the CLI
ccpi install devops-automation-pack     # Install any plugin
```

Or use Claude's built-in command:
```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

**[Browse the marketplace](https://tonsofskills.com)** | **[Explore plugins](https://tonsofskills.com/explore)** | **[Download bundles](https://tonsofskills.com/cowork)**

> **Killer Skill of the Week** — [web-analytics](https://tonsofskills.com/plugins/web-analytics) by Jeremy Longshore ([@jeremylongshore](https://github.com/jeremylongshore))
>
> **Your dashboards don't talk. This skill does.**
>
> A push-based analytics intelligence team — 9 specialist agents that fetch your data, detect anomalies, analyze funnels, verify claims, and deliver narrative reports. Powered by self-hosted [Umami](https://umami.is/) via MCP (Model Context Protocol) — agents call the Umami API in real time to pull visitor counts, pageviews, referrers, events, and session data across your entire site portfolio. GA4 as fallback. Not a dashboard you check. An analytics team that finds you. Three tiers: `/analytics` for a 30-second pulse, `/analytics medium` for a daily brief with traffic + content + anomaly detection, `/analytics full` for a deep dive across all sites with adversarial verification. One config file — swap your sites and it works for any portfolio.
>
> *"I stopped checking dashboards. Now my analytics team wakes me up when something matters."* — Jeremy Longshore
>
> Grade: A | Week of April 17, 2026 | [Browse on Marketplace](https://tonsofskills.com/plugins/web-analytics)
>
> Previous picks: [token-optimizer](https://github.com/alexgreensh/token-optimizer), [executive-assistant-skills](https://tonsofskills.com/plugins/executive-assistant-skills), [skill-creator](https://tonsofskills.com/plugins/skill-creator), [cursor-pack](https://tonsofskills.com/plugins/cursor-pack), [crypto-portfolio-tracker](https://tonsofskills.com/plugins/crypto-portfolio-tracker). See all at [tonsofskills.com](https://tonsofskills.com).

---

## Quick Start

**Option 1: CLI (Recommended)**
```bash
pnpm add -g @intentsolutionsio/ccpi
ccpi search devops              # Find plugins by keyword
ccpi install devops-automation-pack
ccpi list --installed           # See what's installed
ccpi update                     # Pull latest versions
```

**Option 2: Claude Built-in Commands**
```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
/plugin install devops-automation-pack@claude-code-plugins-plus
```

> Already using an older install? Run `/plugin marketplace remove claude-code-plugins` and re-add with the command above to switch to the new slug.

**Browse the catalog:** Visit **[tonsofskills.com](https://tonsofskills.com)** or explore [`plugins/`](./plugins/)

---

<!-- NPM-STATS:START — do not edit; daily cron updates this -->

### 📦 Live npm Downloads

Across **26 published packages** in the 
[claude-code-plugins](https://www.npmjs.com/~jeremylongshore) namespace. Updated daily by GitHub Actions.

| Window | Downloads |
|--------|----------:|
| Last 24 hours | 11 |
| Last 7 days | 117 |
| Last 30 days | 665 |

**Top 10 by last 30 days:**

| # | Package | Last 30d |
|---|---------|---------:|
| 1 | [`@intentsolutionsio/ccpi`](https://www.npmjs.com/package/@intentsolutionsio/ccpi) | 274 |
| 2 | [`@intentsolutionsio/langchain-pack`](https://www.npmjs.com/package/@intentsolutionsio/langchain-pack) | 56 |
| 3 | [`@intentsolutionsio/openrouter-pack`](https://www.npmjs.com/package/@intentsolutionsio/openrouter-pack) | 52 |
| 4 | [`@intentsolutionsio/retellai-pack`](https://www.npmjs.com/package/@intentsolutionsio/retellai-pack) | 33 |
| 5 | [`@intentsolutionsio/windsurf-pack`](https://www.npmjs.com/package/@intentsolutionsio/windsurf-pack) | 33 |
| 6 | [`@intentsolutionsio/firecrawl-pack`](https://www.npmjs.com/package/@intentsolutionsio/firecrawl-pack) | 22 |
| 7 | [`@intentsolutionsio/sentry-pack`](https://www.npmjs.com/package/@intentsolutionsio/sentry-pack) | 20 |
| 8 | [`@intentsolutionsio/supabase-pack`](https://www.npmjs.com/package/@intentsolutionsio/supabase-pack) | 17 |
| 9 | [`@intentsolutionsio/vercel-pack`](https://www.npmjs.com/package/@intentsolutionsio/vercel-pack) | 13 |
| 10 | [`@intentsolutionsio/customerio-pack`](https://www.npmjs.com/package/@intentsolutionsio/customerio-pack) | 12 |

<sub>Last refreshed 2026-04-21T01:30:15.018Z.</sub>

<!-- NPM-STATS:END -->

---

<!-- AUTO-TOC:START — do not edit; run `node scripts/generate-readme-toc.mjs` -->

## Browse Plugins by Category

Jump to any of the 18 categories below. Plugin counts are catalog totals — auto-generated from `marketplace.extended.json`.

|   | Category | Plugins |
|---|----------|--------:|
| 🤖 | [AI & Machine Learning](#ai--machine-learning) | 34 |
| 🎭 | [AI Agents & Agency](#ai-agents--agency) | 7 |
| 🔌 | [API Development](#api-development) | 25 |
| 💼 | [Business Tools](#business-tools) | 21 |
| 👥 | [Community](#community) | 13 |
| ₿ | [Crypto & Web3](#crypto--web3) | 26 |
| 💾 | [Database](#database) | 26 |
| 🎨 | [Design](#design) | 7 |
| 🔧 | [DevOps & Infrastructure](#devops--infrastructure) | 35 |
| 📚 | [Examples & Templates](#examples--templates) | 5 |
| 🧩 | [MCP Servers](#mcp-servers) | 10 |
| 📦 | [Packages](#packages) | 5 |
| ⚡ | [Performance](#performance) | 25 |
| ✅ | [Productivity](#productivity) | 18 |
| 🎁 | [SaaS Skill Packs](#saas-skill-packs) | 106 |
| 🔐 | [Security](#security) | 26 |
| ✨ | [Skill Enhancers](#skill-enhancers) | 8 |
| 🧪 | [Testing](#testing) | 26 |

### AI & Machine Learning

🤖 **34 plugins** · category slug: `ai-ml`

| Plugin | Description |
|--------|-------------|
| `ai-ethics-validator` | AI ethics and fairness validation |
| `ai-sdk-agents` | Multi-agent orchestration with AI SDK v5 - handoffs, routing, and coordination for any AI provider (OpenAI, Anthropic, Google) |
| `anomaly-detection-system` | Detect anomalies and outliers in data |
| `automl-pipeline-builder` | Build AutoML pipelines |
| `classification-model-builder` | Build classification models |
| `clustering-algorithm-runner` | Run clustering algorithms on datasets |
| `computer-vision-processor` | Computer vision image processing and analysis |
| `data-preprocessing-pipeline` | Automated data preprocessing and cleaning pipelines |
| `data-visualization-creator` | Create data visualizations and plots |
| `dataset-splitter` | Split datasets for training, validation, and testing |
| `deep-learning-optimizer` | Deep learning optimization techniques |
| `experiment-tracking-setup` | Set up ML experiment tracking |
| `feature-engineering-toolkit` | Feature creation, selection, and transformation tools |
| `hyperparameter-tuner` | Optimize hyperparameters using grid/random/bayesian search |
| `jeremy-adk-orchestrator` | Production ADK orchestrator for A2A protocol and multi-agent coordination on Vertex AI |
| `jeremy-adk-software-engineer` | ADK software engineer for creating production-ready agents (placeholder - to be implemented) |
| `jeremy-gcp-starter-examples` | Google Cloud starter kits and example code aggregator with ADK samples |
| `jeremy-genkit-pro` | Firebase Genkit expert for production-ready AI workflows with RAG and tool calling |
| `jeremy-vertex-engine` | Vertex AI Agent Engine deployment inspector and runtime validator |
| `jeremy-vertex-validator` | Production readiness validator for Vertex AI deployments and configurations |
| `local-tts` | Offline text-to-speech via VoxCPM2 — 30 languages, voice design, voice cloning. Runs locally on Apple Silicon. |
| `ml-model-trainer` | Train and optimize machine learning models with automated workflows |
| `model-deployment-helper` | Deploy ML models to production |
| `model-evaluation-suite` | Comprehensive model evaluation with multiple metrics |
| `model-explainability-tool` | Model interpretability and explainability |
| `model-versioning-tracker` | Track and manage model versions |
| `neural-network-builder` | Build and configure neural network architectures |
| `nlp-text-analyzer` | Natural language processing and text analysis |
| `ollama-local-ai` | Run AI models locally with Ollama - free alternative to OpenAI, Anthropic, and other paid LLM APIs. Zero-cost, privacy-first AI… |
| `recommendation-engine` | Build recommendation systems and engines |
| `regression-analysis-tool` | Regression analysis and modeling |
| `sentiment-analysis-tool` | Sentiment analysis on text data |
| `time-series-forecaster` | Time series forecasting and analysis |
| `transfer-learning-adapter` | Transfer learning adaptation |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### AI Agents & Agency

🎭 **7 plugins** · category slug: `ai-agency`

| Plugin | Description |
|--------|-------------|
| `discovery-questionnaire` | Generate custom discovery questionnaires for AI agency prospects |
| `make-scenario-builder` | Create Make.com (Integromat) scenarios with AI assistance |
| `n8n-workflow-designer` | Design complex n8n workflows with AI assistance - loops, branching, error handling |
| `roi-calculator` | Calculate and present ROI for AI automation projects |
| `shipwright` | Describe your app in plain English — Shipwright builds, tests, and deploys it autonomously via a 9-phase pipeline. |
| `sow-generator` | Generate professional Statements of Work for AI projects |
| `zapier-zap-builder` | Create multi-step Zapier Zaps with filters, paths, and formatters |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### API Development

🔌 **25 plugins** · category slug: `api-development`

| Plugin | Description |
|--------|-------------|
| `api-authentication-builder` | Build authentication systems with JWT, OAuth2, and API keys |
| `api-batch-processor` | Implement batch API operations with bulk processing and job queues |
| `api-cache-manager` | Implement caching strategies with Redis, CDN, and HTTP headers |
| `api-contract-generator` | Generate API contracts for consumer-driven contract testing |
| `api-documentation-generator` | Generate comprehensive API documentation from OpenAPI/Swagger specs |
| `api-error-handler` | Implement standardized error handling with proper HTTP status codes |
| `api-event-emitter` | Implement event-driven APIs with message queues and event streaming |
| `api-gateway-builder` | Build API gateway with routing, authentication, and rate limiting |
| `api-load-tester` | Load test APIs with k6, Gatling, or Artillery |
| `api-migration-tool` | Migrate APIs between versions with backward compatibility |
| `api-mock-server` | Create mock API servers from OpenAPI specs for testing |
| `api-monitoring-dashboard` | Create monitoring dashboards for API health, metrics, and alerts |
| `api-rate-limiter` | Implement rate limiting with token bucket, sliding window, and Redis |
| `api-request-logger` | Log API requests with structured logging and correlation IDs |
| `api-response-validator` | Validate API responses against schemas and contracts |
| `api-schema-validator` | Validate API schemas with JSON Schema, Joi, Yup, or Zod |
| `api-sdk-generator` | Generate client SDKs from OpenAPI specs for multiple languages |
| `api-security-scanner` | Scan APIs for security vulnerabilities and OWASP API Top 10 |
| `api-throttling-manager` | Manage API throttling with dynamic rate limits and quota management |
| `api-versioning-manager` | Manage API versions with migration strategies and backward compatibility |
| `graphql-server-builder` | Build GraphQL servers with schema-first design, resolvers, and subscriptions |
| `grpc-service-generator` | Generate gRPC services with Protocol Buffers and streaming support |
| `rest-api-generator` | Generate RESTful APIs from schemas with proper routing, validation, and documentation |
| `webhook-handler-creator` | Create secure webhook endpoints with signature verification and retry logic |
| `websocket-server-builder` | Build WebSocket servers for real-time bidirectional communication |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Business Tools

💼 **21 plugins** · category slug: `business-tools`

| Plugin | Description |
|--------|-------------|
| `brand-strategy-framework` | A 7-part brand strategy framework for building comprehensive brand foundations - the same methodology top agencies use with Fortune 500… |
| `excel-analyst-pro` | Professional financial modeling toolkit for Claude Code with auto-invoked Skills and Excel MCP integration. Build DCF models, LBO… |
| `executive-assistant-skills` | AI-powered executive assistant skills that fully replace a human EA. Research meeting attendees, draft emails, create meeting briefs, and… |
| `openbb-terminal` | Open-source investment research terminal integration - comprehensive equity analysis, crypto tracking, macro indicators, portfolio… |
| `promptbook` | Opt-in session analytics for Claude Code. After setup consent, tracks prompts, tokens, build time, and lines changed per session.… |
| `wondelai-blue-ocean-strategy` | Blue Ocean Strategy framework for creating uncontested market space. Use the Strategy Canvas, Four Actions Framework (ERRC), and value… |
| `wondelai-contagious` | Word-of-mouth and virality framework using the STEPPS model (Social Currency, Triggers, Emotion, Public, Practical Value, Stories).… |
| `wondelai-cro-methodology` | Customer-centric conversion rate optimization methodology. Audit landing pages, identify conversion blockers, write persuasive copy,… |
| `wondelai-crossing-the-chasm` | Technology adoption and go-to-market strategy for crossing from early adopters to mainstream market. Choose beachhead segments, build… |
| `wondelai-drive-motivation` | Intrinsic motivation science framework (Autonomy, Mastery, Purpose). Design features that leverage intrinsic motivation, create progress… |
| `wondelai-hundred-million-offers` | Grand Slam Offer creation framework. Create irresistible offers using the Value Equation, stack bonuses, design risk-reversing guarantees,… |
| `wondelai-influence-psychology` | Persuasion science framework based on Cialdini's six principles (Reciprocity, Commitment, Social Proof, Authority, Liking, Scarcity).… |
| `wondelai-jobs-to-be-done` | Strategic product innovation framework using Clayton Christensen's JTBD theory. Discover customer motivations, conduct discovery… |
| `wondelai-made-to-stick` | Sticky messaging framework using the SUCCESs model (Simple, Unexpected, Concrete, Credible, Emotional, Stories). Make product messaging… |
| `wondelai-negotiation` | Tactical negotiation framework based on Chris Voss's techniques. Use mirroring, labeling, calibrated questions, the Ackerman method, and… |
| `wondelai-obviously-awesome` | Product positioning framework for competitive differentiation. Define competitive alternatives, identify unique attributes, map value… |
| `wondelai-one-page-marketing` | End-to-end marketing plan framework. Define target market, craft USP, choose channels, design lead capture and nurture sequences, optimize… |
| `wondelai-predictable-revenue` | Outbound sales methodology for scalable B2B pipeline. Implement Cold Calling 2.0, structure SDR/AE/CSM roles, design prospecting… |
| `wondelai-scorecard-marketing` | Lead generation framework using quiz and assessment funnels. Create lead magnets that convert 30-50%, design qualifying questions, and… |
| `wondelai-storybrand-messaging` | StoryBrand messaging framework that positions customer as hero. Create brand scripts, write website copy that converts, craft one-liners,… |
| `wondelai-traction-eos` | Entrepreneurial Operating System (EOS) for business execution. Create V/TO, set quarterly rocks, run Level 10 meetings, build… |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Community

👥 **13 plugins** · category slug: `community`

| Plugin | Description |
|--------|-------------|
| `b12-claude-plugin` | B12 Website Generator — an official plugin by B12.io. Ships a single auto-activating skill (website-generator) that collects a business… |
| `boycott-filter` | Personal boycott list managed conversationally by your AI agent. Chrome extension warns you on pages from brands you've decided to avoid. |
| `claude-never-forgets` | Persistent memory plugin for Claude Code - remembers preferences, decisions, and corrections across sessions and context limits |
| `claude-reflect` | Self-learning system for Claude Code that captures corrections and updates CLAUDE.md automatically |
| `fairdb-ops-manager` | Database operations management for FairDB PostgreSQL clusters |
| `framecraft` | Generate polished demo videos from a single prompt. Orchestrates Playwright, FFmpeg, and Edge TTS MCP servers to produce 1920x1080 videos… |
| `gastown` | Multi-agent orchestrator for Claude Code. Track work with convoys, sling to polecats. The Cognition Engine for AI-powered software… |
| `geepers` | Multi-agent orchestration system with 51 specialized agents for development workflows, code quality, deployment, research, and more. Built… |
| `geepers-agents` | Multi-agent orchestration system with 51 specialized agents for development workflows, code quality, deployment, research, games, and… |
| `jeremy-firebase` | Firebase platform expert for Firestore, Auth, Functions, and Vertex AI integration |
| `jeremy-firestore` | Firestore database specialist for schema design, queries, and real-time sync |
| `sprint` | Autonomous multi-agent development framework with spec-driven sprints. Write specs, run /sprint, and let coordinated agents (backend,… |
| `zai-cli` | Z.AI vision, search, reader, and GitHub exploration via CLI and MCP. Analyze images, search the web, read pages as markdown, explore repos. |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Crypto & Web3

₿ **26 plugins** · category slug: `crypto`

| Plugin | Description |
|--------|-------------|
| `arbitrage-opportunity-finder` | Find and analyze arbitrage opportunities across exchanges and DeFi protocols |
| `blockchain-explorer-cli` | Command-line blockchain explorer for transactions, addresses, and contracts |
| `cross-chain-bridge-monitor` | Monitor cross-chain bridge activity, track transfers, analyze security, and detect bridge exploits |
| `crypto-derivatives-tracker` | Track crypto futures, options, perpetual swaps with funding rates, open interest, and derivatives market analysis |
| `crypto-news-aggregator` | Aggregate and analyze crypto news from multiple sources with sentiment analysis |
| `crypto-portfolio-tracker` | Professional crypto portfolio tracking with real-time prices, PnL analysis, and risk metrics |
| `crypto-signal-generator` | Generate trading signals from technical indicators and market analysis |
| `crypto-tax-calculator` | Calculate crypto taxes with FIFO/LIFO methods and generate tax reports |
| `defi-yield-optimizer` | Optimize DeFi yield farming strategies across protocols with APY tracking and risk assessment |
| `dex-aggregator-router` | Find optimal DEX routes for token swaps across multiple exchanges |
| `flash-loan-simulator` | Simulate and analyze flash loan strategies including arbitrage, liquidations, and collateral swaps |
| `gas-fee-optimizer` | Optimize transaction gas fees with timing and routing recommendations |
| `liquidity-pool-analyzer` | Analyze DeFi liquidity pools for impermanent loss, APY, and optimization opportunities |
| `market-movers-scanner` | Scan for top market movers - gainers, losers, volume spikes, and unusual activity |
| `market-price-tracker` | Real-time market price tracking with multi-exchange feeds and advanced alerts |
| `market-sentiment-analyzer` | Analyze market sentiment from social media, news, and on-chain data |
| `mempool-analyzer` | Advanced mempool analysis for MEV opportunities, pending transaction monitoring, and gas price optimization |
| `nft-rarity-analyzer` | Analyze NFT rarity scores and valuations across collections |
| `on-chain-analytics` | Analyze on-chain metrics including whale movements, network activity, and holder distribution |
| `options-flow-analyzer` | Track institutional options flow, unusual activity, and smart money movements |
| `staking-rewards-optimizer` | Optimize staking rewards across multiple protocols and chains |
| `token-launch-tracker` | Track new token launches, detect rugpulls, and analyze contract security for early-stage crypto projects |
| `trading-strategy-backtester` | Backtest trading strategies with historical data, performance metrics, and risk analysis |
| `wallet-portfolio-tracker` | Track crypto wallets across multiple chains with portfolio analytics and transaction history |
| `wallet-security-auditor` | Crypto wallet security auditor for reviewing wallet implementations, key management, signing flows, and common vulnerability patterns. |
| `whale-alert-monitor` | Monitor large crypto transactions and whale wallet movements in real-time |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Database

💾 **26 plugins** · category slug: `database`

| Plugin | Description |
|--------|-------------|
| `data-seeder-generator` | Generate realistic test data and database seed scripts for development and testing environments |
| `data-validation-engine` | Database plugin for data-validation-engine |
| `database-archival-system` | Database plugin for database-archival-system |
| `database-audit-logger` | Database plugin for database-audit-logger |
| `database-backup-automator` | Automate database backups with scheduling, compression, encryption, and restore procedures |
| `database-cache-layer` | Database plugin for database-cache-layer |
| `database-connection-pooler` | Implement and optimize database connection pooling for improved performance and resource management |
| `database-deadlock-detector` | Database plugin for database-deadlock-detector |
| `database-diff-tool` | Database plugin for database-diff-tool |
| `database-documentation-gen` | Database plugin for database-documentation-gen |
| `database-health-monitor` | Database plugin for database-health-monitor |
| `database-index-advisor` | Analyze query patterns and recommend optimal database indexes with impact analysis |
| `database-migration-manager` | Manage database migrations with version control, rollback capabilities, and automated schema evolution tracking |
| `database-partition-manager` | Database plugin for database-partition-manager |
| `database-recovery-manager` | Database plugin for database-recovery-manager |
| `database-replication-manager` | Manage database replication, failover, and high availability configurations |
| `database-schema-designer` | Design and visualize database schemas with normalization guidance, relationship mapping, and ERD generation |
| `database-security-scanner` | Database plugin for database-security-scanner |
| `database-sharding-manager` | Database plugin for database-sharding-manager |
| `database-transaction-monitor` | Database plugin for database-transaction-monitor |
| `freshie-inventory-manager` | Interactive command center for the freshie ecosystem inventory database — conversational wizard with subagents for discovery scans,… |
| `nosql-data-modeler` | Database plugin for nosql-data-modeler |
| `orm-code-generator` | Generate ORM models from database schemas or create database schemas from models for TypeORM, Prisma, Sequelize, SQLAlchemy, and more |
| `query-performance-analyzer` | Analyze query performance with EXPLAIN plan interpretation, bottleneck identification, and optimization recommendations |
| `sql-query-optimizer` | Analyze and optimize SQL queries for better performance, suggesting indexes, query rewrites, and execution plan improvements |
| `stored-procedure-generator` | Database plugin for stored-procedure-generator |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Design

🎨 **7 plugins** · category slug: `design`

| Plugin | Description |
|--------|-------------|
| `wondelai-design-everyday-things` | Fundamental design principles from Don Norman. Design affordances, signifiers, constraints, and feedback mechanisms. Apply human-centered… |
| `wondelai-hooked-ux` | Hook Model framework for building habit-forming products. Design trigger-action-reward-investment loops, increase retention, and optimize… |
| `wondelai-ios-hig-design` | Native iOS app design following Apple Human Interface Guidelines. Design SwiftUI/UIKit components, implement navigation patterns, and… |
| `wondelai-refactoring-ui` | Practical UI design system for professional interfaces. Fix visual hierarchy, choose typography and color scales, add depth with shadows,… |
| `wondelai-top-design` | Award-winning web design framework for premium brand experiences. Build immersive websites with custom animations, dramatic typography,… |
| `wondelai-ux-heuristics` | Usability heuristics and UX audit framework based on Nielsen and Krug. Conduct heuristic evaluations, identify usability problems, and… |
| `wondelai-web-typography` | Web typography framework for readable, beautiful type. Select and pair typefaces, set optimal line length and height, implement responsive… |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### DevOps & Infrastructure

🔧 **35 plugins** · category slug: `devops`

| Plugin | Description |
|--------|-------------|
| `ansible-playbook-creator` | Create Ansible playbooks for configuration management |
| `auto-scaling-configurator` | Configure auto-scaling policies for applications and infrastructure |
| `backup-strategy-implementor` | Implement backup strategies for databases and applications |
| `ci-cd-pipeline-builder` | Build CI/CD pipelines for GitHub Actions, GitLab CI, Jenkins, and more |
| `cloud-cost-optimizer` | Optimize cloud costs and generate cost reports |
| `compliance-checker` | Check infrastructure compliance (SOC2, HIPAA, PCI-DSS) |
| `container-registry-manager` | Manage container registries (ECR, GCR, Harbor) |
| `container-security-scanner` | Scan containers for vulnerabilities using Trivy, Snyk, and other security tools |
| `deployment-pipeline-orchestrator` | Orchestrate complex multi-stage deployment pipelines |
| `deployment-rollback-manager` | Manage and execute deployment rollbacks with safety checks |
| `disaster-recovery-planner` | Plan and implement disaster recovery procedures |
| `docker-compose-generator` | Generate Docker Compose configurations for multi-container applications with best practices |
| `environment-config-manager` | Manage environment configurations and secrets across deployments |
| `fairdb-operations-kit` | Complete operations kit for FairDB PostgreSQL as a Service - VPS setup, PostgreSQL management, customer provisioning, monitoring, and… |
| `gh-dash` | GitHub PR dashboard for Claude Code. View PR status, CI/CD progress, bot comments, and merge PRs directly from your terminal. |
| `git-commit-smart` | AI-powered conventional commit message generator with smart analysis |
| `gitops-workflow-builder` | Build GitOps workflows with ArgoCD and Flux |
| `helm-chart-generator` | Generate Helm charts for Kubernetes applications |
| `infrastructure-as-code-generator` | Generate Infrastructure as Code for Terraform, CloudFormation, Pulumi, and more |
| `infrastructure-drift-detector` | Detect infrastructure drift from desired state |
| `jeremy-adk-terraform` | Terraform infrastructure as code for ADK and Vertex AI Agent Engine deployments |
| `jeremy-genkit-terraform` | Terraform modules for Firebase Genkit infrastructure and deployments |
| `jeremy-github-actions-gcp` | GitHub Actions CI/CD workflows for Google Cloud and Vertex AI deployments |
| `jeremy-vertex-terraform` | Terraform configurations for Vertex AI platform and Agent Engine |
| `kubernetes-deployment-creator` | Create Kubernetes deployments, services, and configurations with best practices |
| `load-balancer-configurator` | Configure load balancers (ALB, NLB, Nginx, HAProxy) |
| `log-aggregation-setup` | Set up log aggregation (ELK, Loki, Splunk) |
| `mattyp-changelog` | Automates changelog generation from git history with config validation and quality scoring. Use when publishing weekly updates, release… |
| `monitoring-stack-deployer` | Deploy monitoring stacks (Prometheus, Grafana, Datadog) |
| `network-policy-manager` | Manage Kubernetes network policies and firewall rules |
| `secrets-manager-integrator` | Integrate with secrets managers (Vault, AWS Secrets Manager, etc) |
| `service-mesh-configurator` | Configure service mesh (Istio, Linkerd) for microservices |
| `sugar` | Transform Claude Code into an autonomous AI development powerhouse with rich task context, specialized agents, and intelligent workflow… |
| `terraform-module-builder` | Build reusable Terraform modules |
| `tweetclaw` | X/Twitter automation - post, reply, like, retweet, follow, DM, search, extract data, monitor accounts, run giveaways. 121 endpoints via… |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Examples & Templates

📚 **5 plugins** · category slug: `examples`

| Plugin | Description |
|--------|-------------|
| `formatter` | Code formatting plugin using hooks to auto-format on save |
| `hello-world` | Simple example plugin demonstrating basic slash commands |
| `jeremy-plugin-tool` | Production-grade plugin creator with nixtla-validated quality standards. 4 Agent Skills automate creating, validating, auditing, and… |
| `pi-pathfinder` | PI Pathfinder - Finds the path through 229 plugins. Automatically picks the best plugin for your task, extracts its skills, and applies… |
| `security-agent` | Security review subagent for code analysis |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### MCP Servers

🧩 **10 plugins** · category slug: `mcp`

| Plugin | Description |
|--------|-------------|
| `ai-experiment-logger` | Track and analyze AI experiments with a web dashboard and MCP tools |
| `conversational-api-debugger` | Debug REST API failures using OpenAPI specs and HTTP logs (HAR) - root cause analysis with cURL generation |
| `design-to-code` | Convert Figma designs and screenshots to React/Svelte/Vue components with built-in accessibility |
| `domain-memory-agent` | Knowledge base with TF-IDF semantic search and extractive summarization - no ML dependencies required |
| `lumera-agent-memory` | Durable agent memory with Cascade object storage, client-side encryption, and local full-text search index. Persists agent context across… |
| `pr-to-spec` | The flight envelope for agentic coding — convert PRs and local diffs into structured, agent-consumable specs with intent drift detection |
| `project-health-auditor` | Multi-dimensional code health analysis with complexity, churn, and test coverage - identifies technical debt hot spots |
| `slack-channel` | Two-way Slack channel for Claude Code — chat from Slack DMs and channels via Socket Mode |
| `workflow-orchestrator` | DAG-based workflow automation with parallel task execution and dependency management |
| `x-bug-triage-plugin` | Closed-loop bug triage: X complaints → clusters → repo evidence → owner routing → Slack review → filed issues |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Packages

📦 **5 plugins** · category slug: `packages`

| Plugin | Description |
|--------|-------------|
| `ai-ml-engineering-pack` | Professional AI/ML Engineering toolkit: Prompt engineering, LLM integration, RAG systems, AI safety with 12 expert plugins |
| `creator-studio-pack` | Complete plugin suite for builder-filmmakers: Build products AND create viral videos. 20 plugins covering documentation, video production,… |
| `devops-automation-pack` | Complete DevOps automation suite with 25 plugins covering Git workflows, CI/CD pipelines, Docker optimization, Kubernetes management,… |
| `fullstack-starter-pack` | Complete fullstack development toolkit: React, Express/FastAPI, PostgreSQL scaffolding with AI agents |
| `security-pro-pack` | Professional security tools for Claude Code: vulnerability scanning, compliance, cryptography audit, container & API security |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Performance

⚡ **25 plugins** · category slug: `performance`

| Plugin | Description |
|--------|-------------|
| `alerting-rule-creator` | Create intelligent alerting rules for performance monitoring |
| `apm-dashboard-creator` | Create Application Performance Monitoring dashboards |
| `application-profiler` | Profile application performance with CPU, memory, and execution time analysis |
| `bottleneck-detector` | Detect and resolve performance bottlenecks |
| `cache-performance-optimizer` | Optimize caching strategies for improved performance |
| `capacity-planning-analyzer` | Analyze and plan for capacity requirements |
| `cpu-usage-monitor` | Monitor and analyze CPU usage patterns in applications |
| `database-query-profiler` | Profile and optimize database queries for performance |
| `distributed-tracing-setup` | Set up distributed tracing for microservices |
| `error-rate-monitor` | Monitor and analyze application error rates |
| `infrastructure-metrics-collector` | Collect comprehensive infrastructure performance metrics |
| `load-test-runner` | Create and execute load tests for performance validation |
| `log-analysis-tool` | Analyze logs for performance insights and issues |
| `memory-leak-detector` | Detect memory leaks and analyze memory usage patterns |
| `metrics-aggregator` | Aggregate and centralize performance metrics |
| `network-latency-analyzer` | Analyze network latency and optimize request patterns |
| `performance-budget-validator` | Validate application against performance budgets |
| `performance-optimization-advisor` | Get comprehensive performance optimization recommendations |
| `performance-regression-detector` | Detect performance regressions in CI/CD pipeline |
| `real-user-monitoring` | Implement Real User Monitoring for actual performance data |
| `resource-usage-tracker` | Track and optimize resource usage across the stack |
| `response-time-tracker` | Track and optimize application response times |
| `sla-sli-tracker` | Track SLAs, SLIs, and SLOs for service reliability |
| `synthetic-monitoring-setup` | Set up synthetic monitoring for proactive performance tracking |
| `throughput-analyzer` | Analyze and optimize system throughput |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Productivity

✅ **18 plugins** · category slug: `productivity`

| Plugin | Description |
|--------|-------------|
| `000-jeremy-content-consistency-validator` | Read-only validator that generates comprehensive discrepancy reports comparing messaging consistency across ANY HTML-based website… |
| `002-jeremy-yaml-master-agent` | Intelligent YAML validation, generation, and transformation agent with schema inference, linting, and format conversion capabilities |
| `003-jeremy-vertex-ai-media-master` | Comprehensive Google Vertex AI multimodal mastery for Jeremy - video processing (6+ hours), audio generation, image creation with Gemini… |
| `004-jeremy-google-cloud-agent-sdk` | Google Cloud Agent Development Kit (ADK) and Agent Starter Pack mastery - build containerized multi-agent systems with production-ready… |
| `agent-context-manager` | Automatically detects and loads AGENTS.md files to provide agent-specific instructions |
| `ai-commit-gen` | AI-powered commit message generator - analyzes your git diff and creates conventional commit messages instantly |
| `box-cloud-filesystem` | Transparent cloud filesystem for AI agents using Box CLI (@box/cli). Upload, download, search, share, and sync files to Box cloud storage… |
| `hyperfocus` | ADHD-friendly output formatting for Claude Code. Restructures responses with evidence-based cognitive accessibility: chunking, visual… |
| `navigating-github` | First-time GitHub setup and interactive git learning. Walks users from zero to a working GitHub repo, then teaches git through 9 hands-on… |
| `neurodivergent-visual-org` | Create ADHD-friendly visual organizational tools (Mermaid diagrams) optimized for neurodivergent thinking patterns with accessibility modes |
| `overnight-dev` | Run Claude autonomously for 6-8 hours overnight using Git hooks that enforce TDD - wake up to fully tested features |
| `pm-ai-partner` | 12 PM-specific agent skills, 6 workflow commands, 3 automation hooks for Product Managers |
| `prettier-markdown-hook` | Automatically format markdown files with prettier when Claude stops responding, with configurable organization and path exclusions |
| `travel-assistant` | Intelligent travel assistant with real-time weather, currency conversion, timezone info, and AI-powered itinerary planning. Your complete… |
| `vibe-guide` | Non-technical progress summaries for Claude Code work (hides diffs/log noise). |
| `wondelai-design-sprint` | Google Ventures Design Sprint methodology. Validate product ideas in 5 days with rapid prototyping, user testing, and structured… |
| `wondelai-lean-startup` | Lean Startup methodology for validated learning, MVPs, and innovation accounting. Design experiments, decide when to pivot vs. persevere,… |
| `youtube-strategy` | Complete YouTube content production workflow: research competitors, generate video ideas, build briefs, craft titles and thumbnails, and… |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### SaaS Skill Packs

🎁 **106 plugins** · category slug: `saas-packs`

| Plugin | Description |
|--------|-------------|
| `abridge-pack` | Claude Code skill pack for Abridge (18 skills) |
| `adobe-pack` | Claude Code skill pack for Adobe (30 skills) |
| `alchemy-pack` | Claude Code skill pack for Alchemy (18 skills) |
| `algolia-pack` | Claude Code skill pack for Algolia (24 skills) |
| `anima-pack` | Claude Code skill pack for Anima (18 skills) |
| `anthropic-pack` | Claude Code skill pack for Anthropic (30 skills) |
| `apify-pack` | Claude Code skill pack for Apify (18 skills) |
| `apollo-pack` | Complete Apollo integration skill pack with 24 skills covering sales engagement, prospecting, sequencing, analytics, and outbound… |
| `appfolio-pack` | Claude Code skill pack for AppFolio (18 skills) |
| `apple-notes-pack` | Claude Code skill pack for Apple Notes (24 skills) |
| `assemblyai-pack` | Claude Code skill pack for AssemblyAI (18 skills) |
| `attio-pack` | Claude Code skill pack for Attio (18 skills) |
| `bamboohr-pack` | Claude Code skill pack for BambooHR (18 skills) |
| `brightdata-pack` | Claude Code skill pack for Bright Data (18 skills) |
| `canva-pack` | Claude Code skill pack for Canva (30 skills) |
| `castai-pack` | Claude Code skill pack for Cast AI (18 skills) |
| `clari-pack` | Claude Code skill pack for Clari (18 skills) |
| `clay-pack` | Complete Clay integration skill pack with 30 skills covering data enrichment, waterfall workflows, AI agents, and GTM automation.… |
| `clerk-pack` | Complete Clerk integration skill pack with 24 skills covering authentication, user management, embeddable UIs, and identity platform.… |
| `clickhouse-pack` | Claude Code skill pack for ClickHouse (24 skills) |
| `clickup-pack` | Claude Code skill pack for ClickUp (24 skills) |
| `coderabbit-pack` | Complete CodeRabbit integration skill pack with 24 skills covering AI code review, PR automation, and code quality analysis. Flagship tier… |
| `cohere-pack` | Claude Code skill pack for Cohere (24 skills) |
| `coreweave-pack` | Claude Code skill pack for CoreWeave (24 skills) |
| `cursor-pack` | Complete Cursor integration skill pack with 30 skills covering AI code editing, composer workflows, codebase indexing, and productivity… |
| `customerio-pack` | Complete Customer.io integration skill pack with 24 skills covering marketing automation, email campaigns, SMS, push notifications, and… |
| `databricks-pack` | Complete Databricks integration skill pack with 24 skills covering Delta Lake, MLflow, notebooks, clusters, and data engineering… |
| `deepgram-pack` | Complete Deepgram integration skill pack with 24 skills covering speech-to-text, real-time transcription, voice intelligence, and audio… |
| `documenso-pack` | Complete Documenso integration skill pack with 24 skills covering document signing, templates, workflows, and e-signature automation.… |
| `elevenlabs-pack` | Claude Code skill pack for ElevenLabs (18 skills) |
| `evernote-pack` | Complete Evernote integration skill pack with 24 skills covering note management, notebooks, tags, search, and productivity workflows.… |
| `exa-pack` | Complete Exa integration skill pack with 30 skills covering neural search, semantic retrieval, web search API, and AI-powered discovery.… |
| `fathom-pack` | Claude Code skill pack for Fathom (18 skills) |
| `figma-pack` | Claude Code skill pack for Figma (30 skills) |
| `finta-pack` | Claude Code skill pack for Finta (18 skills) |
| `firecrawl-pack` | Complete Firecrawl integration skill pack with 30 skills covering web scraping, crawling, markdown conversion, and LLM-ready data… |
| `fireflies-pack` | Complete Fireflies integration skill pack with 24 skills covering meeting transcription, AI summaries, and conversation intelligence.… |
| `flexport-pack` | Claude Code skill pack for Flexport (24 skills) |
| `flyio-pack` | Claude Code skill pack for Fly.io (18 skills) |
| `fondo-pack` | Claude Code skill pack for Fondo (18 skills) |
| `framer-pack` | Claude Code skill pack for Framer (18 skills) |
| `gamma-pack` | Complete Gamma integration skill pack with 24 skills covering AI presentations, document generation, templates, and visual content… |
| `glean-pack` | Claude Code skill pack for Glean (24 skills) |
| `grammarly-pack` | Claude Code skill pack for Grammarly (24 skills) |
| `granola-pack` | Complete Granola integration skill pack with 24 skills covering AI meeting notes, transcription, summaries, and meeting intelligence.… |
| `groq-pack` | Complete Groq integration skill pack with 24 skills covering LPU inference, ultra-fast AI, and Groq Cloud deployment. Flagship tier vendor… |
| `guidewire-pack` | Complete Guidewire integration skill pack with 24 skills covering InsuranceSuite, PolicyCenter, ClaimCenter, and insurance platform… |
| `hex-pack` | Claude Code skill pack for Hex (18 skills) |
| `hootsuite-pack` | Claude Code skill pack for Hootsuite (18 skills) |
| `hubspot-pack` | Claude Code skill pack for HubSpot (30 skills) |
| `ideogram-pack` | Complete Ideogram integration skill pack with 24 skills covering AI image generation, text rendering, and creative design workflows.… |
| `instantly-pack` | Complete Instantly integration skill pack with 24 skills covering cold email, outreach automation, and lead generation. Flagship tier… |
| `intercom-pack` | Claude Code skill pack for Intercom (24 skills) |
| `juicebox-pack` | Complete Juicebox integration skill pack with 24 skills covering people data, enrichment, contact search, and AI-powered discovery.… |
| `klaviyo-pack` | Claude Code skill pack for Klaviyo (24 skills) |
| `klingai-pack` | Complete Kling AI integration skill pack with 30 skills covering AI video generation, text-to-video, image-to-video, and creative… |
| `langchain-pack` | Legacy LangChain integration skill pack with 24 skills covering chains, agents, RAG pipelines, memory, and LLM application development.… |
| `langchain-py-pack` | LangChain 1.0 + LangGraph 1.0 skill pack for Python. Pain-first skills anchored to a 68-entry pain catalog covering content blocks,… |
| `langfuse-pack` | Complete Langfuse integration skill pack with 24 skills covering LLM observability, tracing, prompt management, and evaluation. Flagship… |
| `lindy-pack` | Complete Lindy integration skill pack with 24 skills covering AI assistants, task automation, workflows, and intelligent automation.… |
| `linear-pack` | Complete Linear integration skill pack with 24 skills covering issue tracking, project management, workflows, and team collaboration.… |
| `linktree-pack` | Claude Code skill pack for Linktree (18 skills) |
| `lokalise-pack` | Complete Lokalise integration skill pack with 24 skills covering translation management, localization workflows, and i18n automation.… |
| `lucidchart-pack` | Claude Code skill pack for Lucidchart (18 skills) |
| `maintainx-pack` | Complete MaintainX integration skill pack with 24 skills covering work orders, preventive maintenance, asset management, and CMMS… |
| `mindtickle-pack` | Claude Code skill pack for Mindtickle (18 skills) |
| `miro-pack` | Claude Code skill pack for Miro (24 skills) |
| `mistral-pack` | Complete Mistral AI integration skill pack with 24 skills covering model inference, embeddings, fine-tuning, and production deployments.… |
| `navan-pack` | Claude Code skill pack for Navan (24 skills) |
| `notion-pack` | Claude Code skill pack for Notion (30 skills) |
| `obsidian-pack` | Complete Obsidian integration skill pack with 24 skills covering vault management, plugins, sync, templates, and knowledge management.… |
| `onenote-pack` | Claude Code skill pack for OneNote (18 skills) |
| `openevidence-pack` | Complete OpenEvidence integration skill pack with 24 skills covering medical AI, clinical decision support, evidence-based queries, and… |
| `openrouter-pack` | Complete OpenRouter integration skill pack with 30 skills covering LLM routing, model selection, cost optimization, and multi-provider… |
| `oraclecloud-pack` | Claude Code skill pack for Oracle Cloud (24 skills) |
| `palantir-pack` | Claude Code skill pack for Palantir (24 skills) |
| `perplexity-pack` | Complete Perplexity integration skill pack with 30 skills covering AI search, real-time answers, citations, and research workflows.… |
| `persona-pack` | Claude Code skill pack for Persona (18 skills) |
| `podium-pack` | Claude Code skill pack for Podium (18 skills) |
| `posthog-pack` | Complete PostHog integration skill pack with 24 skills covering product analytics, feature flags, session replay, and experimentation.… |
| `procore-pack` | Claude Code skill pack for Procore (24 skills) |
| `quicknode-pack` | Claude Code skill pack for QuickNode (18 skills) |
| `ramp-pack` | Claude Code skill pack for Ramp (24 skills) |
| `remofirst-pack` | Claude Code skill pack for RemoFirst (12 skills) |
| `replit-pack` | Complete Replit integration skill pack with 30 skills covering cloud IDE, deployments, AI assistance, and collaborative coding. Flagship+… |
| `retellai-pack` | Complete Retell AI integration skill pack with 30 skills covering AI voice agents, phone automation, conversational AI, and call center… |
| `runway-pack` | Claude Code skill pack for Runway (18 skills) |
| `salesforce-pack` | Claude Code skill pack for Salesforce (30 skills) |
| `salesloft-pack` | Claude Code skill pack for Salesloft (18 skills) |
| `sentry-pack` | Complete Sentry integration skill pack with 30 skills covering error monitoring, performance tracking, session replay, and observability.… |
| `serpapi-pack` | Claude Code skill pack for SerpApi (18 skills) |
| `shopify-pack` | Claude Code skill pack for Shopify (30 skills) |
| `snowflake-pack` | Claude Code skill pack for Snowflake (30 skills) |
| `speak-pack` | Complete Speak integration skill pack with 24 skills covering AI language learning, speech recognition, conversation practice, and… |
| `stackblitz-pack` | Claude Code skill pack for StackBlitz (18 skills) |
| `supabase-pack` | Complete Supabase integration skill pack with 30 skills covering authentication, database, storage, realtime, edge functions, and… |
| `techsmith-pack` | Claude Code skill pack for TechSmith (18 skills) |
| `together-pack` | Claude Code skill pack for Together AI (18 skills) |
| `twinmind-pack` | Complete TwinMind integration skill pack with 24 skills covering AI meeting assistant, transcription, summaries, and productivity… |
| `vastai-pack` | Complete Vast.ai integration skill pack with 24 skills covering GPU marketplace, cloud compute, and ML infrastructure. Flagship tier… |
| `veeva-pack` | Claude Code skill pack for Veeva (24 skills) |
| `vercel-pack` | Complete Vercel integration skill pack with 30 skills covering deployments, edge functions, preview environments, performance… |
| `webflow-pack` | Claude Code skill pack for Webflow (24 skills) |
| `windsurf-pack` | Complete Windsurf integration skill pack with 30 skills covering AI code editing, Cascade workflows, codebase understanding, and developer… |
| `wispr-pack` | Claude Code skill pack for Wispr (18 skills) |
| `workhuman-pack` | Claude Code skill pack for Workhuman (18 skills) |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Security

🔐 **26 plugins** · category slug: `security`

| Plugin | Description |
|--------|-------------|
| `access-control-auditor` | Audit access control implementations |
| `authentication-validator` | Validate authentication implementations |
| `compliance-report-generator` | Generate compliance reports |
| `cors-policy-validator` | Validate CORS policies |
| `csrf-protection-validator` | Validate CSRF protection |
| `data-privacy-scanner` | Scan for data privacy issues |
| `dependency-checker` | Check dependencies for known vulnerabilities, outdated packages, and license compliance |
| `encryption-tool` | Encrypt and decrypt data with various algorithms |
| `gdpr-compliance-scanner` | Scan for GDPR compliance issues |
| `hipaa-compliance-checker` | Check HIPAA compliance |
| `input-validation-scanner` | Scan input validation practices |
| `owasp-compliance-checker` | Check OWASP Top 10 compliance |
| `pci-dss-validator` | Validate PCI DSS compliance |
| `penetration-tester` | Automated penetration testing for web applications with OWASP Top 10 coverage |
| `secret-scanner` | Scan codebase for exposed secrets, API keys, passwords, and sensitive credentials |
| `security-audit-reporter` | Generate comprehensive security audit reports |
| `security-headers-analyzer` | Analyze HTTP security headers |
| `security-incident-responder` | Assist with security incident response |
| `security-misconfiguration-finder` | Find security misconfigurations |
| `session-security-checker` | Check session security implementation |
| `severity1-marketplace` | Severity level classification and prompt improvement for marketplace plugins. Assigns severity ratings (S1-Critical through S4-Low) and… |
| `soc2-audit-helper` | Assist with SOC2 audit preparation |
| `sql-injection-detector` | Detect SQL injection vulnerabilities |
| `ssl-certificate-manager` | Manage and monitor SSL/TLS certificates |
| `vulnerability-scanner` | Comprehensive vulnerability scanning for code, dependencies, and configurations with CVE detection |
| `xss-vulnerability-scanner` | Scan for XSS vulnerabilities |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Skill Enhancers

✨ **8 plugins** · category slug: `skill-enhancers`

| Plugin | Description |
|--------|-------------|
| `axiom` | Battle-tested Claude Code skills for modern xOS (iOS, iPadOS, watchOS, tvOS) development - 13 production-ready skills covering debugging,… |
| `calendar-to-workflow` | Enhances calendar Skills by automating meeting prep and workflow triggers |
| `file-to-code` | Converts file references into executable code implementations |
| `research-to-deploy` | Transforms research findings into deployed solutions automatically |
| `search-to-slack` | Automatically posts search results to Slack channels |
| `skill-creator` | Create and validate production-grade agent skills with 100-point marketplace grading. Supports creation workflows, eval-driven… |
| `validate-plugin` | Validate Claude Code plugin structure against official Anthropic spec and Intent Solutions enterprise standard with 100-point grading. |
| `web-to-github-issue` | Enhances web_search Skill by automatically creating GitHub issues from research findings. Research topics, extract key insights, and… |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

### Testing

🧪 **26 plugins** · category slug: `testing`

| Plugin | Description |
|--------|-------------|
| `accessibility-test-scanner` | A11y compliance testing with WCAG 2.1/2.2 validation, screen reader compatibility, and automated accessibility audits |
| `api-fuzzer` | Fuzz testing for APIs with malformed inputs, edge cases, and security vulnerability detection |
| `api-test-automation` | Automated API endpoint testing with request generation, validation, and comprehensive test coverage |
| `browser-compatibility-tester` | Cross-browser testing with BrowserStack, Selenium Grid, and Playwright - test across Chrome, Firefox, Safari, Edge |
| `chaos-engineering-toolkit` | Chaos testing for resilience with failure injection, latency simulation, and system resilience validation |
| `code-cleanup` | Comprehensive codebase cleanup across 11 quality dimensions — dead code, duplication, weak types, circular deps, defensive cruft, legacy… |
| `contract-test-validator` | API contract testing with Pact, OpenAPI validation, and consumer-driven contract verification |
| `database-test-manager` | Database testing utilities with test data setup, transaction rollback, and schema validation |
| `e2e-test-framework` | End-to-end test automation with Playwright, Cypress, and Selenium for browser-based testing |
| `integration-test-runner` | Run and manage integration test suites with environment setup, database seeding, and cleanup |
| `load-balancer-tester` | Test load balancing strategies with traffic distribution validation and failover testing |
| `mobile-app-tester` | Mobile app test automation with Appium, Detox, XCUITest - test iOS and Android apps |
| `mutation-test-runner` | Mutation testing to validate test quality by introducing code changes and verifying tests catch them |
| `performance-test-suite` | Load testing and performance benchmarking with metrics analysis and bottleneck identification |
| `regression-test-tracker` | Track and run regression tests to ensure new changes don't break existing functionality |
| `security-test-scanner` | Automated security vulnerability testing covering OWASP Top 10, SQL injection, XSS, CSRF, and authentication issues |
| `smoke-test-runner` | Quick smoke test suites to verify critical functionality after deployments |
| `snapshot-test-manager` | Manage and update snapshot tests with intelligent diff analysis and selective updates |
| `test-coverage-analyzer` | Analyze code coverage metrics, identify untested code, and generate comprehensive coverage reports |
| `test-data-generator` | Generate realistic test data including users, products, orders, and custom schemas for comprehensive testing |
| `test-doubles-generator` | Generate mocks, stubs, spies, and fakes for unit testing with Jest, Sinon, and test frameworks |
| `test-environment-manager` | Manage test environments with Docker Compose, Testcontainers, and environment isolation |
| `test-orchestrator` | Orchestrate complex test workflows with dependencies, parallel execution, and smart test selection |
| `test-report-generator` | Generate comprehensive test reports with coverage, trends, and stakeholder-friendly formats |
| `unit-test-generator` | Automatically generate comprehensive unit tests from source code with multiple testing framework support |
| `visual-regression-tester` | Visual diff testing with Percy, Chromatic, BackstopJS - catch unintended UI changes |

<sub>⬆ [Back to category index](#browse-plugins-by-category)</sub>

<!-- AUTO-TOC:END -->

---

## How Agent Skills Work

Agent Skills are instruction files (`SKILL.md`) that teach Claude Code **when** and **how** to perform specific tasks. Unlike commands that require explicit `/slash` triggers, skills activate automatically when Claude detects relevant conversation context.

### The Activation Flow

```
1. INSTALL     /plugin install ansible-playbook-creator@claude-code-plugins-plus
2. STARTUP     Claude reads SKILL.md frontmatter → learns trigger phrases
3. ACTIVATE    You say "create an ansible playbook for Apache"
4. EXECUTE     Claude matches trigger → reads full skill → follows instructions
```

### What a Skill Looks Like

```yaml
---
name: ansible-playbook-creator
description: |
  Generate production-ready Ansible playbooks. Use when automating server
  configuration or deployments. Trigger with "ansible playbook" or
  "create playbook for [task]".
allowed-tools: Read, Write, Bash(ansible:*), Glob
version: 2.0.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: MIT
---

# Ansible Playbook Creator

## Overview
Generates idempotent Ansible playbooks following infrastructure-as-code best practices.

## Instructions
1. Gather target host details and desired state
2. Select appropriate Ansible modules
3. Generate playbook with proper variable templating
4. Validate syntax with `ansible-lint`

## Output
- Complete playbook YAML ready for `ansible-playbook` execution
```

### The Numbers

| Metric | Count |
|--------|-------|
| Total skills | 2,811 |
| Plugins (marketplace) | 415 |
| Agents | 154 |
| Plugin categories | 22 |
| Contributors | 16 |

---

## Plugin Types

### AI Instruction Plugins (295 plugins)
Markdown files that guide Claude's behavior through structured instructions, skills, commands, and agents. No external code — everything runs through Claude's built-in capabilities.

### MCP Server Plugins (9 plugins)
TypeScript applications that run as separate Node.js processes. Claude communicates with them through the Model Context Protocol.

### SaaS Skill Packs (111 plugins across 22 pack collections)
Pre-built skill collections for specific platforms — Deepgram, LangChain, Linear, Gamma, and others. Each pack includes install/auth, core workflows, debugging, deployment, and advanced pattern skills.

---

## Building Your Own

### Templates

| Template | Includes | Best For |
|----------|----------|----------|
| **minimal-plugin** | plugin.json + README | Simple utilities |
| **command-plugin** | Slash commands | Custom workflows |
| **agent-plugin** | Specialized AI agent | Domain expertise |
| **full-plugin** | Commands + agents + hooks + skills | Complex automation |

All templates live in [`templates/`](templates/).

### Step by Step

1. Copy a template: `cp -r templates/command-plugin my-plugin`
2. Edit `.claude-plugin/plugin.json` with your metadata
3. Add your skill to `skills/my-skill/SKILL.md`
4. Validate: `ccpi validate ./my-plugin`
5. Submit a pull request

### Skill Frontmatter Reference

```yaml
---
# Recommended (all fields optional per Anthropic spec)
name: my-skill-name                     # kebab-case, matches folder name
description: |                          # Include "Use when..." and "Trigger with..."
  Describe what this skill does. Use when building X.
  Trigger with "build X" or "create X workflow".
allowed-tools: Read, Write, Bash(npm:*) # Comma-separated, scoped Bash recommended
version: 1.0.0                          # Semver
author: Your Name <you@example.com>
license: MIT

# Optional
model: sonnet                           # Model override (sonnet, haiku, opus)
context: fork                           # Run in subagent
agent: Explore                          # Subagent type
user-invocable: false                   # Hide from / menu
argument-hint: "<file-path>"            # Autocomplete hint
hooks: {}                               # Lifecycle hooks
compatibility: "Node.js >= 18"          # Environment requirements
compatible-with: claude-code, cursor    # Platform compatibility
tags: [devops, ci]                      # Discovery tags
---
```

Path variable: Use `${CLAUDE_SKILL_DIR}` to reference files relative to the skill directory.

---

## Learning Lab

Production agent workflow patterns with empirical verification — guides, diagrams, and working examples.

**[Start Here (5 min)](workspace/lab/README.md)** | **[Architecture Map](workspace/lab/VISUAL-MAP.md)** | **[System Summary](workspace/lab/BUILT-SYSTEM-SUMMARY.md)**

<table>
<tr>
<td width="50%">

**Guides** (90+ pages)
- [Mental Model (5 min)](workspace/lab/GUIDE-00-START-HERE.md)
- [Architecture Deep Dive (15 min)](workspace/lab/GUIDE-01-PATTERN-EXPLAINED.md)
- [Build Your Own (30 min)](workspace/lab/GUIDE-02-BUILDING-YOUR-OWN.md)
- [Debugging Tips (15 min)](workspace/lab/GUIDE-03-DEBUGGING-TIPS.md)
- [Orchestration Pattern (60 min)](workspace/lab/ORCHESTRATION-PATTERN.md)

</td>
<td width="50%">

**Interactive Tutorials** [![Open In Colab](https://colab.research.google.com/assets/colab-badge.svg)](https://colab.research.google.com/github/jeremylongshore/claude-code-plugins-plus-skills/blob/main/tutorials/)
- [Skills (5 notebooks)](000-docs/185-MS-INDX-tutorials.md#skills-tutorials-5-notebooks)
- [Plugins (4 notebooks)](000-docs/185-MS-INDX-tutorials.md#plugins-tutorials-4-notebooks)
- [Orchestration (2 notebooks)](000-docs/185-MS-INDX-tutorials.md#orchestration-tutorials-2-notebooks)

**Reference Implementation**
- [5-Phase Workflow](workspace/lab/schema-optimization/SKILL.md)
- [Phase Contracts & Agents](workspace/lab/schema-optimization/agents/)
- [Verification Scripts](workspace/lab/schema-optimization/scripts/)

</td>
</tr>
</table>

---

## Contributors

Community contributors make this marketplace better. Newest first.

- **[@mjaskolski](https://github.com/mjaskolski) (Michal Jaskolski)** — Added 25 externally-synced agent skills from [wondelai/skills](https://github.com/wondelai/skills) covering product strategy, UX design, marketing/CRO, sales/influence, and growth frameworks. ([#303](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/303))
- **[@clowreed](https://github.com/clowreed) (B12.io)** — Created [b12-claude-plugin](https://tonsofskills.com/plugins/b12-claude-plugin), an official B12.io plugin with a website-generator skill that takes users from idea to production-ready website draft in one conversation. ([#307](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/307))
- **[@duskfallcrew](https://github.com/duskfallcrew) (Duskfall Crew)** — Reported PHP webshell payloads in penetration-tester plugin README that triggered AV false positives. Drove a complete v2.0.0 rebuild with real Python security scanners. ([#300](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/300))
- **[@rowanbrooks100](https://github.com/rowanbrooks100) (Rowan Brooks)** — Created [brand-strategy-framework](https://tonsofskills.com/plugins/brand-strategy-framework), a 7-part brand strategy methodology used by top agencies with Fortune 500 clients. ([#292](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/292))
- **[@RichardHightower](https://github.com/RichardHightower) (Rick Hightower)** — Creator of [SkillzWave](https://skillzwave.ai/) (44,000+ agentic skills). His quality reviews exposed validation gaps and drove 4,300+ lines of fixes plus new validator checks. Author of the [Claude Code Skills Deep Dive](https://pub.spillwave.com/claude-code-skills-deep-dive-part-1-82b572ad9450) series. ([#293](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/293), [#294](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/294), [#295](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/issues/295))
- **[@TomLucidor](https://github.com/TomLucidor) (Tom)** — His question about paid API requirements sparked the "Make All Plugins Free" initiative (v4.1.0) and drove 2,400+ lines of constraint documentation across 6 plugins. ([#148](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/discussions/148))
- **[@alexfazio](https://github.com/alexfazio) (Alex Fazio)** — Production agent workflow patterns and validation techniques that inspired the Learning Lab system (v4.0.0).
- **[@lukeslp](https://github.com/lukeslp) (Lucas Steuber)** — Created geepers-agents with 51 specialized agents for development, deployment, quality audits, research, and game development. ([#159](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/159))
- **[@BayramAnnakov](https://github.com/bayramannakov) (Bayram Annakov)** — Created claude-reflect, a self-learning system that captures corrections and syncs them to CLAUDE.md. ([#241](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/241))
- **[@jleonelion](https://github.com/jleonelion) (James Leone)** — Fixed bash variable scoping bug in Learning Lab scripts and improved markdown formatting. ([#239](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/239))
- **[@CharlesWiltgen](https://github.com/CharlesWiltgen) (Charles Wiltgen)** — Created Axiom, iOS development plugin with 13 production-ready skills for Swift/Xcode. ([#121](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/121))
- **[@aledlie](https://github.com/aledlie) (Alyshia Ledlie)** — Fixed 7 critical JSON syntax errors and added production CI/CD patterns. ([#117](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/117))
- **[@JackReis](https://github.com/JackReis) (Jack Reis)** — Contributed neurodivergent-visual-org plugin with ADHD-friendly Mermaid diagrams. ([#106](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/106))
- **[@terrylica](https://github.com/terrylica) (Terry Li)** — Built prettier-markdown-hook with zero-config markdown formatting. ([#101](https://github.com/jeremylongshore/claude-code-plugins-plus/pull/101))
- **[@beepsoft](https://github.com/beepsoft)** — Quality feedback on skill implementations that drove ecosystem-wide improvements. ([#134](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/134))
- **[@clickmediapropy](https://github.com/clickmediapropy)** — Reported mobile horizontal scrolling bug. ([#120](https://github.com/jeremylongshore/claude-code-plugins-plus/issues/120))

**Want to contribute?** See [CONTRIBUTING.md](./000-docs/007-DR-GUID-contributing.md) or reach out to **jeremy@intentsolutions.io**

---

## Resources

### Official Anthropic

- [Claude Code Documentation](https://docs.anthropic.com/en/docs/claude-code/)
- [Agent Skills Guide](https://docs.anthropic.com/en/docs/claude-code/skills)
- [Plugin Reference](https://docs.anthropic.com/en/docs/claude-code/plugins)
- [Best Practices](https://www.anthropic.com/engineering/claude-code-best-practices)

### Technical Deep Dives

- [Claude Skills Deep Dive](https://leehanchung.github.io/blogs/2025/10/26/claude-skills-deep-dive/) — Lee-Han Chung's definitive technical analysis
- [Skills Deep Dive Series](https://pub.spillwave.com/claude-code-skills-deep-dive-part-1-82b572ad9450) — Rick Hightower's architecture-focused analysis
- [SkillzWave](https://skillzwave.ai/) — Universal skill installer supporting 14+ coding agents

### Community

- [Claude Developers Discord](https://discord.com/invite/6PPFFzqPDZ) — 40,000+ members
- [GitHub Discussions](https://github.com/jeremylongshore/claude-code-plugins/discussions) — Ideas, Q&A, show and tell
- [Issue Tracker](https://github.com/jeremylongshore/claude-code-plugins/issues) — Bugs and feature requests
- [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code) — Curated resource list

### Ecosystem

- [AgentSkills.io](https://agentskills.io) — Open standard for skill compatibility fields
- [Numman Ali's Skills](https://github.com/numman-ali/n-skills) — Externally-synced community skills
- [Prism Scanner](https://github.com/aidongise-cell/prism-scanner) — Open-source security scanner for agent skills, plugins, and MCP servers (39+ rules, AST taint tracking, A-F grading)
- [CCHub](https://github.com/Moresl/cchub) - A desktop control panel for the Claude Code / Codex / Gemini CLI ecosystem. Manage MCP servers, config profiles, agent skills, CLAUDE.md, hooks, and workflow templates from a single Tauri app (Windows / macOS / Linux).

---

<details>
  <summary><strong>Documentation & Playbooks</strong> (click to expand)</summary>

  | Document | Purpose |
  |----------|---------|
  | **[User Security Guide](./000-docs/071-DR-GUID-user-security.md)** | How to safely evaluate and install plugins |
  | **[Code of Conduct](./000-docs/006-BL-POLI-code-of-conduct.md)** | Community standards |
  | **[Security Policy](./000-docs/008-TQ-SECU-security.md)** | Threat model, vulnerability reporting |
  | **[Changelog](./000-docs/247-OD-CHNG-changelog.md)** | Release history |

  **Production Playbooks** (11 guides, ~53,500 words):
  - [Multi-Agent Rate Limits](000-docs/204-DR-SOPS-01-multi-agent-rate.md)
  - [Cost Caps & Budgets](000-docs/196-DR-SOPS-02-cost-caps.md)
  - [MCP Server Reliability](000-docs/198-DR-SOPS-03-mcp-reliability.md)
  - [Incident Debugging](000-docs/203-DR-SOPS-05-incident-debugging.md)
  - [Compliance & Audit](000-docs/200-DR-SOPS-07-compliance-audit.md)
  - [Advanced Tool Use](000-docs/207-DR-SOPS-11-advanced-tool-use.md)
  - [Full Index](000-docs/206-DR-SOPS-readme.md)

</details>

---

## Important Notes

**Not on GitHub Marketplace.** Claude Code plugins use a separate ecosystem with JSON-based catalogs hosted in Git repositories. This repository is a Claude Code plugin marketplace.

**Free and open-source.** All plugins are MIT-licensed. No monetization mechanism exists for Claude Code plugins. See [Monetization Alternatives](docs/monetization-alternatives.md) for external revenue strategies.

**Production status.** Claude Code plugins launched in public beta (October 2025) and are now a stable part of the Claude Code workflow. This marketplace tracks all specification changes.

---

## License

MIT License — See [LICENSE](LICENSE) for details.

---

<div align="center">

**[Star this repo](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)** if you find it useful

**[Get Started](#quick-start)** | **[Browse Plugins](https://tonsofskills.com/explore)** | **[Contribute](#contributors)**

</div>

---

**Version**: 4.20.0 | **Last Updated**: March 2026 | **Skills**: 2,811 | **Plugins**: 415
