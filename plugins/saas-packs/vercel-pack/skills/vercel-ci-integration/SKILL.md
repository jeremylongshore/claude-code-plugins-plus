---
name: vercel-ci-integration
description: |
  Configure Vercel CI/CD integration with GitHub Actions and testing.
  Use when setting up automated testing, configuring CI pipelines,
  or integrating Vercel tests into your build process.
  Trigger with phrases like "vercel CI", "vercel GitHub Actions",
  "vercel automated tests", "CI vercel".
allowed-tools: Read, Write, Edit, Bash(gh:*)
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---

# Vercel Ci Integration

## Prerequisites
- GitHub repository with Actions enabled
- Vercel test API key
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
- [Vercel CI Guide](https://vercel.com/docs/ci)
