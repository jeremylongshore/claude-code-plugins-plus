---
name: status-update-writer
description: |
  Generates dual-product status updates for claude-code-plugins repo and
  tonsofskills.com website. Reads git log, marketplace data, and trackers
  to produce data-driven progress reports.
  Trigger with "write a status update", "status update", "weekly update",
  "progress report", "/status-update-writer".
allowed-tools: 'Read,Glob,Grep,Bash(git:*),Bash(wc:*),Bash(jq:*)'
metadata:
  author: 'Jeremy Longshore <jeremy@intentsolutions.io>'
  version: '1.0.0'
  tier: enterprise
  category: product-management
---

# Status Update Writer

Generates data-driven dual-product status updates by reading actual repo state,
git history, and marketplace metadata.

## Product Context

### Products Tracked

1. **claude-code-plugins** — `~/000-projects/claude-code-plugins`
2. **tonsofskills.com** — marketplace frontend (Astro 5 / Firebase)

### Key Milestones to Track

- Plugin count (current baseline: 340)
- Skill count (current baseline: 1537+)
- SaaS integration packs progress (target: 50)
- Playwright test coverage
- Website deployment status
- Community contributions and PRs

## Instructions

### Step 1: Gather Repo Data

Run these to collect real metrics:

1. **Recent git activity** — Use Bash to run:
   - `git -C ~/000-projects/claude-code-plugins log --oneline --since="1 week ago" --no-merges` (or 2 weeks if sparse)
   - `git -C ~/000-projects/claude-code-plugins shortlog -sn --since="1 week ago" --no-merges`

2. **Current plugin count** — Read `.claude-plugin/marketplace.extended.json` for totalPlugins, skillsEnabled, version

3. **Plugin categories** — Use Glob on `plugins/*/` to count by category

4. **Open PRs/issues** — Use Bash: `git -C ~/000-projects/claude-code-plugins branch -r --list 'origin/*' | wc -l`

### Step 2: Gather Website Data (if accessible)

Check for tonsofskills.com project:

- Look for Astro config, package.json, deployment status
- Recent commits if repo is local
- Firebase hosting status if available

If website project isn't locally available, note "Website data unavailable — manual input needed" and skip to Step 3.

### Step 3: Compute Deltas

Compare current state against known baselines:

- Plugin delta: current - 340 (last known baseline)
- Skill delta: current - 1537
- New categories or SaaS packs added
- Notable new features or breaking changes from git log

### Step 4: Write the Status Update

Format as:

```
# Status Update — {date}

## TL;DR
{2-3 sentence summary of the most important progress}

---

## REPO: claude-code-plugins

### Metrics
| Metric | Current | Delta | Target |
|--------|---------|-------|--------|
| Plugins | {n} | +{delta} | — |
| Skills | {n} | +{delta} | — |
| SaaS Packs | {n} | +{delta} | 50 |
| Version | {ver} | — | — |

### Highlights
- {Notable commits, features, or fixes from git log}
- {New plugins or categories added}
- {Community contributions}

### Issues / Blockers
- {Any open issues or technical debt}

---

## WEBSITE: tonsofskills.com

### Progress
- {Deployment status}
- {New pages or features}
- {SEO or performance improvements}

### Issues / Blockers
- {Any website-specific issues}

---

## Next Week Priorities
1. {Top priority for repo}
2. {Top priority for website}
3. {Stretch goal}
```

### Step 5: Review and Adjust

Before presenting to the user:

- Verify all numbers came from actual data (git log, marketplace.json)
- Flag any metrics that couldn't be verified as "[estimated]"
- Keep it concise — executives read the TL;DR, contributors read details

## Examples

```
User: "write a status update"
→ Runs git log for past week, reads marketplace.json, computes deltas,
  outputs dual-product status update with metrics table and highlights.

User: "weekly update for the last 2 weeks"
→ Same workflow with --since="2 weeks ago" for git log, wider delta window.

User: "progress report"
→ Identical to status update — same trigger, same output format.
```

## Error Handling

| Error                     | Cause                           | Solution                                                           |
| ------------------------- | ------------------------------- | ------------------------------------------------------------------ |
| Git log empty             | No commits in time window       | Widen to 2 weeks, then 1 month; note sparse activity               |
| marketplace.json missing  | Repo path changed               | Ask user for current repo location                                 |
| Website project not found | tonsofskills.com repo not local | Note "Website data unavailable" and produce repo-only update       |
| Metrics unchanged         | No deltas to report             | Report "No changes" with context on why (holiday, focus elsewhere) |
