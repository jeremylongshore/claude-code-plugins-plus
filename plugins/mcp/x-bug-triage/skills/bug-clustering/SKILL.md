---
name: bug-clustering
description: |
  Internal process for the bug-clusterer agent. Defines the step-by-step
  procedure for parsing, classifying, redacting, scoring, and clustering
  bug candidates from raw X/Twitter posts. Not user-invocable — loaded
  by the agent via its `skills: ["bug-clustering"]` frontmatter property.
user-invocable: false
version: 0.1.0
author: Jeremy Longshore <jeremy@intentsolutions.io>
license: SEE LICENSE IN LICENSE
model: inherit
effort: high
compatible-with: claude-code
tags: [triage, clustering, pii-redaction, classification, internal-agent-skill]
---

# Bug Clustering Process

Step-by-step procedure for transforming raw XPost objects into structured, clustered bug candidates with PII redaction and reliability scoring.

## Instructions

### Step 1: Parse

For each XPost, produce a BugCandidate with all 33 fields using `lib/parser.ts`:
- Extract product_surface, feature_area, symptoms, error_strings, repro_hints
- Extract urls, media_keys, language, conversation references
- Determine source_type (mention, reply, quote_post, search_hit)

### Step 1.5: Deduplicate

Before classification, run content-similarity deduplication using `lib/dedupe.ts`:
- Call `deduplicateCandidates()` with parsed candidates and the `candidate_dedup.hybrid_similarity_threshold` from `config/cluster-matching-thresholds.json` (default 0.70)
- Uses char-trigram + token-Jaccard hybrid similarity
- Does NOT remove posts — tags them as duplicate groups with a canonical post (highest engagement)
- Only canonical posts and non-duplicates (`forward_ids`) proceed to classification
- Log dedup stats: `"{n} posts ({m} unique, {k} duplicate groups)"`

### Step 2: Classify

Run `lib/classifier.ts` on each candidate:
- Assign one of 12 classifications with confidence score (0.0-1.0) and rationale
- Sarcastic bug reports get classified separately — still treated as signal

### Step 3: Redact PII

Run `lib/redactor.ts` on each candidate:
- Detect 6 PII types: email, API key, phone, account ID, media flag, URL token
- Replace with `[REDACTED:type]` tags
- Set pii_flags array and raw_text_storage_policy

### Step 4: Score Reliability

Run `lib/reporter-scorer.ts` on each candidate:
- 4 dimensions: report quality, independence, account authenticity, historical accuracy
- Composite reporter_reliability_score (0.0-1.0)

### Step 5: Tag Reporter Category

Match author against approved_accounts config:
- Categories: public, internal, partner, tester

### Step 6: Cluster

Using `lib/clusterer.ts` and `lib/signatures.ts`:
- Generate deterministic bug signature from error_strings + symptoms + feature_area
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

## References

Load evidence tier definitions for proper cluster evidence assessment:
```
!cat skills/x-bug-triage/references/evidence-policy.md
```

Load data model reference for BugCandidate fields and cluster schemas:
```
!cat skills/x-bug-triage/references/schemas.md
```
