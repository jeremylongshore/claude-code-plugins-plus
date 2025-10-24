---
name: 001-jeremy-taskwarrior-integration
description: |
  Enforces complete Taskwarrior integration protocol for ALL coding tasks. Activates automatically when user mentions "taskwarrior", "task warrior", "tw", or discusses task management. Decomposes all coding work into properly tracked Taskwarrior tasks with full lifecycle: task add → task start → implementation → task done. Integrates with Timewarrior for automatic time tracking.
---

## What This Skill Does

This skill **enforces mandatory Taskwarrior integration** for ALL coding activities. It ensures every piece of work is:

1. **Decomposed** into trackable Taskwarrior tasks BEFORE code is written
2. **Tracked** with proper attributes (project, priority, due date, tags)
3. **Time-accounted** via automatic Timewarrior integration
4. **Dependency-managed** for complex multi-step projects
5. **Completed** with proper task lifecycle (add → start → done)

**CRITICAL: NO CODE IS WRITTEN until Taskwarrior tasks are created and started.**

## When This Skill Activates

Trigger this skill when you mention:
- "taskwarrior"
- "task warrior"
- "tw" (as abbreviation)
- "create a task for this"
- "track this work"
- "add to taskwarrior"
- "start a task"
- "task management"
- "time tracking"

## Complete Taskwarrior Integration Protocol

### Phase 1: Task Decomposition (MANDATORY FIRST STEP)

**Before writing ANY code**, decompose the request into Taskwarrior tasks:

**For Simple Requests (1 task):**
```bash
task add "Brief description of work" project:ProjectName priority:H/M/L due:today/tomorrow/YYYY-MM-DD +tag1 +tag2
```

**For Complex Requests (multiple tasks with dependencies):**
```bash
# Parent task
task add "Main project goal" project:ProjectName priority:H due:3days +architecture +planning

# Subtasks with dependencies
task add "Subtask 1" project:ProjectName depends:1 priority:M +implementation
task add "Subtask 2" project:ProjectName depends:2 priority:M +testing
task add "Subtask 3" project:ProjectName depends:3 priority:L +documentation
```

**Required Task Attributes:**
- **project:** Categorize the work (e.g., project:DevOps, project:WebDev)
- **priority:** H (high), M (medium), or L (low) based on urgency
- **due:** Realistic deadline (today, tomorrow, YYYY-MM-DD, or relative like 3days)
- **tags:** At least 2 relevant tags (+feature, +bugfix, +refactor, +testing, +deployment, +security, etc.)

### Phase 2: Task Activation & Time Tracking

**After creating tasks**, activate them to start time tracking:

```bash
# Start the first task in the dependency chain
task <ID> start

# Verify task is active
task active

# Timewarrior should automatically begin tracking
timew
```

**What happens:**
- Taskwarrior marks task as started
- Timewarrior begins tracking time spent
- Task appears in `task active` list
- Urgency score increases for started tasks

### Phase 3: Code Implementation

**Now and ONLY now** proceed with writing code:

1. Implement the solution following best practices
2. Annotate task with key decisions or blockers:
```bash
task <ID> annotate "Decision: Using FastAPI over Flask for async support"
task <ID> annotate "Blocker: Waiting for API credentials"
```

3. If blocked, stop the task temporarily:
```bash
task <ID> stop
task <ID> modify +blocked
```

4. If scope changes mid-implementation:
```bash
task <ID> modify +additional_tag description:"Updated description"
```

### Phase 4: Task Completion

**After code is delivered and verified**, complete the task:

```bash
# Complete the task
task <ID> done

# Timewarrior automatically stops tracking
# View time summary for this task
timew summary :ids

# Check if dependent tasks are now unblocked
task next
```

**Completion Checklist:**
- ✅ Code is written and tested
- ✅ Documentation is updated (if applicable)
- ✅ Task annotations reflect final state
- ✅ Any blockers are resolved or escalated
- ✅ Time tracking is accurate

### Phase 5: Verification & Reporting

**After completing tasks**, provide summary:

```bash
# Show completed task details
task <ID> info

# Show time spent
timew summary :ids

# Show remaining work
task next
```

