---
description: Detect potential memory leaks in code
---

# Memory Leak Detector

Analyze code for potential memory leaks and improper resource management.

## Detection Patterns

1. **Event Listeners**: Unremoved event listeners
2. **Closures**: Variables captured in closures preventing GC
3. **Timers**: Uncancelled setTimeout/setInterval
4. **Cache Growth**: Unbounded cache or collection growth
5. **Circular References**: Objects referencing each other
6. **DOM References**: Detached DOM nodes held in memory
7. **Global Variables**: Unnecessary global state accumulation

## Analysis Process

1. Search for common leak patterns in codebase
2. Identify resource allocation without cleanup
3. Check for proper disposal in cleanup methods
4. Analyze object lifecycle management
5. Generate detailed report with locations and fixes

## Output

Provide markdown report with:
- Identified leak patterns with severity ratings
- File locations and line numbers
- Code snippets showing the issue
- Recommended fixes with examples
- Prevention strategies
