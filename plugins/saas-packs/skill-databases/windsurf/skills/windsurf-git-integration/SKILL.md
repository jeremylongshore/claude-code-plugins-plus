---
name: windsurf-git-integration
description: |
  Configure Git integration with Cascade AI assistance. Activate when users mention
  "git setup", "version control", "commit messages", "branch management",
  or "source control". Handles Git configuration and AI-assisted workflows.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Git Integration

Configure Git workflows enhanced by Cascade AI assistance.

## Directory Structure

```
project-root/
    .git/
        config                   # Repository Git configuration
            # Remote URLs and credentials
            # Branch tracking settings
            # Hook configurations

        hooks/
            pre-commit           # Pre-commit validation hook
                # Lint checks before commit
                # Test execution gates
                # Format verification

            commit-msg           # Commit message validation
                # Format enforcement
                # Issue reference checking
                # AI-suggested improvements

            pre-push             # Pre-push validation
                # Branch protection checks
                # CI preview execution
                # Security scanning

    .gitignore                   # Ignore patterns
        # Build artifacts
        # IDE settings (selective)
        # Environment files

    .windsurfrules               # AI Git behavior
        # Commit message style
        # Branch naming conventions
        # PR description format
```

## AI-Assisted Git Features

### Commit Messages
- Auto-generated from staged changes
- Conventional commits format
- Issue/ticket reference suggestions
- Breaking change detection

### Branch Management
- AI-suggested branch names
- Merge conflict assistance
- Rebase guidance
- Branch cleanup recommendations

## Configuration Steps

1. **Configure Git Credentials**
   - Set up SSH or HTTPS authentication
   - Configure credential caching
   - Set up commit signing (optional)

2. **Set Up AI Assistance**
   - Enable commit message suggestions
   - Configure branch naming rules
   - Set up PR template assistance

3. **Install Git Hooks**
   - Add pre-commit validation
   - Configure commit message checks
   - Set up pre-push gates

## Success Criteria

- Git operations complete successfully
- AI-suggested commit messages accepted 80%+
- Code review cycles shortened by 35%
