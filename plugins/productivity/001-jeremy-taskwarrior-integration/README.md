# 001-Jeremy Taskwarrior Integration

**Enforces complete Taskwarrior integration protocol for ALL coding tasks with automatic task lifecycle management and time tracking.**

## What It Does

This plugin **mandates** that EVERY coding activity follows the complete Taskwarrior integration protocol:

1. **Task Decomposition** - Break down work into trackable tasks BEFORE writing code
2. **Task Activation** - Start tasks to begin automatic time tracking
3. **Code Implementation** - Write code with proper annotations and blocker handling
4. **Task Completion** - Mark tasks as done and show time summaries

**CRITICAL: NO CODE IS WRITTEN until Taskwarrior tasks are created and started.**

## Your Workflow Problem (Solved)

**Problem:** You want to track ALL development work in Taskwarrior, but it's easy to forget to create tasks, start them, annotate progress, and complete them properly.

**Solution:** This plugin automatically enforces the complete Taskwarrior protocol whenever you mention "taskwarrior" or start any coding task, ensuring 100% compliance with proper task tracking.

## Use Cases

### Use Case 1: Simple Script Creation

**Your Request:**
> "Help me with taskwarrior - create a Bash backup script"

**What The Plugin Does:**
```bash
# 1. Creates task
task add "Create Bash backup script" project:DevOps priority:M due:today +scripting +automation +backup

# 2. Starts task
task 42 start

# 3. Implements code
[Writes backup.sh with error handling]

# 4. Completes task
task 42 done
timew summary :ids

Result: 15 minutes tracked, task completed
```

### Use Case 2: Complex Multi-Step Project

**Your Request:**
> "Build a REST API with JWT authentication and PostgreSQL using taskwarrior"

**What The Plugin Does:**
```bash
# Decomposes into dependent tasks
task add "Build REST API with auth" project:WebDev priority:H due:5days +api +backend
task add "Design PostgreSQL schema" depends:43 priority:H +database
task add "Implement JWT auth" depends:44 priority:H +security +jwt
task add "Create CRUD endpoints" depends:45 priority:M +crud
task add "Write API docs" depends:46 priority:L +documentation

# Works through each task sequentially
task 44 start
[Implements schema]
task 44 done

task 45 start
[Implements JWT]
task 45 done

# ... continues through dependency chain
```

### Use Case 3: Debugging Investigation

**Your Request:**
> "My app crashes with ECONNREFUSED - use taskwarrior to track the debugging"

**What The Plugin Does:**
```bash
task add "Debug ECONNREFUSED crash" project:Debugging priority:H due:today +debugging +urgent
task 50 start
task 50 annotate "Error in PostgreSQL connection"
task 50 annotate "Root cause: PostgreSQL not running"
task 50 annotate "Solution: systemctl start postgresql"
[Provides fix]
task 50 done
```

## Installation

```bash
# Add marketplace
/plugin marketplace add jeremylongshore/claude-code-plugins

# Install plugin
/plugin install 001-jeremy-taskwarrior-integration@claude-code-plugins-plus
```

## How to Use

### Method 1: Agent Skill (Automatic Activation)

Just mention "taskwarrior" in your request:

- "Help me with taskwarrior - create a Python scraper"
- "Use taskwarrior to track this: build authentication system"
- "Track this work in tw - refactor database queries"

**The Agent Skill activates automatically** and enforces the complete protocol.

### Method 2: Manual Command

Run explicit enforcement:

```bash
/taskwarrior-protocol
```

Then make your coding request. The protocol will be applied.

## What Gets Tracked

### 1. Task Attributes (ALL Required)

Every task includes:
- **project:** Category (project:DevOps, project:WebDev, project:DataScience)
- **priority:** H/M/L based on urgency
- **due:** Realistic deadline
- **tags:** At least 2-3 relevant tags

### 2. Time Tracking (Automatic via Timewarrior)

- Automatic start when `task start` is run
- Automatic stop when `task done` or `task stop`
- Tagged with task metadata
- Full time reports available

### 3. Task Annotations

- Key decisions documented
- Blockers identified
- Solutions noted
- Progress tracked

### 4. Dependency Chains

- Complex projects broken into linked subtasks
- Sequential execution enforced
- Dependencies automatically managed

## Task Priority Guidelines

The plugin assigns priority using this matrix:

