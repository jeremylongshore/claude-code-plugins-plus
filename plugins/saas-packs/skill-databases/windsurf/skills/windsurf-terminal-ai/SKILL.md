---
name: windsurf-terminal-ai
description: |
  Leverage AI-assisted terminal commands and debugging. Activate when users mention
  "terminal help", "command suggestion", "debug terminal", "shell assistance",
  or "cli help". Handles AI-enhanced terminal operations.
allowed-tools: Read,Bash,Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Terminal AI

Leverage AI-assisted terminal commands for efficient debugging and operations.

## Directory Structure

```
project-root/
    .windsurf/
        terminal/
            command-history.json     # AI-analyzed command history
                # Successful patterns
                # Error contexts
                # Suggested alternatives

            aliases.json             # AI-suggested aliases
                # Frequent command shortcuts
                # Project-specific commands
                # Workflow automation

            snippets/
                debug-commands.sh    # Common debug commands
                    # Log inspection commands
                    # Process monitoring
                    # Network diagnostics

                build-commands.sh    # Build workflow commands
                    # Clean build sequences
                    # Incremental builds
                    # Artifact management

    .bashrc / .zshrc                 # Shell configuration
        # Windsurf terminal integration
        # AI completion setup
        # Custom prompt configuration

    scripts/
        common-tasks.sh              # Reusable task scripts
            # Parameterized commands
            # Error handling
            # Logging integration
```

## AI Terminal Features

### Command Suggestions
- Context-aware completions
- Error correction proposals
- Alternative command options
- Parameter hints

### Debugging Assistance
- Error message interpretation
- Log analysis suggestions
- Stack trace navigation
- Environment diagnostics

## Configuration Steps

1. **Enable AI Assistance**
   - Configure terminal integration
   - Set up completion triggers
   - Enable error analysis

2. **Build Command Library**
   - Document common commands
   - Create reusable scripts
   - Set up aliases

3. **Optimize Workflows**
   - Identify repetitive patterns
   - Automate common sequences
   - Set up command templates

## Success Criteria

- 80% reduction in command errors
- Context-aware completions
- 45% reduction in debugging time
