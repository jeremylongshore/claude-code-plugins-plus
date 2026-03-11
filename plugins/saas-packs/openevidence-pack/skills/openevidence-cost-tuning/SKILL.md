---
name: openevidence-cost-tuning
description: |
  Optimize OpenEvidence API costs and usage efficiency.
  Use when reducing API costs, implementing usage budgets,
  or optimizing DeepConsult spend for clinical AI applications.
  Trigger with phrases like "openevidence cost", "openevidence billing",
  "reduce openevidence spend", "openevidence budget", "openevidence pricing".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# OpenEvidence Cost Tuning

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Optimize OpenEvidence API costs while maintaining clinical decision support quality. Covers usage tracking, DeepConsult optimization, user quotas, and cost reporting.

## Prerequisites
- OpenEvidence billing dashboard access
- Usage metrics configured
- Understanding of pricing model
- Budget authority

## Pricing Model

| Feature | Unit | Typical Cost |
|---------|------|--------------|
| Clinical Query | Per query | Included in subscription |
| DeepConsult | Per research synthesis | Premium (100x query cost) |
| API Overage | Per 1000 queries over limit | Tier-dependent |
| Enterprise Features | Monthly | Custom pricing |

## Instructions

### Step 1: Implement Usage Tracking
Create `UsageTracker` with Redis-backed daily/monthly counters per user and global. Track queries and DeepConsults separately with budget alerts at configurable thresholds.

### Step 2: Optimize DeepConsult Usage
Build decision logic: use regular queries for simple questions (dosage, half-life, contraindications, side effects). Reserve DeepConsult for complex research (treatment comparisons, systematic reviews, emerging therapies). Cache DeepConsult results for 1 week.

### Step 3: Implement User Quotas
Define tier-based quotas (free: 10/day, professional: 100/day + 10 DeepConsults/month, enterprise: 1000/day + 100 DeepConsults/month). Enforce with middleware.

### Step 4: Build Cost Reporting
Generate periodic reports with breakdowns by specialty, user, and day. Include automated recommendations for high DeepConsult ratio, low cache hits, and concentrated usage.

## Output
- Usage tracking with Redis counters
- Budget alert system with configurable thresholds
- Smart DeepConsult decision logic
- Tier-based user quota enforcement
- Cost reporting dashboard with recommendations

## Error Handling
| Cost Issue | Detection | Resolution |
|------------|-----------|------------|
| Budget exceeded | Alert triggered | Implement throttling or upgrade tier |
| High DeepConsult costs | Monthly report | Review patterns, improve caching |
| Low cache efficiency | Metrics show low hits | Adjust TTL, increase cache size |
| User abuse | Usage concentration | Implement per-user quotas |

## Examples

### DeepConsult Decision
```typescript
// Simple question -> regular query (free)
"What is the dosage of metformin?" -> clinicalQuery

// Complex research -> DeepConsult (premium)
"Compare emerging therapies for treatment-resistant depression" -> deepConsult
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [OpenEvidence Pricing](https://www.openevidence.com/pricing)
- [OpenEvidence API Terms](https://www.openevidence.com/policies/api)
