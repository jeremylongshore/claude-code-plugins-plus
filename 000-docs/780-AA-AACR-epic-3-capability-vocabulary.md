<!-- doc-class: record -->

# Epic 3 Capability Vocabulary — After-Action Review

- **Date:** 2026-08-18
- **Authority:** Blueprint 727, Epic 3 bead 3.3
- **Filing standard:** [Document Filing Standard v4.4](000-DR-STND-document-filing-system.md)
- **Bead:** `claude-t9s9.3`
- **Implementation PR:** [#1268](https://github.com/jeremylongshore/claude-code-plugins-plus-skills/pull/1268)
- **Merge method:** squash with disclosed, owner-authorized administrator bypass
- **Status:** E3.3 controls implemented; merge fields are recorded in Beads/Dolt after review

## Outcome

The capability vocabulary exists, and coverage over the live corpus is **total and
gate-enforced**: `scripts/check-capability-coverage.mjs` sweeps every tracked `SKILL.md` and
agent definition, parses all four tool-list fields with a real YAML parser, tokenizes through
the ONE shared parser, and reports **30,323 tokens across 5,904 allowlist-bearing files (of
5,949 targets) all covered, zero unparseable frontmatter** — wired as
`validate:capability-coverage` in `doc-governance` (blocks via `ci-required`).

Deliverables:

1. **`scripts/lib/tool-token-parser.mjs`** — THE parser ("one parser, one vocabulary"). Token
   shapes: `builtin` (with `Bash(...)` scopes; scope-internal commas never split),
   `mcp` (`mcp__server[__tool]`), `namespaced` (`ns:tool` custom platform names), `unknown`
   (never silently accepted). Consumers named in the header: E3.4, E3.5, E3.10, E4.2.
2. **`schemas/canonical/v0/capability-map.json`** — 15 abstract capabilities; 20 builtin
   mappings (including `Monitor`/`TaskStop`/`TaskOutput` → `agent.control`, discovered by the
   sweep); shape rules for `mcp` → `service.mcp` and `namespaced` → `service.custom`; and an
   enumerated `dispositions.tolerated` set.
3. **The unknown-token disposition.** All six tolerated tokens live in `.source.json` mirror
   subtrees — `hermes-tweet`'s bare custom tool names and `claude-workflow-skills`'
   space-separated legacy lists — where the never-clobber rule forbids local edits; repair flows
   by upstreaming. An unknown token NOT enumerated fails the gate, naming file and token.

## Jurisdiction boundary

Frontmatter that YAML cannot parse is counted and skipped, not failed here: structural
allowlist validity is the schema validator's jurisdiction (E1.11 made it an ERROR there).
Double-reporting the same defect would create two owners for one fact — the sweep reported
**zero** such files at filing.

## Verification

- `pnpm run validate:capability-coverage` — parser + coverage tests 7/7 (shape classification,
  scope-comma safety, YAML-list flattening, red runs for unmapped builtin and undispositioned
  unknown, disposition/shape coverage, all-four-fields sweep) and the live corpus sweep OK.
- Hosted CI on the implementation PR is the final gate.

## Scope discipline

No SKILL.md, agent file, mirror file, or catalog entry changed — measurement and vocabulary
only. The two upstream-shape repairs (hermes-tweet, claude-workflow-skills) are candidates for
respectful upstreaming per the external-sync model, never local edits.

## Follow-up

- E3.4 extends the contract schema with the adapters/compatibility generator consuming this
  vocabulary; E3.5/E3.10 build their gates on the same parser; Epic 4's E4.2 consumes the
  vocabulary for the runtime-safety boundary.
- The `service.custom` namespace class (`triage:*` etc.) carries Epic 4's per-pack
  runtime-safety review as its disposition.
