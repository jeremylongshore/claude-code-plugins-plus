---
name: cad-dxf-agent
description: Analyzes DXF drawings deterministically — ADA/IBC code compliance, drawing health and QA, quantity takeoff, plain-English summaries, RFI generation, and room/zone detection — with no LLM or API key. Use when a user has a .dxf file and wants to check code compliance, audit drawing quality, pull quantities, summarize a drawing, generate RFIs, or detect rooms and areas. Trigger with "analyze this DXF", "check compliance", "drawing health", "quantity takeoff", "summarize this drawing", "generate RFIs", "detect zones", or "/cad-dxf-agent".
allowed-tools: Read, Glob, Bash(cad-analyze:*), Bash(cad-revision:*), Bash(pip:*), Bash(python:*), Bash(python3:*), AskUserQuestion
argument-hint: a path to a .dxf file (and optionally which check — compliance, health, takeoff, summary, rfi, zones)
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: Apache-2.0
compatibility: Designed for Claude Code, also compatible with Codex and OpenClaw
tags:
  - dxf
  - cad
  - compliance
  - takeoff
  - drawing-analysis
---

# cad-dxf-agent — DXF Drawing Analysis

## Overview

CAD reviewers manually scan drawings for code compliance, QA defects, quantities,
and ambiguities — slow and error-prone. This skill automates that for DXF files by
driving the deterministic `cad-analyze` CLI (no LLM, no API key, no network) and
reporting the findings in prose.

| Capability | What it answers | Command |
|---|---|---|
| **compliance** | Does it meet ADA / IBC / a custom code? | `cad-analyze compliance FILE [--profile ada\|ibc-2021\|residential]` |
| **health** | Is the drawing clean? (overlaps, text, orphan layers) | `cad-analyze health FILE` |
| **takeoff** | How much of everything? | `cad-analyze takeoff FILE` |
| **summary** | What is this drawing, in plain English? | `cad-analyze summary FILE` |
| **rfi** | What's ambiguous / needs clarification? | `cad-analyze rfi FILE` |
| **zones** | What rooms/areas are enclosed, and how big? | `cad-analyze zones FILE` |
| **compare** | What changed between two revisions? | `cad-revision diff MASTER REVISION` |

## Prerequisites

The CLI ships with the `cad-dxf-agent` Python package. Check, install only if missing:

```bash
command -v cad-analyze >/dev/null 2>&1 || \
  pip install "git+https://github.com/jeremylongshore/cad-ai-agent.git"
```

## Instructions

1. Locate the DXF. If the user named a file, use it; otherwise `Glob` for `**/*.dxf` and, if several match, ask which one with `AskUserQuestion`.
2. Pick the capability from the trigger words. If unclear, ask.
3. Run the CLI with `--json`, e.g. `cad-analyze health DRAWING.dxf --json`.
4. Parse the JSON and report in prose. For compliance, pass `--profile` when the user names a code; default `ada`.

See `references/capabilities.md` for each report's JSON shape.

## Output

Report in prose, not raw JSON. Lead with the headline, then cite the drawing's
own evidence—entity handles and layers—so a reviewer can act.

- **compliance**: profile pass/fail, violation count, then each finding.
- **health**: score (0–100), then issues grouped by severity.
- **takeoff**: quantities by category, name, quantity, and unit.
- **summary**: narrative and room list.
- **rfi**: numbered questions ready to send to a reviewer.
- **zones**: detected rooms or areas and computed area.

## Error Handling

- Exit `0` means the command completed. Compliance may exit `1` when violations
  are present; parse its JSON and report the findings rather than treating it as
  a command failure.
- Exit `2` means the file is missing or unreadable. Confirm the path and that it
  is a valid DXF before retrying.
- If `cad-analyze` is unavailable, install the prerequisite once and rerun the
  requested command.
- An empty findings or issues list is a pass; never invent findings.

## Examples

**Check a floor plan for ADA compliance**

```bash
cad-analyze compliance ./plans/level-1.dxf --profile ada --json
```

Report the violation count and every finding's rule and evidence handles.

**Audit drawing quality**

```bash
cad-analyze health drawing.dxf --json
```

Report the score, then group issues by severity.

## Safety

- **Read-only.** Analysis never modifies the DXF. `cad-revision apply`/`bundle` writes a new file; the original is never touched.
- **Offline.** The analysis capabilities make no network calls and use no secrets.

Natural-language editing and agent-mode tool use require a bring-your-own LLM provider and are not exposed here.

## Resources

- `references/capabilities.md` — JSON shape of each report and how to read it.
- Source + issues: <https://github.com/jeremylongshore/cad-ai-agent>
