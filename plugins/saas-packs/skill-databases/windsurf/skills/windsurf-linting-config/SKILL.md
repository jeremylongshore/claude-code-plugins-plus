---
name: windsurf-linting-config
description: |
  Configure and enforce code quality with AI-assisted linting. Activate when users mention
  "configure linting", "eslint setup", "code quality rules", "linting configuration",
  or "code standards". Handles linting tool configuration.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Linting Configuration

Configure and enforce code quality with AI-assisted linting.

## Directory Structure

```
project-root/
    .eslintrc.js                     # ESLint configuration
        # Rule definitions
        # Plugin configuration
        # Environment settings
        # Override patterns

    .eslintignore                    # ESLint exclusions
        # Build directories
        # Generated files
        # Third-party code

    .prettierrc                      # Prettier configuration
        # Format rules
        # Parser options
        # Plugin settings

    .prettierignore                  # Prettier exclusions
        # Minified files
        # Vendor code
        # Lock files

    .stylelintrc.js                  # CSS/SCSS linting
        # Style rules
        # Property ordering
        # Selector patterns

    .windsurf/
        linting/
            profiles/
                strict.eslintrc.js       # Strict rule set
                    # Maximum enforcement
                    # No warnings allowed
                    # All best practices

                relaxed.eslintrc.js      # Relaxed rule set
                    # Essential rules only
                    # Warning level for style
                    # Flexible formatting

            custom-rules/
                project-rules.js         # Project-specific rules
                    # Custom patterns
                    # Domain-specific checks
                    # Team conventions

            auto-fix-config.json         # Auto-fix preferences
                # Rules to auto-fix
                # Confirmation requirements
                # Exclusion patterns
```

## Linting Features

### ESLint Integration
- Real-time error highlighting
- Auto-fix on save
- Custom rule support
- Plugin ecosystem

### AI Enhancement
- Rule suggestion based on code patterns
- Conflict resolution
- Performance optimization
- Migration assistance

## Configuration Steps

1. **Choose Base Configuration**
   - Select framework preset
   - Enable relevant plugins
   - Set environment targets

2. **Customize Rules**
   - Adjust severity levels
   - Add project-specific rules
   - Configure exceptions

3. **Integrate with Workflow**
   - Enable format on save
   - Add pre-commit hooks
   - Configure CI checks

## Success Criteria

- Zero false positives
- Auto-fix capability for most issues
- 90% reduction in style-related review comments