## Task Decomposition Examples

### Example 1: Simple Single-File Script

**User Request:** "Create a Bash script that backs up my home directory"

**Task Decomposition:**
```bash
task add "Create home directory backup script" project:DevOps priority:M due:today +scripting +automation +backup
```

**Lifecycle:**
```bash
task 42 start
[Write backup.sh script]
task 42 done
timew summary :ids
```

### Example 2: Complex Multi-Component Feature

**User Request:** "Build a REST API with authentication, user management, and PostgreSQL"

**Task Decomposition:**
```bash
# Parent task
task add "Build FastAPI REST API with auth" project:WebDev priority:H due:5days +api +backend

# Dependent subtasks
task add "Design PostgreSQL schema" project:WebDev depends:43 priority:H due:1day +database +design
task add "Implement JWT authentication" project:WebDev depends:44 priority:H due:2days +auth +security
task add "Create user management endpoints" project:WebDev depends:45 priority:M due:3days +crud +endpoints
task add "Write API documentation" project:WebDev depends:46 priority:L due:5days +documentation +openapi
task add "Deploy to staging environment" project:WebDev depends:47 priority:M due:5days +deployment +staging
```

**Lifecycle:**
```bash
task 44 start  # Start with database schema
[Design and implement schema]
task 44 done

task 45 start  # Next: authentication
[Implement JWT auth]
task 45 done

# Continue through dependency chain...
```

### Example 3: Debugging Investigation

**User Request:** "My Node.js app crashes with ECONNREFUSED"

**Task Decomposition:**
```bash
task add "Debug ECONNREFUSED error in Node.js app" project:Debugging priority:H due:today +debugging +nodejs +urgent +investigation
```

**Lifecycle with Annotations:**
```bash
task 50 start
task 50 annotate "Error occurs during PostgreSQL connection"
task 50 annotate "Root cause: PostgreSQL service not running"
task 50 annotate "Solution: systemctl start postgresql"
[Provide debugging steps and code fixes]
task 50 done
```

### Example 4: Recurring Maintenance Task

**User Request:** "Create a script I need to run weekly to clean Docker images"

**Task Decomposition:**
```bash
task add "Weekly Docker cleanup script" project:Maintenance recur:weekly due:friday priority:M +automation +docker +cleanup
```

**Lifecycle:**
```bash
task 55 start
[Write docker-cleanup.sh script]
task 55 done

# Future instances auto-generate every Friday
task next  # Will show next week's instance
```

## Task Priority Guidelines

Use this urgency matrix to assign priority:

**priority:H (High) - Use when:**
- Blocking other work
- Production outage or critical bug
- Security vulnerability
- Hard deadline within 24-48 hours
- Explicitly marked as urgent by user

**priority:M (Medium) - Use when:**
- Normal feature development
- Non-blocking improvements
- Deadline within 3-7 days
- Standard maintenance work
- Default for most tasks

**priority:L (Low) - Use when:**
- Nice-to-have enhancements
- Documentation updates
- Refactoring for cleanliness (not performance)
- No specific deadline
- Can be deferred without impact

## Tag Taxonomy

**Common Project Tags:**
- `+feature` - New functionality
- `+bugfix` - Fixing existing issues
- `+refactor` - Code restructuring
- `+testing` - Test creation/execution
- `+documentation` - Docs and comments
- `+deployment` - Release and infrastructure
- `+security` - Security-related work
- `+performance` - Optimization work
- `+debugging` - Investigation and diagnosis
- `+maintenance` - Routine upkeep
- `+automation` - Scripting and tooling
- `+infrastructure` - DevOps and systems

**Technology Tags:**
- `+python`, `+javascript`, `+bash`, `+typescript`
- `+docker`, `+kubernetes`, `+cicd`
- `+postgresql`, `+redis`, `+mongodb`
- `+fastapi`, `+react`, `+nextjs`

**Status Tags:**
- `+blocked` - Cannot proceed (annotate reason)
- `+urgent` - Needs immediate attention
- `+waiting` - Awaiting external input
- `+review` - Ready for review

