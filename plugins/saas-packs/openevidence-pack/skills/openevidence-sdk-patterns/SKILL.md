---
name: openevidence-sdk-patterns
description: |
  OpenEvidence SDK patterns and best practices for clinical AI integration.
  Use when implementing advanced SDK features, optimizing API usage,
  or following clinical decision support best practices.
  Trigger with phrases like "openevidence patterns", "openevidence best practices",
  "openevidence sdk", "clinical ai patterns".
allowed-tools: Read, Write, Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# OpenEvidence SDK Patterns

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Best practices and design patterns for building production clinical decision support with OpenEvidence. Covers client singleton, typed queries, query builder, response transformer, and caching strategies.

## Prerequisites
- Completed `openevidence-install-auth` setup
- Understanding of async/await patterns
- Familiarity with clinical workflows

## Instructions

### Step 1: Client Singleton with DI
Create `OpenEvidenceClientFactory` with `configure()`, `getClient()`, and `setClient()` (for testing). Ensures single client instance across the application.

### Step 2: Define Typed Clinical Queries
Create TypeScript types for `ClinicalSpecialty` (10 specialties), `QueryUrgency` (stat/urgent/routine/research), `ClinicalContext` (specialty, urgency, patient demographics, conditions, medications), and `QueryOptions`.

### Step 3: Implement Query Builder
Build fluent `ClinicalQueryBuilder` with `.question()`, `.specialty()`, `.urgency()`, `.withPatient()`, `.withConditions()`, `.withMedications()`, `.maxCitations()`, `.includeGuidelines()`, and `.build()` with validation.

### Step 4: Create Response Transformer
Transform raw API responses into `FormattedClinicalAnswer` with summary, detailed answer, key points, evidence with strength ratings (high for NEJM/JAMA/Lancet, moderate for recent, low otherwise), and confidence level.

### Step 5: Implement Caching Layer
Build `ClinicalQueryCache` with SHA-256 key generation, configurable TTL (1 hour default for clinical data), and invalidation support.

## Output
- Client singleton factory with dependency injection
- Typed clinical query interfaces
- Fluent query builder with validation
- Response transformer with evidence strength ratings
- In-memory caching with TTL management

## Error Handling
| Pattern | Use Case | Benefit |
|---------|----------|---------|
| Singleton | Single client instance | Memory efficiency, connection reuse |
| Builder | Complex queries | Type safety, validation, readability |
| Transformer | Response normalization | Consistent UI layer, evidence grading |
| Cache | Repeated queries | Reduced API calls, lower latency |

## Examples

### Query Builder Usage
```typescript
const query = new ClinicalQueryBuilder()
  .question('Recommended statin dosing for secondary prevention?')
  .specialty('cardiology')
  .urgency('routine')
  .withPatient(65, 'male')
  .withConditions(['prior MI', 'hyperlipidemia'])
  .includeGuidelines()
  .build();
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [OpenEvidence API Reference](https://docs.openevidence.com/)
- [TypeScript Design Patterns](https://refactoring.guru/design-patterns/typescript)