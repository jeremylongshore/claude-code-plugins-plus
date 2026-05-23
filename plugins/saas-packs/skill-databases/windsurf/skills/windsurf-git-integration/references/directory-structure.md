# Directory Structure

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
