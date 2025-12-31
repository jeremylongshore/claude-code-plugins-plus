---
name: windsurf-multi-file-editing
description: |
  Execute multi-file edits with Cascade coordination. Activate when users mention
  "multi-file edit", "edit multiple files", "cross-file changes", "refactor across files",
  or "batch modifications". Handles coordinated multi-file operations.
allowed-tools: Read,Write,Edit,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Multi-File Editing

Execute coordinated changes across multiple files with Cascade assistance.

## Directory Structure

```
project-root/
    .windsurf/
        operations/
            pending-edits.json       # Queued multi-file operations
                # Files to be modified
                # Change descriptions
                # Dependency order

            edit-history.json        # Completed operation log
                # Timestamps and changes
                # Rollback information
                # Success/failure status

            templates/
                rename-pattern.json  # Rename operation template
                    # Find/replace patterns
                    # File scope definitions
                    # Exclusion rules

                feature-add.json     # Feature addition template
                    # Files to create/modify
                    # Import updates
                    # Test file additions

    src/
        components/                  # Example component directory
            ComponentA.tsx           # Component implementation
                # Renamed imports
                # Updated references
                # Consistent changes

            ComponentA.test.tsx      # Corresponding test file
                # Synchronized test updates
                # Import path corrections

            index.ts                 # Barrel export file
                # Updated exports
                # Maintained ordering
```

## Multi-File Operations

### Common Patterns
- **Rename** - Update symbol across all usages
- **Move** - Relocate file with import updates
- **Extract** - Pull code into new file
- **Inline** - Merge files together

### Safety Mechanisms
- Preview changes before applying
- Atomic rollback capability
- Syntax validation per file
- Reference integrity checking

## Configuration Steps

1. **Scope the Operation**
   - Identify all affected files
   - Map dependencies
   - Plan change order

2. **Execute with Preview**
   - Generate change preview
   - Review all modifications
   - Apply atomically

3. **Verify Results**
   - Run syntax checks
   - Execute tests
   - Validate references

## Success Criteria

- All files modified atomically
- Consistent syntax across changes
- No broken references
