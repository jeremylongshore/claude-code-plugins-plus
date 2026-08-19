<!-- doc-class: record -->

# Epic 3 Adapter-Thinness Gate — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 3 bead 3.5
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.5`
- **Implementation PR:** [#1270](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1270)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.5 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

The thin-adapter conformance gate exists and blocks through the required aggregate: an adapter
subtree (a harness-named hidden directory under `plugins/`, or a future generated
`adapters/<harness>/` directory) may never contain a file **byte-identical** to its canonical
counterpart ("a fork is not an adapter"), nor any of the forbidden content classes — reference
material, executable payloads, eval specs, licenses, version manifests — which live exactly
once, in canonical.

Landed **gate-first with a dated waiver**, exactly as the blueprint's execution prompt orders:
`schemas/canonical/v0/adapter-thinness-waivers.json` waives the known Kobiton `.codex` fork
(27 files, all 27 measured byte-identical to canonical at filing — matching the blueprint's
count precisely), names its reason, its date, and its removal owner (`727:epic-3.6`), and is
deleted in the same PR that converts the fork. A waiver without a removal owner is an exemption
class; the live-file test asserts every waiver carries both.

The repo-root `.gemini/` reviewer configuration is explicitly out of adapter scope (host
configuration, not a harness adapter) — pinned by test after the live sweep surfaced it as a
false positive.

## Verification

- `node --test scripts/check-adapter-thinness.test.mjs` — 6/6: subtree recognition (root
  dotdirs excluded), counterpart derivation, byte-identical red run + thin-file pass,
  forbidden-class red runs, waiver prefix scoping, live-waiver shape assertions.
- Live run: `adapter-thinness: OK (27 adapter file(s); 27 under dated waiver)`.
- Wired as `validate:adapter-thinness` in `doc-governance` (blocks via `ci-required`, the same
  aggregate route every Epic 1–3 gate uses — the blueprint's "in ci-required.needs" is satisfied
  through the `doc-governance` dependency). Hosted CI final.

## Scope discipline

No adapter file, canonical file, or mirror changed — the gate and its waiver land first; the
fork conversion is E3.6's PR, which also deletes the waiver and un-double-grades the plugin in
Freshie.

## Follow-up

- E3.6: convert the Kobiton `.codex` fork into a real thin adapter; delete the 27 duplicated
  files and this gate's waiver in the same PR.
- The "adapter capability absent from canonical" check activates when generated adapters carry
  capability declarations (E3.4's generator) — the structural gate lands now, the semantic
  cross-check extends it then.
