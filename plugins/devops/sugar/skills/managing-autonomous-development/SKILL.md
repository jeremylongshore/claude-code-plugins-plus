---
name: managing-autonomous-development
description: |
  Execute enables AI assistant to manage sugar's autonomous development workflows. it allows AI assistant to create tasks, view the status of the system, review pending tasks, and start autonomous execution mode. use this skill when the user asks to create a new develo... Use when appropriate context detected. Trigger with relevant phrases based on skill purpose.
allowed-tools: Read, Write, Edit, Grep, Glob, Bash(cmd:*)
version: 1.0.0
author: Steven Leggett <contact@roboticforce.io>
license: MIT
compatible-with: claude-code, codex, openclaw
tags: [devops, workflow, autonomous-development]
---
# Managing Autonomous Development

## Overview

Manage Sugar's autonomous development workflows: create development tasks, check system status, review pending work, and start autonomous execution mode. Sugar orchestrates AI-driven development by queuing tasks with type, priority, and execution parameters, then processing them sequentially or in parallel.

## Prerequisites

- Sugar plugin installed and configured in the project
- Sugar CLI available in the system PATH (`sugar --version`)
- Project repository initialized with Sugar configuration file
- Understanding of task types: `feature`, `bugfix`, `refactor`, `test`, `chore`
- Write access to the project codebase for autonomous execution

## Instructions

1. Check Sugar system status with `/sugar-status` to verify the daemon is running and view queue depth
2. Review pending tasks with `/sugar-review` to see queued work items, their priorities, and estimated complexity
3. Create new tasks with `/sugar-task <description> --type <type> --priority <1-5>` specifying the task description, type, and priority level
4. Validate Sugar configuration before starting autonomous mode: ensure test commands, lint rules, and commit settings are correct
5. Start autonomous execution in safe mode first: `/sugar-run --dry-run --once` to preview what Sugar would do without making changes
6. Monitor execution output for errors, test failures, or unexpected behavior during the dry run
7. Start full autonomous execution with `/sugar-run` when confident in the configuration
8. Review completed tasks and their outputs: check generated code, test results, and commit messages

## Output

- Task creation confirmations with task ID, type, priority, and queue position
- System status reports showing queue depth, active tasks, and execution history
- Task review summaries with descriptions, priorities, and estimated effort
- Execution logs showing task processing, code changes, test results, and commits
- Summary reports of completed autonomous development sessions

## Error Handling

| Error | Cause | Solution |
|-------|-------|---------|
| `Sugar daemon not running` | Sugar service not started or crashed | Start with `sugar start` or check logs for crash reason |
| `Task creation failed: invalid type` | Unsupported task type specified | Use valid types: `feature`, `bugfix`, `refactor`, `test`, `chore` |
| `Autonomous execution failed: tests failing` | Generated code does not pass project tests | Review the failing test output; fix the test or adjust the task description for clarity |
| `Configuration file not found` | Sugar config missing from project root | Initialize with `sugar init` to create the configuration file |
| `Priority out of range` | Priority value not between 1 and 5 | Use priority 1 (lowest) through 5 (highest/critical) |

## Examples

- "Create a new Sugar task: 'Add input validation to the user registration endpoint' with type feature and priority 3."
- "Check the current Sugar system status and list all pending tasks in the queue."
- "Start Sugar autonomous mode in dry-run to preview what changes it would make for the next queued task."

## Resources

- Sugar plugin documentation: https://github.com/roboticforce/sugar
- Task automation patterns: https://roboticforce.io/docs/sugar/
- Autonomous development best practices: https://roboticforce.io/docs/sugar/best-practices/