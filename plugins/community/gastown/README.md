# Gas Town

**Multi-agent orchestrator for Claude Code.** Track work with convoys, sling to polecats. The Cognition Engine for AI-powered software factories.

## Overview

Gas Town is a multi-agent workspace manager that enables you to run multiple Claude Code agents on projects simultaneously. Think of it as a factory floor where:

- **Polecats** (🦨) are quick task workers that spawn, complete work, and vanish
- **Crew** (👷) are persistent named helpers that stick around
- **Mayor** (🦊) dispatches work and coordinates across rigs
- **Witness** (🦅) watches workers and nudges when stuck
- **Refinery** (🦡) merges code and handles quality control

## Installation

```bash
# Install the Gas Town CLI
go install github.com/steveyegge/gastown/cmd/gt@latest

# Install the Beads tracker
go install github.com/steveyegge/beads/cmd/bd@latest

# Set up your workspace
gt up
```

## Quick Start

```bash
# Create a task
bd create --title "Fix the login bug"

# Sling it to a polecat
gt sling gt-123 myproject

# Watch it work
gt peek Toast
```

## Usage

Simply describe what you need - Gas Town activates when you mention:
- gastown, gas town, gt commands, bd commands
- convoys, polecats, crew, rigs
- slinging work, multi-agent coordination
- beads, hooks, molecules, workflows

## Author

**Numman Ali** - [@numman-ali](https://github.com/numman-ali)

## Resources

- [Gas Town Repository](https://github.com/steveyegge/gastown)
- [n-skills Marketplace](https://github.com/numman-ali/n-skills)

## License

Apache-2.0
