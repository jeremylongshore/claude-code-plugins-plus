# Tonone

<img src="https://img.shields.io/badge/version-1.2.0-green"> <img src="https://img.shields.io/badge/license-MIT-green"> <img src="https://img.shields.io/badge/platform-Claude%20Code-blue">

**Founder + Tonone = whole company.**

31 specialists. Engineering executes. Product decides. Operations runs. One session, two commands, zero meetings. 214 skills across every discipline. MIT licensed.

## The idea

A solo founder used to have one choice: stay small, or hire. Now there's a third path.

Tonone is an open-source AI team you install into Claude Code. Not a generalist assistant — specialists. Each agent owns one domain deeply: infrastructure, security, user research, product strategy, growth. They share context, hand off cleanly, and produce work you can ship.

The engineering team (15 agents) builds and ships. The product team (12 agents) decides what to build and why. The operations team (4 agents) keeps the company running. Together, one founder can run what used to take a company.

## Install

**Prerequisites:** [Claude Code](https://docs.anthropic.com/en/docs/claude-code) v1.0+

From your terminal:

```bash
claude plugin marketplace add tonone-ai/tonone
claude plugin install tonone@tonone-ai
```

Or inside an active Claude Code session:

```text
/plugin marketplace add tonone-ai/tonone
/plugin install tonone@tonone-ai
```

### Codex CLI

**Prerequisites:** [Codex CLI](https://github.com/openai/codex) installed

```bash
git clone https://github.com/tonone-ai/tonone
cd tonone
codex
```

Codex reads `AGENTS.md` automatically. Invoke agents and skills by describing what you want:

```text
> Read agents/forge.md and act as Forge — audit this infrastructure
> Read agents/apex.md — plan this project with S/M/L options
> Follow the workflow in skills/warden-audit/SKILL.md
```

Skills are markdown workflow documents in `skills/<name>/SKILL.md`. Read them and follow the steps — no slash commands needed.

## Usage

```text
> /apex-plan Build a real-time analytics platform for our IoT fleet
> /helm-brief Define the next product sprint
> /forge-infra Set up cloud infrastructure for a new SaaS product
> /spine-api Design a REST API for user management
> /warden-audit Run a full security audit on this codebase
> /echo-interview Run a user research session
> /crest-roadmap Build a product roadmap
> /mint-runway How long is our runway and how do we extend it?
> /folk-hire Build a hiring pipeline for a senior engineer
> /brace-sla Define our support SLA tiers
```

Every specialist ships in three modes:

| Mode       | What It Means                                         | Example Skills                                                  |
| ---------- | ----------------------------------------------------- | --------------------------------------------------------------- |
| **Build**  | Create from scratch — production-ready, not tutorials | `/forge-infra`, `/spine-api`, `/prism-ui`, `/touch-app`         |
| **Review** | Audit and fix existing systems                        | `/warden-audit`, `/relay-audit`, `/prism-audit`, `/vigil-check` |
| **Recon**  | Survey a domain for system takeover                   | `/forge-recon`, `/spine-recon`, `/flux-recon`, `/apex-takeover` |

### The Leads

**Apex** leads the engineering team. Tell it what you're building:

```text
You: "Build user authentication for our SaaS"

Apex: I see 3 ways to approach this:

  S — Quick & focused (Spine + Warden, ~30K tokens, ~$0.05)
      Basic JWT auth with security review.

  M — Solid implementation (Spine + Warden + Flux + Relay, ~120K tokens, ~$0.20)
      Auth + session management + user schema + CI tests.

  L — Full build-out (+ Vigil + Atlas, ~250K tokens, ~$0.45)
      Everything in M + monitoring + documentation.

  My recommendation: M. Which level?
```

**Helm** is the head of product. It orchestrates research, strategy, design, and marketing — then hands off a structured brief to Apex when it's time to build.

### System Takeover

Inherited a codebase? Apex runs parallel reconnaissance across all specialists:

```text
> /apex-takeover

Phase 1 — Recon (parallel):
  Atlas maps the architecture
  Forge inventories infrastructure
  Relay assesses the pipeline
  Warden scans for security issues
  Vigil checks observability

Phase 2 — Deep dive (targeted):
  Spine reviews backend quality
  Flux assesses database health
  Prism audits frontend

Phase 3 — Takeover report:
  System map, risk assessment, quick wins, roadmap
```

## The Team

### Engineering — 15 agents

| Agent      | Hat                         | What They Do                                                  |
| ---------- | --------------------------- | ------------------------------------------------------------- |
| **Apex**   | Engineering Lead            | Orchestrates the team, scopes work, controls depth and budget |
| **Forge**  | Infrastructure              | Cloud services, networking, IaC, cost optimization            |
| **Relay**  | DevOps                      | CI/CD, deployments, GitOps, developer experience              |
| **Spine**  | Backend                     | APIs, system design, performance, distributed systems         |
| **Flux**   | Data                        | Databases, migrations, pipelines, data modeling               |
| **Warden** | Security                    | IAM, secrets, compliance, threat modeling                     |
| **Vigil**  | Observability + Reliability | Monitoring, alerting, SRE, incident response, SLOs            |
| **Prism**  | Frontend/DX                 | UI, internal tools, developer portals                         |
| **Cortex** | ML/AI                       | Model training, MLOps, feature engineering, LLM integration   |
| **Touch**  | Mobile                      | Native iOS/Android, cross-platform, app stores                |
| **Volt**   | Embedded/IoT                | Firmware, microcontrollers, edge computing, protocols         |
| **Atlas**  | Knowledge Engineering       | Architecture docs, ADRs, API specs, system diagrams           |
| **Lens**   | Data Analytics & BI         | Dashboards, metrics design, reporting, data storytelling      |
| **Proof**  | QA & Testing                | Test strategy, E2E suites, integration testing, flaky triage  |
| **Pave**   | Platform Engineering        | Developer experience, golden paths, service catalogs          |

### Product — 12 agents

| Agent     | Hat               | What They Do                                                    |
| --------- | ----------------- | --------------------------------------------------------------- |
| **Helm**  | Head of Product   | Orchestrates the product team, writes briefs, hands off to Apex |
| **Echo**  | User Research     | User interviews, personas, Jobs-to-Be-Done, feedback synthesis  |
| **Lumen** | Product Analytics | Metrics frameworks, funnel analysis, OKRs, A/B test design      |
| **Draft** | UX Design         | User flows, information architecture, wireframes                |
| **Form**  | Visual Design     | Brand identity, color systems, typography, design system        |
| **Crest** | Product Strategy  | Roadmap planning, prioritization, competitive analysis          |
| **Pitch** | Product Marketing | Positioning, messaging, value prop, GTM, launch copy            |
| **Surge** | Growth            | Acquisition channels, activation funnels, retention playbooks   |
| **Deal**  | Revenue & Sales   | B2B pipeline, deal strategy, pricing, sales playbooks           |
| **Keep**  | Customer Success  | Onboarding optimization, health scoring, expansion revenue      |
| **Ink**   | Content Marketing | Blog strategy, SEO, thought leadership, developer content       |
| **Buzz**  | PR & Community    | Press pitches, social media, open source community, DevRel      |

### Operations — 4 agents

| Agent     | Hat        | What They Do                                                                        |
| --------- | ---------- | ----------------------------------------------------------------------------------- |
| **Mint**  | Finance    | P&L, runway, unit economics, fundraising, board reporting, cap table                |
| **Folk**  | People     | Org design, hiring pipelines, comp frameworks, onboarding, human-to-agent migration |
| **Keel**  | Operations | Process design, vendor management, legal ops, compliance (SOC2/GDPR)                |
| **Brace** | Support    | Ticket workflow, SLA design, knowledge base, escalation paths                       |

## How it works

Each agent is a system prompt (a markdown file in `agents/`) paired with a set of skills (markdown workflow documents in `skills/<name>/SKILL.md`). The Claude Code plugin system installs all 31 agents and 214 skills in a single command. When you invoke a skill, Claude loads the workflow document and follows it — no code runs, no build step, no configuration.

Every engineering agent detects your stack automatically:

- **Cloud:** GCP, AWS, Azure, Cloudflare, Vercel, Fly.io, Hetzner, DigitalOcean
- **CI/CD:** GitHub Actions, GitLab CI, Cloud Build, CircleCI, Bitbucket Pipelines
- **Backend:** Node.js, Python, Go, Rust, Java/Kotlin, Ruby
- **Databases:** PostgreSQL, MySQL, MongoDB, Redis, BigQuery, Snowflake, Supabase, Planetscale
- **Frontend:** React/Next.js, Vue/Nuxt, Svelte/SvelteKit, Astro
- **Mobile:** Swift/SwiftUI, Kotlin/Compose, React Native, Flutter
- **ML:** PyTorch, scikit-learn, Vertex AI, SageMaker, OpenAI, Anthropic

## All 214 Skills

<details>
<summary>Click to expand full skill list</summary>

### Apex (Engineering Lead)

- `/apex` — Accept any engineering task, route internally to the right sub-skill
- `/apex-plan` — Plan and scope a project with S/M/L options
- `/apex-review` — Cross-cutting review of recent work
- `/apex-status` — CTO-level project status
- `/apex-recon` — Engineering reconnaissance
- `/apex-takeover` — System takeover with parallel recon

### Forge (Infrastructure)

- `/forge` — Accept any infrastructure task, route internally
- `/forge-infra` — Build infrastructure from scratch
- `/forge-network` — Design and build networking
- `/forge-audit` — Audit existing infrastructure
- `/forge-cost` — Estimate and optimize infrastructure cost
- `/forge-diagnose` — Diagnose runtime infra issues
- `/forge-recon` — Infrastructure reconnaissance

### Relay (DevOps)

- `/relay` — Accept any DevOps task, route internally
- `/relay-pipeline` — Build CI/CD pipeline from scratch
- `/relay-docker` — Build production Dockerfiles
- `/relay-deploy` — Set up deployment strategy
- `/relay-ship` — Ship a release end to end
- `/relay-audit` — Audit existing pipeline
- `/relay-recon` — Pipeline reconnaissance

### Spine (Backend)

- `/spine` — Accept any backend task, route internally
- `/spine-api` — Design and build an API
- `/spine-service` — Build a new service from scratch
- `/spine-design` — System design
- `/spine-perf` — Find and fix performance bottlenecks
- `/spine-review` — API and code review
- `/spine-recon` — Backend reconnaissance

### Flux (Data)

- `/flux` — Accept any data task, route internally
- `/flux-schema` — Design and build database schema
- `/flux-migrate` — Build zero-downtime migration
- `/flux-pipeline` — Build a data pipeline
- `/flux-query` — Optimize slow queries
- `/flux-health` — Data quality and pipeline health
- `/flux-recon` — Database reconnaissance

### Warden (Security)

- `/warden` — Accept any security task, route internally
- `/warden-audit` — Full security audit
- `/warden-harden` — Harden a service
- `/warden-iam` — Build IAM from scratch
- `/warden-threat` — Threat model a system
- `/warden-scan` — Automated SAST and dependency vulnerability scan
- `/warden-recon` — Security reconnaissance

### Vigil (Observability + Reliability)

- `/vigil` — Accept any observability task, route internally
- `/vigil-instrument` — Instrument a service
- `/vigil-alert` — Build alerting and runbooks
- `/vigil-incident` — Incident response
- `/vigil-check` — Verify observability posture
- `/vigil-recon` — Observability reconnaissance

### Prism (Frontend/DX)

- `/prism` — Accept any frontend task, route internally
- `/prism-ui` — Build a UI from scratch
- `/prism-component` — Build a reusable component
- `/prism-dashboard` — Build an internal dashboard
- `/prism-chart` — Build data visualization
- `/prism-audit` — Frontend audit
- `/prism-stack` — Audit and document the frontend technology stack
- `/prism-recon` — Frontend reconnaissance

### Cortex (ML/AI)

- `/cortex` — Accept any ML/AI task, route internally
- `/cortex-model` — Build an ML pipeline
- `/cortex-prompt` — Build and test prompts
- `/cortex-integrate` — Integrate LLM into a service
- `/cortex-eval` — Evaluate model performance
- `/cortex-recon` — ML reconnaissance

### Touch (Mobile)

- `/touch` — Accept any mobile task, route internally
- `/touch-app` — Build mobile app from scratch
- `/touch-feature` — Build a mobile feature
- `/touch-ui` — Design and build mobile UI
- `/touch-release` — Set up mobile release pipeline
- `/touch-audit` — Mobile audit
- `/touch-recon` — Mobile reconnaissance

### Volt (Embedded/IoT)

- `/volt` — Accept any embedded/IoT task, route internally
- `/volt-firmware` — Build firmware from scratch
- `/volt-driver` — Build device driver or protocol handler
- `/volt-ota` — Build OTA update system
- `/volt-power` — Power management and optimization
- `/volt-recon` — Firmware reconnaissance

### Atlas (Knowledge)

- `/atlas` — Accept any knowledge/docs task, route internally
- `/atlas-map` — Map the system architecture
- `/atlas-adr` — Write an Architecture Decision Record
- `/atlas-onboard` — Generate onboarding documentation
- `/atlas-report` — Render findings as styled HTML reports in browser
- `/atlas-changelog` — Three-layer changelog management (per-repo, cross-repo, per-agent)
- `/atlas-present` — Release presentations as HTML + Obsidian Canvas
- `/atlas-recon` — Documentation reconnaissance

### Lens (Analytics/BI)

- `/lens` — Accept any analytics/BI task, route internally
- `/lens-dashboard` — Build an analytical dashboard
- `/lens-metrics` — Define and implement metrics framework
- `/lens-chart` — Build a data visualization
- `/lens-report` — Build a reporting pipeline
- `/lens-audit` — Review existing analytics
- `/lens-recon` — Analytics reconnaissance

### Proof (QA & Testing)

- `/proof` — Accept any QA/testing task, route internally
- `/proof-strategy` — Design a test strategy for a project
- `/proof-design` — Design tests before implementation
- `/proof-e2e` — Build E2E test suites with Playwright/Cypress
- `/proof-api` — Build API test suites
- `/proof-audit` — Audit test suite health
- `/proof-recon` — Testing reconnaissance

### Pave (Platform Engineering)

- `/pave` — Accept any platform/DX task, route internally
- `/pave-golden` — Build golden path templates
- `/pave-env` — Set up local development environments
- `/pave-catalog` — Build a service catalog
- `/pave-audit` — Audit developer experience
- `/pave-contribute` — Contribute session learnings back to tonone upstream
- `/pave-recon` — Platform reconnaissance

### Helm (Head of Product)

- `/helm` — Accept any product task, route internally
- `/helm-plan` — Plan a product sprint or initiative
- `/helm-brief` — Write a structured product brief for Apex
- `/helm-handoff` — End-to-end Helm to Apex delivery
- `/helm-arbiter` — Resolve product vs. engineering tension
- `/helm-recon` — Product reconnaissance

### Echo (User Research)

- `/echo` — Accept any user research task, route internally
- `/echo-interview` — Run a structured user interview
- `/echo-feedback` — Synthesize user feedback
- `/echo-segment` — Define user segments and personas
- `/echo-jobs` — Map Jobs-to-Be-Done
- `/echo-recon` — Research reconnaissance

### Lumen (Product Analytics)

- `/lumen` — Accept any product analytics task, route internally
- `/lumen-metrics` — Define a metrics framework
- `/lumen-funnel` — Analyze and improve a funnel
- `/lumen-abtest` — Design an A/B test
- `/lumen-instrument` — Instrument product analytics
- `/lumen-recon` — Analytics reconnaissance

### Draft (UX Design)

- `/draft` — Accept any UX design task, route internally
- `/draft-wireframe` — Wireframe a flow or screen
- `/draft-flow` — Map a user flow end to end
- `/draft-ia` — Design information architecture
- `/draft-patterns` — Document design patterns
- `/draft-landing` — Design a landing page
- `/draft-review` — Review a design for UX quality
- `/draft-recon` — UX reconnaissance

### Form (Visual Design)

- `/form` — Accept any visual design task, route internally
- `/form-brand` — Define or audit brand identity
- `/form-logo` — Design a logo system
- `/form-tokens` — Build a design token system
- `/form-style` — Define a visual style guide
- `/form-component` — Specify UI components
- `/form-web` — Design a web interface
- `/form-mobile` — Design a mobile screen
- `/form-email` — Design an email template
- `/form-social` — Design social and ad creatives
- `/form-palette` — Build a color palette
- `/form-audit` — Audit visual quality and consistency
- `/form-deck` — Design a presentation deck
- `/form-exam` — Evaluate visual quality against standards

### Crest (Product Strategy)

- `/crest` — Accept any strategy task, route internally
- `/crest-roadmap` — Build a product roadmap
- `/crest-okr` — Define OKRs for a team or product
- `/crest-compete` — Competitive analysis
- `/crest-narrative` — Write a strategic narrative
- `/crest-recon` — Strategy reconnaissance

### Pitch (Product Marketing)

- `/pitch` — Accept any marketing task, route internally
- `/pitch-position` — Define positioning and value prop
- `/pitch-message` — Write core messaging
- `/pitch-copy` — Write launch copy
- `/pitch-launch` — Plan a product launch
- `/pitch-landing` — Write a landing page
- `/pitch-recon` — Marketing reconnaissance

### Surge (Growth)

- `/surge` — Accept any growth task, route internally
- `/surge-activation` — Design an activation funnel
- `/surge-plg` — Build a PLG strategy
- `/surge-experiment` — Design a growth experiment
- `/surge-retention` — Build a retention playbook
- `/surge-landing` — Build a growth-optimized landing page
- `/surge-recon` — Growth reconnaissance

### Deal (Revenue & Sales)

- `/deal` — Accept any revenue or sales task, route internally
- `/deal-close` — Diagnose why a deal stalls and write a tailored proposal
- `/deal-outreach` — Cold outbound sequence builder by persona
- `/deal-pipeline` — Design or audit B2B sales pipeline
- `/deal-playbook` — Write sales playbooks and discovery guides
- `/deal-pricing` — Design pricing strategy and packaging
- `/deal-proposal` — Generate a complete B2B proposal
- `/deal-qualify` — MEDDPICC-based deal qualification worksheet
- `/deal-recon` — Audit current pipeline, deal patterns, and ICP definitions

### Keep (Customer Success)

- `/keep` — Accept any customer success task, route internally
- `/keep-churn` — Churn risk classification and intervention sequences
- `/keep-expand` — Design expansion revenue playbooks
- `/keep-health` — Design a customer health scoring model
- `/keep-onboard` — Optimize customer onboarding
- `/keep-playbook` — Write churn prevention and win-back playbooks
- `/keep-qbr` — Generate a QBR for a customer
- `/keep-recon` — Audit onboarding completion, health signals, and churn patterns
- `/keep-segment` — Customer segmentation model by ARR, health, and expansion potential

### Ink (Content Marketing)

- `/ink` — Accept any content marketing task, route internally
- `/ink-brief` — Content brief generator with keyword, intent, structure
- `/ink-calendar` — Build a content calendar
- `/ink-case` — Write customer case studies and success stories
- `/ink-cluster` — Topic cluster architect — pillar posts and internal linking map
- `/ink-distribute` — Distribution plan per piece
- `/ink-post` — Write a blog post from keyword research to publish-ready draft
- `/ink-recon` — Audit current content, SEO health, and competitor coverage
- `/ink-seo` — SEO strategy — topic clusters, keyword gap analysis

### Buzz (PR & Community)

- `/buzz` — Accept any PR or community task, route internally
- `/buzz-community` — Build and manage open source community
- `/buzz-devrel` — Developer relations program design
- `/buzz-hn` — Hacker News post crafter with anti-shadowban rules
- `/buzz-launch` — Design and execute a launch plan
- `/buzz-outreach` — Personalized media and podcast pitch
- `/buzz-pitch` — Write media pitches and press releases
- `/buzz-recon` — Audit press coverage, social presence, community health
- `/buzz-social` — Social media strategy and post drafting

### Mint (Finance)

- `/mint-recon` — Financial recon — audit burn rate, runway, and unit economics health
- `/mint-model` — Build or audit a 3-statement financial model with scenario analysis
- `/mint-budget` — Design annual operating budget — headcount, spend, revenue targets
- `/mint-runway` — Calculate runway and map levers available to extend it
- `/mint-unit` — Audit unit economics — LTV, CAC, payback period, gross margin
- `/mint-board` — Produce board financial package — P&L, cash, metrics, variance vs plan
- `/mint-raise` — Prepare fundraising materials — investor model, data room, cap table
- `/mint-report` — Generate monthly close package, variance analysis, management reports

### Folk (People)

- `/folk-recon` — People recon — audit org design, hiring, comp, onboarding, and perf
- `/folk-org` — Design or review org structure — spans, reporting lines, headcount plan
- `/folk-hire` — Build hiring pipeline — JD, sourcing strategy, interview scorecard
- `/folk-comp` — Design compensation framework — salary bands, equity, total comp
- `/folk-onboard` — Build onboarding playbook — day 1 through week 4, access, milestones
- `/folk-perf` — Design performance management — review cycles, calibration, career ladder
- `/folk-migrate` — Human-to-agent migration — audit roles, design transition playbook
- `/folk-culture` — Document and strengthen company culture — values, norms, health check

### Keel (Operations)

- `/keel-recon` — Ops recon — audit processes, vendors, compliance, OKRs, and friction
- `/keel-process` — Document or redesign a business process — SOP, process map, RACI
- `/keel-vendor` — Manage vendors — selection scorecard, contract review, renewal tracking
- `/keel-legal` — Draft or review legal ops docs — NDA, MSA, SaaS agreement checklist
- `/keel-comply` — Build or audit compliance program — SOC2, GDPR, HIPAA gap analysis
- `/keel-okr` — Design and run OKR program — objectives, key results, cascade, review
- `/keel-cadence` — Design meeting cadence — what to run, how often, who decides what
- `/keel-audit` — Operational efficiency audit — waste, redundancy, and friction scan

### Brace (Support)

- `/brace-recon` — Support recon — audit ticket volume, SLA compliance, CSAT, and KB gaps
- `/brace-triage` — Design ticket triage — routing rules, priority tags, queue structure
- `/brace-kb` — Build or audit knowledge base — coverage gaps, deflection, maintenance
- `/brace-sla` — Design SLA framework — response targets, tier definitions, breach paths
- `/brace-escalate` — Design escalation path — Tier 1 to Tier 2 to Engineering handoff
- `/brace-onboard` — Design support onboarding flow — first-contact experience, setup check
- `/brace-metrics` — Design support metrics dashboard — CSAT, FRT, TTR, deflection, trends
- `/brace-playbook` — Write support playbook — response templates, runbooks, tone guide

</details>

## Roadmap

| Phase                       | Status | What it covers                     |
| --------------------------- | ------ | ---------------------------------- |
| **Engineering** (15 agents) | Done   | Build, ship, operate               |
| **Product** (12 agents)     | Done   | Research, strategy, design, growth |
| **Operations** (4 agents)   | Done   | Finance, people, ops, support      |

## Contributing

Everything is Markdown. Fork it, improve it, open a PR. Agents are system prompts. Skills are workflow docs. No build step.

See [CONTRIBUTING.md](CONTRIBUTING.md) to get started. The highest-leverage contributions right now:

- **Sharpen existing skills** — better steps, sharper output formats, fewer hallucinations
- **Build a new agent** — extend the roster with a domain not yet covered
- **Test on real codebases** — try `/apex-takeover` on a production repo and file what breaks

Tests run with `uv run pytest` from any agent's `scripts/` directory.

| Doc                                  | Covers                       |
| ------------------------------------ | ---------------------------- |
| [Architecture](docs/architecture.md) | How the plugin system works  |
| [Skill Guide](docs/skill-guide.md)   | Writing and improving skills |
| [Agent Guide](docs/agent-guide.md)   | Creating new agents          |
| [Naming Guide](docs/naming-guide.md) | Agent naming conventions     |

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for full release history.

## Shoutouts

Tonone stands on the shoulders of giants. Big thanks to the plugins that shaped how this team thinks and works:

| Plugin              | What it brought                                                                                                                                                                                                                          |
| ------------------- | ---------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
| **superpowers**     | Structured skill workflows, brainstorming loops, TDD discipline, and the worktree-native development model that Tonone runs on                                                                                                           |
| **impeccable**      | Design critique vocabulary and the polish-first mindset baked into Form and Draft                                                                                                                                                        |
| **frontend-design** | Frontend implementation patterns that Prism and Touch draw from                                                                                                                                                                          |
| **ui-ux-pro-max**   | 161 color palettes, 84 UI styles, 57 font pairings, 99 UX guidelines, and the BM25 design search engine now powering `lib/uiux`                                                                                                          |
| **caveman**         | The communication mode that cuts every response to its bones — no fluff, all signal                                                                                                                                                      |
| **open-design**     | 19 design skills and the I-Lang brief protocol that power `form-brief`, the hand-drawn wireframe mode in `draft-wireframe`, and the HTML radar report in `form-critique` — [nexu-io/open-design](https://github.com/nexu-io/open-design) |

## License

MIT. Fork it. Ship it. Use it anywhere. [LICENSE](LICENSE)

---

> README maintained automatically by [🐘 elephant](https://github.com/tonone-ai/elephant) — keep your docs in sync without the manual work.
