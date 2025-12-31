---
name: windsurf-flows-automation
description: |
  Create and manage Windsurf Flows for repetitive tasks. Activate when users mention
  "windsurf flows", "task automation", "workflow automation", "repetitive tasks",
  or "process automation". Handles Flow creation and management.
allowed-tools: Read,Write,Edit,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Flows Automation

Create and manage Flows to automate repetitive development tasks.

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

## Flow Types

### Creation Flows
- Component generation
- Module scaffolding
- Test file creation
- Documentation generation

### Transformation Flows
- Code refactoring patterns
- Migration scripts
- Format conversions
- Batch updates

## Configuration Steps

1. **Identify Repetitive Tasks**
   - Audit daily workflows
   - Measure time spent
   - Document steps manually

2. **Create Flow Definitions**
   - Define step sequence
   - Add variable placeholders
   - Configure error handling

3. **Test and Deploy**
   - Run in sandbox mode
   - Verify outputs
   - Enable for team

## Success Criteria

- Flows execute reliably
- Rollback capability working
- 10+ hours saved per developer monthly
