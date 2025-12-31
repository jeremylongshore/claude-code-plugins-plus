---
name: windsurf-extension-pack
description: |
  Install and configure essential Windsurf extensions for productivity. Activate when users mention
  "install extensions", "setup windsurf plugins", "configure extensions", "extension recommendations",
  or "productivity extensions". Handles extension installation and configuration.
allowed-tools: Read,Write,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Extension Pack

Install and configure essential extensions for maximum Windsurf productivity.

## Directory Structure

```
~/.windsurf/
    extensions/
        extension-manifest.json  # Installed extensions registry
            # Extension IDs and versions
            # Installation timestamps
            # Dependency mappings

        ms-python.python/        # Python language support
            # Interpreter configuration
            # Linting and formatting
            # Debugging support

        dbaeumer.vscode-eslint/  # JavaScript/TypeScript linting
            # ESLint configuration
            # Auto-fix settings
            # Rule customization

        esbenp.prettier-vscode/  # Code formatting
            # Formatter configuration
            # Language-specific settings
            # Format on save rules

project-root/
    .vscode/
        extensions.json          # Workspace extension recommendations
            # Required extensions list
            # Optional productivity tools
            # Development-specific extensions

        settings.json            # Extension-specific settings
            # Per-extension configuration
            # Workspace overrides
            # Feature toggles
```

## Recommended Extensions

### Essential
- **Python** - Full Python language support
- **ESLint** - JavaScript/TypeScript linting
- **Prettier** - Code formatting
- **GitLens** - Git integration enhancement

### Productivity
- **Error Lens** - Inline error display
- **Todo Tree** - Task tracking
- **Bracket Pair Colorizer** - Code readability
- **Path Intellisense** - File path completion

## Configuration Steps

1. **Install Core Extensions**
   - Add language support extensions
   - Install linting and formatting tools
   - Configure Git enhancements

2. **Configure Extension Settings**
   - Set up formatters per language
   - Configure linting rules
   - Enable productivity features

3. **Document Team Extensions**
   - Create extensions.json recommendations
   - Document required vs optional
   - Set up automated installation

## Success Criteria

- All extensions installed without conflicts
- Verified functionality for each extension
- Environment operational within 30 minutes
