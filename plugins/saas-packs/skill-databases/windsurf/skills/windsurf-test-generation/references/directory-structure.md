# Directory Structure

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
