# Microservice Architecture

## Microservice Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│                           Load Balancer                              │
│                         (nginx / ALB)                                │
└───────────────────────────┬─────────────────────────────────────────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
│   API GW    │      │   API GW    │      │   API GW    │
│  (replica)  │      │  (replica)  │      │  (replica)  │
└──────┬──────┘      └──────┬──────┘      └──────┬──────┘
       │                    │                    │
       └────────────────────┼────────────────────┘
                            │
                    ┌───────┴───────┐
                    │ Message Queue │
                    │   (Redis)     │
                    └───────┬───────┘
                            │
       ┌────────────────────┼────────────────────┐
       │                    │                    │
┌──────┴──────┐      ┌──────┴──────┐      ┌──────┴──────┐
│   Worker    │      │   Worker    │      │   Worker    │
│ (OpenRouter)│      │ (OpenRouter)│      │ (OpenRouter)│
└─────────────┘      └─────────────┘      └─────────────┘
```

### Worker Service

```python
# worker.py
from celery import Celery
from openrouter_service import OpenRouterService, OpenRouterConfig

app = Celery('llm_worker', broker=os.environ["REDIS_URL"])

config = OpenRouterConfig(
    api_key=os.environ["OPENROUTER_API_KEY"],
    default_model="anthropic/claude-3.5-sonnet"
)
service = OpenRouterService(config)

@app.task(bind=True, max_retries=3)
def process_llm_request(self, prompt: str, model: str = None, **kwargs):
    try:
        return service.chat(prompt, model=model, **kwargs)
    except Exception as e:
        self.retry(countdown=2 ** self.request.retries)

@app.task
def process_batch(prompts: list, model: str = None):
    results = []
    for prompt in prompts:
        try:
            result = service.chat(prompt, model=model)
            results.append({"prompt": prompt, "result": result, "success": True})
        except Exception as e:
            results.append({"prompt": prompt, "error": str(e), "success": False})
    return results
```

### API Gateway

```python
# api.py
from fastapi import FastAPI, BackgroundTasks, HTTPException
from pydantic import BaseModel
from celery.result import AsyncResult
from worker import process_llm_request, process_batch

app = FastAPI()

class ChatRequest(BaseModel):
    prompt: str
    model: str = None
    async_mode: bool = False

class BatchRequest(BaseModel):
    prompts: list[str]
    model: str = None

@app.post("/chat")
async def chat(request: ChatRequest):
    if request.async_mode:
        # Async processing
        task = process_llm_request.delay(request.prompt, request.model)
        return {"task_id": task.id}
    else:
        # Sync processing
        result = process_llm_request(request.prompt, request.model)
        return {"result": result}

@app.post("/batch")
async def batch(request: BatchRequest):
    task = process_batch.delay(request.prompts, request.model)
    return {"task_id": task.id}

@app.get("/task/{task_id}")
async def get_task_result(task_id: str):
    result = AsyncResult(task_id)
    if result.ready():
        return {"status": "complete", "result": result.get()}
    return {"status": "pending"}
```
