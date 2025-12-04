---
description: Enables claude to manage sugar's autonomous development workflows. it
  allows claude to create tasks, view the status of the system, review pending tasks,
  and start autonomous execution mode. use this skill when the user asks to create
  a new develo...
allowed-tools:
- Read
- Write
- Edit
- Grep
- Glob
- Bash
name: managing-autonomous-development
license: MIT
---
## Overview

This skill empowers Claude to orchestrate and monitor autonomous development processes within the Sugar environment. It provides a set of commands to create, manage, and execute tasks, ensuring efficient and automated software development workflows.

## How It Works

1. **Command Recognition**: Claude identifies the appropriate Sugar command (e.g., `/sugar-task`, `/sugar-status`, `/sugar-review`, `/sugar-run`).
2. **Parameter Extraction**: Claude extracts relevant parameters from the user's request, such as task type, priority, and execution flags.
3. **Execution**: Claude executes the corresponding Sugar command with the extracted parameters, interacting with the Sugar plugin.
4. **Response Generation**: Claude presents the results of the command execution to the user in a clear and informative manner.

## When to Use This Skill

This skill activates when you need to:
- Create a new development task with specific requirements.
- Check the current status of the Sugar system and task queue.
- Review and manage pending tasks in the queue.
- Start or manage the autonomous execution mode.

## Examples

### Example 1: Creating a New Feature Task

User request: "/sugar-task Implement user authentication --type feature --priority 4"

The skill will:
1. Parse the request and identify the command as `/sugar-task` with parameters "Implement user authentication", `--type feature`, and `--priority 4`.
2. Execute the `sugar` command to create a new task with the specified parameters.
3. Confirm the successful creation of the task to the user.

### Example 2: Checking System Status

User request: "/sugar-status"

The skill will:
1. Identify the command as `/sugar-status`.
2. Execute the `sugar` command to retrieve the system status.
3. Display the system status, including task queue information, to the user.

## Best Practices

- **Clarity**: Always confirm the parameters before executing a command to ensure accuracy.
- **Safety**: When using `/sugar-run`, strongly advise the user to use `--dry-run --once` first.
- **Validation**: Recommend validating the Sugar configuration before starting autonomous mode.

## Integration

This skill integrates directly with the Sugar plugin, leveraging its command-line interface to manage autonomous development workflows. It can be combined with other skills to provide a more comprehensive development experience.