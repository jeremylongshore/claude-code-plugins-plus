# Workflow State Machine

## Workflow State Machine

```python
from enum import Enum
from dataclasses import dataclass, field
from typing import Dict, Optional, Callable, Any
from datetime import datetime
import json

class WorkflowState(Enum):
    CREATED = "created"
    VALIDATED = "validated"
    QUEUED = "queued"
    GENERATING = "generating"
    POST_PROCESSING = "post_processing"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"

@dataclass
class WorkflowJob:
    id: str
    prompt: str
    state: WorkflowState = WorkflowState.CREATED
    params: Dict = field(default_factory=dict)
    klingai_job_id: Optional[str] = None
    video_url: Optional[str] = None
    processed_url: Optional[str] = None
    error: Optional[str] = None
    metadata: Dict = field(default_factory=dict)
    created_at: datetime = field(default_factory=datetime.utcnow)
    updated_at: datetime = field(default_factory=datetime.utcnow)
    history: list = field(default_factory=list)

class WorkflowEngine:
    """State machine for video generation workflows."""

    # Valid state transitions
    TRANSITIONS = {
        WorkflowState.CREATED: [WorkflowState.VALIDATED, WorkflowState.FAILED],
        WorkflowState.VALIDATED: [WorkflowState.QUEUED, WorkflowState.FAILED],
        WorkflowState.QUEUED: [WorkflowState.GENERATING, WorkflowState.CANCELLED],
        WorkflowState.GENERATING: [WorkflowState.POST_PROCESSING, WorkflowState.FAILED],
        WorkflowState.POST_PROCESSING: [WorkflowState.COMPLETED, WorkflowState.FAILED],
        WorkflowState.COMPLETED: [],  # Terminal state
        WorkflowState.FAILED: [],     # Terminal state
        WorkflowState.CANCELLED: [],  # Terminal state
    }

    def __init__(self):
        self.handlers: Dict[WorkflowState, Callable] = {}
        self.on_transition: Optional[Callable] = None

    def register_handler(self, state: WorkflowState, handler: Callable):
        """Register a handler for a workflow state."""
        self.handlers[state] = handler

    def transition(self, job: WorkflowJob, new_state: WorkflowState, **kwargs):
        """Transition job to new state."""
        if new_state not in self.TRANSITIONS.get(job.state, []):
            raise ValueError(
                f"Invalid transition: {job.state.value} -> {new_state.value}"
            )

        old_state = job.state
        job.state = new_state
        job.updated_at = datetime.utcnow()
        job.history.append({
            "from": old_state.value,
            "to": new_state.value,
            "timestamp": job.updated_at.isoformat(),
            "data": kwargs
        })

        # Update job with any additional data
        for key, value in kwargs.items():
            if hasattr(job, key):
                setattr(job, key, value)

        if self.on_transition:
            self.on_transition(job, old_state, new_state)

    async def process(self, job: WorkflowJob) -> WorkflowJob:
        """Process job through workflow."""
        while job.state not in [
            WorkflowState.COMPLETED,
            WorkflowState.FAILED,
            WorkflowState.CANCELLED
        ]:
            handler = self.handlers.get(job.state)
            if not handler:
                raise RuntimeError(f"No handler for state: {job.state.value}")

            try:
                await handler(self, job)
            except Exception as e:
                self.transition(job, WorkflowState.FAILED, error=str(e))

        return job
```
