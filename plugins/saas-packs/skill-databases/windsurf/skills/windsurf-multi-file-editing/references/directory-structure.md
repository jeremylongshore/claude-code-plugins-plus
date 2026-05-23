# Directory Structure

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
