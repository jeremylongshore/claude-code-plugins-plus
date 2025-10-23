---
name: taskwarrior-protocol
description: Manually enforce complete Taskwarrior integration protocol with full task lifecycle management and time tracking
model: sonnet
---

# Taskwarrior Integration Protocol - Manual Enforcement

Enforce the complete Taskwarrior integration protocol for the current coding request.

## Protocol Overview

This command enforces a **mandatory 4-phase workflow** for ALL coding activities:

1. **Phase 1: Task Decomposition** - Create Taskwarrior tasks BEFORE writing code
2. **Phase 2: Task Activation** - Start tasks to begin time tracking
3. **Phase 3: Implementation** - Write code with proper annotations
4. **Phase 4: Completion** - Complete tasks and show time summary

**CRITICAL RULE: NO CODE IS WRITTEN until Taskwarrior tasks are created and started.**

## Phase 1: Task Decomposition

Analyze the user's request and create appropriate Taskwarrior tasks.

### Simple Request (1 task)

```bash
task add "Brief description" project:ProjectName priority:H/M/L due:today/tomorrow/YYYY-MM-DD +tag1 +tag2 +tag3
```

### Complex Request (multiple dependent tasks)

```bash
# Parent task
task add "Main goal" project:ProjectName priority:H due:5days +architecture

# Dependent subtasks
task add "Subtask 1" project:ProjectName depends:1 priority:H due:1day +implementation
task add "Subtask 2" project:ProjectName depends:2 priority:M due:2days +testing
task add "Subtask 3" project:ProjectName depends:3 priority:L due:5days +documentation
```

### Required Attributes

Every task MUST include:

- **project:** Category for the work (project:DevOps, project:WebDev, project:DataScience)
- **priority:** H (high/urgent), M (medium/normal), L (low/deferred)
- **due:** Realistic deadline (today, tomorrow, YYYY-MM-DD, or relative like 3days)
- **tags:** At least 2-3 relevant tags for filtering and reporting

### Priority Assignment Rules

**priority:H** - Use when:
- Blocking other work
- Production outage or critical bug
- Security vulnerability
- Hard deadline within 24-48 hours

**priority:M** - Use when:
- Normal feature development (DEFAULT)
- Non-blocking improvements
- Deadline within 3-7 days

**priority:L** - Use when:
- Nice-to-have enhancements
- Documentation updates
- No specific deadline

### Common Tag Taxonomy

**Work Type Tags:**
- `+feature` - New functionality
- `+bugfix` - Fixing issues
- `+refactor` - Code restructuring
- `+testing` - Test creation
- `+documentation` - Docs and comments
- `+deployment` - Release work
- `+security` - Security-related
- `+performance` - Optimization
- `+debugging` - Investigation
- `+maintenance` - Routine upkeep
- `+automation` - Scripting/tooling

**Technology Tags:**
- `+python`, `+javascript`, `+bash`, `+typescript`
- `+docker`, `+kubernetes`, `+cicd`
- `+postgresql`, `+redis`, `+api`
- `+fastapi`, `+react`, `+nextjs`

**Status Tags:**
- `+blocked` - Cannot proceed
- `+urgent` - Immediate attention
- `+waiting` - Awaiting input
- `+review` - Ready for review

## Phase 2: Task Activation & Time Tracking

After creating tasks, activate them:

```bash
# Start the first task (or first in dependency chain)
task <ID> start

# Verify task is active
task active

# Verify Timewarrior tracking
timew
```

**What happens:**
- Task status changes to "started"
- Timewarrior begins tracking time with task tags
- Urgency score increases for active tasks

## Phase 3: Code Implementation

**NOW proceed with writing code.**

### During Implementation

**Annotate important decisions:**
```bash
task <ID> annotate "Decision: Using FastAPI over Flask for async support"
task <ID> annotate "Found performance issue in database query"
```

**If encountering blockers:**
```bash
# Stop the task temporarily
task <ID> stop

# Document the blocker
task <ID> annotate "Blocked: Need AWS credentials from ops team"

# Mark as blocked
task <ID> modify +blocked

# Explain blocker to user and wait for resolution
```

**If scope changes:**
```bash
# Update existing task
task <ID> modify +additional_tag description:"Updated description"

# Or create dependent subtask
task add "Additional work: Email notifications" depends:<ID> project:SameProject +feature
```

## Phase 4: Task Completion

After code is delivered and verified:

```bash
# Complete the task
task <ID> done

# Timewarrior automatically stops tracking

# Show time summary
timew summary :ids

# Check remaining work
task next
```

### Completion Checklist

Before marking task as done:
- ✅ Code is written and tested
- ✅ Documentation updated (if applicable)
- ✅ Task annotations reflect final state
- ✅ Blockers resolved or escalated
- ✅ Time tracking accurate

