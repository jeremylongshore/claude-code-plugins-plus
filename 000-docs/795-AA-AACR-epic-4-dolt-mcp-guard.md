<!-- doc-class: record -->

# Epic 4 Dolt-MCP Guard — Prove-or-Withdraw at the Wire — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.9 (escalation #1 from the E4.1 register sweep)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.7`
- **Implementation PR:** [#1283](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1283)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.9 controls implemented; merge fields are recorded in Beads/Dolt after review

## Verdict: PROVEN, not withdrawn

The claim ("destructive verbs are recommend-only — the plugin surfaces them but won't
execute") was **false as shipped**: the registered MCP entrypoint was the raw upstream
`dolt-mcp-server` binary, and `drop_database` / `dolt_reset_hard` / `dolt_push_branch` /
branch deletes / both merges were live, ungated tools for any connected host. The
recommend-only classifier lived only on `dolt-mcp-client.py` — the ancillary path the
plugin's agents use, which no MCP host is obliged to take.

The blueprint's instruction was "drive the **actual MCP entrypoint**, not a unit-tested
helper; if you cannot make it refuse, withdraw the claim." It now refuses.

## What shipped

`plugins/mcp/dolt-mcp-vcs/scripts/dolt-mcp-guard.py` — a stdlib-only stdio JSON-RPC proxy
that IS the documented entrypoint (`guard.py -- dolt-mcp-server --stdio …`):

- The declared destructive set (push / pull / both merges / `reset --hard` / branch-delete /
  `DROP DATABASE`) is refused before the child server ever sees the call, and filtered out of
  `tools/list` responses.
- Every `query`/`exec` runs its `query` argument through the existing `sql_classifier.py`
  chokepoint: `query` must classify read-only; `exec` refuses history-affecting SQL always
  and safe-write SQL without `DOLT_MCP_ALLOW_MUTATION=1` (the wire equivalent of the client's
  `--allow-mutation`).
- Missing or unclassifiable SQL fails **closed**.

## Proof at the wire

- `tests/test_dolt_mcp_guard.py` drives the guard **as a subprocess over real JSON-RPC**
  against a scripted fake server that loudly echoes `EXECUTED` for anything that leaks
  through: all 7 destructive tools refused; reads pass and execute; write-SQL refusals;
  opt-in safe-write path; fail-closed on missing SQL; `tools/list` hides the refused set —
  6/6.
- Live smoke against the **pinned v0.3.6 binary**: an `initialize` + `tools/call
drop_database` handshake through the guard returned `isError: true — REFUSED
(recommend-only)`.

## Deployment + claim surfaces

- This machine's project registration (`~/.claude.json`) re-wired through the guard.
- Plugin README: wiring instructions now register through the guard and say plainly that a
  bare `dolt-mcp-server` registration exposes the destructive verbs ungated; the posture
  section names both enforcement boundaries.
- CLAUDE.md's freshie section wording updated ("surfaces them but won't execute" →
  enforced-at-the-wire wording), and the register (790 § 6) row flipped to `E4.9 closed`.

## Mirror discipline (corrected mid-slice)

`plugins/mcp/dolt-mcp-vcs` is a `.source.json` mirror of Jeremy's own
`jeremylongshore/dolt-mcp-vcs-plugin` — and Epic 4's prohibited scope forbids editing mirror
content. The first draft of this slice hand-edited the mirror; corrected before merge: the
guard + README landed **upstream first**
([dolt-mcp-vcs-plugin#10](https://github.com/jeremylongshore/dolt-mcp-vcs-plugin/pull/10),
merged at `56cb984`), the hand edits were reverted, and the mirror content arrived through the
engine (`sync-external.mjs --relock=dolt-mcp-vcs`, advancing `sources.lock.json` and the
`.source.json` ledger). The upstream repo remains the source of truth; the weekly sync can no
longer clobber the guard because upstream now carries it.

## Scope discipline

E4.10 (declared `destructive_policy` for all MCP plugins + refusal tests) is the separate
next bead; this slice is the single prove-or-withdraw escalation. No other MCP plugin
changed.
