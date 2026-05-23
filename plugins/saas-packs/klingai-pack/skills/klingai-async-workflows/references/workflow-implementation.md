# Workflow Implementation

## Workflow Implementation

```python
import asyncio
import aiohttp
import os

async def validate_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Validate job parameters."""
    # Validation logic
    if not job.prompt or len(job.prompt) < 10:
        raise ValueError("Prompt too short")

    if len(job.prompt) > 2000:
        raise ValueError("Prompt too long")

    # Validate params
    duration = job.params.get("duration", 5)
    if duration not in [5, 10]:
        raise ValueError(f"Invalid duration: {duration}")

    engine.transition(job, WorkflowState.VALIDATED)

async def queue_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Queue job for processing."""
    # In production, this would add to a real queue
    # For now, transition directly
    engine.transition(job, WorkflowState.QUEUED)
    engine.transition(job, WorkflowState.GENERATING)

async def generate_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Submit to Kling AI and wait for completion."""
    api_key = os.environ["KLINGAI_API_KEY"]

    async with aiohttp.ClientSession() as session:
        # Submit job
        async with session.post(
            "https://api.klingai.com/v1/videos/text-to-video",
            headers={
                "Authorization": f"Bearer {api_key}",
                "Content-Type": "application/json"
            },
            json={
                "prompt": job.prompt,
                **job.params
            }
        ) as response:
            if response.status != 200:
                raise RuntimeError(f"API error: {response.status}")

            data = await response.json()
            job.klingai_job_id = data["job_id"]

        # Poll for completion
        while True:
            async with session.get(
                f"https://api.klingai.com/v1/videos/{job.klingai_job_id}",
                headers={"Authorization": f"Bearer {api_key}"}
            ) as response:
                data = await response.json()

                if data["status"] == "completed":
                    job.video_url = data["video_url"]
                    break
                elif data["status"] == "failed":
                    raise RuntimeError(data.get("error", "Generation failed"))

            await asyncio.sleep(5)

    engine.transition(job, WorkflowState.POST_PROCESSING)

async def post_process_handler(engine: WorkflowEngine, job: WorkflowJob):
    """Post-process the generated video."""
    # Example post-processing:
    # - Download video
    # - Generate thumbnails
    # - Add watermark
    # - Upload to CDN

    # For now, just use original URL
    job.processed_url = job.video_url

    engine.transition(job, WorkflowState.COMPLETED)

# Build workflow
async def create_workflow() -> WorkflowEngine:
    engine = WorkflowEngine()

    engine.register_handler(WorkflowState.CREATED, validate_handler)
    engine.register_handler(WorkflowState.VALIDATED, queue_handler)
    engine.register_handler(WorkflowState.GENERATING, generate_handler)
    engine.register_handler(WorkflowState.POST_PROCESSING, post_process_handler)

    def on_transition(job, old_state, new_state):
        print(f"[{job.id}] {old_state.value} -> {new_state.value}")

    engine.on_transition = on_transition

    return engine

# Usage
async def main():
    engine = await create_workflow()

    job = WorkflowJob(
        id="workflow_001",
        prompt="A beautiful sunset over a calm ocean with gentle waves",
        params={"duration": 5, "model": "kling-v1.5"}
    )

    result = await engine.process(job)

    if result.state == WorkflowState.COMPLETED:
        print(f"Success! Video: {result.processed_url}")
    else:
        print(f"Failed: {result.error}")

asyncio.run(main())
```
