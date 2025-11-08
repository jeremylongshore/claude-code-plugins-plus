# Sugar 🍰 - Claude Code Plugin

Transform your Claude Code experience with autonomous AI development capabilities!

## What is Sugar?

Sugar is a premier Claude Code plugin that brings true autonomous development to your projects. Unlike simple automation plugins, Sugar provides:

- **🤖 Autonomous Task Execution** - Let AI handle complex, multi-step development work
- **📋 Enterprise Task Management** - Persistent SQLite-backed task tracking with rich metadata
- **🎯 Intelligent Agent Orchestration** - Specialized agents for different development aspects
- **🔍 Automatic Work Discovery** - Finds work from error logs, GitHub issues, and code quality metrics
- **👥 Team Collaboration** - Shared task queues with multi-project support

## Quick Start

### Prerequisites

1. **Install Sugar CLI** (if not already installed):
   ```bash
   pip install sugarai
   ```

2. **Initialize in your project**:
   ```bash
   cd /path/to/your/project
   sugar init
   ```

### Installation

Install the Sugar plugin via Claude Code:

```
/plugin install sugar
```

### Basic Usage

#### Create Tasks
```
/sugar-task "Implement user authentication" --type feature --priority 4
```

#### View Status
```
/sugar-status
```

#### Start Autonomous Mode
```
/sugar-run --dry-run  # Test first
/sugar-run            # Start autonomous development
```

## Features

### Slash Commands

- `/sugar-task` - Create comprehensive tasks with rich context
- `/sugar-status` - View system status and task queue
- `/sugar-review` - Review and manage pending tasks
- `/sugar-run` - Start autonomous execution mode
- `/sugar-analyze` - Analyze codebase for potential work

### Specialized Agents

- **sugar-orchestrator** - Coordinates autonomous development workflows
- **task-planner** - Strategic task planning and breakdown
- **quality-guardian** - Code quality and testing enforcement
- **autonomous-executor** - Handles autonomous task execution

### Automatic Task Discovery

Sugar automatically discovers work from:
- Error logs and crash reports
- GitHub issues and pull requests
- Code quality metrics and technical debt
- Missing test coverage
- Documentation gaps

## Advanced Features

### Rich Task Context

Create tasks with comprehensive metadata:

```bash
sugar add "User Dashboard Redesign" --json --description '{
  "priority": 5,
  "type": "feature",
  "context": "Complete overhaul of user dashboard for better UX",
  "business_context": "Improve user engagement and reduce support tickets",
  "technical_requirements": ["responsive design", "accessibility compliance"],
  "agent_assignments": {
    "ux_design_specialist": "UI/UX design leadership",
    "frontend_developer": "Implementation and optimization",
    "qa_test_engineer": "Testing and validation"
  },
  "success_criteria": ["mobile responsive", "passes accessibility audit"]
}'
```

### Custom Task Types

Define your own task types beyond the defaults:

```bash
sugar task-type add security_audit \
  --name "Security Audit" \
  --description "Security vulnerability scanning" \
  --agent "tech-lead" \
  --emoji "🔒"
```

### Multi-Project Support

Sugar maintains isolated instances per project:
- Separate `.sugar/` directory in each project
- Independent task queues and execution
- No interference between projects

## Configuration

Sugar auto-generates `.sugar/config.yaml` with sensible defaults. Key settings:

```yaml
sugar:
  loop_interval: 300           # 5 minutes between autonomous cycles
  max_concurrent_work: 3       # Execute multiple tasks per cycle
  dry_run: false               # Set to true for safe testing

  claude:
    enable_agents: true        # Enable Claude agent mode selection
    use_structured_requests: true
```

## Safety Features

- **Dry Run Mode** - Test without making changes
- **Project Isolation** - Clean `.sugar/` directory structure
- **Graceful Shutdown** - Handles interrupts cleanly
- **Audit Trail** - Complete history of all autonomous actions

## Documentation

- [Complete Documentation](https://github.com/cdnsteve/sugar/tree/main/docs)
- [Quick Start Guide](https://github.com/cdnsteve/sugar/blob/main/docs/user/quick-start.md)
- [CLI Reference](https://github.com/cdnsteve/sugar/blob/main/docs/user/cli-reference.md)
- [GitHub Integration](https://github.com/cdnsteve/sugar/blob/main/docs/user/github-integration.md)

## Support

- **Issues**: [GitHub Issues](https://github.com/cdnsteve/sugar/issues)
- **Discussions**: [GitHub Discussions](https://github.com/cdnsteve/sugar/discussions)
- **Documentation**: [docs.roboticforce.io/sugar](https://docs.roboticforce.io/sugar)

## License

MIT License - see [LICENSE](https://github.com/cdnsteve/sugar/blob/main/LICENSE)

---

**Sugar 🍰 v1.9.1** - Transform any project into an autonomous development environment.

⚠️ **Disclaimer**: Sugar is an independent third-party tool. "Claude," "Claude Code," and related marks are trademarks of Anthropic, Inc. Sugar is not affiliated with, endorsed by, or sponsored by Anthropic, Inc.
