> ***If your UI screams AI, your app is dead.***

# Stop Making UI Slop

Build distinctive UI with 800,000+ real web and iOS screens via [UIZZE](https://uizze.com).

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
- [Agent Skill Index listing](https://github.com/heilcheng/awesome-agent-skills/pull/420) (6,110-star directory; maintainer review pending)
- [UIZZE on skills.sh](https://www.skills.sh/site/uizze.com/anti-ui-slop) (free install listing; the page reports 348.5K installs on 2026-08-18, a third-party directory metric rather than a UIZZE product-usage claim)
- [UIZZE organization profile](https://github.com/uizze)
- [Latest distribution update](https://github.com/uizze/uizze/discussions/44#discussioncomment-18059783)
- [Full distribution map](DISTRIBUTION.md)
