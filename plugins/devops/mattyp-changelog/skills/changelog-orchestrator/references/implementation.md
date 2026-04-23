# Implementation Guide

### Phase 1: Initialize & Load Config

1. Read `.changelog-config.json` from the repo root.
2. Validate it with `${CLAUDE_SKILL_DIR}/scripts/validate_config.py`.
3. Decide date range:
   - Weekly mode: today minus 7 days → today
   - Custom mode: use provided `start_date`/`end_date`

### Phase 2: Fetch Changelog Inputs

Collect items from configured sources:
- GitHub: merged PRs + closed issues in date range (labels filtering if configured)
- Slack (optional): messages from configured channels
- Git: commit log summary (conventional commits if enabled)

If a live API isn’t available, still proceed with Git-only changes and record gaps in the final draft.

### Phase 3: AI Synthesis (Narrative Draft)

Create a first draft that:
- Groups changes into **Highlights**, **Features**, **Fixes**, **Breaking Changes**, **Internal/Infra**
- Uses a user-facing tone (clear outcomes, minimal jargon)
- Links back to PRs/issues when URLs are present

### Phase 4: Template Formatting + Frontmatter

1. Load the configured markdown template (or fall back to `${CLAUDE_SKILL_DIR}/assets/weekly-template.md`).
2. Render the final markdown using `${CLAUDE_SKILL_DIR}/scripts/render_template.py`.
3. Ensure frontmatter contains at least `date` (ISO) and `version` (SemVer if known; otherwise `0.0.0`).

### Phase 5: Quality Gate (Deterministic + Editorial)

1. Run deterministic checks using `${CLAUDE_SKILL_DIR}/scripts/quality_score.py`.
2. If score is below threshold:
   - Fix structural issues first (missing sections, broken links, invalid frontmatter)
   - Rewrite only the weakest sections (max 2 iterations)

### Phase 6: PR Creation + User Handoff

1. Write the changelog file to the configured `output_path`.
2. Create a branch `changelog-YYYY-MM-DD`, commit with `docs: add changelog for YYYY-MM-DD`.
3. If `gh` is configured, open a PR; otherwise, print the exact commands the user should run.

---
*[Tons of Skills](https://tonsofskills.com) by [Intent Solutions](https://intentsolutions.io) | [jeremylongshore.com](https://jeremylongshore.com)*
