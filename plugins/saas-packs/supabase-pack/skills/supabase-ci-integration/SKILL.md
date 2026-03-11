---
name: supabase-ci-integration
description: |
  Configure Supabase CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Supabase tests into your build process.
  Trigger with phrases like "supabase CI", "supabase GitHub Actions",
  "supabase automated tests", "CI supabase".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Supabase Ci Integration

## Prerequisites
- GitHub repository with Actions enabled
- Supabase test API key
- npm/pnpm project configured


See `${CLAUDE_SKILL_DIR}/references/implementation.md` for detailed implementation guide.

## Output
- Automated test pipeline
- PR checks configured
- Coverage reports uploaded
- Release workflow ready

## Error Handling

See `${CLAUDE_SKILL_DIR}/references/errors.md` for comprehensive error handling.

## Examples

See `${CLAUDE_SKILL_DIR}/references/examples.md` for detailed examples.

## Resources
- [GitHub Actions Documentation](https://docs.github.com/en/actions)
- [Supabase CI Guide](https://supabase.com/docs/ci)

## Overview

Configure Supabase CI/CD integration with GitHub Actions and testing.

## Instructions

1. Assess the current state of the CI/CD configuration
2. Identify the specific requirements and constraints
3. Apply the recommended patterns from this skill
4. Validate the changes against expected behavior
5. Document the configuration for team reference