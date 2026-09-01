# PRD: cad-dxf-agent

**Author:** Jeremy Longshore  
**Date:** 2026-08-31  
**Status:** Active

## Problem

AEC professionals routinely need a quick, trustworthy read of DXF drawings for
health checks, compliance questions, quantity takeoffs, summaries, RFIs, and
zone detection. The deterministic `cad-analyze` CLI provides those capabilities,
but its subcommands and JSON contract are not discoverable through the
marketplace without a focused skill.

## Target users

| User | Context | Primary need |
| --- | --- | --- |
| AEC designer | Reviewing a DXF before a design or bid decision | A concise, reproducible drawing analysis |
| Project manager | Responding to a drawing question or RFI | A traceable summary or issue report |
| Estimator | Preparing quantities from a drawing | A deterministic takeoff without manual entity counting |

## Success criteria

1. A marketplace user can install the plugin and invoke a supported analysis on a DXF through `cad-analyze`.
2. The skill never modifies the source drawing and reports when the local CLI is unavailable.
3. The marketplace skill validator accepts the skill with zero errors.

## Functional requirements

- **FR-1:** Guide users to `cad-analyze` summary, health, compliance, takeoff, RFI, and zone-analysis subcommands.
- **FR-2:** Keep the original DXF read-only; any future editing flow must require an explicit save-as destination.
- **FR-3:** Return concise results and link to the capability reference for command details.

## Out of scope

- Editing, saving, or overwriting CAD drawings.
- LLM or cloud-provider configuration; the wrapped analysis is deterministic and local.
- Rendering or replacing a full CAD desktop application.
