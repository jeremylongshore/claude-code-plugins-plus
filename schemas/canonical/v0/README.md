# Canonical harness-free skill contract — v0 (DRAFT)

**Status: DRAFT · UPSTREAM-PENDING.** This repository must never become its own schema
authority: the contract here is the draft to be proposed to `@intentsolutions/core` as the
`skill-contract` authoring schema (blueprint 727, Epic 3 bead 3.13 —
FILED as [intent-eval-core#90](https://github.com/jeremylongshore/intent-eval-core/issues/90),
2026-08-19). Until the kernel adopts it, this directory is the single draft
source and every consumer cites it as DRAFT.

## What this is

`skill-contract.schema.json` validates **`skill-card.yaml`** — home **B** of the four-home
split defined by blueprint 727 § 5.1:

| Home  | File                   | Writer                        | Read by                                                                  |
| ----- | ---------------------- | ----------------------------- | ------------------------------------------------------------------------ |
| A     | `SKILL.md` frontmatter | skill author                  | the model, at catalog load                                               |
| **B** | **`skill-card.yaml`**  | **skill author / maintainer** | **validators, adapter generators, marketplace filters, security review** |
| C     | catalog entry          | catalog maintainer            | catalog builds, the site                                                 |
| D     | evidence store (Dolt)  | CI / eval lab only            | badges, gates, history                                                   |

**Home A is untouched.** The frontmatter keeps the IS 8 required fields (`ALWAYS_REQUIRED`)
exactly as governed by `000-docs/SCHEMA_CHANGELOG.md` § NON-NEGOTIABLES — this contract is
additive. Any governance field the model does not need in order to decide whether to fire lives
here, not in frontmatter.

## The load-bearing rules the schema encodes

1. **Capabilities are abstract.** `filesystem.read`, `shell.exec: { commands: [jq] }`,
   `network.http: { hosts: [...] }` — never a harness tool spelling. `Bash(jq:*)` is a Claude
   Code _expression_ of `shell.exec`; the adapter map owns that translation, and the frontmatter
   `allowed-tools` is derived-checked against it (E3.4/E3.5).
2. **`model_class`, never a vendor literal.** `reasoning-high | balanced | fast`. Adapters
   resolve the tier to a concrete model; an adapter with no matching model **errors** — silent
   substitution is a schema violation (§ 5.4 rule 4).
3. **`adapters[]` is a registry enum, not a wish list.** `claude-code` is the only registered
   adapter at v0. A harness may be listed only when a generated adapter artifact exists; the
   enum grows in lockstep with the registry (E3.11's ratchet). `compatibility` is a GENERATED
   projection of `adapters[]` + `requires` + `unsupported[]` and is rejected here as an unknown
   key — it must never be hand-authored into the contract.
4. **`unsupported[]` fails closed.** Declaring what a harness cannot do (with a reason and a
   `degradation` that defaults to `fail-closed`) is a stronger honest claim than an untested
   portability sentence.
5. **Provenance pins are real.** SPDX-only license expressions; a mirrored skill records the
   upstream URL and a **resolved 40-hex commit** — a branch name is not a pin.
6. **Closed everywhere.** `additionalProperties: false` at every level: an unknown key is a
   contract violation, not an extension point. Extensions go through a schema version bump and,
   eventually, the kernel.

## Validation

```bash
node --test scripts/check-canonical-schema.test.mjs
```

The test suite validates the blueprint § 5.2 example, a minimal contract, and red runs for the
five failure classes the rules above name (unknown keys, vendor-literal model class,
unregistered adapter, branch-name pin, harness tool spelling as capability).

## Companions

- `capability-map.json` (E3.3) — the committed vocabulary mapping every corpus tool token to an
  abstract capability, one parser, one vocabulary.
- `000-docs/778-RA-DATA-model-agnostic-migration-surface.md` — the measured surface every
  Epic 3 bead consumes.
- Blueprint 727 § 5 — the contract's authority; § 5.3 is the field-disposition table for
  today's frontmatter/agent fields.
