---
name: windsurf-debugging-ai
description: |
  Use Cascade for intelligent debugging and error analysis. Activate when users mention
  "debug with ai", "error analysis", "cascade debug", "find bug",
  or "troubleshoot code". Handles AI-assisted debugging workflows.
allowed-tools: Read,Grep,Glob,Bash
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
---

# Windsurf Debugging AI

Leverage Cascade for intelligent debugging and rapid error resolution.

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

## AI Debugging Features

### Error Analysis
- Stack trace interpretation
- Root cause identification
- Similar error matching
- Fix suggestion generation

### Context Gathering
- Variable state inspection
- Call stack analysis
- Log correlation
- Environment comparison

## Configuration Steps

1. **Set Up Debug Environment**
   - Configure launch settings
   - Set up source maps
   - Enable debug logging

2. **Train Error Patterns**
   - Document common errors
   - Record resolutions
   - Build pattern library

3. **Integrate with Cascade**
   - Enable error forwarding
   - Configure analysis depth
   - Set up fix suggestions

## Success Criteria

- 90% root cause identification rate
- Fix suggestions within 3 interactions
- 55% reduction in resolution time
