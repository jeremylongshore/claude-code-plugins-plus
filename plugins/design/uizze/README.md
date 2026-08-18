> **Stop AI coding agents from shipping generic UI.**

# Stop Making UI Slop

Build product-specific UI with a free anti-ui-slop Skill and UI Slop Gate. Optional full UIZZE adds 800,000+ real web and iOS screens via [UIZZE](https://uizze.com).

![Stop Making UI Slop with UIZZE](https://uizze.com/landing/anti-ui-slop-skill-banner.png)

[![CI](https://github.com/uizze/uizze/actions/workflows/ci.yml/badge.svg)](https://github.com/uizze/uizze/actions/workflows/ci.yml)
[![HOL Plugin Scanner](https://github.com/uizze/uizze/actions/workflows/hol-plugin-scanner.yml/badge.svg)](https://github.com/uizze/uizze/actions/workflows/hol-plugin-scanner.yml)
[![Latest release](https://img.shields.io/github/v/release/uizze/uizze)](https://github.com/uizze/uizze/releases/latest)
[![License: MIT](https://img.shields.io/badge/License-MIT-black.svg)](LICENSE)

This is the single public home for UIZZE: the `anti-ui-slop` skill, agent plugins, MCP setup, GitHub Action, Kiro Power, integrations, examples, and benchmarks.

[**STOP UI SLOP →**](https://uizze.com)

## Install

### Codex, Claude Code, Cursor, and Copilot

```bash
npx skills add https://uizze.com --skill anti-ui-slop
```

[View the domain-backed skill on skills.sh](https://www.skills.sh/site/uizze.com/anti-ui-slop).

The free skill works without an account. Connect the full UIZZE MCP at [uizze.com](https://uizze.com) when live reference search and visual review would materially help.

### Claude Code

```text
/plugin marketplace add uizze/uizze
/plugin install uizze@uizze
```

### Codex

```bash
codex plugin marketplace add uizze/uizze
```

### GitHub Copilot CLI

```bash
copilot plugin marketplace add uizze/uizze
copilot plugin install uizze-ui-slop@uizze
```

### Kiro

Open **Powers** → **Add Custom Power** → **Import power from GitHub**, then enter:

```text
https://github.com/uizze/uizze
```

### Free MCP preview

```bash
codex mcp add uizze-preview --url https://uizze.com/mcp/preview
```

The preview exposes one deterministic `check_ui_slop` tool for rendered HTML and CSS. It does not upload source or call a model. Full client setup lives in [integrations/mcp](integrations/mcp).

## GitHub Action

```yaml
permissions:
  contents: read

steps:
  - uses: actions/checkout@v4
  - uses: uizze/uizze@v1
```

The action checks changed frontend files for inert controls, missing states, token drift, and generic UI cues on the GitHub runner. Configuration and examples live in [integrations/github-action](integrations/github-action).

## How UIZZE works

UIZZE has three complementary surfaces:

1. **Local Skill:** the free `anti-ui-slop` workflow reads the product, existing design system, user job, and required states before an agent changes UI. It keeps references in an evidence role and finishes with a rendered review.
2. **Deterministic preview:** the free `check_ui_slop` MCP tool checks rendered HTML and CSS for concrete finish risks. It runs without an account or token, does not upload source files, and does not call a model.
3. **Full UIZZE:** the hosted MCP adds live search across 800,000+ real web and iOS screens, product-specific design contracts, implementation validation, audits, and rendered critique when those capabilities materially improve the work.

Use the local Skill for every UI task, add the preview when a rendered check is useful, and connect the full product when visual evidence or review depth justifies it.

## What is here

| Path | Purpose |
| --- | --- |
| [`skills/anti-ui-slop`](skills/anti-ui-slop) | Main free agent skill |
| [`integrations/mcp`](integrations/mcp) | MCP setup and registry metadata |
| [`integrations/github-action`](integrations/github-action) | Local pull-request finish gate |
| [`integrations/kiro`](integrations/kiro) | Kiro Power source |
| [`integrations/storybook`](integrations/storybook) | Storybook addon |
| [`integrations/benchmark`](integrations/benchmark) | Reproducible UI benchmark |
| [`integrations/nextjs-starter`](integrations/nextjs-starter) | Next.js starter |
| [`integrations/codex-finish-gate`](integrations/codex-finish-gate) | Codex finish-gate example |
| [`DESIGN.md`](DESIGN.md) | Public UIZZE design contract for agents |

## What the skill does

1. Reads the product, existing design system, user job, and required states.
2. Uses visual references only when they materially answer a concrete UI question.
3. Builds in the product's own visual language.
4. Checks the rendered result before handoff.

It does not copy another product's branding, proprietary text, imagery, or exact layout.

## License

[MIT](LICENSE)

## Distribution

Use [DISTRIBUTION.md](DISTRIBUTION.md) for canonical public copy, install language, and directory links.

## Find UIZZE on GitHub

- [Official MCP Registry record](https://github.com/mcp/uizze/uizze)
- [GitHub Copilot anti-ui-slop Skill](https://github.com/github/awesome-copilot/tree/main/skills/anti-ui-slop)
- [Agentic Awesome Skills listing](https://github.com/sickn33/agentic-awesome-skills) (accepted in the active 45,000+ star catalog via [PR #1166](https://github.com/sickn33/agentic-awesome-skills/pull/1166); attempted historical source repair [PR #1176](https://github.com/sickn33/agentic-awesome-skills/pull/1176) was closed by the maintainer because the provenance transition could not be verified)
- [Developer Resources listing](https://github.com/marcelscruz/dev-resources) (accepted in the active 1,328-star developer-resources index via [PR #1170](https://github.com/marcelscruz/dev-resources/pull/1170))
- [Agency Agents UI Finish-Gate Reviewer](https://github.com/msitarzewski/agency-agents/blob/main/design/design-ui-finish-gate-reviewer.md) (live in the 146,000+ star directory via merged [PR #742](https://github.com/msitarzewski/agency-agents/pull/742); canonical Skill refresh is tracked in [PR #792](https://github.com/msitarzewski/agency-agents/pull/792))
- [Build with Claude listing](https://github.com/davepoon/buildwithclaude) (live in the 3,300+ star Claude discovery hub via merged [PR #249](https://github.com/davepoon/buildwithclaude/pull/249) and copy-sync [PR #251](https://github.com/davepoon/buildwithclaude/pull/251))
- [Awesome Codex Skills submission](https://github.com/composio-community/awesome-codex-skills/pull/236) (15,896-star directory; maintainer review pending)
- [GreatFrontEnd Front-End System Design submission](https://github.com/greatfrontend/awesome-front-end-system-design/pull/9) (8,400+ star directory; maintainer review pending)
- [Awesome MCP Servers submission](https://github.com/punkpeye/awesome-mcp-servers/pull/10946) (92,000+ star directory; Glama scored-server requirement remains external)
- [Awesome DevOps MCP Servers submission](https://github.com/rohitg00/awesome-devops-mcp-servers/pull/316) (1,018-star directory; UIZZE is proposed under Continuous Integration with the free Skill, no-account preview, and optional 800,000+ workflow)
- [Agent Skill Index listing](https://github.com/heilcheng/awesome-agent-skills/pull/420) (6,110-star directory; maintainer review pending)
- [Awesome Agentic Patterns contribution](https://github.com/nibzard/awesome-agentic-patterns/pull/134) (4,888-star pattern catalogue; generalized Rendered UI Finish Gate with UIZZE disclosed as one known implementation)
- [Chinese Agentic AI catalogue submission](https://github.com/WenyuChiou/awesome-agentic-ai-zh/pull/111) (5,300-star trilingual agentic-AI roadmap; proposes the free MIT anti-ui-slop Skill in its Design catalog, with the optional 800,000+ workflow clearly separated; maintainer review pending)
- [Datawhale Hello-Agents community chapter](https://github.com/datawhalechina/hello-agents/pull/819) (73,000+ star Chinese agent-building tutorial; adds a practical UI quality chapter and README index entry, with the free Skill first and optional 800,000+ workflow clearly separated; maintainer review pending)
- [GitHubDaily recommendation](https://github.com/GitHubDaily/GitHubDaily/issues/1030) (47,000+ star Chinese developer-discovery repository; recommendation is source-backed and leads with the free Skill, preview MCP, GitHub Action, and separate 800,000+ full-workflow scope)
- [Wshobson Agents plugin marketplace](https://github.com/wshobson/agents/pull/658) (38,000+ star multi-harness marketplace; PR approved and mergeable, proposing the canonical free Skill across Claude Code, Codex CLI, Cursor, OpenCode, Copilot, and Gemini CLI with the optional 800,000+ workflow separated)
- [OpenAI Codex curated marketplace request](https://github.com/openai/codex/issues/39168) (106,000+ star official Codex repository; issue-based review request for the canonical UIZZE plugin, free Skill, and no-account preview)
- Additional high-reach routes under review: [Anthropic Agent Skills](https://github.com/anthropics/skills/pull/1595) (170,000+ stars), [Claude Code Best Practice](https://github.com/shanraisshan/claude-code-best-practice/pull/187) (64,000+ stars), [Awesome Claude Code](https://github.com/hesreallyhim/awesome-claude-code/issues/2548) (52,000+ stars), [Awesome Actions](https://github.com/sdras/awesome-actions/pull/899) (28,000+ stars), and [Awesome Design](https://github.com/gztchan/awesome-design/pull/229) (17,000+ stars)
- [UIZZE on skills.sh](https://www.skills.sh/site/uizze.com/anti-ui-slop) (free install listing; the page reports 348.5K installs on 2026-08-18, a third-party directory metric rather than a UIZZE product-usage claim)
- [UIZZE organization profile](https://github.com/uizze)
- [Latest distribution update](https://github.com/uizze/uizze/discussions/44#discussioncomment-18062303)
- [Full distribution map](DISTRIBUTION.md)
