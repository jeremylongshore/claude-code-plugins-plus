# Directory Structure

## Directory Structure

```
project-root/
    .windsurf/
        flows/
            flow-registry.json       # Registered flows index
                # Flow names and descriptions
                # Trigger conditions
                # Execution statistics

            definitions/
                create-component.flow.json   # Component creation flow
                    # Steps: template, naming, imports
                    # Variable substitutions
                    # Post-creation tasks

                test-coverage.flow.json      # Test coverage flow
                    # Find untested functions
                    # Generate test templates
                    # Run coverage report

                refactor-extract.flow.json   # Extract refactoring flow
                    # Select code block
                    # Create new module
                    # Update imports

            templates/
                component-template.tsx   # Component boilerplate
                    # Parameterized template
                    # Style includes
                    # Test file companion

                hook-template.ts         # Custom hook template
                    # State management
                    # Effect patterns
                    # Return type structure

            logs/
                execution-log.json       # Flow execution history
                    # Timestamps and outcomes
                    # Error details
                    # Rollback markers
```
