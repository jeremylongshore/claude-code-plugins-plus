---
name: guidewire-local-dev-loop
description: |
  Configure local Guidewire development workflow with Guidewire Studio, Gosu debugging,
  and hot reload capabilities.
  Use when setting up development environment, configuring IDE, or optimizing dev workflow.
  Trigger with phrases like "guidewire local dev", "guidewire studio setup",
  "gosu development", "guidewire debugging", "configure guidewire ide".
allowed-tools: Read, Write, Edit, Bash(java:*), Bash(gradle:*), Bash(git:*), Grep
version: 1.0.0
license: MIT
author: Jeremy Longshore <jeremy@intentsolutions.io>
compatible-with: claude-code, codex, openclaw
---
# Guidewire Local Dev Loop

## Overview

Set up an efficient local development workflow with Guidewire Studio, including hot reload, Gosu debugging, and continuous testing.

## Prerequisites

- JDK 17 installed and configured
- IntelliJ IDEA (Ultimate recommended) or Guidewire Studio
- Gradle 8.x
- Git for version control
- Access to Guidewire Cloud sandbox environment

## Instructions

### Step 1: Configure IDE Settings

Install IntelliJ plugins: Gosu Language Support, Guidewire Studio Plugin, EditorConfig. Set Gradle JVM to JDK 17, enable auto-import, and set test runner to Gradle.

### Step 2: Database Setup

```bash
createdb -U postgres pc_dev
./gradlew dbUpgrade
./gradlew loadSampleData    # Generate sample data
```

### Step 3: Start Development Server

```bash
./gradlew runServer              # Start with hot reload
./gradlew runServer --debug-jvm  # Start with debugging on port 5005
./gradlew :policycenter:runServer  # Start specific application
```

### Step 4: Configure Hot Reload

Enable hot swap in `config/dev-config.xml`, then attach IntelliJ debugger to port 5005. Gosu and PCF changes will auto-reload.

### Step 5: Run Tests

```bash
./gradlew test                                # All tests
./gradlew test --tests "gw.custom.MyServiceTest"  # Specific class
./gradlew test jacocoTestReport               # With coverage
./gradlew test --continuous                   # Watch mode
```

For detailed Gradle config, Gosu examples, PCF development, and keyboard shortcuts, load the reference guide:
`Read(${CLAUDE_SKILL_DIR}/references/implementation-guide.md)`

## Output

- Running local development server
- Hot reload enabled for Gosu and PCF changes
- Debug session attached to IDE
- Unit tests executing successfully

## Error Handling

| Error | Cause | Solution |
|-------|-------|----------|
| Port already in use | Server already running | Kill existing process or change port |
| Database connection failed | Wrong credentials/missing DB | Check postgres is running |
| Gosu compilation error | Syntax error | Check IDE error highlights |
| Hot reload not working | Debug not attached | Reconnect debugger |
| Out of memory | Insufficient heap | Increase -Xmx in jvmArgs |

## Resources

- [Guidewire Studio Documentation](https://docs.guidewire.com/cloud/gcc-guide/insurer-developer/)
- [Gosu Language Reference](https://gosu-lang.github.io/)
- [Gradle Plugin Documentation](https://docs.guidewire.com/tools/gradle-plugin/)

## Next Steps

For SDK and API patterns, see `guidewire-sdk-patterns`.

## Examples

**Basic usage**: Apply guidewire local dev loop to a standard project setup with default configuration options.

**Advanced scenario**: Customize guidewire local dev loop for production environments with multiple constraints and team-specific requirements.