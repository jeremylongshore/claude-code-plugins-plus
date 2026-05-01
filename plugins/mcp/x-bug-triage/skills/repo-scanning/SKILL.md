---
name: repo-scanning
description: |
  Internal process for the repo-scanner agent. Defines the step-by-step
  procedure for scanning GitHub repos for evidence that supports or explains
  bug clusters. Not user-invocable — loaded by the repo-scanner agent
  through its skills frontmatter.
allowed-tools: "Read, Bash(cat:*), Grep, Glob"
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: medium
compatibility: "Designed for Claude Code; internal agent-loaded skill (not user-invocable)"
tags: [triage, repo-scanning, evidence, github, internal-agent-skill]
---

# Repo Scanning Process

Step-by-step procedure for scanning GitHub repos to gather corroborating evidence for bug clusters, assigning confidence tiers to each finding.

## Overview

Loaded by the `repo-scanner` agent inside the `x-bug-triage` plugin. Walks each clustered bug through a fixed evidence-gathering pipeline against the up-to-three repos most likely to host the bug: matching open/recent issues, recent commits in the impact window, affected code paths, and recent deploys correlated to the cluster's first_seen timestamp. Each finding is graded against the evidence-tier policy and recorded as cluster evidence.

## Prerequisites

- Cluster table populated upstream by the bug-clustering stage
- `surface_repo_mapping` configured for every product_surface present in clusters
- Triage MCP server reachable for `mcp__triage__search_issues`, `mcp__triage__inspect_recent_commits`, `mcp__triage__inspect_code_paths`, and `mcp__triage__check_recent_deploys`
- GitHub access tokens with read scope on the target repos

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

## Output

- `cluster_evidence` rows tagged with tier (1–4), source kind, repo, and finding link
- `cluster_scan_warnings` rows for any repo skipped or degraded during scanning
- Updated cluster `evidence_summary` field with per-tier counts

## Error Handling

- Missing surface→repo mapping: warn, skip the cluster's scan, proceed with remaining clusters
- GitHub API rate limit hit: pause and resume, or degrade to "rate_limited" warning if budget exhausted
- Single tool call failure: capture error reason, continue to next step, never abort a multi-step scan
- All four signal sources empty for a cluster: record evidence_summary="empty" — downstream stages still run

## Examples

Triggered automatically after owner-routing for each clustered bug. Typical output for a 12-cluster batch against 3 repos each: "12 clusters scanned, 7 with Tier 1 evidence, 3 with Tier 2 only, 2 with no evidence (Tier 4 weak only). 1 repo skipped (rate limit)."

## Resources

Load evidence tier definitions for proper tier assignment:

```
!cat skills/x-bug-triage/references/evidence-policy.md
```
