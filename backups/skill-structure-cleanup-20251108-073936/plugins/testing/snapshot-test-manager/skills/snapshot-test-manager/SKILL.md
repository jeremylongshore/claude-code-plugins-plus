---
name: managing-snapshot-tests
description: |
  This skill enables Claude to manage and update snapshot tests using intelligent diff analysis and selective updates. It is triggered when the user asks to analyze snapshot failures, update snapshots, or manage snapshot tests in general. It helps distinguish intentional changes from regressions, selectively update snapshots, and validate snapshot integrity. Use this when the user mentions "snapshot tests", "update snapshots", "snapshot failures", or requests to run "/snapshot-manager" or "/sm". It supports Jest, Vitest, Playwright, and Storybook frameworks.
allowed-tools: Read, Bash, Grep, Glob
version: 1.0.0
---

## Overview

This skill empowers Claude to efficiently manage snapshot tests by analyzing differences, selectively updating snapshots based on intentional changes, and identifying potential regressions. It provides a streamlined approach to maintain snapshot test suites across various JavaScript testing frameworks.

## How It Works

1. **Analyzing Failures**: Reviews failed snapshot diffs, highlighting intentional and unintentional changes with side-by-side comparisons.
2. **Selective Updating**: Updates specific snapshots that reflect intentional UI or code changes, while preserving snapshots that have caught regressions.
3. **Batch Processing**: Allows for batch updating of related snapshots to streamline the update process.

## When to Use This Skill

This skill activates when you need to:
- Analyze snapshot test failures after code changes.
- Update snapshot tests to reflect intentional UI changes.
- Identify and preserve snapshots that are catching regressions.

## Examples

### Example 1: Updating Snapshots After UI Changes

User request: "I've made some UI changes and now my snapshot tests are failing. Can you update the snapshots?"

The skill will:
1. Analyze the snapshot failures, identifying the diffs caused by the UI changes.
2. Update the relevant snapshot files to reflect the new UI.

### Example 2: Investigating Unexpected Snapshot Changes

User request: "My snapshot tests are failing, but I don't expect any UI changes. Can you help me figure out what's going on?"

The skill will:
1. Analyze the snapshot failures, highlighting the unexpected diffs.
2. Present the diffs to the user for review, indicating potential regressions.

## Best Practices

- **Clear Communication**: Clearly state the intention behind updating or analyzing snapshots.
- **Framework Awareness**: Specify the testing framework (Jest, Vitest, etc.) if known for more accurate analysis.
- **Selective Updates**: Avoid blindly updating all snapshots. Focus on intentional changes and investigate unexpected diffs.

## Integration

This skill works independently but can be used in conjunction with other code analysis and testing tools to provide a comprehensive testing workflow.