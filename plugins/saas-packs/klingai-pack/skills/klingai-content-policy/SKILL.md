---
name: klingai-content-policy
description: |
  Implement content policy compliance for Kling AI. Use when ensuring generated content meets
  guidelines or filtering inappropriate prompts. Trigger with phrases like 'klingai content policy',
  'kling ai moderation', 'safe video generation', 'klingai content filter'.
allowed-tools: Read, Write, Edit, Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Klingai Content Policy

## Overview

This skill teaches how to implement content policy compliance including prompt filtering, output moderation, age-appropriate content controls, and handling policy violations for Kling AI.

## Prerequisites

- Kling AI API key configured
- Understanding of content policies
- Python 3.8+

## Instructions

Follow these steps for content compliance:

1. **Review Policies**: Understand Kling AI content rules
2. **Implement Filters**: Add prompt screening
3. **Handle Violations**: Manage rejected content
4. **Add Moderation**: Post-generation review
5. **Document Policies**: Create user guidelines

## Output

Successful execution produces:
- Filtered and approved prompts
- Blocked policy-violating content
- Sanitized alternative prompts
- Violation audit trail

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources

- [Kling AI Content Policy](https://klingai.com/content-policy)
- [AI Content Moderation](https://platform.openai.com/docs/guides/moderation)
- [NSFW Detection APIs](https://sightengine.com/)
