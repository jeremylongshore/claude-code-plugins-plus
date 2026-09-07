# Capability reference — `cad-analyze` JSON shapes

Each subcommand prints one JSON object on stdout under `--json`. Lead the summary
with the headline field and surface the list entries. All fields come straight
from the drawing — never invent them.

## compliance

`cad-analyze compliance <file> [--profile ada|ibc-2021|residential]` reports
`profile_name`, `violation_count`, `warning_count`, `pass_count`, `checks_run`,
and `findings`. Report pass/fail on the profile, then each violation with its
evidence handles and layers.

## health

`cad-analyze health <file>` reports `score` (0–100), `entity_count`,
`layer_count`, `checks_run`, and `issues`. Report the score, then group issues by
severity.

## takeoff

`cad-analyze takeoff <file>` reports `items`, each with `name`, `category`,
`quantity`, `unit`, `source_layer`, and `entity_handles`. Report a quantities
table grouped by category.

## summary

`cad-analyze summary <file>` reports a narrative, layer breakdown, key features,
and `rooms`. Report the narrative and room list.

## rfi

`cad-analyze rfi <file>` reports `items` with `question`, `category`, and
`context`. Report the RFIs as a numbered list.

## zones

`cad-analyze zones <file> [--tolerance 0.5]` reports `zones` with `zone_id`,
`area`, and `label`. Increase tolerance for small geometric gaps.

## compare

`cad-revision diff <master> <revision> --json` exits 0 for no changes, 1 when
changes are found, and 2 on error. `cad-revision bundle` writes a new master,
overlay, and changelog; it never alters the original drawing.
