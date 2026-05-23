# Directory Structure

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
