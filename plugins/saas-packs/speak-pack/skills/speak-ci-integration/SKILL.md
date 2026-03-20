---
name: speak-ci-integration
description: |
  Configure Speak CI/CD integration with GitHub Actions and automated testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Speak language learning tests into your build process.
  Trigger with phrases like "speak CI", "speak GitHub Actions",
  "speak automated tests", "CI speak".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Speak CI Integration

## Overview
Integrate Speak language learning API validation into CI/CD pipelines. Covers pronunciation analysis endpoint testing, lesson content validation, API response format verification, and regression testing for language assessment accuracy.

## Prerequisites
- Speak API key stored as GitHub secret
- GitHub Actions configured
- Test framework (Vitest or Jest)
- Audio test fixtures for pronunciation tests

## Instructions

1. For full implementation details, load: `Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Error Handling
| Issue | Cause | Solution |
|-------|-------|----------|
| API key invalid | Secret not set | Add `SPEAK_API_KEY` to repo secrets |
| Audio fixture too large | Uncompressed WAV | Compress to 16-bit mono |
| Lesson validation fails | Missing required field | Check schema and fix JSON files |
| Flaky pronunciation test | Audio quality varies | Use consistent test recordings |

## Examples
### Minimal Smoke Test
```yaml
- name: Speak API health check
  env:
    SPEAK_API_KEY: ${{ secrets.SPEAK_API_KEY }}
  run: |
    curl -s -H "Authorization: Bearer $SPEAK_API_KEY" \
      https://api.speak.com/v1/languages | jq '.languages | length'
```

## Resources
- [Speak API Documentation](https://docs.speak.com)
- [Speak Developer Guide](https://speak.com/developers)

## Output

- GitHub Actions workflow file (`.github/workflows/speak-tests.yml`)
- Pronunciation regression test suite with audio fixtures
- CI badge and test result artifacts uploaded per run

See [CI/CD implementation details](${CLAUDE_SKILL_DIR}/references/implementation.md) for output format specifications.