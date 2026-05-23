# Changelog

All notable changes to this skill are documented in this file. Format follows [Keep a Changelog](https://keepachangelog.com/en/1.1.0/).

## [0.2.0] - 2026-04-20

### Added

- **Docs-layout output shape** for dense architecture diagrams — widescreen two-column layout (260px sticky sidebar + main column) modelled on Anthropic docs, Linear docs, and Vercel architecture pages. Hybrid HTML nodes + SVG arrow overlay so node cards stay editable without re-running collision math.
- `templates/docs-layout.html` — parameterized widescreen starter with sidebar (version badge, on-this-page nav, architectural invariants list, legend), diagram card (two-plane stage with HTML nodes and SVG arrow overlay), 2-column detail grid, and footer.
- `references/docs-layout.md` — full widescreen spec: when-to-use decision tree, GitHub-inspired design tokens (`#0f1117` / `#161b22` / `#1c2128` + 4 accent tokens), Inter + JetBrains Mono typography scale, sidebar anatomy, diagram stage geometry, arrow catalogue, detail grid rules, verification math (Liang-Barsky line-rect intersection + endpoint attachment + text-overflow check), anti-patterns.

### Changed

- **SKILL.md** now opens with a `Layout Philosophy` section explaining when to pick single-SVG hero vs docs-layout page. Dense content (≥ 8 nodes, multiple planes, or 4+ subcomponents per node) routes to docs-layout; simple graphs stay with the classic template.
- Step 3 template-selection table now covers both layout shapes. Docs-layout mode is widescreen-first with no mobile breakpoints — target `min-width: 1024px` on `<html>`.
- Feedback loop adds a collision-math step for docs-layout mode (arrow-through-node, endpoint attachment, text overflow) before re-screenshotting.

### Rationale

- Single-SVG hero doesn't scale past ~8 nodes or multi-plane topologies — text packing fights you, arrow-crossing math gets expensive, and there's nowhere to put accompanying detail without stacking below.
- Hybrid HTML + SVG was the clear winner after two rounds of fighting pure-SVG text sizing on a real monorepo diagram (intentional-cognition-os v0.11.0): HTML cards edit cleanly, SVG arrows stay pixel-perfect, and `position: absolute` with known pixel coords makes collision math trivial to verify.

## [0.1.0] - 2026-04-19

### Added

- Initial skill skeleton with SKILL.md, README, LICENSE (MIT), THIRD_PARTY_LICENSES.md
- Four-mode command surface: `/design:generate`, `/design:diff`, `/design:trace`, `/design:watch`
- DCI injection block for package manifests, docker-compose, k8s, terraform, git state
- Base HTML template with OKLCH color tokens, grid background, accessibility scaffolding
- Sequence diagram template for trace-mode output
- Mermaid fallback template for >50-node diagrams
- `scripts/fingerprint.py` for structural fingerprint write/read/diff
- `scripts/validate_html.py` for ARIA + no-external-deps verification
- `scripts/collect_dci.sh` for bounded lazy topology harvesting
- `scripts/open_in_browser.sh` for OS-aware HTML opening
- Reference documentation for color tokens, layout heuristics, fingerprint schema, mode playbooks, accessibility, attribution, troubleshooting
- Eval harness with 4 scenarios (generate/diff/trace/watch) and fixture data
- Attribution to Cocoon-AI/architecture-diagram-generator (MIT) for design pattern borrowing
