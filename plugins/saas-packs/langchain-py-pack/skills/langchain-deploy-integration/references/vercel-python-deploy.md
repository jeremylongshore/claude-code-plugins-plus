# Vercel Python Deploy Reference

Vercel's Python runtime has three gotchas that catch every LangChain deploy:
the 10-second default timeout (P35), the Edge Runtime mirage (you cannot use
it), and the `requirements.txt` build step (Vercel does not read `pyproject.toml`).

## `vercel.json` schema

```json
{
  "functions": {
    "api/chat.py": {
      "maxDuration": 60,
      "memory": 1024,
      "runtime": "python3.12"
    },
    "api/embed.py": {
      "maxDuration": 300,
      "memory": 3008
    }
  },
  "headers": [
    {
      "source": "/api/chat/stream",
      "headers": [
        { "key": "X-Accel-Buffering", "value": "no" },
        { "key": "Cache-Control", "value": "no-cache, no-transform" }
      ]
    }
  ]
}
```

## `maxDuration` per plan tier

| Plan | Max | Default |
|------|-----|---------|
| **Hobby** | 10s | 10s |
| **Pro** | 60s | 10s |
| **Enterprise** | 900s | 10s |

The default is always 10s regardless of plan tier. Set `maxDuration`
explicitly or watch `FUNCTION_INVOCATION_TIMEOUT` in your logs.

## Streaming as the mitigation when `maxDuration` is not enough

Even on Enterprise's 900s cap, a runaway agent can hit it. Streaming does two
things:

1. **Time-to-first-byte under 1 second** — the Vercel proxy considers the
   request alive as soon as the first chunk ships; long completions no longer
   trigger the stall detector.
2. **User sees partial output** — when the cap finally triggers, the client
   has already rendered 80% of the answer; the UX degrades gracefully.

```python
# api/chat.py
from fastapi import FastAPI
from fastapi.responses import StreamingResponse
from app.chain import build_chain

app = FastAPI()
chain = build_chain()  # module-level so warm invocations reuse it

@app.post("/api/chat")
async def chat(payload: dict):
    async def gen():
        async for chunk in chain.astream(payload["input"]):
            yield f"data: {chunk.model_dump_json()}\n\n"
        yield "data: [DONE]\n\n"
    return StreamingResponse(
        gen(),
        media_type="text/event-stream",
        headers={"X-Accel-Buffering": "no", "Cache-Control": "no-cache"},
    )
```

## Edge Runtime: not an option for LangChain

Vercel's Edge Runtime runs on V8 / workerd and does **not** support Python —
the `@vercel/edge` runtime is for TypeScript / JavaScript only. Anything that
imports `langchain`, `langgraph`, `openai`, or `anthropic` must run on
`@vercel/python` (serverless, Node.js-free Python container).

If you need edge-like cold start, look at Vercel's Fluid Compute (beta) or
move to Cloud Run with `--min-instances=1`.

## Cold start profile

Vercel Python cold start is usually 2-5 seconds for a LangChain app. The
dominant costs are:

- `import langchain_core` / `langchain_anthropic` / `langchain_openai` — ~1.5s
- `import tiktoken` (forces BPE merge table load) — ~0.8s
- `import langgraph` — ~0.4s
- Any embedding model instantiation (even lazy) — ~1-3s

Defer `tiktoken` and embedding model loading to request time when possible —
serverless only pays the import cost on cold start, but a deferred import
lets you warm critical paths first.

```python
# at module level: cheap imports only
from fastapi import FastAPI
from langchain_core.messages import HumanMessage

app = FastAPI()

# deferred: don't import at cold-start time
_chain = None
def get_chain():
    global _chain
    if _chain is None:
        from app.chain import build_chain  # 1.5s import deferred
        _chain = build_chain()
    return _chain
```

## `requirements.txt` build step

Vercel's Python runtime reads `requirements.txt`, not `pyproject.toml`.
If you use `uv` or `poetry`, add a build step:

```json
{
  "buildCommand": "pip install uv && uv export --format requirements-txt --no-hashes > requirements.txt"
}
```

Alternative: commit `requirements.txt` and gate it in CI to match `uv.lock`.

## Vercel Secrets vs env vars

Two ways to pass secrets:

**Environment variables** (`vercel env add`):
```bash
vercel env add ANTHROPIC_API_KEY production
# enter value when prompted
```
Stored encrypted at rest, exposed as `os.environ["ANTHROPIC_API_KEY"]` at runtime.

**Vercel Secrets** (legacy, deprecated for new projects):
Older alias system. Use env vars for new projects — simpler and equivalent.

Never commit `.env` and add `.env*` to `.vercelignore`:
```
.env
.env.*
!.env.example
```

## Memory tiers

| Memory | Use case | Cost multiplier |
|--------|----------|-----------------|
| 128-512 MB | Tiny agents, no local embedding | 1x |
| 1024 MB | Standard LangChain app | 2x |
| 3008 MB | In-process FAISS / Chroma / embedding | 6x |

Memory and CPU scale together on Vercel — a 3008 MB function has more CPU
than a 128 MB one. If cold start matters, pay for more memory.

## Serverless vs Fluid Compute

Vercel's Fluid Compute (beta as of late 2026) runs long-lived Python workers
that handle multiple requests. It fixes the cold-start problem but is
pre-GA; production deploys should stick to standard serverless and use
`--min-instances=1` on Cloud Run if cold start is the blocker.

## Common failure modes

| Symptom | Cause | Fix |
|---------|-------|-----|
| `FUNCTION_INVOCATION_TIMEOUT` | 10s default (P35) | Set `maxDuration: 60` |
| `500 Module not found` | Missing `requirements.txt` | Add build step or commit file |
| `MemoryError` or OOM kill | 1024 MB not enough for embedding | Bump to 3008 MB |
| Stream truncates mid-response | Proxy buffering | Add `X-Accel-Buffering: no` header |
| `.env` values in prod | Committed to repo | Add `.env*` to `.vercelignore` |
