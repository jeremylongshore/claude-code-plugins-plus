---
name: cursor-known-pitfalls
description: |
  Avoid common Cursor IDE pitfalls and mistakes. Triggers on "cursor pitfalls",
  "cursor mistakes", "cursor gotchas", "cursor issues", "cursor problems".
allowed-tools: Read, Write, Edit, Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Cursor Known Pitfalls & Solutions

## AI Feature Pitfalls

### Over-Trusting AI Output
```
PITFALL:
Accepting AI suggestions without review.
AI can generate plausible but incorrect code.

SOLUTION:
- Always review before accepting
- Test generated code
- Understand what the code does
- Don't accept security-sensitive code blindly
```

### Context Pollution
```
PITFALL:
Long conversations accumulate irrelevant context.
AI responses become less accurate over time.

SOLUTION:
- Start new chat for new topics (Cmd+Shift+L)
- Keep conversations focused
- Clear context when switching tasks
- Use @-mentions strategically
```

### Vague Prompts
```
PITFALL:
"Make it better" or "Fix this" without specifics.
AI can't read your mind.

SOLUTION:
- Be specific about what you want
- Include error messages
- Describe expected vs actual behavior
- Provide context with @-mentions
```

### Wrong Model for Task
```
PITFALL:
Using GPT-4 for simple completions (slow, expensive).
Using GPT-3.5 for complex architecture (insufficient).

SOLUTION:
- GPT-3.5/Cursor-small: Simple completions
- GPT-4 Turbo: Complex tasks, large context
- Claude: Explanations, documentation
- Match model to task complexity
```

## Completion Pitfalls

### Tab Key Confusion
```
PITFALL:
Tab accepts completion when you wanted indentation.
Accidentally inserting AI-generated code.

SOLUTION:
- Watch for ghost text before pressing Tab
- Use Esc to dismiss unwanted completions
- Configure completion delay
- Be aware of completion mode
```

### Outdated Completions
```
PITFALL:
Completions based on old patterns in codebase.
AI suggests deprecated approaches.

SOLUTION:
- Update .cursorrules with current patterns
- Re-index after major refactors
- Include modern examples in rules
- Clear index cache if stale
```

### Language/Framework Mismatch
```
PITFALL:
AI suggests React patterns in Vue project.
Wrong framework conventions in completions.

SOLUTION:
- Configure .cursorrules with correct framework
- Check file associations
- Be explicit in prompts about framework
- Verify language mode in status bar
```

## Configuration Pitfalls

### Missing .cursorrules
```
PITFALL:
AI doesn't know your project conventions.
Inconsistent code generation.

SOLUTION:
- Always create .cursorrules for projects
- Include coding standards
- Document framework/library choices
- Add examples of preferred patterns
```

### Poor .cursorignore
```
PITFALL:
Indexing node_modules, build outputs.
Slow indexing, irrelevant search results.

SOLUTION:
- Create comprehensive .cursorignore
- Exclude all dependency folders
- Exclude build outputs
- Exclude large data files
```

### Settings Not Synced
```
PITFALL:
Different settings on different machines.
Inconsistent Cursor behavior.

SOLUTION:
- Enable Settings Sync
- Commit .vscode/settings.json to repo
- Document team settings
- Use workspace settings for project-specific
```

## Security Pitfalls

### Exposing Secrets
```
PITFALL:
AI context includes sensitive data.
Secrets sent to AI providers.

SOLUTION:
- Use .cursorignore for .env files
- Use environment variables
- Enable Privacy Mode for sensitive code
- Never hardcode credentials
```

### Trusting AI for Security Code
```
PITFALL:
AI-generated auth/crypto code may have flaws.
Security vulnerabilities in generated code.

SOLUTION:
- Extra review for security code
- Use established libraries
- Security review by human expert
- Test with security tools
```

### API Keys in Settings
```
PITFALL:
Storing API keys in settings.json.
Keys visible in plaintext.

SOLUTION:
- Use environment variables
- Use secrets managers
- Never commit keys to repo
- Rotate keys if exposed
```

## Performance Pitfalls

### Too Many Extensions
```
PITFALL:
Installing every interesting extension.
Slow startup, memory issues.

SOLUTION:
- Audit extensions regularly
- Disable unused extensions
- Use workspace-specific extensions
- Remove completely if not needed
```

### Large Context Requests
```
PITFALL:
@-mentioning entire folders.
Slow responses, context overflow.

SOLUTION:
- @-mention specific files
- Select only relevant code
- Use focused queries
- Start new chat when bloated
```

### Indexing Entire Codebase
```
PITFALL:
Indexing massive monorepo.
Never-ending indexing, high CPU.

SOLUTION:
- Aggressive .cursorignore
- Open specific packages
- Use workspace folders
- Manual indexing for large projects
```

## Workflow Pitfalls

### Not Using Chat History
```
PITFALL:
Re-asking questions you've already asked.
Wasting time and tokens.

SOLUTION:
- Scroll up in chat history
- Reference previous responses
- Save useful responses
- Build knowledge base
```

### Ignoring Composer Review
```
PITFALL:
Clicking "Apply All" without review.
Unwanted changes across files.

SOLUTION:
- Review each file change
- Check for unintended modifications
- Apply selectively
- Use version control for safety
```

### Single-Tool Mindset
```
PITFALL:
Using only chat or only completions.
Missing efficiency gains from tool combinations.

SOLUTION:
- Completions for flow coding
- Chat for questions and review
- Composer for multi-file changes
- Inline edit for quick fixes
```

## Team Pitfalls

### No Shared Configuration
```
PITFALL:
Everyone has different .cursorrules.
Inconsistent AI-generated code.

SOLUTION:
- Commit .cursorrules to repo
- Document team standards
- Review rules in PRs
- Onboard new members
```

### Conflicting Extensions
```
PITFALL:
Team members with different extensions.
Code formatted differently.

SOLUTION:
- .vscode/extensions.json in repo
- Shared formatter config
- Enforce in CI
- Document required extensions
```

### Knowledge Silos
```
PITFALL:
Best prompts/techniques not shared.
Duplicate effort discovering patterns.

SOLUTION:
- Share effective prompts
- Document in .cursorrules
- Team prompt library
- Regular knowledge sharing
```

## Recovery Strategies

### When Things Go Wrong
```
1. Don't panic - use version control
2. Git stash or commit work in progress
3. Restart Cursor if behaving oddly
4. Clear cache if persistent issues
5. Start new chat for fresh context
```

### Reset Options
```bash
# Clear just cache
rm -rf ~/Library/Caches/Cursor/

# Clear extension state
rm -rf ~/.cursor/extensions/

# Full reset (last resort)
rm -rf ~/Library/Application\ Support/Cursor/
rm -rf ~/.cursor/
```

### Getting Help
```
1. Check Cursor documentation
2. Search GitHub issues
3. Ask in Discord community
4. Contact support (paid plans)
5. Reproduce and report bugs
```

## Prevention Checklist

```
[ ] .cursorrules created and maintained
[ ] .cursorignore comprehensive
[ ] Settings committed to repo
[ ] Extensions audited regularly
[ ] Team using shared configurations
[ ] Security guidelines followed
[ ] Performance monitored
[ ] Regular cache clearing
[ ] Version control always used
```
