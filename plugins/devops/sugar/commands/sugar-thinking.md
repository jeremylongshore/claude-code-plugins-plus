---
name: sugar-thinking
description: View Claude's thinking logs for task execution
usage: /sugar-thinking [TASK_ID] [OPTIONS]
examples:
  - /sugar-thinking task-abc123
  - /sugar-thinking --list
  - /sugar-thinking task-abc123 --stats
---

# Sugar Thinking Command

View Claude's thinking logs for task execution, providing visibility into Claude's reasoning process during autonomous task execution.

## Usage

```
/sugar-thinking [TASK_ID] [OPTIONS]
```

## Description

The `sugar-thinking` command allows you to view the captured thinking blocks from Claude's execution of tasks. This provides critical visibility into how Claude approaches problems and makes decisions during autonomous development.

## Arguments

- `TASK_ID` - Task ID to view thinking for (required unless using `--list`)

## Options

- `--list, -l` - List all available thinking logs
- `--stats, -s` - Show thinking statistics only (blocks count, characters, tools considered)

## Examples

### View Full Thinking Log

```
/sugar-thinking task-abc123
```

Shows the complete thinking log with timestamped thinking blocks.

### View Statistics Only

```
/sugar-thinking task-abc123 --stats
```

Shows summary statistics including:
- Total thinking blocks captured
- Total characters
- Average thinking block length
- Tools considered during thinking
- Timing information

### List All Thinking Logs

```
/sugar-thinking --list
```

Lists all available thinking logs sorted by modification time (newest first).

## Output Format

### Full Log

```markdown
# Thinking Log: Implement user authentication

**Task ID:** abc123
**Started:** 2026-01-07T10:30:00

---

## 10:30:05

First, I need to understand the current authentication system...

---

## 10:30:12

*Considering tool: `Read`*

I should read the existing auth module to see what's already implemented...

---

## Summary

- **Total thinking blocks:** 15
- **Total characters:** 3,247
- **Average length:** 216 chars
- **Tools considered:** Read, Write, Bash

**Completed:** 2026-01-07T10:35:42
```

### Statistics

```
📊 Thinking Statistics for: Implement user authentication
Task ID: abc123
============================================================

  Thinking Blocks: 15
  Total Characters: 3,247
  Average Length: 216 chars
  Tools Considered: Read, Write, Bash
  First Thinking: 2026-01-07T10:30:05
  Last Thinking: 2026-01-07T10:35:40

  Full log: .sugar/thinking/abc123.md
```

## Use Cases

1. **Debugging Failed Tasks**: Understand why a task succeeded or failed by reviewing Claude's reasoning
2. **Learning from Claude**: Study how Claude approaches different types of problems
3. **Verification**: Confirm Claude is following expected strategies and approaches
4. **Pattern Analysis**: Track thinking patterns across tasks to improve prompts

## Configuration

Thinking capture is enabled by default. To disable, add to `.sugar/config.yaml`:

```yaml
sugar:
  executor:
    thinking_capture: false
```

## Related Commands

- `/sugar-status` - View overall system status
- `/sugar-view` - View task details
- `/sugar-task-type` - Manage task type configurations
