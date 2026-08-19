<!-- doc-class: record -->

# Epic 4 MCP Destructive-Operation Policies — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.10
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.14`
- **Implementation PR:** [#1288](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1288)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.10 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

Every tracked MCP plugin now carries a declared destructive-operation policy backed by
enforcement:

- **Registry:** `plugins/mcp/destructive-policies.json` — one entry per tracked
  `plugins/mcp/*` dir, living BESIDE the plugin dirs so `.source.json` mirrors stay
  untouched. Each entry: `policy ∈ {refuse, recommend-only, permit-with-confirmation,
permit}` + enforcing artifact + rationale naming the blast radius.
- **Gate:** `scripts/check-mcp-destructive-policy.mjs` (blocking in `validate` via
  `ci-required`) — undeclared/orphan entries fail, artifacts must exist, and every
  refuse/recommend-only declaration **executes** its named refusal test and must pass. A
  declaration is only as good as its passing test.

## The honest tally (full 15-dir sweep, per-plugin code reading)

`refuse=8` (read-only or stubbed surfaces, pinned by `tests/test_mcp_refusal_surfaces.py` —
each surface's tool list is pinned and its falsifying capabilities are banned, so wiring
`child_process` into workflow-orchestrator or octokit into x-bug-triage fails the suite
before it silently becomes `permit`) · `recommend-only=1` (dolt-mcp-vcs, wire-proven by
E4.9's harness) · `permit-with-confirmation=2` (slack-channel's authored policy engine +
nonce HITL; **servicegraph upgraded from prose**: a shipped PreToolUse hook returns
`permissionDecision: ask` on every `unlock_rows` credit spend — curated hardening, the
register's "prose-only against a remote server" escalation resolved) · `permit=3` (honest
no-gate declarations: ai-experiment-logger, domain-memory-agent, pr-to-spec — blast radius
named in each rationale).

## Corrections to the blueprint's premises

- "All 14" — measured **15** dirs, **14 tracked**: `a2a-client` is untracked build output
  from open PR #1170 (leftovers removed from the working tree); the gate's UNDECLARED_PLUGIN
  check self-enforces its declaration the moment that PR merges.
- The register's § 6 intro now points at the registry as the enforced source.

## Verification

Gate live run: `OK (14 tracked MCP plugins declared: permit=3 refuse=8 recommend-only=1
permit-with-confirmation=2)` with both refusal tests executed and passing · gate unit tests
8/8 · refusal-surface suite 3/3 · hosted CI final.
