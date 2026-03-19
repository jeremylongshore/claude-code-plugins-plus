---
name: mistral-migration-deep-dive
description: |
  Execute Mistral AI major migrations and re-architecture strategies.
  Use when migrating to Mistral AI from another provider, performing major refactoring,
  or re-platforming existing AI integrations to Mistral AI.
  Trigger with phrases like "migrate to mistral", "mistral migration",
  "switch to mistral", "mistral replatform", "openai to mistral".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(node:*), Bash(kubectl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Mistral AI Migration Deep Dive

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Table of Contents
- [Overview](#overview)
- [Prerequisites](#prerequisites)
- [Instructions](#instructions)
- [Output](#output)
- [Error Handling](#error-handling)
- [Examples](#examples)
- [Resources](#resources)

## Overview
Comprehensive guide for migrating to Mistral AI from other providers (OpenAI, Anthropic) or performing major version upgrades. Covers assessment, adapter pattern, feature-flag rollout, model mapping, validation testing, and rollback.

## Prerequisites
- Current system documentation
- Mistral AI SDK installed
- Feature flag infrastructure
- Rollback strategy tested

## Migration Types

| Type | Complexity | Duration | Risk |
|------|-----------|----------|------|
| Fresh install | Low | Days | Low |
| OpenAI to Mistral | Medium | Weeks | Medium |
| Multi-provider | Medium | Weeks | Medium |
| Full replatform | High | Months | High |

## Instructions

### Step 1: Pre-Migration Assessment
Audit current AI code: find all files with AI imports, count integration points (chat completions, embeddings, function calling, streaming). Detect current provider and estimate effort (>10 points = high, >3 = medium, else low).

### Step 2: Create Provider-Agnostic Adapter
Define `AIAdapter` interface with `chat()`, `chatStream()`, and `embed()` methods. Use `Message`, `ChatOptions`, and `ChatResponse` types to abstract away provider differences.

### Step 3: Implement OpenAI Adapter
Build `OpenAIAdapter` implementing `AIAdapter` that wraps `openai` SDK. Maps OpenAI-specific fields (prompt_tokens, completion_tokens) to normalized types.

### Step 4: Implement Mistral Adapter
Build `MistralAdapter` implementing `AIAdapter` that wraps `@mistralai/mistralai` SDK. Maps Mistral-specific fields (promptTokens, completionTokens) to normalized types.

### Step 5: Feature Flag Migration
Create `createAIAdapter()` factory using `MISTRAL_ROLLOUT_PERCENT` env var. Random percentage check routes traffic to Mistral or OpenAI adapter.

### Step 6: Gradual Rollout
Phase rollout: 0% (validation) -> 5% (canary) -> 25% -> 50% -> 100%. Monitor errors and latency at each phase for 24-48 hours before advancing.

### Step 7: Model Mapping
Map models: gpt-3.5-turbo -> mistral-small-latest, gpt-4/gpt-4-turbo -> mistral-large-latest, text-embedding-ada-002 -> mistral-embed (1024 dimensions).

### Step 8: Validation Testing
Run A/B comparison tests with identical prompts at temperature=0. Verify both providers return non-empty content. Log results for manual quality review.

### Step 9: Rollback Plan
Set `MISTRAL_ROLLOUT_PERCENT=0` to immediately route all traffic back to OpenAI. Verify health and notify team.

## Output
- Migration assessment with effort estimation
- Provider-agnostic adapter interface
- OpenAI and Mistral adapter implementations
- Feature-flag controlled gradual rollout
- Model mapping configuration
- A/B validation test suite
- Rollback procedure

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| Different output format | API differences | Normalize in adapter |
| Missing feature | Not supported by Mistral | Implement fallback |
| Performance difference | Model characteristics | Adjust timeouts |
| Cost increase | Token differences | Monitor and optimize |

## Examples

### Quick A/B Comparison
```typescript
const [openaiResponse, mistralResponse] = await Promise.all([
  openaiAdapter.chat(messages, { temperature: 0 }),
  mistralAdapter.chat(messages, { temperature: 0 }),
]);
console.log('OpenAI tokens:', openaiResponse.usage);
console.log('Mistral tokens:', mistralResponse.usage);
```

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Mistral AI Documentation](https://docs.mistral.ai/)
- [Strangler Fig Pattern](https://martinfowler.com/bliki/StranglerFigApplication.html)
- [Feature Flags Best Practices](https://www.martinfowler.com/articles/feature-toggles.html)