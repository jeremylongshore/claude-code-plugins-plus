# 716-RA-DATA — Repository State Baseline (Mission 01)

**Mission:** 01 — repository cleanup state & governance baseline
**Captured:** 2026-08-11 · HEAD `4358a65a382d136a70f6ccde51f545b77ec5e9d4` (main, clean tree)
**Machine-readable:** `716-RA-DATA-repo-state-baseline.json` (beside this file)

## Snapshot

| Metric                   | Value                     | Command                                                                |
| ------------------------ | ------------------------- | ---------------------------------------------------------------------- |
| HEAD                     | `4358a65a3`               | `git rev-parse HEAD`                                                   |
| Working tree             | clean (0 entries)         | `git status --porcelain \| wc -l`                                      |
| Tracked files            | 22,963                    | `git ls-files \| wc -l`                                                |
| Worktree size            | 3.2 G                     | `du -sh --exclude=.git .`                                              |
| `.git` size              | 439 M                     | `du -sh .git`                                                          |
| Tracked bytes (stat-sum) | 267,860,729 B (255.5 MiB) | `git ls-files -z \| xargs -0 stat -c %s \| awk '{s+=$1} END{print s}'` |
| Submodules               | 0                         | `git submodule status`                                                 |
| LFS                      | none                      | no lfs entries in `.gitattributes`                                     |
| Local branches / stashes | 15 / 0                    | `git branch` / `git stash list`                                        |

**Measurement-basis note:** earlier discovery quoted "~306 M tracked" from `du` block-allocation;
the reproducible metric is the stat-sum above. Both bases are recorded so future runs diff
apples-to-apples.

## Docs estate at baseline

- Highest filed doc number: **715** → this mission files from **716**.
- `000-docs/000-INDEX.md` **did not exist** at baseline (doc-filing v4.4 violation) — created by
  this PR.
- Tracked docs at baseline: 143. On-disk total was larger; the gap is inventoried in the
  documentation crosswalk (doc 720) and governed by register row 9 (doc 719).

## Reproduce

Re-run the commands above at `4358a65a3` and diff against the JSON. Any drift in tracked-file
count or byte-sum after this PR is explained by the PR's own manifest (docs 719/720).
