# engineer-design-diagram

Generate production-grade engineering design diagrams as single-file dark-themed HTML with inline SVG, grounded in real repository topology.

## Why this exists

Most diagramming tools produce pretty pictures disconnected from reality. This skill does the opposite: it reads the actual repo (package manifests, docker-compose, k8s, terraform, import graph) and emits a diagram that reflects the real system. It also knows how the system *changed* — PR-diff mode highlights structural deltas, trace mode turns a stack/log into a sequence diagram, and drift mode detects when the architecture has wandered from a stored fingerprint.

## Installation

```bash
/plugin install engineer-design-diagram@claude-code-plugins-plus
```

## Modes

| Mode | What it does | Trigger |
|---|---|---|
| `generate` | Diagram from a live repo's topology | `/design:generate` or "draw the architecture" |
| `diff` | Highlight structural deltas in a PR | `/design:diff` or "diagram this PR" |
| `trace` | Stack/log → sequence diagram | `/design:trace` |
| `watch` | Detect drift against a stored fingerprint | `/design:watch` |

## Output

Single self-contained HTML file that opens in any browser, plus a Mermaid text block for copy-paste into docs. Dark theme with semantic OKLCH color coding by component role. Accessible by default (ARIA, `<title>`/`<desc>`, reduced-motion, keyboard navigation).

## Usage

```bash
/design:generate                # diagram from current repo
/design:diff PR-123             # diff a specific PR
/design:trace ./crash.log       # sequence diagram from a stack trace
/design:watch                   # check for drift since last fingerprint
```

Or invoke the skill directly with natural language: *"draw the architecture for this repo"*, *"diagram this PR"*, *"engineer design diagram"*.

## Pipeline

All four modes share a common five-step flow:

1. **DCI grounding** — read real repo signals (manifests, compose files, k8s, terraform, import graph)
2. **Node/edge graph** — build a typed graph (services, datastores, external systems, queues)
3. **Template fill** — Astro-style HTML template with inline SVG
4. **Fingerprint write** — store the canonical graph for future drift detection
5. **Render** — single-file HTML output, optionally opened in the browser

## Reference materials

| File | Purpose |
|---|---|
| `references/dci-block.md` | Discovery/Categorization/Inference grounding rules |
| `references/drawing-rules.md` | When to use which template, color semantics |
| `references/mode-playbooks.md` | Per-mode step-by-step recipes |
| `references/docs-layout.md` | How to embed diagrams in long-form docs |
| `references/fingerprint-spec.md` | Drift-detection fingerprint format |
| `references/accessibility.md` | ARIA, semantic HTML, reduced-motion |
| `references/troubleshooting.md` | Common failure modes |
| `references/THIRD_PARTY_LICENSES.md` | Cocoon AI palette + arrow-masking attribution |

## Templates

| Template | Use case |
|---|---|
| `templates/base.html` | General architecture diagrams |
| `templates/sequence.html` | Sequence diagrams (trace mode) |
| `templates/docs-layout.html` | Long-form documentation embedding |
| `templates/mermaid-fallback.html` | When the graph is too large for inline SVG |

## Scripts

| Script | Use |
|---|---|
| `scripts/collect_dci.sh` | Gather DCI signals from a repo |
| `scripts/fingerprint.py` | Compute architecture fingerprint |
| `scripts/validate_html.py` | Lint generated HTML for accessibility + correctness |
| `scripts/open_in_browser.sh` | Open the result (xdg-open / open / wslview) |

## Examples

`examples/aws-serverless.html`, `examples/microservices.html`, `examples/tiny-monorepo/expected-architecture.html` — reference outputs you can open directly to see what the skill produces.

## Origin

This is the marketplace plugin port of the global Claude Code skill at `~/.claude/skills/engineer-design-diagram`. Both maintain the same SKILL.md, references, templates, and scripts. The global version is the prototype / reference implementation; this plugin makes it installable from the marketplace for any Claude Code user.

## Credits

Design palette and arrow-masking pattern inspired by [Cocoon AI's architecture-diagram-generator](https://github.com/Cocoon-AI/architecture-diagram-generator) (MIT). See `skills/engineer-design-diagram/references/THIRD_PARTY_LICENSES.md`.

## License

MIT — see [LICENSE](LICENSE).
