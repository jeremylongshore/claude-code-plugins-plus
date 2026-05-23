# Directory Structure

## Directory Structure

```
project-root/
    package.json                     # NPM dependencies
        # Direct dependencies
        # Dev dependencies
        # Peer dependencies
        # Version constraints

    package-lock.json                # Lock file
        # Exact versions
        # Integrity hashes
        # Dependency tree

    .npmrc                           # NPM configuration
        # Registry settings
        # Authentication
        # Scope mappings

    .windsurf/
        dependencies/
            audit-report.json            # Security audit results
                # Vulnerability details
                # Severity levels
                # Remediation steps

            update-plan.json             # Planned updates
                # Version changes
                # Breaking change notes
                # Migration requirements

            compatibility-matrix.json    # Version compatibility
                # Tested combinations
                # Known conflicts
                # Recommended versions

            policies/
                update-policy.json       # Update frequency rules
                    # Major version handling
                    # Security update urgency
                    # Testing requirements

                block-list.json          # Blocked packages
                    # License violations
                    # Known vulnerabilities
                    # Deprecated packages
```
