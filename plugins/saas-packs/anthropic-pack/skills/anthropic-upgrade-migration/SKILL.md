---
name: anthropic-upgrade-migration
description: |
  Upgrade Anthropic SDK versions and migrate between Claude model generations.
  Trigger with "upgrade anthropic sdk", "migrate claude model",
  "anthropic breaking changes", "new claude model".
allowed-tools: Read, Write, Edit, Bash(npm:*), Bash(pip:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code
tags: [saas, anthropic, claude, migration, upgrade]
---

# Anthropic Upgrade & Migration

## SDK Upgrade
```bash
# Check current version
npm list @anthropic-ai/sdk
pip show anthropic

# Upgrade to latest
npm install @anthropic-ai/sdk@latest
pip install --upgrade anthropic

# Check changelog for breaking changes
# https://github.com/anthropics/anthropic-sdk-typescript/releases
```

## Model Migration Checklist
When Anthropic releases new model versions:

1. **Read the model card** — check for behavior changes, new capabilities
2. **Update model IDs** — find and replace old IDs
```bash
# Find all model references in your codebase
grep -r "claude-" --include="*.ts" --include="*.py" --include="*.json" .
```
3. **Test with new model** — run integration tests against both old and new
4. **Compare outputs** — spot-check key prompts for quality regression
5. **Update max_tokens** — new models may have different limits
6. **Gradual rollout** — use env var to control model selection

```typescript
// Environment-based model selection for safe rollout
const MODEL = process.env.CLAUDE_MODEL || 'claude-sonnet-4-20250514';

const message = await client.messages.create({
  model: MODEL,
  max_tokens: 1024,
  messages,
});
```

## Common Migration Issues
| Issue | Fix |
|-------|-----|
| Model ID not found (404) | Update to current model ID |
| Different output format | Adjust parsing — test with real prompts |
| Higher/lower token usage | Re-evaluate max_tokens and cost estimates |
| Deprecated SDK method | Check SDK changelog for replacement |

## Resources
- [SDK Releases (TS)](https://github.com/anthropics/anthropic-sdk-typescript/releases)
- [SDK Releases (Python)](https://github.com/anthropics/anthropic-sdk-python/releases)
- [Model Deprecation Policy](https://docs.anthropic.com/en/docs/about-claude/models)

## Next Steps
See `anthropic-known-pitfalls` for common mistakes to avoid.
