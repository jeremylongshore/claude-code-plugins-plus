# 720-DR-REFF — Documentation Crosswalk & Governance Reconciliation (Mission 01)

**Captured:** 2026-08-11 @ `4358a65a3`. Sensitive detail (per-file inventory of local-only
documents) lives in the local Mission 01 register, deliberately not in this public document.

## The headline finding

At baseline, `.gitignore` blanket-ignores `000-docs/*` + `000-docs/**/*` behind a narrow
allowlist. Result: **the majority of the on-disk documentation estate (200 of 343 files) was
local-only** — invisible to every clone, including documents **cited by tracked files**. Root
cause: the 2026-05 doc-filing sweep (doc 257) filed legacy docs into the naming scheme locally,
but the allowlist was never extended. None of the 200 was ever in git history.

**Two of the ignore rules are deliberate** (patterns `000-docs/680-AT-DECR-*` and
`000-docs/683-AT-DECR-*`) — those records stay local by standing policy; that part works as
intended and is out of scope for any "fix".

## Classification of the local-only corpus (per-file detail: local register)

| Class                        | Count | Recovery posture                                                                                                                             |
| ---------------------------- | ----- | -------------------------------------------------------------------------------------------------------------------------------------------- |
| historical                   | 158   | leave local; optional future archive cluster (v4.4 nesting) — own bead                                                                       |
| sensitive                    | 20    | never committed without explicit review; subset governed by standing policy                                                                  |
| canonical candidate          | 9     | **5 committed by this PR** (147, 685, 686, 687, 691 — cited + clean); 2 need sanitized versions (bead claude-co8a.15); 2 optional-historical |
| superseded                   | 5     | stale MS-INDX indexes + filing-standard v2 — leave local                                                                                     |
| local runtime evidence       | 4     | leave local                                                                                                                                  |
| duplicate (number collision) | 3     | renumber-on-commit proposal only; numbers 256/264/265 have tracked and local claimants                                                       |
| unresolved                   | 1     | non-conforming filename — own decision                                                                                                       |

## Citations repaired vs deferred

- **Repaired by this PR:** root `CLAUDE.md` § External-sync → doc 691; security-pro-pack
  `012-AT-ARCH` → docs 685/686/687; doc 696 → 686/687; doc 247 changelog → 147.
- **Deferred (bead claude-co8a.15):** two governance records cited by `CLAUDE.md` /
  `012-AT-ARCH` contain identifiers that require sanitized public versions before commit;
  originals retained locally. Citation-resolution proposal accompanies that bead.

## Other governance findings (register rows in doc 719)

1. **`000-INDEX.md` was missing** — created by this PR; indexes the tracked estate. Deviation
   note: local-only files are counted, not listed, by design.
2. **Six stale MS-INDX-era indexes** frozen 2026-05-29 (two duplicate-titled) — superseded by
   `000-INDEX.md`; retirement is a follow-up bead.
3. **`workspace/` is gitignored yet 18 files are tracked** — new work there is silently ignored
   (register row 10).
4. **`tests/RTM.md` dead reference** ("ADR #619" / `000-DR-ADR-*`; real: `260–263-AT-ADEC`) —
   hash-pinned POLICY zone, fix reserved to the repo owner (register row 11).
5. **CLAUDE.md L13** misdescribes AGENTS.md — doc-drift fix bead.
6. **Duplicate governance authority:** `.github/{CONTRIBUTING,SECURITY,CODE_OF_CONDUCT}.md` vs
   filed `000-docs/{007,008,006}` — one canonical home needed (bead).
7. **Non-conforming `000-docs` filenames** (`.sh`/`.txt`/`.json` legacy, `6767/6768/6769`,
   `20260131-*`, `PLAN-*`) — rename bead, approval-gated (renames break citations).
8. **Doc-number collisions** at 256 / 264 / 265 between tracked and local-only claimants —
   global-sequence integrity broken at 3 points; renumber-on-commit proposal only.
