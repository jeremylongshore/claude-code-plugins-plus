# cad-dxf-agent (Claude Code plugin)

Deterministic DXF drawing analysis from natural language — **no LLM or API key
required**. The plugin ships a single skill, `cad-dxf-agent`, that drives the
`cad-analyze` CLI and reports the findings.

## Capabilities

| Capability | What it answers |
|---|---|
| compliance | ADA / IBC / custom code compliance |
| health | drawing quality / QA (overlaps, text, orphan layers) |
| takeoff | automated quantity takeoff (counts, lengths, areas) |
| summary | plain-English drawing summary |
| rfi | RFIs generated from detected ambiguities |
| zones | closed-loop room/area detection with area calc |
| compare | revision diff between two DXFs (via `cad-revision`) |

## Prerequisite

The skill drives the `cad-analyze` CLI from the `cad-dxf-agent` Python package:

```bash
pip install "git+https://github.com/jeremylongshore/cad-ai-agent.git"
cad-analyze --version
```

## Use

Install the plugin from the marketplace, then ask Claude Code to analyze a DXF
— for example, *"check this floor plan for ADA compliance"* or *"run a health
report on drawing.dxf"*. The skill (`skills/cad-dxf-agent/SKILL.md`) handles the
rest.

## License

Apache-2.0 — source: <https://github.com/jeremylongshore/cad-ai-agent>.
