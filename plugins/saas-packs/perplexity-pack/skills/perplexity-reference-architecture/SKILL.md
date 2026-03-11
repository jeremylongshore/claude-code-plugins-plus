---
name: perplexity-reference-architecture
description: |
  Implement Perplexity reference architecture with best-practice project layout.
  Use when designing new Perplexity integrations, reviewing project structure,
  or establishing architecture standards for Perplexity applications.
  Trigger with phrases like "perplexity architecture", "perplexity best practices",
  "perplexity project structure", "how to organize perplexity", "perplexity layout".
allowed-tools: Read, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Perplexity Reference Architecture

## Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Production architecture for AI-powered research and search with Perplexity Sonar API. Covers model routing for cost/quality tradeoffs, citation extraction, multi-query research pipelines, and conversational search.

## Prerequisites
- Perplexity API key (Sonar access)
- OpenAI-compatible client library
- Understanding of search models (sonar, sonar-pro, sonar-reasoning)

## Architecture

```
Application Layer (Research Agent, Fact Checker, Content Writer)
        |
Search Router (sonar/sonar-pro/sonar-reasoning)
        |
Citation Pipeline (Extract URLs, Validate, Store, Render)
        |
Cache Layer (Query Hash -> Result, TTL by freshness need)
```

## Instructions

### Step 1: Set Up Search Service with Model Routing
Use OpenAI-compatible client pointed at `api.perplexity.ai`. Route queries by depth: quick/standard (sonar), deep (sonar-pro), reasoning (sonar-reasoning).

### Step 2: Build Citation Extraction Pipeline
Parse response text for `[N] URL` patterns and inline URLs. Deduplicate and store citations with metadata.

### Step 3: Create Research Pipeline
Multi-phase: broad overview (fast model) -> identify subtopics -> deep dive each (sonar-pro) -> deduplicate citations.

### Step 4: Implement Conversational Search
Maintain message history for follow-up questions that build on previous context.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for search service, citation extraction, multi-query research pipeline, conversational session, and fact-check service code.

## Output
- Search service with model routing by query depth
- Citation extraction from responses
- Multi-query research pipeline
- Conversational search with context

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| No citations returned | Using basic sonar for complex query | Upgrade to sonar-pro |
| Stale information | Outdated sources | Add recency preference in system prompt |
| High cost | Using sonar-pro for simple queries | Route simple queries to sonar |
| Rate limit | Too many concurrent searches | Add request queue with delays |

## Examples

### Quick Fact Check
```typescript
const result = await factCheck("The Earth is approximately 4.5 billion years old");
console.log(result.verdict);  // Accurate, with sources
console.log(result.sources);  // Citation URLs
```

## Resources
- [Perplexity API Docs](https://docs.perplexity.ai/)
- [Perplexity Model Guide](https://docs.perplexity.ai/guides/model-cards)
