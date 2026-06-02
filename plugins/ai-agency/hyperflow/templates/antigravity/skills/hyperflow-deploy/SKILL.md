---
name: hyperflow-deploy
description: Hyperflow ship phase. Use when the user is ready to release — verbs like ship, push, release, deploy, "cut a release", "ready to push". Runs pre-push gates (lint + typecheck + build + tests + security sweep), then asks before pushing. Never --no-verify, never force-push to main.
---

# hyperflow-deploy — ship phase (Antigravity single-agent)

Gate, then ship. Follow the `hyperflow` doctrine. Pushing is always an explicit, confirmed step.

## Steps

1. **Pre-push gates** — run in order, fix or halt on failure:
   - lint · typecheck · build · tests · a quick security sweep (no secrets in the diff, no blocked files committed).
2. **Report** the gate results in one short block (pass/fail per gate).
3. **Push gate** via AskUserQuestion — binary `Push / Hold` (no recommended marker). State the branch, ahead/behind vs the remote, and any caveat (e.g. red gate from someone else's files).
4. On **Push**: `git push` the branch (never `--force` to `main`/`master`). On **Hold**: leave commits local and say so.

## Hard rules

- **Never** `git push --no-verify`. If a pre-push hook fails — even on files you don't own — surface it and hold; do not bypass.
- **Never** force-push to `main`/`master`.
- If a gate is red because of a concurrent session's uncommitted/untracked files, report that the push is held on external failure — your commits stay clean and local until the tree is green.
