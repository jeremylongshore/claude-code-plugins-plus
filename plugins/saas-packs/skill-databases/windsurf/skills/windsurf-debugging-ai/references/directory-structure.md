# Directory Structure

## Directory Structure

```
project-root/
    .windsurf/
        debug/
            error-patterns.json      # Known error patterns
                # Common error signatures
                # Resolution strategies
                # Prevention recommendations

            debug-sessions/
                session-YYYY-MM-DD.json  # Debug session logs
                    # Error contexts captured
                    # AI analysis results
                    # Resolution steps taken

            breakpoint-sets/
                api-debugging.json       # API debug breakpoints
                    # Request entry points
                    # Response handlers
                    # Error boundaries

                state-debugging.json     # State management breakpoints
                    # State mutation points
                    # Effect triggers
                    # Selector evaluations

    .vscode/
        launch.json                  # Debug configurations
            # Application debug configs
            # Test debug configs
            # Attach configurations

        tasks.json                   # Debug task definitions
            # Pre-debug build tasks
            # Log clearing tasks
            # Environment setup
```
