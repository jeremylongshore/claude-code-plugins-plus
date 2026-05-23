# Directory Structure

## Directory Structure

```
project-root/
    .windsurf/
        completion/
            preferences.json         # Completion behavior settings
                # Trigger delay configuration
                # Suggestion quantity limits
                # Context window size

            language-config/
                typescript.json      # TypeScript-specific settings
                    # Type inference depth
                    # Import suggestion behavior
                    # JSDoc completion

                python.json          # Python-specific settings
                    # Type hint suggestions
                    # Docstring completion
                    # Import organization

                rust.json            # Rust-specific settings
                    # Lifetime suggestion behavior
                    # Macro expansion
                    # Cargo integration

            snippets/
                custom-snippets.json # User-defined completions
                    # Project-specific patterns
                    # Boilerplate templates
                    # Common code blocks

    .windsurfrules                   # AI completion guidance
        # Code style for suggestions
        # Naming convention preferences
        # Pattern priorities
```