**priority:H (High) - Used for:**
- Blocking other work
- Production outages
- Security vulnerabilities
- Hard deadlines within 24-48 hours

**priority:M (Medium) - Used for:**
- Normal feature development (DEFAULT)
- Non-blocking improvements
- Deadlines within 3-7 days

**priority:L (Low) - Used for:**
- Nice-to-have enhancements
- Documentation updates
- No specific deadline

## Tag Taxonomy

### Work Type Tags

- `+feature` - New functionality
- `+bugfix` - Fixing issues
- `+refactor` - Code restructuring
- `+testing` - Test creation
- `+documentation` - Docs
- `+deployment` - Release work
- `+security` - Security-related
- `+performance` - Optimization
- `+debugging` - Investigation
- `+maintenance` - Routine upkeep
- `+automation` - Scripting/tooling

### Technology Tags

- `+python`, `+javascript`, `+bash`, `+typescript`
- `+docker`, `+kubernetes`, `+cicd`
- `+postgresql`, `+redis`, `+api`
- `+fastapi`, `+react`, `+nextjs`

### Status Tags

- `+blocked` - Cannot proceed
- `+urgent` - Immediate attention
- `+waiting` - Awaiting input
- `+review` - Ready for review

## Your Taskwarrior Command Examples

The plugin uses these patterns from your workflow:

### Repository / CI-CD Tasks

```bash
task add "Audit GitHub Actions workflows" project:devops tags:ci,release priority:H due:2025-10-12
task add "Bump Docker base images" project:devops tags:docker,security priority:M
task add "Lock dependency versions with Renovate" project:devops tags:dependencies priority:M
```

### Cloud / Infrastructure Tasks

```bash
task add "Confirm Cloud Run service quotas" project:infra tags:gcp,quotas due:2025-10-15
task add "Check Firestore indexes" project:infra tags:gcp,db priority:H
task add "Rotate API keys and secrets" project:infra tags:security,keys due:2025-10-20
```

### Documentation / Standards Tasks

```bash
task add "Update CLAUDE.md with directory standards" project:docs tags:standards,claude
task add "Add PRD template to claudes-docs" project:docs tags:prd,template
task add "Write ADR for OAuth2 token refresh" project:docs tags:adr,auth priority:H
```

### Product / Features Tasks

```bash
task add "Implement soccer stats sync" project:hustle tags:feature,soccer priority:H
task add "Test DiagnosticPro intake form" project:diagnostic-pro tags:form,testing
task add "QA Hustle PWA on mobile" project:hustle tags:pwa,mobile due:2025-10-18
```

## Complete Workflow Example

**Your Request:**
> "Help with taskwarrior - implement FastAPI authentication"

**Plugin Response:**

```markdown
## Phase 1: Task Decomposition

Creating Taskwarrior tasks for FastAPI authentication:

task add "Implement FastAPI auth system" project:WebDev priority:H due:2days +fastapi +auth +security
task add "JWT token generation" depends:1 priority:H +jwt
task add "Login/logout endpoints" depends:2 priority:M +endpoints
task add "Password hashing with bcrypt" depends:3 priority:M +security
task add "Authentication tests" depends:4 priority:M +testing

## Phase 2: Task Activation

task 1 start
timew  # Tracking started: 2025-10-23 10:30:00

## Phase 3: Implementation

[Full FastAPI authentication code with:
- JWT token generation
- Secure password hashing
- Login/logout endpoints
- Error handling
- Tests]

task 1 annotate "Using python-jose for JWT"
task 1 annotate "Bcrypt rounds set to 12 for security"

## Phase 4: Completion

task 1 done

### Summary
- Time spent: 45 minutes
- Project: WebDev
- Tags: fastapi, auth, security
- Status: ✅ Completed

### Next Tasks
- Task 2: JWT token generation (ready to start)
```

## Handling Special Scenarios

### Scenario 1: Working with Your Existing Tasks

**Your Request:**
> "Help me complete task 42: 'Optimize database queries'"

**Plugin Response:**
```bash
# Uses your existing task
task 42 start
[Provides optimization recommendations]
task 42 annotate "Added indexes on user_id and created_at"
task 42 done
```

### Scenario 2: Mid-Task Scope Change

**Your Request:**
> "Also add email notifications"

**Plugin Response:**
```bash
# Expands scope
task 42 modify +email +notifications
task add "Email notification system" depends:42 +email +feature
```

### Scenario 3: Blocked Work

