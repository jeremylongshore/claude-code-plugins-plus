# PR Pre-screen System — Operator Runbook

Status: production, advisory (never a required check).
Owner: Jeremy Longshore.
Replaces: `.github/workflows/gemini-code-review.yml` (deleted in Phase 3).

## What it does

For every external PR opened against `main`, the `PR Pre-screen` workflow
runs the deterministic `validate-skills-schema.py --marketplace --json`
scanner, classifies the result via `scripts/pr-prescreen/classify.py`,
optionally asks Groq for a 5-line human summary via
`scripts/pr-prescreen/summarize.py`, and emits one of three verdicts:

| Verdict | What it means | PR action | Slack action |
|---|---|---|---|
| `PASS` | zero errors, every changed skill graded C or better | comment on PR | ping `#operation-hired` |
| `CHANGES_REQUESTED` | validator errors OR any skill graded D/F | request-changes review | silent — contributor is the audience |
| `HARD_BLOCK` | structural concern (fatal frontmatter, missing catalog entry, no implementation files, etc.) | request-changes review | ping `#operation-hired` |

The workflow is **advisory**. A failure here NEVER blocks a merge. The
required checks are still `validate` and `marketplace-validation`.

## How it stays fork-safe

The workflow runs on `pull_request_target`, which means it executes in
the base-branch context with access to repo secrets even when the PR
comes from a fork. Two rules keep this safe:

1. PR content is checked out **by HEAD SHA** (not ref) with
   `persist-credentials: false`. Using the SHA prevents TOCTOU on
   force-pushes mid-run.
2. PR-controlled code is **never executed**. We only:
   - Read the diff via the GitHub API.
   - Run the repo's pinned validator (from `main`) against PR content.
   - Send the validator's JSON output to Groq.

The Groq prompt explicitly treats the payload as data, not as
instructions. Prompt-injection resistance is unit-tested in
`scripts/pr-prescreen/test_summarize.py`.

## How to disable in an emergency

```bash
# Flip the repo variable to false. Workflow no-ops on next run.
gh variable set ENABLE_PR_PRESCREEN --body false
```

Workflow stays defined in `.github/workflows/pr-prescreen.yml`; only the
`if:` guard short-circuits. Re-enable by setting the variable back to
`true`.

## How to debug

1. **The workflow didn't run at all.**
   Check `gh variable list` for `ENABLE_PR_PRESCREEN=true`. The whole
   job is gated on that.

2. **The workflow ran but posted no comment.**
   Check the run logs for the `Compute changed plugin paths` step. If
   the PR doesn't touch any `plugins/...` paths, the classifier emits
   `PASS: no plugin paths matched the PR diff.` That's expected, but no
   comment is posted in that case to avoid noise. (Comment-on-empty is
   a future change if needed.)

3. **Comment posted but no Groq summary.**
   Look for `LLM status:` in the comment body. Common reasons:
   - `skipped: no api key` → `GROQ_API_KEY` secret missing.
   - `failed: http 429` → Groq free-tier rate limit hit; will recover
     on next run.
   - `failed: TimeoutError` → 5s deadline exceeded; usually transient.
   The deterministic verdict is always present regardless of Groq state.

4. **Slack ping never arrived.**
   `SLACK_OPERATION_HIRED_WEBHOOK_URL` secret must be set. The workflow
   exits 0 silently if it's missing (matches the rest of the Slack
   surfaces in this repo).

5. **The verdict feels wrong.**
   Reproduce locally:
   ```bash
   python3 scripts/validate-skills-schema.py --marketplace --json > /tmp/v.json
   jq '[.[] | select(.path | contains("plugins/<cat>/<plugin>"))]' /tmp/v.json \
     | python3 scripts/pr-prescreen/classify.py -
   ```

## How to query the audit log

Every pre-screen run appends one row to `freshie/inventory.sqlite` table
`pr_prescreen_log`. Example queries:

```bash
# Verdict distribution over the last 30 days
sqlite3 freshie/inventory.sqlite "
  SELECT verdict, COUNT(*) AS n
  FROM pr_prescreen_log
  WHERE created_at > datetime('now', '-30 day')
  GROUP BY verdict ORDER BY n DESC;
"

# Average end-to-end latency by verdict
sqlite3 freshie/inventory.sqlite "
  SELECT verdict, AVG(latency_ms) AS avg_ms, COUNT(*) AS n
  FROM pr_prescreen_log
  GROUP BY verdict;
"

# Groq hit rate
sqlite3 freshie/inventory.sqlite "
  SELECT groq_used, COUNT(*) AS n
  FROM pr_prescreen_log GROUP BY groq_used;
"
```

The audit step is `continue-on-error: true`, so a DB write failure can
never mask the primary signal (the PR comment + Slack ping already
fired before this step runs).

## Operator-provisioned secrets and variables

| Name | Type | Scope | Purpose |
|---|---|---|---|
| `SLACK_OPERATION_HIRED_WEBHOOK_URL` | secret | repo | Incoming webhook to `#operation-hired`. Shared with 3 other workflows. |
| `GROQ_API_KEY` | secret | repo | Free-tier key from console.groq.com. Optional — workflow falls back to deterministic-only if absent. |
| `ENABLE_PR_PRESCREEN` | variable | repo | `true` enables the workflow. Set to `false` to disable in an emergency. |

## Critical files

| File | Role |
|---|---|
| `.github/workflows/pr-prescreen.yml` | The workflow itself. |
| `scripts/pr-prescreen/classify.py` | Pure function: validator JSON → verdict. |
| `scripts/pr-prescreen/summarize.py` | Optional Groq layer with deterministic fallback. |
| `scripts/pr-prescreen/audit.py` | Appends one row per run to the audit log. |
| `scripts/pr-prescreen/test_classify.py` | Unit tests for the classifier (12 tests). |
| `scripts/pr-prescreen/test_summarize.py` | Unit tests for the summarizer (9 tests). |

Run all tests locally:

```bash
python3 scripts/pr-prescreen/test_classify.py
python3 scripts/pr-prescreen/test_summarize.py
```

## Deferred (separate beads, not in scope here)

- NVIDIA Nemotron as alternative LLM provider — only if Groq rate-limit
  becomes a real constraint.
- Retroactive run against the `claude-tcss` PR backlog.
- Cross-repo rollout to other Intent Solutions repos.
- Promoting any pre-screen verdict to auto-merge — explicit non-goal.
  Humans still approve all merges.
