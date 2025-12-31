---
name: windsurf-dependency-management
description: |
  Analyze and update dependencies with vulnerability scanning. Activate when users mention
  "update dependencies", "security audit", "npm audit", "vulnerability scan",
  or "dependency updates". Handles dependency analysis and updates.
allowed-tools: Read,Write,Edit,Bash,Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Dependency Management

Analyze and update dependencies with AI-assisted vulnerability management.

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

## Dependency Features

### Security Scanning
- Automated vulnerability detection
- Severity classification
- Remediation guidance
- Continuous monitoring

### Update Management
- Semantic version analysis
- Breaking change detection
- Rollback preparation
- Changelog summarization

## Configuration Steps

1. **Run Initial Audit**
   - Execute security scan
   - Categorize findings
   - Prioritize remediation

2. **Plan Updates**
   - Identify safe updates
   - Flag breaking changes
   - Prepare migration steps

3. **Apply and Verify**
   - Update incrementally
   - Run test suite
   - Monitor for regressions

## Success Criteria

- Zero high/critical CVEs
- Updates applied without breaking changes
- Minimal developer intervention required
