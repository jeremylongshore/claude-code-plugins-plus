---
name: repo-scanning
description: |
  Internal process for the repo-scanner agent. Defines the step-by-step
  procedure for scanning GitHub repos for evidence that supports or explains
  bug clusters. Not user-invocable — loaded by the agent via its
  `skills: ["repo-scanning"]` frontmatter property.
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: medium
compatible-with: claude-code
tags: [triage, repo-scanning, evidence, github, internal-agent-skill]
---

# Repo Scanning Process

Step-by-step procedure for scanning GitHub repos to gather corroborating evidence for bug clusters, assigning confidence tiers to each finding.

## Instructions

### Step 1: Select Repos

For each cluster:
1. Look up repos from surface_repo_mapping using the cluster's product_surface
2. Cap at top 3 repos per cluster (hard limit — never scan more)
3. If no mapping exists, note it as a warning and skip

### Step 2: Search Issues

For each repo, call `mcp__triage__search_issues` with the cluster's symptoms and error_strings:
- Match error strings against open/recent issues
- Assign evidence tier based on match confidence

### Step 3: Inspect Recent Commits

Call `mcp__triage__inspect_recent_commits` for each repo:
- 7-day window from current date
- Filter by affected paths if known from the cluster's feature_area
- Look for commits that touch relevant code paths

### Step 4: Inspect Code Paths

Call `mcp__triage__inspect_code_paths` with the cluster's surface and feature_area:
- Identify likely affected code paths
- Check for recent changes or known fragile areas

### Step 5: Check Recent Deploys

Call `mcp__triage__check_recent_deploys` for each repo:
- Correlate deploy/release timing with cluster's first_seen timestamp
- Recent deploy near first_seen is a stronger signal

### Step 6: Assign Evidence Tiers

For each piece of evidence, assign a tier:

| Tier | Name | Criteria |
|------|------|----------|
| 1 | Exact | issue_match at >=0.9 confidence |
| 2 | Strong | issue_match >=0.7, recent_commit >=0.8, affected_path >=0.7, recent_deploy >=0.8 |
| 3 | Moderate | Lower confidence matches, sibling_failure |
| 4 | Weak | external_dependency, heuristic proximity |

### Step 7: Handle Degradation

If a repo is inaccessible or an API call fails:
1. Log a degraded scan result with the error reason
2. Continue scanning remaining repos — never abort the whole scan
3. Include degradation warnings in output

## References

Load evidence tier definitions for proper tier assignment:
```
!cat skills/x-bug-triage/references/evidence-policy.md
```