**Situation:** Missing credentials

**Plugin Response:**
```bash
task 50 stop
task 50 annotate "Blocked: Need AWS credentials"
task 50 modify +blocked
"This task is blocked. Please provide AWS credentials to continue."
```

### Scenario 4: Multi-Session Work

**Session 1:**
```bash
task add "E-commerce - product catalog" project:Ecommerce +feature
task 60 start
[Implements catalog]
task 60 done
```

**Session 2 (later):**
```bash
task project:Ecommerce list  # Check existing work
task add "E-commerce - shopping cart" depends:60 project:Ecommerce +feature
task 61 start
```

## Time Tracking Reports

After working, view comprehensive reports:

```bash
# Time spent per task
timew summary :ids

# This week's breakdown
timew report :ids :week

# Today's work
timew day

# Most-used tags
timew tags

# Project-level time
timew summary project:WebDev :ids
```

## Task Management Best Practices

### ✅ DO:

- Use the plugin for ALL coding activities
- Let tasks accumulate for historical record
- Leverage annotations for important decisions
- Use proper priority levels (don't overuse H)
- Create dependencies for related work
- Review `task next` regularly

### ❌ DON'T:

- Skip the plugin for "quick" tasks
- Use generic descriptions
- Forget to complete tasks
- Leave tasks hanging when switching contexts
- Ignore the dependency system
- Use priority:H for everything

## Quick Reference Commands

| Operation | Command |
|-----------|---------|
| **Create task** | `task add "description" project:Name priority:M due:today +tag1 +tag2` |
| **Start task** | `task <ID> start` |
| **Stop task** | `task <ID> stop` |
| **Complete task** | `task <ID> done` |
| **View active** | `task active` |
| **View next** | `task next` |
| **Annotate** | `task <ID> annotate "note"` |
| **Modify** | `task <ID> modify priority:H +tag` |
| **Task info** | `task <ID> info` |
| **By project** | `task project:ProjectName list` |
| **Completed** | `task completed` |
| **Time tracking** | `timew` |
| **Time summary** | `timew summary :ids` |
| **Weekly report** | `timew report :ids :week` |

## Integration with Other Tools

### VS Code Integration

- Install "Taskwarrior" extension by Alex Lushpai
- Tasks created by the plugin appear in sidebar
- Start/stop directly from VS Code

### Git Workflow

Reference task IDs in commit messages:
```bash
git commit -m "feat: implement auth system (task 42)"
```

### CI/CD Integration

Create tasks for deployments:
```bash
task add "Deploy v1.2.0 to production" project:Deployment +release +production
```

### Team Collaboration

Share Taskwarrior server for team visibility:
- Tasks created by plugin visible to team
- Annotations serve as communication
- Dependencies coordinate work

## Success Metrics

Track plugin effectiveness:

```bash
# Total tasks completed
task count status:completed

# Average task duration
timew summary :ids | grep Total

# Most productive project
task summary

# Task completion rate
task completed due.before:today count
```

## Prerequisites

- **Taskwarrior** installed (`sudo apt install task` or `brew install task`)
- **Timewarrior** installed for time tracking (optional but recommended: `sudo apt install timew`)
- Basic familiarity with Taskwarrior commands

## Troubleshooting

### Issue: "Task not tracking time"

**Solution:**
```bash
# Verify Timewarrior is installed
which timew

# Check if task is active
task active

# Manually start tracking
timew start +tag1 +tag2
```

### Issue: "Can't find task ID"

**Solution:**
```bash
# List all tasks
task list

# Search by keyword
task /keyword/ list

# Show recent completions
task completed
```

### Issue: "Forgot to start task before coding"

**Solution:**
```bash
# Start retroactively
task <ID> start

# Adjust Timewarrior manually
timew track yesterday 2:00pm - 3:30pm +project +feature
```

## License

MIT License - See LICENSE file

## Support

- **Documentation:** This README + SKILL.md
- **Issues:** https://github.com/jeremylongshore/claude-code-plugins/issues
- **Taskwarrior Docs:** https://taskwarrior.org/docs/
- **Timewarrior Docs:** https://timewarrior.net/docs/

---

**Built by:** Jeremy Longshore
**Version:** 1.0.0
**Category:** Productivity
**Type:** Task Management Integration

**Perfect for:** Developers who want complete visibility into their coding work with automatic task tracking, time accounting, and dependency management through Taskwarrior.
