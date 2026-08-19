<!-- doc-class: record -->

# Epic 4 MCP Config Validator Deadline and Fail-Closed Lane — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.8
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.8`
- **Implementation PR:** [#1284](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1284)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.8 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

The `.mcp.json` validation step loses its blanket `|| true`. Two lanes now:

1. **Blocking (`--gate-unambiguous`)** — JSON parse failures, non-object server maps/entries,
   and any server entry missing its transport-essential field (`stdio` ⇒ `command`,
   `http`/`sse` ⇒ `url`). Landed with **zero baseline debt**: all 13 pre-existing findings
   are IS-overlay fields (description/version/enabled), none transport-essential.
2. **Advisory with a deadline** — the overlay findings keep reporting under
   `REPORT-ONLY-UNTIL: 2026-11-17`, policed by the workflow's existing deadline-enforcement
   step, so the report-only state can no longer rot indefinitely. Full `--strict` promotion
   remains the DR-049 soak checklist's call, unchanged.

## Verification

A synthetic probe (`{"type":"http"}` server with no `url`) placed in the scan glob exits 1
with the violation named; removing it returns exit 0 on the live corpus. Hosted CI runs the
new step on this PR.
