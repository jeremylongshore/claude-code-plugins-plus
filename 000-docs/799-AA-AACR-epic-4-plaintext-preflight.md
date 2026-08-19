<!-- doc-class: record -->

# Epic 4 Plaintext-Credential Refuse-to-Start Pre-Flight — After-Action Review

- **Date:** 2026-08-19
- **Authority:** Blueprint 727, Epic 4 bead 4.14 (owner-gated)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-or1m.13`
- **Implementation PR:** [#1287](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1287)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E4.14's deliverable half implemented; merge fields recorded in Beads/Dolt after review

## The owner-gated half, dispositioned

The bead has two halves. **Rotation is deferred by the owner** (Jeremy, 2026-08-19: "whop is
sidelined right now — good to move forward in everything else"). Per § 18.7's asked-once
discipline this is never re-asked; the residual risk is accepted until Whop resumes. The key
already lives SOPS-encrypted in the machine-local `.sops.env`, injected at launch by
`scripts/sops-env` — what is deferred is retiring the historical value, not the encrypted
posture.

## The delivered half: refuse to start

`check-mcp-plaintext-creds.mjs` (the E1.14 gate) gains `--all-local`: besides the repo
`.mcp.json` it scans **`~/.claude.json`'s project `mcpServers` block for this repo** — the
config that actually launches the MCP servers, and where the § 18.7 plaintext key historically
lived. Wired twice:

- **Blocking pre-commit pre-flight** (`.husky/pre-commit`): work on this box refuses to
  proceed while a live-shaped plaintext `env` value sits in either config.
- **Loud SessionStart hook** (`.claude/settings.json`): every session in this repo opens with
  the pre-flight; a failure prints the sanctioned fix (`.sops.env` + `scripts/sops-env`).

CI keeps the tracked-scope run unchanged (untracked local files never reach a checkout).

## Verification

Both modes green live: tracked scope `OK (1 config)`; `--all-local` `OK (2 configs …; local
pre-flight)` — the Whop servers launch via `sops-env`, the dolt registration carries only an
empty `DOLT_PASSWORD`. Existing gate tests 5/5. Register 790 § 2 gains the § 18.7 row in this
PR.
