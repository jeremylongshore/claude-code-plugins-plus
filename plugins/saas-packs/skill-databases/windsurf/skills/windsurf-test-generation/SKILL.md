---
name: windsurf-test-generation
description: |
  Generate comprehensive test suites using Cascade. Activate when users mention
  "generate tests", "test coverage", "write unit tests", "create test suite",
  or "tdd assistance". Handles AI-powered test generation.
allowed-tools: Read,Write,Edit,Bash,Grep,Glob
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Test Generation

Generate comprehensive test suites using Cascade AI assistance.

## Directory Structure

```
project-root/
    src/
        components/
            Button.tsx               # Component to test
            Button.test.tsx          # Generated test file
                # Render tests
                # Interaction tests
                # Accessibility tests

        utils/
            formatters.ts            # Utility functions
            formatters.test.ts       # Generated unit tests
                # Input validation tests
                # Edge case coverage
                # Error handling tests

        services/
            api.ts                   # API service
            api.test.ts              # Integration tests
                # Mock setup
                # Request/response tests
                # Error scenario tests

    .windsurf/
        testing/
            templates/
                unit-test.template.ts    # Unit test template
                    # Describe/it structure
                    # Setup and teardown
                    # Assertion patterns

                integration-test.template.ts   # Integration template
                    # Service mocking
                    # Database fixtures
                    # Cleanup procedures

            coverage-config.json         # Coverage requirements
                # Minimum thresholds
                # Exclude patterns
                # Report formats

            test-patterns/
                component-tests.md       # Component test patterns
                    # Rendering tests
                    # Event handling
                    # State changes

                hook-tests.md            # Hook test patterns
                    # renderHook usage
                    # Act and waitFor
                    # Cleanup patterns
```

## Test Generation Features

### Analysis
- Function signature analysis
- Edge case identification
- Dependency detection
- Error path mapping

### Generation
- Test structure scaffolding
- Meaningful assertions
- Mock data creation
- Coverage optimization

## Configuration Steps

1. **Configure Testing Framework**
   - Set up test runner (Jest/Vitest)
   - Configure mocking libraries
   - Set coverage thresholds

2. **Generate Tests with Cascade**
   - Select target functions
   - Request test generation
   - Review and refine

3. **Integrate into Workflow**
   - Add to CI pipeline
   - Set up pre-commit hooks
   - Monitor coverage trends

## Success Criteria

- 80%+ code coverage achieved
- Meaningful assertions (not just coverage)
- 65% reduction in test writing time
