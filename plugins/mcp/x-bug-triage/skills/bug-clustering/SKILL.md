---
name: bug-clustering
description: |
  Internal procedure for the bug-clusterer agent. Defines the step-by-step process
  for parsing, classifying, redacting, scoring, and clustering bug candidates from
  raw X/Twitter posts. Loaded by the parent agent via its skills frontmatter
  property; not user-invocable. Use when the bug-clusterer agent runs against
  an XPost batch.
allowed-tools: Read, Bash(node:*), Bash(bun:*)
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: high
compatibility: Designed for claude-code
tags: [triage, clustering, pii-redaction, classification, internal-agent-skill]
---

# Bug Clustering Process

## Overview

Transforms raw XPost objects into structured, clustered bug candidates with PII
redaction and reliability scoring. Driven by the bug-clusterer agent inside the
x-bug-triage plugin. Each invocation runs a 7-step deterministic pipeline whose
outputs are persisted to the triage database and consumed by the routing,
display, and review steps that follow.

The clustering uses a family-first guard so unrelated bug families never merge,
and uses content-similarity dedup so a flood of retweet-shaped duplicates does
not inflate cluster severity.

## Prerequisites

- Input: an array of `XPost` objects (already fetched by the parent agent).
- Library modules under `plugins/mcp/x-bug-triage/mcp/triage-server/lib/`:
  `parser.ts`, `dedupe.ts`, `classifier.ts`, `redactor.ts`, `reporter-scorer.ts`,
  `clusterer.ts`, `signatures.ts`, `db.ts`.
- Config files under `plugins/mcp/x-bug-triage/config/`:
  `cluster-matching-thresholds.json`, `approved_accounts.json`.
- Active triage DB connection (the parent agent owns the connection lifecycle).

## Instructions

### Step 1: Parse

For each XPost, produce a BugCandidate with all 33 fields using `lib/parser.ts`:
- Extract product_surface, feature_area, symptoms, error_strings, repro_hints
- Extract urls, media_keys, language, conversation references
- Determine source_type (mention, reply, quote_post, search_hit)

### Step 1.5: Deduplicate

Before classification, run content-similarity deduplication using `lib/dedupe.ts`:
- Call `deduplicateCandidates()` with parsed candidates and the
  `candidate_dedup.hybrid_similarity_threshold` from
  `config/cluster-matching-thresholds.json` (default 0.70)
- Uses char-trigram + token-Jaccard hybrid similarity
- Does NOT remove posts — tags them as duplicate groups with a canonical post
  (highest engagement)
- Only canonical posts and non-duplicates (forward_ids) proceed to classification
- Log dedup stats: "N posts (M unique, K duplicate groups)"

### Step 2: Classify

Run `lib/classifier.ts` on each candidate:
- Assign one of 12 classifications with confidence score (0.0-1.0) and rationale
- Sarcastic bug reports get classified separately — still treated as signal

### Step 3: Redact PII

Run `lib/redactor.ts` on each candidate:
- Detect 6 PII types: email, API key, phone, account ID, media flag, URL token
- Replace with [REDACTED:type] tags
- Set pii_flags array and raw_text_storage_policy

### Step 4: Score Reliability

Run `lib/reporter-scorer.ts` on each candidate:
- 4 dimensions: report quality, independence, account authenticity, historical
  accuracy
- Composite reporter_reliability_score (0.0-1.0)

### Step 5: Tag Reporter Category

Match author against approved_accounts config:
- Categories: public, internal, partner, tester

### Step 6: Cluster

Using `lib/clusterer.ts` and `lib/signatures.ts`:
- Generate deterministic bug signature from error_strings + symptoms +
  feature_area
- Match against active_clusters at >=70% signature overlap
- Family-first guard: different ClusterFamilies NEVER cluster together
- New match: create cluster (initial severity "low")
- Existing match: update report_count, last_seen, sub_status
- Resolved match: reopen with sub_status "regression_reopened"
- Suppressed match: skip, log to audit

### Step 7: Persist

- Insert candidates to DB via `lib/db.ts`
- Insert/update clusters and cluster_posts junction
- Write audit events for each classification, redaction, and cluster action

## Output

- BugCandidate rows in the `candidates` table (one per parsed XPost, with PII
  redacted and reliability score attached).
- Cluster rows in the `clusters` table (created or updated per Step 6).
- Junction rows in `cluster_posts`.
- Audit events in the `audit_log` table — one per classification, redaction, and
  cluster action so every transformation is reproducible.
- Dedup stats logged to stderr in the form
  `"N posts (M unique, K duplicate groups)"`.

## Error Handling

- **Family collision**: a candidate that matches multiple cluster signatures
  but only one cluster family — the family-first guard prevents the merge and
  routes the candidate to a new cluster in the correct family.
- **Suppressed match**: candidate signature matches a cluster marked
  `status=suppressed`. Skip the cluster update; emit an audit event so the
  suppression remains explicit; do not raise.
- **Resolved match (regression)**: candidate signature matches a cluster
  marked `status=resolved`. Reopen the cluster with `sub_status =
  regression_reopened` rather than creating a new one — this preserves history.
- **PII redactor failure on a single candidate**: log the error,
  set `raw_text_storage_policy = redact-failed`, drop the candidate from
  classification (do not store unredacted text under any circumstance).
- **Classifier confidence under threshold**: still persist the candidate; the
  parent agent decides whether to surface low-confidence classifications.

## Examples

### Example 1: New cluster from a fresh symptom

Input: 4 XPosts mentioning "checkout 500" within a 30-minute window from
distinct authors. None match an existing cluster signature.

Walk: parse → dedup (4 unique, 0 duplicate groups) → classify (all 4 tagged
`bug_report`, mean confidence 0.83) → redact (0 PII detected) → score
(reliability 0.6 average) → cluster (no signature match → new cluster with
`status=open`, `severity=low`, `report_count=4`).

### Example 2: Existing cluster with a regression reopen

Input: 1 XPost matching the signature of a cluster previously marked
`status=resolved` two weeks ago.

Walk: parse → dedup → classify → redact → score → cluster (signature match
hits a resolved cluster → reopen with `sub_status=regression_reopened`,
increment `report_count`, set `last_seen=now`, emit audit event
`cluster.regression_reopened`).

### Example 3: PII-heavy report

Input: 1 XPost with the user's email address and an API key in the body.

Walk: parse → dedup → classify → redact (2 PII matches: 1 email, 1 api_key →
both replaced with `[REDACTED:email]` / `[REDACTED:api_key]`,
`pii_flags=["email","api_key"]`) → score → cluster.

## Resources

The parent x-bug-triage skill ships these references at
`plugins/mcp/x-bug-triage/skills/x-bug-triage/references/` and the agent loads
them on demand:

- `evidence-policy.md` — tier definitions for cluster evidence assessment.
- `schemas.md` — BugCandidate fields and cluster table schemas.

Trigger phrase: this skill is loaded by the bug-clusterer agent as it processes
a fresh XPost batch — there is no user-facing trigger. Trigger with the parent
plugin's `/x-bug-triage` command, which orchestrates this skill end-to-end.
