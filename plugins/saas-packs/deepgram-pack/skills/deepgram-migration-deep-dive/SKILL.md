---
name: deepgram-migration-deep-dive
description: |
  Deep dive into complex Deepgram migrations and provider transitions.
  Use when migrating from other transcription providers, planning large-scale
  migrations, or implementing phased rollout strategies.
  Trigger with phrases like "deepgram migration", "switch to deepgram",
  "migrate transcription", "deepgram from AWS", "deepgram from Google".
allowed-tools: Read, Write, Edit, Bash(kubectl:*), Bash(curl:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Deepgram Migration Deep Dive

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
Comprehensive guide for migrating to Deepgram from other transcription providers (AWS Transcribe, Google Cloud STT, Azure Speech, OpenAI Whisper, Rev.ai, AssemblyAI) using an adapter pattern with parallel running and gradual traffic shifting.

## Prerequisites
- Current provider SDK and credentials
- Deepgram API key and project configured
- Test audio dataset for comparison
- Monitoring infrastructure ready

## Instructions

### Step 1: Assessment
Audit current usage (hours/month, features), map features to Deepgram equivalents, and estimate costs.

### Step 2: Implement Adapter Pattern
Create a `TranscriptionAdapter` interface with `transcribe()` and `transcribeFile()` methods, then implement both the legacy adapter and `DeepgramAdapter`.

### Step 3: Build Migration Router
Create a `MigrationRouter` that routes traffic by percentage (0-100%) between providers, with optional parallel comparison mode.

### Step 4: Parallel Running & Validation
Run both providers simultaneously, compare results using Jaccard similarity, and verify accuracy meets >= 90% threshold.

### Step 5: Gradual Rollout
Shift traffic incrementally: 5% -> 25% (monitor 1 week) -> 50% (monitor 1 week) -> 100%.

### Step 6: Cutover & Cleanup
Complete migration, decommission old provider, update documentation.

## Output
- TranscriptionAdapter interface and implementations
- MigrationRouter with percentage-based routing
- Validation script with similarity scoring
- Feature mapping tables (AWS/Google -> Deepgram)
- Rollback manager with checkpoint/restore

## Error Handling
| Issue | Cause | Resolution |
|-------|-------|------------|
| Low similarity scores | Feature mismatch | Check feature mapping, adjust options |
| Deepgram latency higher | Cold start or model | Pre-warm connections, verify model selection |
| Missing features | Incomplete mapping | Use Deepgram `keywords` for custom vocabulary |
| Rollback needed | Quality regression | Call `emergencyRollback()` to set percentage to 0% |

## Examples

### Feature Mapping (AWS -> Deepgram)
- `LanguageCode: en-US` -> `language: "en"` (ISO 639-1)
- `ShowSpeakerLabels: true` -> `diarize: true`
- `VocabularyName: custom` -> `keywords: ["term:1.5"]`
- `ContentRedaction` -> `redact: ["pci", "ssn"]`

### Migration Checklist
Pre-migration, validation phase, rollout phase (5% -> 25% -> 50% -> 100%), post-migration cleanup.

See [detailed implementation](${CLAUDE_SKILL_DIR}/references/implementation.md) for advanced patterns.

## Resources
- [Deepgram Migration Guide](https://developers.deepgram.com/docs/migration)
- [Feature Comparison](https://developers.deepgram.com/docs/features)
- [Pricing Calculator](https://deepgram.com/pricing)