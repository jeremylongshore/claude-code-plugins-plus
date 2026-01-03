---
name: windsurf-code-completion
description: |
  Configure and optimize Supercomplete code suggestions. Activate when users mention
  "code completion", "autocomplete", "supercomplete", "inline suggestions",
  or "ai completions". Handles completion configuration and optimization.
allowed-tools: Read,Write,Edit
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Code Completion

Configure and optimize Supercomplete for maximum productivity.

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

## Completion Features

### Supercomplete
- Multi-line intelligent completions
- Context-aware suggestions
- Import auto-resolution
- Type inference integration

### Configuration Options
- Trigger sensitivity
- Suggestion ranking
- Inline vs popup display
- Tab/Enter acceptance

## Configuration Steps

1. **Set Trigger Behavior**
   - Configure delay timing
   - Set trigger characters
   - Define context requirements

2. **Language-Specific Setup**
   - Enable language servers
   - Configure type providers
   - Set import preferences

3. **Personalize Experience**
   - Create custom snippets
   - Train on codebase patterns
   - Adjust ranking weights

## Success Criteria

- Completions appear within 150ms
- 85%+ suggestion acceptance rate
- 60% faster boilerplate writing
