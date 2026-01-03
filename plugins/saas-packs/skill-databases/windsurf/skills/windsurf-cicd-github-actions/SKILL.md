---
name: windsurf-cicd-github-actions
description: |
  Generate and maintain GitHub Actions with Cascade assistance. Activate when users mention
  "github actions", "ci/cd pipeline", "workflow automation", "continuous integration",
  or "deployment pipeline". Handles CI/CD configuration with AI assistance.
allowed-tools: Read,Write,Edit,Bash,Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf CI/CD GitHub Actions

Generate and maintain GitHub Actions workflows with Cascade AI assistance.

## Directory Structure

```
project-root/
    .github/
        workflows/
            ci.yml                   # Continuous integration workflow
                # Test execution on push/PR
                # Linting and type checking
                # Build verification

            cd.yml                   # Continuous deployment workflow
                # Production deployment steps
                # Environment configuration
                # Rollback procedures

            pr-checks.yml            # Pull request validation
                # Code review automation
                # Preview deployments
                # Status checks

            release.yml              # Release automation
                # Version bumping
                # Changelog generation
                # Asset publishing

        actions/
            custom-action/
                action.yml           # Reusable action definition
                    # Input parameters
                    # Output definitions
                    # Execution steps

        CODEOWNERS                   # Code ownership rules
            # Team responsibilities
            # Review requirements

    .windsurf/
        cicd/
            workflow-templates/
                standard-ci.yml      # Standard CI template
                    # Common job definitions
                    # Matrix configurations
                    # Caching strategies

            secrets-reference.md     # Required secrets documentation
                # Secret names and purposes
                # Rotation schedules
                # Access requirements
```

## Workflow Patterns

### Standard CI
- Checkout and cache setup
- Dependency installation
- Linting and type checking
- Test execution with coverage
- Build verification

### Deployment
- Environment-based triggers
- Approval gates
- Blue-green deployment
- Health checks

## Configuration Steps

1. **Analyze Project Requirements**
   - Identify build steps
   - Map test commands
   - Document deploy targets

2. **Generate Workflows**
   - Use Cascade for initial generation
   - Customize for project needs
   - Add environment variables

3. **Test and Iterate**
   - Run workflows locally (act)
   - Debug failures with Cascade
   - Optimize for speed

## Success Criteria

- Workflows pass validation
- Successful execution on first commit
- Pipeline setup in hours vs days
