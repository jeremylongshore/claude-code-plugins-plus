<!-- doc-class: record -->

# Marketplace Content Projection Security — After-Action Review

- **Date:** 2026-09-02
- **Authority:** [Master Modernization Blueprint 727](727-AT-ARCH-master-modernization-blueprint.md), deterministic projection and security invariants
- **Epic bead:** `claude-sb8j`
- **Canonical children:** `claude-sb8j.1`–`claude-sb8j.7`
- **Implementation PR:** [#1422](https://github.com/jeremylongshore/tons-of-skills-marketplace/pull/1422)
- **Approved candidate:** `6a8f59e86ae64422adb498f52200dbb2301676cc`
- **Merge:** `bf5bac9a9e7d9950b6e86d58e798d8a9e4a06ab3`
- **Status:** Closure candidate; the epic closes only after this record merges, the evidence walk is reproduced, and an independent closure audit passes

## Verdict

The marketplace's public skill and README projection boundary is now fail-closed from source parsing
through browser delivery. Safe YAML parsing replaces the handwritten scalar parser; Markdown rendering
escapes raw HTML and refuses dangerous links; serialized preview truncation preserves Unicode, entities,
and element structure; the generated-content lane executes planted-red parser, renderer, and truncation
proofs inside `ci-required`; and production Caddy now emits a reviewed route-aware Content Security
Policy plus the complete response-header set.

The merge used the normal protected lane. The exact approved tree and squash-merge tree are both
`d5454afa3f52c34b105e1c468b3be790a9d90b27`. Required `ci-required`, `gitleaks`, and
`skill-conform` contexts passed on the approved candidate. CodeQL, all three test-matrix partitions,
the full Playwright/accessibility job, and an independent adversarial review also passed. No admin
bypass, branch-protection change, provenance-mirror edit, secret waiver, CodeQL dismissal, or
production file copy outside the transactional installer was used.

The exact GitHub run receipts are Validate Plugins `33683193620`, gitleaks `33683193598`,
skill-conform `33683193759`, CodeQL `33683193579`, and Playwright/accessibility `33683193605`.

## Canonical bead-to-evidence map

| Scope                      | Bead            | Shipped evidence                                                                                                                            |
| -------------------------- | --------------- | ------------------------------------------------------------------------------------------------------------------------------------------- |
| Safe frontmatter semantics | `claude-sb8j.1` | Pinned install-free YAML parser; malformed, cyclic, aliased, tagged, oversized, and prototype-sensitive inputs refuse                       |
| Safe Markdown rendering    | `claude-sb8j.2` | Inline code remains opaque; raw HTML escapes; executable and obfuscated links refuse                                                        |
| Corpus rollout             | `claude-sb8j.3` | 2,984-skill current projection check; intended semantic deltas classified; 3,775-page build and browser checks pass                         |
| Required CI propagation    | `claude-sb8j.4` | Parser, renderer, and truncation suites execute exactly once in the unconditional credential-free generated-content job                     |
| Presentation recovery      | `claude-sb8j.5` | Eight-README/178-token cohort accounted for; one first-party README converted to safe Markdown; seven mirrors untouched and routed upstream |
| CSP defense in depth       | `claude-sb8j.6` | Base/chat CSP split, ratchet tests, immutable preview snapshot, transactional Caddy installer, and live receipt                             |
| Structure-safe truncation  | `claude-sb8j.7` | No partial Unicode/entity/tag output; corpus-wide balance invariant and raw-response browser proof                                          |

## What shipped

### Source and generated-content boundary

The renderer now accepts the repository's supported YAML forms without exposing YAML syntax as public
description or tool text. It rejects ambiguous or unsafe YAML graph shapes before copying values. The
Markdown boundary treats code as opaque, escapes executable raw HTML, validates link protocols, and
buffers block structure deterministically. The truncator operates on serialized structure rather than
blind character slices, reserving space for closing tags and the ellipsis.

The authoritative public cohort at merge is 2,984 skills across 440 plugins. The rollout retained
catalog identity and ordering while correcting description, tool-list, version, author, and license
semantics. The generated-content lane reported 42/42 tests and exact L0, L1, and catalog projections.
The Epic-1 measurement lane reported 41/41 tests and an exact scorecard read-back.

### Presentation and provenance

All eight affected README projections are recorded in
`marketplace/ops/readme-presentation-routes.json` with source and current hashes. The first-party
Databricks README uses safe accessible Markdown. Kobiton, PortalJS, slack-channel, servicegraph,
claudebase, tonone, and hermes-tweet remain byte-identical to their pinned upstream-owned sources;
their presentation limitations route to upstream rather than being silently patched in a mirror.
The generated-content job explicitly fetches the fixed audit source commit from a depth-one checkout,
so the proof does not depend on that commit remaining an ancestor of the current branch.

### Response security and production

The base policy contains no wildcard, `unsafe-eval`, broad HTTP(S) scheme source, WebSocket scheme, or
`upgrade-insecure-requests`. `/chats` alone receives the reviewed `ws:`/`wss:` exception needed for
user-supplied chat endpoints. The remaining inline script/style exceptions are explicit; script
externalization or nonce work remains separately tracked by `claude-i076` and is not represented as
complete here.

The dependency-free preview uses the same policy source as the Caddy projection. It rejects malformed
and ambiguous request targets, normalizes encoded and dot-segment paths before policy selection,
refuses symlink entries, and snapshots canonical regular-file bytes before request handling. Requests
therefore cannot construct a filesystem path or change served content through a post-index file,
symlink, or ancestor-directory swap. On the representative build, 4,292 files / 295,021,972 bytes
indexed in about 2.2 seconds with about 412 MiB peak RSS; this cost is confined to local/CI preview.

Production Caddy 2.11.2 installed fragment SHA-256
`9fb6990323cd867f009e7f84dc6fab59a0512b2f0567f02b40b2dd0aaa9d0d1e` at
`/etc/caddy/tonsofskills-security-headers.caddy`. Candidate adaptation, post-install validation,
reload, service-active check, and live header probes passed. Nine representative live Chromium routes
returned HTTP 200 with zero `securitypolicyviolation` events; WebSocket policy appeared only on
`/chats/`. Plain and encoded dot-segment chat aliases received the base policy.

## Ten-part closure evidence walk

|   # | Evidence item       | Result and reproducing authority                                                                                                                                                                                                                                                |
| --: | ------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------- |
|   1 | Deploy / execution  | **PASS.** PR #1422 merged; Caddy installer reported the exact fragment hash; `systemctl is-active caddy` returned `active`; live probes returned HTTP 200.                                                                                                                      |
|   2 | Happy path          | **PASS.** `pnpm run validate:generated-content`, `pnpm run validate:security-headers`, production build, Playwright, and live root/chat/skill/plugin/docs/search routes pass.                                                                                                   |
|   3 | Failure path        | **PASS.** Planted tests refuse parser aliases/tags/bounds, executable links/raw HTML, broken truncation, CSP weakening, malformed targets, traversal, outside symlinks, dot-segment overgrant, and post-index swaps.                                                            |
|   4 | Rollback            | **PASS.** Installer fault injection covers both live-file writes and post-install validation for prior-present and prior-absent fragment states. Production retained `/etc/caddy/Caddyfile.bak.csp.20260902T212037Z`; restoring it and reloading Caddy is the bounded rollback. |
|   5 | Durable receipt     | **PASS after merge of this record.** Exact SHAs, run URLs, production hash, backup path, and child mapping are retained here and in Beads/Dolt notes.                                                                                                                           |
|   6 | Docs vs reality     | **PASS.** PR body, tracked policy comments, route registry, package scripts, workflow, and this record describe the merged and observed behavior; no raw-HTML or global-WebSocket claim remains.                                                                                |
|   7 | Blueprint vs actual | **PASS.** The defect remediation was not a numbered Blueprint-727 task. It strengthens Epic-1 deterministic projection and the rank-2/3/4/10 security, provenance, integrity, and portability invariants without changing the model-agnostic architecture.                      |
|   8 | Reproduction first  | **PASS.** Every material defect gained an executable red proof before settlement, including the reviewer-discovered crash, symlink disclosure, route alias overgrant, CodeQL path flow, and post-index TOCTOU.                                                                  |
|   9 | Vertical slice      | **PASS.** Source parser → renderer → truncator → generated artifacts → required CI → preview browser → production Caddy is complete. Nonce/externalization remains explicitly deferred to `claude-i076`.                                                                        |
|  10 | Observed vs claimed | **PASS.** Exact merged-tree equality, independent exact-head approval, CodeQL success, full CI, production hashes, HTTP probes, and live browser events agree with the claims above.                                                                                            |

The closure command map reflects this repository rather than silently assuming the Intent OS
operator layout. There is no root `pnpm run gate` script here; the canonical CI-equivalent command is
`pnpm run verify`, which passed and was observed to refresh catalog scoring as a side effect. That
generated worktree delta was discarded, leaving only this AAR and the regenerated documentation index.
Fresh touched-surface runs of `validate:generated-content`, `validate:security-headers`,
`validate:doc-fact-assertions`, docs-index generation, and markdownlint passed. `audit-harness scan`
returned 2 PASS, 6 ADVISORY, and 0 FAIL: its generic environment lacked OSV Scanner, Semgrep, and a
PATH-visible markdownlint; its full-repository gitleaks subprocess timed out; and its generic local
link scan cannot resolve site-root-relative URLs. These advisories do not replace or contradict the
exact-head required gitleaks, CodeQL, supply-chain, markdownlint, link-check, and browser receipts
listed above.

## Review chronology and corrections

Independent review materially changed the result rather than rubber-stamping it:

1. The first preview implementation used Astro's development middleware and did not put CSP on the
   built static preview. It was replaced with a production-faithful server.
2. The server initially crashed on a malformed absolute request target and followed an outside-root
   symlink. Both received planted raw-HTTP regressions and fail-closed handling.
3. Encoded, double-slash, and dot-segment aliases selected policies differently from Caddy. One shared
   normalized path now drives both policy and asset selection.
4. CodeQL then identified request-derived data reaching a filesystem path expression. An indexed
   lookup removed that flow instead of dismissing the alert.
5. Independent re-review found a post-index TOCTOU swap that could still disclose outside content.
   Immutable byte snapshots removed every request-time filesystem read. The exact final head then
   received independent **APPROVE**, CodeQL success, and 20/20 focused security tests.

## Rollback and residuals

Rollback is deliberately split by layer. Repository rollback is a normal revert of merge
`bf5bac9a9e7d9950b6e86d58e798d8a9e4a06ab3` through protected review. Production header rollback
restores `/etc/caddy/Caddyfile.bak.csp.20260902T212037Z`, removes the installed fragment only if the
restored configuration no longer imports it, validates, reloads, and repeats live probes. The installer
tests prove the same transaction automatically for injected failures; no production outage rehearsal
was needed after a successful first install.

Three residuals are explicit and non-blocking for this epic:

- `claude-i076` owns retirement of the remaining justified `script-src 'unsafe-inline'` debt.
- Preview snapshot memory should be monitored as the generated download corpus grows; it is not a
  production runtime.
- Caddy validation reports pre-existing `basicauth` deprecation and formatting warnings in unrelated
  site blocks. They did not affect adaptation or reload and are not silently folded into this scope.

No remaining child requirement is deferred without an owner. The parent may close only after this AAR
is merged, its exact-head closure bundle is independently audited, and each child is settled through
the mirror-aware Beads path.
