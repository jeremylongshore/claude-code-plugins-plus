---
name: repo-scanning
description: |
  Internal procedure for the repo-scanner agent. Scans GitHub repos for
  evidence that supports or explains bug clusters and assigns confidence
  tiers to each finding. Loaded by the parent agent via its skills frontmatter
  property; not user-invocable. Use when the repo-scanner agent runs against a
  clustered batch.
allowed-tools: Read, Bash(node:*), Bash(gh:*)
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: medium
compatibility: Designed for claude-code
tags: [triage, repo-scanning, evidence, github, internal-agent-skill]
---

# Repo Scanning Process

## Overview

Scans GitHub repos to gather corroborating evidence for bug clusters and
assigns confidence tiers to each finding. Run by the repo-scanner agent inside
the x-bug-triage plugin once owner routing completes.

The scanner is bounded — at most 3 repos per cluster — and degrades gracefully:
inaccessible repos, rate limits, and API failures never abort the whole scan;
each becomes a degraded result with a logged reason.

## Prerequisites

- Input: clustered bugs with assigned owners (output of the owner-routing skill).
- `surface_repo_mapping` config that maps each `product_surface` to candidate
  repos.
- MCP tools registered by the triage server: `mcp__triage__search_issues`,
  `mcp__triage__inspect_recent_commits`, `mcp__triage__inspect_code_paths`,
  `mcp__triage__check_recent_deploys`.
- GitHub access scoped to read-only on the configured repos.

## Instructions

### Step 1: Select Repos

For each cluster:
1. Look up repos from surface_repo_mapping using the cluster's product_surface
2. Cap at top 3 repos per cluster (hard limit — never scan more)
3. If no mapping exists, note it as a warning and skip

### Step 2: Search Issues

For each repo, call `mcp__triage__search_issues` with the cluster's symptoms
and error_strings:
- Match error strings against open/recent issues
- Assign evidence tier based on match confidence

### Step 3: Inspect Recent Commits

Call `mcp__triage__inspect_recent_commits` for each repo:
- 7-day window from current date
- Filter by affected paths if known from the cluster's feature_area
- Look for commits that touch relevant code paths

### Step 4: Inspect Code Paths

Call `mcp__triage__inspect_code_paths` with the cluster's surface and
feature_area:
- Identify likely affected code paths
- Check for recent changes or known fragile areas

### Step 5: Check Recent Deploys

Call `mcp__triage__check_recent_deploys` for each repo:
- Correlate deploy/release timing with cluster's first_seen timestamp
- Recent deploy near first_seen is a stronger signal

### Step 6: Assign Evidence Tiers

For each piece of evidence, assign a tier:

| Tier | Name     | Criteria                                                                                            |
|------|----------|-----------------------------------------------------------------------------------------------------|
| 1    | Exact    | issue_match at >=0.9 confidence                                                                     |
| 2    | Strong   | issue_match >=0.7, recent_commit >=0.8, affected_path >=0.7, recent_deploy >=0.8                    |
| 3    | Moderate | Lower confidence matches, sibling_failure                                                           |
| 4    | Weak     | external_dependency, heuristic proximity                                                            |

### Step 7: Handle Degradation

If a repo is inaccessible or an API call fails:
1. Log a degraded scan result with the error reason
2. Continue scanning remaining repos — never abort the whole scan
3. Include degradation warnings in output

## Output

Per cluster, an `EvidenceBundle` containing:
- `repos_scanned`: list of repos actually scanned (after the 3-repo cap).
- `evidence`: list of evidence findings, each with `{ repo, source_type
  (issue / commit / code_path / deploy), confidence, tier, snippet }`.
- `degraded_repos`: list of repos that returned errors with the failure
  reason — used for the display layer's "scan was partial" notice.
- `top_evidence`: a single highest-tier evidence pick used in the summary
  display.

## Error Handling

- **No surface_repo_mapping match**: emit warning, skip the cluster, continue
  with the next cluster. Do not block the whole batch.
- **Repo inaccessible** (404, permission denied): record a degraded result
  with the error reason, continue.
- **GitHub rate limit (`rate-limit-exceeded`)**: stop scanning that repo,
  record degraded reason `rate_limit_remaining=0`, continue with the next
  repo. Surface the rate-limit window in the parent agent's audit log.
- **MCP tool unexpected exception**: catch, log, mark the specific scan step
  as degraded for that repo, continue with the remaining steps. The cluster
  still produces an EvidenceBundle even if 1–2 of 5 tools failed.
- **3-repo cap reached**: log a `repo_cap_reached` warning so reviewers know
  why a clearly relevant repo was not scanned.

## Examples

### Example 1: Tier-1 issue match

Cluster has error_string "TypeError: cannot read 'auth' of undefined". Repo
scan finds an open GitHub issue with the same error string at confidence 0.95.
Result: `tier=1`, `source_type=issue`, becomes `top_evidence`.

### Example 2: Tier-2 deploy correlation

Cluster `first_seen=2026-04-21T14:30Z`. Repo scan finds a deploy at
`2026-04-21T14:18Z`. Twelve-minute lead time → `recent_deploy_match=0.85`.
Result: `tier=2`, `source_type=deploy`. Surfaces in evidence list, not
necessarily as top_evidence.

### Example 3: Degraded scan

3 repos selected. Repo A scans fully. Repo B returns 403 (token scope changed).
Repo C succeeds for issues but rate-limits on commit inspection. Output:
`repos_scanned=[A, B, C]`, `degraded_repos=[B(403), C(rate_limit on
inspect_recent_commits)]`. Evidence from A and the issue match from C still
ship.

## Resources

The parent x-bug-triage skill ships its evidence policy at
`plugins/mcp/x-bug-triage/skills/x-bug-triage/references/evidence-policy.md` —
load on demand for the canonical tier definitions referenced in Step 6.

Trigger phrase: this skill is loaded by the repo-scanner agent and has no
direct user-facing trigger. Trigger with the parent plugin's `/x-bug-triage`
command.
