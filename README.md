# Tons of Skills — Claude Code Plugins Marketplace

[![CLI](https://img.shields.io/badge/CLI-ccpi-blueviolet?logo=npm)](https://www.npmjs.com/package/@intentsolutionsio/ccpi)
[![Plugins](https://img.shields.io/badge/plugins-418-blue)](https://tonsofskills.com/explore)
[![Skills](https://img.shields.io/badge/skills-2%2C834-green)](https://tonsofskills.com/skills)
[![GitHub Stars](https://img.shields.io/github/stars/jeremylongshore/claude-code-plugins-plus-skills?style=social)](https://github.com/jeremylongshore/claude-code-plugins-plus-skills)
[![Sponsor: Nixtla](https://img.shields.io/badge/Sponsor-nixtla.io-ff6b35)](https://nixtla.io)
[![Buy me a monster](https://img.shields.io/badge/Buy%20me%20a-Monster-FFDD00?logo=buy-me-a-coffee&logoColor=black)](https://buymeacoffee.com/jeremylongshore)

418 plugins, 2,834 skills, 166 agents, 16 community contributors — validated and ready to install.

```bash
pnpm add -g @intentsolutionsio/ccpi    # Install the CLI
ccpi install devops-automation-pack     # Install any plugin
```

Or use Claude's built-in command:
```bash
/plugin marketplace add jeremylongshore/claude-code-plugins
```

**[Browse the marketplace](https://tonsofskills.com)** | **[Explore plugins](https://tonsofskills.com/explore)** | **[Download bundles](https://tonsofskills.com/cowork)**

> **Killer Skill of the Week** — [token-optimizer](https://github.com/alexgreensh/token-optimizer) by Alex Greenshpun ([@alexgreensh](https://github.com/alexgreensh))
>
> **Ghost tokens eat your context. Find them. Fix them. Prevent rot.**
>
> Claude gets measurably dumber as your context fills. Compaction destroys 60-70% of your conversation. Ghost tokens burn through your rate limits on every message. Token Optimizer tracks all of it: live quality scoring on your status line, smart compaction that saves your decisions before they're lost, full analytics dashboard with per-session cost breakdowns, and 6 parallel audit agents that optimize your entire setup. Not a one-time scan. An ongoing intelligence layer for your Claude Code workflow.
>
> *"My Claude Code kept leaking tokens. So I built this. Now my limits last longer, context stays fresh, and I have full visibility and control over my usage & setup."* — Alex Greenshpun
>
> Grade: A | Week of March 23, 2026 | [Install from GitHub](https://github.com/alexgreensh/token-optimizer)
>
> Previous picks: [executive-assistant-skills](https://tonsofskills.com/plugins/executive-assistant-skills), [skill-creator](https://tonsofskills.com/plugins/skill-creator), [cursor-pack](https://tonsofskills.com/plugins/cursor-pack), [crypto-portfolio-tracker](https://tonsofskills.com/plugins/crypto-portfolio-tracker). See all at [tonsofskills.com](https://tonsofskills.com).

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
