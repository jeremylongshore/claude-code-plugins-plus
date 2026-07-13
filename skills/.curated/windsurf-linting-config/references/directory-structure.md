# Directory Structure

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
