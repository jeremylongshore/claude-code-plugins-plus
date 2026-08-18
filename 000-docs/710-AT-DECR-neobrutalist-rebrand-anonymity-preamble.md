<!-- doc-class: record -->

# 710-AT-DECR — Neobrutalist rebrand: design-reference anonymity preamble

**Date:** 2026-08-02
**Status:** Accepted
**Scope:** `marketplace/` visual system, `scripts/name-leak-gate.sh`, `.github/workflows/validate-plugins.yml`

---

## Decision

A specific third-party site was studied as directional reference for the
tonsofskills.com neobrutalist rebrand. **Its name, its author, and its related
properties must not appear in any tracked file, commit message, PR body, doc, or
code comment in this repository.** This preamble is the record that the
constraint exists; it deliberately does not record what the constraint is about.

Enforcement is mechanical, not a matter of remembering: `scripts/name-leak-gate.sh`
fails the build on any hit.

## Why anonymity, and why mechanically

Studying a peer site is ordinary design practice. Naming it in a public
repository is not the same act — a commit is permanent, cached, and syndicated
through forks and mirrors, so a single careless line reads forever as a claim
about someone else's work that they never agreed to be part of. The cost of
avoiding that is one grep in CI; the cost of undoing it after the fact is zero,
because it cannot be undone.

A convention alone would not hold. The repository is worked by multiple parallel
Claude sessions plus external contributors, and the failure mode is a scratch
note or a commit message written at speed. So the rule is a gate.

## Mechanism — adopted, not invented

The sibling repository `blog/jeremylongshore` already solved this problem. We
port its script rather than write a second implementation, and we preserve the
four properties that make it work:

| Property                           | Why it matters                                                                                                                                                                                                     |
| ---------------------------------- | ------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------------ |
| Patterns stored **base64-encoded** | The gate file itself would otherwise be the leak it exists to prevent.                                                                                                                                             |
| `git grep -I -i -F --untracked`    | `--untracked` catches scratch files and drafts, so a leak is caught before it can ever enter a diff — not merely at commit time. `-F` is literal (no regex surprises), `-i` case-insensitive, `-I` skips binaries. |
| Excludes only itself               | Nothing else gets a carve-out; an exclusion list is how gates rot.                                                                                                                                                 |
| Non-zero exit on any hit           | Fails loudly. No advisory mode, no `continue-on-error`.                                                                                                                                                            |

### One deliberate deviation from the sibling list

The sibling's pattern set includes one generic hyphenated term that also occurs,
entirely unrelated, in six files of the in-repo `plugins/community/skills-janitor`
plugin. In a repository carrying 3,000+ skills, that term is ordinary vocabulary.
Carrying it here would make the gate fail on every run from the moment it lands,
and a gate that always fails is a gate somebody deletes. It is omitted, and the
omission is documented in the script header so the next reader does not "restore"
it. Every remaining pattern is distinctive enough that a hit means a real leak.

## Where it runs

A **step in the `validate` job** of `.github/workflows/validate-plugins.yml` —
not a new workflow. Rationale is the one already established by
`check-internal-doc-links.mjs` directly above it: `validate` is in `ci-required`'s
`needs:`, so the gate is blocking on merge with **no change to branch protection**
and no new required-status context to register. Per the CI-gate rules in
`CLAUDE.md`, adding a path-filtered workflow to the required set is exactly the
mistake that produced the stuck-PR class of failures; this avoids it.

Run it locally at any time:

```bash
bash scripts/name-leak-gate.sh   # exits 0 clean, 1 on leak
```

## Consequences

- Reviewers do not need to know the reference site to enforce the rule.
- A contributor who has never read this document still cannot leak the name.
- Should the constraint ever be lifted, the change is a single file deletion plus
  a workflow step removal — and this record explains what was being protected and
  why, without itself becoming the disclosure.

## Refs

- `scripts/name-leak-gate.sh`
- `.github/workflows/validate-plugins.yml` (job `validate`)
- `marketplace/DESIGN.md` — the rebrand's constitution, which likewise names no
  external reference.
