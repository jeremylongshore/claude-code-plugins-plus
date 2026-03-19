---
name: openrouter-upgrade-migration
description: |
  Migrate or upgrade your OpenRouter integration. Use when updating SDK versions, switching models, or modernizing your setup. Trigger with phrases like 'openrouter migrate', 'openrouter upgrade', 'openrouter update', 'switch openrouter model'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Openrouter Upgrade Migration

## Current State
!`npm list 2>/dev/null | head -20`
!`pip freeze 2>/dev/null | head -20`

## Overview

This skill provides a step-by-step migration guide for upgrading SDK versions, switching between models, or migrating from direct provider APIs to OpenRouter.

## Prerequisites

- Existing OpenRouter integration or direct provider API integration
- Test environment for validating the migration

## Instructions

1. **Audit current integration**: Document all API calls, models used, parameters set, and any provider-specific features relied upon
2. **Identify breaking changes**: If upgrading the SDK, check the changelog for breaking changes; if switching models, compare parameter support and response format differences
3. **Update in a feature branch**: Make all changes in a branch; update base URL, API key, model IDs, and any changed parameters; add the OpenRouter-specific headers
4. **Run comparison tests**: Send the same prompts through old and new configurations; compare response quality, latency, and costs to validate the migration
5. **Deploy with a rollback plan**: Use feature flags or traffic splitting to gradually migrate traffic; keep the old configuration available for quick rollback

## Output

- Migration checklist with all changes documented
- Comparison report showing quality, latency, and cost differences
- Rollback runbook in case the migration needs to be reverted

## Error Handling

| Error | Cause | Fix |
|-------|-------|-----|
| Changed response format | New model or SDK version returns different structure | Update response parsing code; add version-specific handling |
| Missing parameter support | New model doesn't support a parameter used in old code | Remove or conditionally set the unsupported parameter; check `/models` for capabilities |
| Quality regression | New model performs worse on specific prompts | Adjust prompts for the new model; consider keeping the old model for affected use cases |

See `${CLAUDE_SKILL_DIR}/references/errors.md` for full error reference.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for runnable code samples.

## Resources

- [OpenRouter Documentation](https://openrouter.ai/docs)
- [OpenRouter Models](https://openrouter.ai/models)
- [OpenRouter API Reference](https://openrouter.ai/docs/api-reference)
- [OpenRouter Status](https://status.openrouter.ai)