## Handling Special Scenarios

### Scenario 1: Mid-Task Scope Change

If requirements change while working:

```bash
# Modify existing task
task <ID> modify +new_tag description:"Updated description"

# Or create dependent subtask for additional work
task add "Additional scope: Email notifications" depends:<ID> project:SameProject +feature
```

### Scenario 2: Blocked Work

If encountering blockers (missing credentials, API limits, permissions):

```bash
# Stop the task
task <ID> stop

# Annotate the blocker
task <ID> annotate "Blocked: Need AWS credentials from ops team"

# Mark as blocked
task <ID> modify +blocked

# Explain to user what's needed to unblock
```

### Scenario 3: Multi-Session Work

For work spanning multiple conversations:

**Session 1:**
```bash
task add "Build e-commerce platform - product catalog" project:Ecommerce priority:H +feature
task 60 start
[Implement product catalog]
task 60 done
```

**Session 2 (later):**
```bash
# Check existing project tasks
task project:Ecommerce status:pending

# Create related task
task add "Build e-commerce platform - shopping cart" project:Ecommerce depends:60 priority:H +feature
task 61 start
[Implement shopping cart]
task 61 done
```

### Scenario 4: Working with User's Existing Tasks

If user references an existing Taskwarrior task:

**User:** "Help me complete task 42: 'Optimize database queries'"

**Response:**
```bash
# Start user's existing task
task 42 start

[Provide optimization recommendations and code]

# Complete user's task
task 42 done

# Show results
task 42 info
timew summary :ids
```

## Integration with Timewarrior

Taskwarrior automatically integrates with Timewarrior when configured. Here's what happens:

**When you start a task:**
```bash
task <ID> start
# Timewarrior begins tracking with tags from the task
```

**Check current tracking:**
```bash
timew  # Shows what's currently being tracked
task active  # Shows active Taskwarrior tasks
```

**Stop tracking (when you stop or complete a task):**
```bash
task <ID> stop  # Pauses tracking
task <ID> done  # Stops tracking and completes task
```

**View time reports:**
```bash
timew summary :ids              # Total time per task
timew report :ids :week         # This week's breakdown
timew tags                      # Most-used tags
timew day                       # Today's time usage
```

## Workflow Enforcement Rules

### MANDATORY RULES:

1. **NO CODE BEFORE TASKS** - Always run `task add` BEFORE writing any code
2. **ALWAYS START TASKS** - Run `task <ID> start` to activate time tracking
3. **ALWAYS COMPLETE TASKS** - Run `task <ID> done` when work is delivered
4. **USE PROPER ATTRIBUTES** - Every task needs project:, priority:, due:, and tags:
5. **RESPECT DEPENDENCIES** - Work tasks in order defined by `depends:` relationships
6. **ANNOTATE DECISIONS** - Use `task <ID> annotate` to document key choices
7. **HANDLE BLOCKERS EXPLICITLY** - Stop tasks and mark as +blocked when stuck

### VERIFICATION CHECKLIST:

Before delivering code, confirm:
- ✅ Task was created with proper attributes
- ✅ Task was started (appears in `task active`)
- ✅ Time tracking is running (verify with `timew`)
- ✅ Code is implemented and tested
- ✅ Task is completed with `task done`
- ✅ Time summary is shown

## Refusing Non-Compliant Requests

If user asks for code without mentioning Taskwarrior, **proactively enforce the protocol**:

**User:** "Write me a Python script to parse CSV files"

**Your Response:**
```
Before I write the code, I need to create a Taskwarrior task to track this work properly.

I'll decompose this as:
task add "Create CSV parser Python script" project:DataProcessing priority:M due:today +python +scripting +parsing

Then I'll start the task and implement the solution.

[Proceed with task creation → task start → code implementation → task done]
```

## Success Metrics

After completing work, provide these metrics:

```bash
# Task details
task <ID> info

# Time spent
timew summary :ids

# Project progress
task project:<ProjectName> completed
task project:<ProjectName> status:pending

# Personal productivity
task completed count
task active count
```

## Quick Reference Commands

