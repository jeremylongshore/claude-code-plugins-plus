# klingai-async-workflows

> Build asynchronous video generation workflows

## Directory Structure

```
klingai-async-workflows/
├── 📄 SKILL.md                    # Main skill definition with YAML frontmatter
└── 📂 examples/                   # Optional examples directory
    ├── 🐍 state_machine.py        # Workflow state machine
    ├── 🐍 workflow_engine.py      # Async workflow orchestrator
    └── 🐍 celery_tasks.py         # Celery task definitions
```

## File Descriptions

| File | Type | Purpose |
|------|------|---------|
| `SKILL.md` | 📄 Markdown | Skill definition with async workflow patterns |
| `state_machine.py` | 🐍 Python | State machine for workflow states |
| `workflow_engine.py` | 🐍 Python | Orchestrate multi-step workflows |
| `celery_tasks.py` | 🐍 Python | Celery-based async tasks |

## Summary

**Category:** cicd
**Target Audience:** Developer building pipelines
**Trigger Phrases:** `klingai workflow`, `kling ai pipeline`, `async klingai`, `klingai orchestration`

### What This Skill Does

This skill teaches building async video generation workflows. It covers:

- State machine design for workflows
- Multi-step pipeline orchestration
- Integration with Celery/Redis
- Workflow persistence and recovery
- Error handling and compensation
- Parallel and sequential step patterns

### Technical Success Criteria

- State machine driven workflow processing
- Recoverable workflows after failures
- Proper step orchestration

### Business Success Criteria

- Scalable and maintainable video pipelines
- Reliable multi-step video processing
- Clear workflow visibility

## Related Skills

- `klingai-webhook-config` - Webhook-triggered workflows
- `klingai-batch-processing` - Batch workflow patterns
- `klingai-storage-integration` - Storage in workflows
