<!-- doc-class: record -->

# Epic 1 MCP Credential SOPS Migration — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 1 bead 1.14 (§ 18.7)
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-hz8f.16`
- **Implementation PR:** [#1256](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1256)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E1.14 delegable controls implemented; rotation asked once, answer pending; merge fields are recorded in Beads/Dolt after review

## Owner gate

Blueprint § 18.7 marks this bead owner-gated: the SOPS move and pre-flight are delegable, the
rotation is not. The owner authorized gated Epic 1–3 execution on 2026-08-18 ("act as owner in
any gated calls u have permission"), under which the SOPS migration below was performed. Per the
blueprint's **asked once, never assumed** rule, the rotation question was put to the owner once
during this slice; no rotation is performed or assumed pending the answer.

## Outcome

The working-tree `/.mcp.json` no longer holds a live-shaped key in plaintext `env`. Before this
slice it carried the Whop API key in plaintext for two MCP server entries (`whop`, `whop-docs`)
— git-ignored and never in git history (verified in § 18.7), but unencrypted on a box where
multiple agent sessions run with filesystem access.

1. **Value moved to SOPS.** The key is age-encrypted in a machine-local `.env.sops`
   (`sops -e --input-type dotenv`), staged only through `/dev/shm` (never plaintext on the SSD),
   with a verified decrypt round-trip. Both MCP entries now launch through `scripts/sops-env`,
   which decrypts to tmpfs, injects the env, and execs the server — the config carries no `env`
   block at all.
2. **`.env.sops` is deliberately UNTRACKED.** The estate SOPS standard commits encrypted files
   to git, but that standard was written for private repos. This repository is public
   (2,000+ stars); publishing ciphertext of a live credential to the public remote buys nothing
   and advertises the target. Chose machine-local-untracked (with an explicit `.gitignore` entry
   and rationale comment) over the committed-ciphertext standard for exactly this repo class.
   What IS tracked: `.sops.yaml` (age recipient rules), `secrets.example.yaml`,
   `scripts/sops-env` (the /dev/shm decrypt-exec wrapper), and the pre-flight gate.
3. **Fail-closed pre-flight.** `scripts/check-mcp-plaintext-creds.mjs` scans the root
   `.mcp.json`'s `env` values: known live prefixes (`apik_`, `sk-`, `ghp_`/`github_pat_`,
   `xox*-`, `AKIA`, `glpat-`, `AGE-SECRET-KEY-`) fail, and any 20+ character opaque
   non-placeholder value fails closed; `${VAR}` interpolations and placeholder shapes pass.
   Scope is exactly the repo root — plugin directories ship example configs with placeholders by
   design and are graded by the skill validator instead. Wired as
   `validate:mcp-plaintext-creds` in the `validate` job (trivially green in CI, where the
   untracked file never exists; the classifier is pinned by unit tests). Epic 4 bead 4.14 owns
   the stronger refuse-to-start integration and the CI-enforced rotation record.

## Verification

- `node --test scripts/check-mcp-plaintext-creds.test.mjs` — 5/5 pass (prefix classes,
  placeholder allowance, opaque-value fail-closed, server/key naming, env-free configs).
- `node scripts/check-mcp-plaintext-creds.mjs` — OK against the migrated `.mcp.json`; the
  pre-migration file fails the same check.
- `scripts/sops-env node -e '…'` — decrypt round-trip OK (value length asserted, never printed).
- A live server start could not be exercised inside the sandboxed session (network-restricted
  `npx`); first natural launch is the next Claude Code session, and the wrapper's env injection
  is proven by the round-trip.

## Scope discipline

No credential value appears in any log, commit, PR body, or this record. No rotation was
performed. No plugin, catalog, package, or release surface changed. Tracked changes are limited
to SOPS scaffolding, the pre-flight gate and tests, `package.json`/workflow wiring,
`.gitignore`, and this AAR's governed projections.

## Follow-up

- **Owner (asked once, pending):** rotate the Whop key in the Whop dashboard; on a yes, the new
  value is re-encrypted into `.env.sops` in one step.
- Epic 4 bead 4.14: refuse-to-start pre-flight at MCP launch plus the rotation record.