| Operation | Command |
|-----------|---------|
| **Create task** | `task add "description" project:Name priority:M due:today +tag1 +tag2` |
| **Start task** | `task <ID> start` |
| **Stop task** | `task <ID> stop` |
| **Complete task** | `task <ID> done` |
| **View active tasks** | `task active` |
| **View next tasks** | `task next` |
| **Modify task** | `task <ID> modify priority:H +new_tag` |
| **Annotate task** | `task <ID> annotate "note"` |
| **View task details** | `task <ID> info` |
| **List by project** | `task project:ProjectName list` |
| **Show time tracking** | `timew` |
| **Time summary** | `timew summary :ids` |
| **Weekly report** | `timew report :ids :week` |

## Expected User Workflow

**Typical Interaction:**

**User:** "I need help with taskwarrior - create a FastAPI authentication system"

**Your Response:**
```
I'll enforce the Taskwarrior integration protocol for this work.

## Phase 1: Task Decomposition

Creating tasks for FastAPI authentication system:

task add "Build FastAPI authentication system" project:WebDev priority:H due:2days +fastapi +auth +security +backend
task add "Implement JWT token generation" project:WebDev depends:1 priority:H +jwt +auth
task add "Create login/logout endpoints" project:WebDev depends:2 priority:M +endpoints +api
task add "Add password hashing with bcrypt" project:WebDev depends:3 priority:M +security +passwords
task add "Write authentication tests" project:WebDev depends:4 priority:M +testing +pytest

## Phase 2: Task Activation

task 1 start
timew  # Verify tracking started

## Phase 3: Implementation

[Now I'll implement the authentication system...]

[Provide complete FastAPI auth code]

## Phase 4: Completion

task 1 done
timew summary :ids

Total time: 45 minutes
Next task: Implement JWT token generation (task 2)
```

## Best Practices

### ✅ DO:
- Create tasks for EVERY coding activity, no matter how small
- Use descriptive task names that explain the "what" and "why"
- Set realistic due dates based on complexity
- Add multiple relevant tags for better filtering
- Annotate tasks with important decisions or blockers
- Leverage the dependency system for related work
- Complete tasks when work is done (don't leave tasks hanging)
- Review `task next` regularly to prioritize work

### ❌ DON'T:
- Skip task creation for "quick" tasks
- Write code before creating and starting tasks
- Use generic descriptions ("Fix bug" vs. "Fix OAuth redirect loop")
- Ignore the dependency system
- Leave tasks incomplete after delivering code
- Forget to stop/complete tasks when switching contexts
- Use priority:H for everything (dilutes urgency)

## Troubleshooting

### Issue: "Task not tracking time"

**Solution:**
```bash
# Verify Timewarrior is installed
which timew

# Check if task is active
task active

# Manually start tracking if needed
timew start +tag1 +tag2
```

### Issue: "Can't find task ID"

**Solution:**
```bash
# List all tasks
task list

# Show task details by description search
task /keyword/ list

# Show recently completed tasks
task completed
```

### Issue: "Forgot to start task before coding"

**Solution:**
```bash
# Start the task now (retroactively)
task <ID> start

# Manually adjust Timewarrior if needed
timew track yesterday 2:00pm - 3:30pm +projecttag +featuretag
```

## Integration with Your Workflow

This skill integrates seamlessly with:
- **VS Code Taskwarrior extensions** - See tasks in your editor sidebar
- **CI/CD pipelines** - Auto-create tasks for deployments
- **Git workflows** - Reference task IDs in commit messages
- **Team collaboration** - Shared Taskwarrior server for team visibility
- **Reporting tools** - Export to JSON for dashboards

## Summary

This skill enforces a **mandatory, comprehensive Taskwarrior integration** for ALL coding activities. It ensures:

✅ Every piece of work is tracked as a task
✅ Time spent is automatically accounted via Timewarrior
✅ Complex projects are decomposed into manageable, linked subtasks
✅ Complete audit trail of all work performed
✅ Proper prioritization and deadline management
✅ Full lifecycle from creation → activation → implementation → completion

**NO CODE GETS WRITTEN without following the complete Taskwarrior protocol.**
