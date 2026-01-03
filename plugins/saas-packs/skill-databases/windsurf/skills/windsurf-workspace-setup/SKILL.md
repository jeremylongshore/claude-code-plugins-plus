---
name: windsurf-workspace-setup
description: |
  Initialize Windsurf workspace with project-specific AI rules. Activate when users mention
  "create windsurfrules", "setup workspace", "configure project ai", "initialize windsurf workspace",
  or "migrate to windsurf". Handles workspace configuration and team standardization.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Workspace Setup

Initialize and configure Windsurf workspace for consistent AI-assisted development.

## Directory Structure

```
project-root/
    .windsurfrules               # Primary AI configuration file
        # YAML-formatted rules for Cascade behavior
        # Project-specific coding conventions
        # Framework and library preferences
        # Security and compliance requirements

    .vscode/
        settings.json            # Editor settings (Windsurf compatible)
            # Windsurf-specific configuration overrides
            # Theme and UI preferences
            # Extension settings

        extensions.json          # Recommended extensions list
            # Essential Windsurf extensions
            # Language-specific tools
            # Team productivity extensions

    .editorconfig                # Cross-editor consistency
        # Indentation and whitespace rules
        # Line ending configuration
        # File encoding standards

    .gitattributes               # Git handling rules
        # Line ending normalization
        # Binary file handling
        # Merge strategy definitions

    workspace.code-workspace     # Multi-root workspace config
        # Folder definitions for monorepos
        # Shared settings across projects
        # Task and launch configurations
```

## Configuration Steps

1. **Create .windsurfrules**
   - Define project language and framework
   - Set coding style preferences
   - Configure AI behavior guidelines

2. **Set Up Workspace Settings**
   - Configure editor preferences
   - Install recommended extensions
   - Set up debugging configurations

3. **Establish Team Standards**
   - Document configuration decisions
   - Create onboarding checklist
   - Set up validation scripts

## Success Criteria

- Valid YAML syntax in .windsurfrules
- Consistent AI behavior across team members
- 60% reduction in onboarding time