### Post-Completion Report

Provide user with:
```bash
# Task details
task <ID> info

# Time spent
timew summary :ids

# Project status
task project:<ProjectName> status:pending
task project:<ProjectName> completed

# Next tasks (if any dependencies)
task next
```

## Example Workflows

### Example 1: Simple Script Creation

**User Request:** "Create a Bash script that backs up /home to /backup"

**Phase 1: Decomposition**
```bash
task add "Create home directory backup script" project:DevOps priority:M due:today +scripting +automation +backup
```

**Phase 2: Activation**
```bash
task 42 start
timew  # Verify tracking
```

**Phase 3: Implementation**
```bash
[Write backup.sh script with error handling, logging, etc.]
```

**Phase 4: Completion**
```bash
task 42 done
timew summary :ids
```

**Output:**
```
Task 42 completed: Create home directory backup script
Time spent: 15 minutes
Project: DevOps
Tags: scripting, automation, backup
```

### Example 2: Complex Multi-Component Project

**User Request:** "Build a REST API with JWT authentication and PostgreSQL"

**Phase 1: Decomposition**
```bash
# Parent task
task add "Build REST API with authentication" project:WebDev priority:H due:5days +api +backend

# Subtasks with dependencies
task add "Design PostgreSQL schema" project:WebDev depends:43 priority:H due:1day +database +design
task add "Implement JWT authentication" project:WebDev depends:44 priority:H due:2days +auth +security +jwt
task add "Create CRUD endpoints" project:WebDev depends:45 priority:M due:3days +crud +endpoints
task add "Write API documentation" project:WebDev depends:46 priority:L due:5days +documentation +openapi
```

**Phase 2: Activation (Sequential)**
```bash
task 44 start  # Start with database schema
```

**Phase 3: Implementation**
```bash
[Implement database schema]
task 44 annotate "Using Alembic for migrations"
task 44 done

task 45 start  # Next: JWT auth
[Implement JWT authentication]
task 45 done

# Continue through dependency chain...
```

**Phase 4: Completion (After all subtasks)**
```bash
task 43 done  # Complete parent task

# Show project summary
task project:WebDev completed
timew summary project:WebDev :ids
```

### Example 3: Debugging Investigation

**User Request:** "My app crashes with ECONNREFUSED, help debug"

**Phase 1: Decomposition**
```bash
task add "Debug ECONNREFUSED crash" project:Debugging priority:H due:today +debugging +urgent +investigation +nodejs
```

**Phase 2: Activation**
```bash
task 50 start
```

**Phase 3: Implementation**
```bash
task 50 annotate "Error occurs during PostgreSQL connection"
[Analyze error, check logs, test solutions]
task 50 annotate "Root cause: PostgreSQL service not running"
task 50 annotate "Solution: systemctl start postgresql + auto-start configuration"
```

**Phase 4: Completion**
```bash
task 50 done
timew summary :ids
```

### Example 4: Recurring Maintenance

**User Request:** "Script to clean Docker images weekly"

**Phase 1: Decomposition**
```bash
task add "Weekly Docker cleanup script" project:Maintenance recur:weekly due:friday priority:M +automation +docker +cleanup
```

**Phase 2: Activation**
```bash
task 55 start
```

**Phase 3: Implementation**
```bash
[Write docker-cleanup.sh with:
- Remove dangling images
- Remove unused volumes
- Remove stopped containers older than 7 days
- Log cleanup results]
```

**Phase 4: Completion**
```bash
task 55 done

# Note: Task will auto-generate next Friday
task next  # Shows next week's instance
```

## Handling Special Scenarios

### Scenario 1: User Has Existing Task

**User:** "Help me complete task 42: 'Optimize database queries'"

**Response:**
```bash
# Use user's existing task
task 42 start

[Provide optimization recommendations]

task 42 annotate "Added indexes on user_id and created_at columns"
task 42 annotate "Query time reduced from 2.3s to 45ms"
task 42 done
```

### Scenario 2: Mid-Task Scope Change

**User:** "Also add email notifications when backup completes"

**Response:**
```bash
# Modify existing task to reflect expanded scope
task 42 modify +email +notifications

# Or create dependent subtask
task add "Add email notifications to backup script" depends:42 project:DevOps priority:M +email +notifications
```

### Scenario 3: Blocked Task

**Situation:** Cannot proceed due to missing credentials/permissions

**Response:**
```bash
# Stop the task
task 50 stop

# Document the blocker
task 50 annotate "Blocked: Need AWS S3 credentials (AWS_ACCESS_KEY_ID, AWS_SECRET_ACCESS_KEY)"

# Mark as blocked
task 50 modify +blocked

# Inform user
"This task is blocked. Please provide AWS credentials to continue."
```

