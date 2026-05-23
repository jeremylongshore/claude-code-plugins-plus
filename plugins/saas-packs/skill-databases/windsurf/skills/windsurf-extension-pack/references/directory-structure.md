# Directory Structure

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