### Scenario 4: Multi-Session Work

**Session 1:**
```bash
task add "Build e-commerce platform - product catalog" project:Ecommerce priority:H due:3days +feature +catalog
task 60 start
[Implement product catalog]
task 60 done
```

**Session 2 (later):**
```bash
# Check existing work
task project:Ecommerce list

# Create related task
task add "Build e-commerce platform - shopping cart" project:Ecommerce depends:60 priority:H +feature +cart
task 61 start
[Implement shopping cart]
task 61 done
```

## Verification Requirements

Before delivering code, verify:

✅ **Task Created** - Task exists with proper attributes
```bash
task <ID> info  # Should show project, priority, tags, due date
```

✅ **Task Started** - Task is active
```bash
task active  # Should list your task
```

✅ **Time Tracking Active** - Timewarrior is running
```bash
timew  # Should show current tracking
```

✅ **Code Implemented** - Solution is complete and tested

✅ **Task Completed** - Task marked done
```bash
task completed | grep "<description>"
```

✅ **Time Summary Shown** - User sees time spent
```bash
timew summary :ids
```

## Enforcement Rules

### MANDATORY RULES:

1. **NO CODE BEFORE TASKS** - Always create tasks FIRST
2. **ALWAYS START TASKS** - Activate time tracking
3. **ALWAYS COMPLETE TASKS** - Mark as done when finished
4. **USE PROPER ATTRIBUTES** - Every task needs project:, priority:, due:, tags:
5. **RESPECT DEPENDENCIES** - Work in order
6. **ANNOTATE DECISIONS** - Document key choices
7. **HANDLE BLOCKERS** - Stop and mark as +blocked

### REFUSAL PROTOCOL:

If user requests code without proper task setup:

**DO NOT** write code immediately.

**INSTEAD:**

```
Before implementing this, I need to create a Taskwarrior task to track the work properly.

I'll decompose this as:

task add "[description]" project:[ProjectName] priority:M due:today +[tag1] +[tag2]

Then I'll start the task and implement the solution.

[Proceed with proper protocol]
```

## Integration Features

### Timewarrior Time Tracking

Automatically integrated when tasks are started:

```bash
# When you start a task
task <ID> start
# → Timewarrior begins tracking with task tags

# Check current tracking
timew

# View time reports
timew summary :ids              # Total per task
timew report :ids :week         # Weekly breakdown
timew day                       # Today's time
```

### Dependency Management

For complex projects with ordered steps:

```bash
# Create dependency chain
task add "Step 1" project:Project priority:H
task add "Step 2" depends:1 project:Project priority:M
task add "Step 3" depends:2 project:Project priority:M

# Only Step 1 is ready to start
task ready  # Shows tasks with no pending dependencies

# After completing Step 1, Step 2 becomes ready
```

### Task Modification

Update tasks as requirements evolve:

```bash
# Change priority
task <ID> modify priority:H

# Add tags
task <ID> modify +urgent +critical

# Update description
task <ID> modify description:"New description"

# Extend deadline
task <ID> modify due:+3days
```

## Quick Reference Commands

| Operation | Command |
|-----------|---------|
| Create task | `task add "description" project:Name priority:M due:today +tag1 +tag2` |
| Start task | `task <ID> start` |
| Stop task | `task <ID> stop` |
| Complete task | `task <ID> done` |
| View active | `task active` |
| View next tasks | `task next` |
| Task details | `task <ID> info` |
| Annotate task | `task <ID> annotate "note"` |
| Modify task | `task <ID> modify priority:H +tag` |
| List by project | `task project:ProjectName list` |
| Show completed | `task completed` |
| Current time tracking | `timew` |
| Time summary | `timew summary :ids` |

## Success Metrics

After completing work, provide:

```bash
# Individual task metrics
task <ID> info
timew summary :ids

# Project-level metrics
task project:<ProjectName> completed count
task project:<ProjectName> status:pending count

# Personal productivity
task completed count
task active count
timew summary :week
```

## Output Format

After completing all phases, provide user with:

```markdown
## Taskwarrior Integration Complete

### Tasks Created
- Task 42: "Create home directory backup script"
  - Project: DevOps
  - Priority: M
  - Due: 2025-10-23
  - Tags: scripting, automation, backup

### Implementation Summary
[Brief description of code delivered]

### Time Spent
- Task 42: 15 minutes

### Task Status
✅ Task 42 completed successfully

### Next Steps
[Any remaining work or follow-up tasks]
```

---

**This protocol ensures every coding activity is properly tracked, time-accounted, and managed through Taskwarrior's powerful task management system.**
